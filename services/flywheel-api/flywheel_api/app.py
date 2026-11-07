"""The HTTP routes (spec 02 section 9, question 2, as decision 16 took it).

    GET  /healthz
    GET  /api/usecases
    GET  /api/usecases/{name}
    GET  /api/models                         the models the gateway routes
    GET  /api/agents                         AI hub › Agents
    GET  /api/agents/{name}
    POST /api/agents                         JSON, one agent (agents.py)
    GET  /api/usecases/{name}/versions       every version's record, newest first
    GET  /api/usecases/{name}/versions/{n}
    POST /api/usecases/{name}/imports    an upload (multipart, field `file`: one
                                         .tar.gz or .zip of the use case folder)
                                         or JSON {"git": {"url", "ref", "path"}}
    POST /api/usecases/{name}/evaluations      JSON {"version", "split", "agent", "model",
                                               "brain", "training"}, each optional: an EvalHub job
    GET  /api/usecases/{name}/evaluations      the use case's jobs, newest first
    GET  /api/usecases/{name}/evaluations/{id} one job: judges, tasks, threshold verdicts
    DELETE /api/usecases/{name}/evaluations/{id} stop it; ?delete=true removes it
    GET  /api/usecases/{name}/evaluations/{id}/logs its pod logs, as text
    GET  /api/usecases/{name}/evaluations/{id}/tasks/{task_id}
                                             one task: its answer, steps and cost (exchange.py)
    GET  /api/usecases/{name}/versions/{n}/tasks/{id}/results
                                               every run of the version that
                                               scored the task, its verdicts
    GET  /api/usecases/{name}/trainings        the use case's training runs (trainings.py)
    GET  /api/usecases/{name}/trainings/{id}   one run with every brain it made
    GET  /api/usecases/{name}/trainings/{id}/brains/{n}
                                               one brain's files and its adjuster's reports

An import answers 201 with the new version, 200 "unchanged" with the current
one, or 422 with every problem by file and field. A use case and its versions
have no delete. The evaluation
routes exist when EvalHub is configured (evaluations.py), and run as their
caller: they need its Bearer token, which the dashboard module's BFF sends.
"""

from __future__ import annotations

from fastapi import Body, FastAPI, HTTPException, Request
from fastapi import Path as PathParam
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel, ConfigDict, ValidationError, model_validator
from starlette.concurrency import run_in_threadpool
from starlette.datastructures import UploadFile

from . import sources
from .agents import Agents
from .evaluations import Evaluations, StartRequest
from .problems import BadRequest, ImportRefused, NotFound, TooLarge, Unauthorized
from .registry import Registry, check_name
from .remote import RemoteError
from .trainings import Trainings

MAX_UPLOAD_BYTES = 100 * 1024 * 1024
MAX_JSON_BYTES = 64 * 1024


class GitImport(BaseModel):
    model_config = ConfigDict(extra="forbid")
    url: str
    ref: str | None = None  # a branch or a tag; the default branch when left out
    path: str = "."  # the use case folder inside the repository


class ImportRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    git: GitImport | None = None
    hf: dict | None = None  # phase 4: dataset, revision, mapping

    @model_validator(mode="after")
    def one_source(self) -> ImportRequest:
        if (self.git is None) == (self.hf is None):
            raise ValueError("give exactly one of git and hf")
        return self


def create_app(
    registry: Registry,
    evaluations: Evaluations | None = None,
    agents: Agents | None = None,
    *,
    allow_file_urls: bool = False,
) -> FastAPI:
    """*allow_file_urls* lets a git import read a `file://` repository; only the tests set it."""
    app = FastAPI(title="Agent Flywheel API")
    _add_error_handlers(app)
    _add_registry_routes(app, registry, allow_file_urls)
    if agents is not None:
        _add_hub_routes(app, agents)
    if evaluations is not None:
        _add_evaluation_routes(app, evaluations)
    return app


def _add_registry_routes(app: FastAPI, registry: Registry, allow_file_urls: bool) -> None:

    @app.get("/healthz")
    def healthz() -> dict:
        return {"status": "ok"}

    @app.get("/api/usecases")
    def usecase_list() -> list[dict]:
        return registry.list()

    @app.get("/api/usecases/{name}")
    def usecase(name: str) -> dict:
        return registry.get(name)

    @app.get("/api/usecases/{name}/versions")
    def version_list(name: str) -> list[dict]:
        """Every version's record, newest first: hash, source, time, tasks per split, diff."""
        return registry.records(name)

    @app.get("/api/usecases/{name}/versions/{number}")
    def version(name: str, number: int = PathParam(ge=1)) -> dict:
        """The version's record, definition, tasks, judges, diff to the version before, and file list."""
        return registry.version(name, number)

    @app.post("/api/usecases/{name}/imports")
    async def import_usecase(name: str, request: Request) -> JSONResponse:
        check_name(name)
        fetched = await _fetch(request, allow_file_urls)
        result = await run_in_threadpool(registry.import_files, name, fetched.files, fetched.source)
        status = 201 if result.status == "created" else 200
        return JSONResponse({"status": result.status, "version": result.version}, status_code=status)


def _add_hub_routes(app: FastAPI, agents: Agents) -> None:
    """AI hub › Agents and Models: the agents in the store, the models the gateway routes."""

    @app.get("/api/models")
    def model_list() -> list[dict]:
        used_by: dict[str, list[str]] = {}
        for agent in agents.list():
            for model in agent["models"]:
                used_by.setdefault(model, []).append(agent["name"])
        return [{**model, "used_by": used_by.get(model["name"], [])} for model in agents.gateway.models()]

    @app.get("/api/agents")
    def agent_list() -> list[dict]:
        return agents.list()

    @app.get("/api/agents/{name}")
    def agent(name: str) -> dict:
        return agents.get(name)

    @app.post("/api/agents", status_code=201)
    def add_agent(body: dict = Body()) -> dict:
        return agents.add(body)


def _add_evaluation_routes(app: FastAPI, evaluations: Evaluations) -> None:
    # Plain functions: FastAPI runs them in its thread pool, where the calls to EvalHub block.
    @app.post("/api/usecases/{name}/evaluations", status_code=201)
    def start_evaluation(name: str, request: Request, body: StartRequest | None = None) -> dict:
        return evaluations.start(name, body or StartRequest(), _token(request))

    @app.get("/api/usecases/{name}/evaluations")
    def evaluation_list(name: str, request: Request) -> list[dict]:
        return evaluations.list(name, _token(request))

    @app.get("/api/usecases/{name}/evaluations/{job_id}")
    def evaluation(name: str, job_id: str, request: Request) -> dict:
        return evaluations.get(name, job_id, _token(request))

    @app.get("/api/usecases/{name}/versions/{number}/tasks/{task_id}/results")
    def task_results(name: str, task_id: str, request: Request, number: int = PathParam(ge=1)) -> list[dict]:
        """Every run of the version that scored the task, with the task's reward and verdicts."""
        return evaluations.task_results(name, number, task_id, _token(request))

    @app.delete("/api/usecases/{name}/evaluations/{job_id}", status_code=204)
    def stop_evaluation(name: str, job_id: str, request: Request, delete: bool = False) -> None:
        """Stop the job; with ?delete=true remove it from EvalHub too."""
        evaluations.stop(name, job_id, _token(request), delete=delete)

    @app.get("/api/usecases/{name}/evaluations/{job_id}/tasks/{task_id}")
    def evaluation_task(name: str, job_id: str, task_id: str, request: Request) -> dict:
        """One task of the job: verdicts, the agent's answer, its steps and its cost."""
        return evaluations.task(name, job_id, task_id, _token(request))

    @app.get("/api/usecases/{name}/evaluations/{job_id}/logs", response_class=PlainTextResponse)
    def evaluation_logs(name: str, job_id: str, request: Request) -> str:
        return evaluations.logs(name, job_id, _token(request))

    trainings = Trainings(evaluations.registry, evaluations.mlflow)

    @app.get("/api/usecases/{name}/trainings")
    def training_list(name: str, request: Request) -> list[dict]:
        return trainings.list(name, _token(request))

    @app.get("/api/usecases/{name}/trainings/{training}")
    def training(name: str, training: str, request: Request) -> dict:
        return trainings.get(name, training, _token(request))

    @app.get("/api/usecases/{name}/trainings/{training}/brains/{number}")
    def training_brain(name: str, training: str, request: Request, number: int = PathParam(ge=0)) -> dict:
        """One brain's files and the adjuster's reports of the step that made it."""
        return trainings.brain(name, training, number, _token(request))


def _token(request: Request) -> str:
    scheme, _, token = request.headers.get("authorization", "").partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise Unauthorized("an evaluation runs as its caller: send its Bearer token")
    return token.strip()


async def _fetch(request: Request, allow_file_urls: bool) -> sources.Fetched:
    media = request.headers.get("content-type", "").split(";")[0].strip().lower()
    if media == "application/json":
        _check_length(request, MAX_JSON_BYTES)
        git = _import_request(await request.body()).git
        if git is None:  # the request validates to exactly one source, so it is hf
            raise HTTPException(501, "a Hugging Face import comes with spec 02 phase 4")
        return await run_in_threadpool(sources.from_git, git.url, git.ref, git.path, allow_file_urls=allow_file_urls)
    if media == "multipart/form-data":
        _check_length(request, MAX_UPLOAD_BYTES)
        form = await request.form(max_files=1, max_fields=1)
        upload = form.get("file")
        if not isinstance(upload, UploadFile):
            raise BadRequest("a multipart import carries the archive in the field 'file'")
        data = await upload.read()
        return await run_in_threadpool(sources.from_archive, upload.filename or "upload", data)
    raise HTTPException(415, "an import is multipart/form-data (an archive) or application/json (git)")


def _import_request(body: bytes) -> ImportRequest:
    try:
        return ImportRequest.model_validate_json(body)
    except ValidationError as exc:
        reasons = "; ".join(f"{'.'.join(str(p) for p in e['loc']) or 'body'}: {e['msg']}" for e in exc.errors())
        raise BadRequest(reasons) from exc


def _check_length(request: Request, limit: int) -> None:
    """The body is refused on its Content-Length, before any of it is read."""
    length = request.headers.get("content-length")
    if length is None or not length.isdigit():
        raise BadRequest("an import needs a Content-Length")
    if int(length) > limit:
        raise TooLarge(f"this import is at most {limit} bytes")


def _add_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ImportRefused)
    def refused(_: Request, exc: ImportRefused) -> JSONResponse:
        body = {"status": "refused", "detail": str(exc), "errors": [p.as_dict() for p in exc.problems]}
        return JSONResponse(body, status_code=422)

    @app.exception_handler(BadRequest)
    def bad_request(_: Request, exc: BadRequest) -> JSONResponse:
        return JSONResponse({"detail": str(exc)}, status_code=exc.status)

    @app.exception_handler(NotFound)
    def not_found(_: Request, exc: NotFound) -> JSONResponse:
        return JSONResponse({"detail": str(exc.args[0])}, status_code=404)

    @app.exception_handler(RemoteError)
    def remote(_: Request, exc: RemoteError) -> JSONResponse:
        return JSONResponse({"detail": str(exc)}, status_code=exc.status)
