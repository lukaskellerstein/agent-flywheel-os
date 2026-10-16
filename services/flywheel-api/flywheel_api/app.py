"""The HTTP routes (spec 02 section 9, question 2, as decision 16 took it).

    GET  /healthz
    GET  /api/usecases
    GET  /api/usecases/{name}
    GET  /api/usecases/{name}/versions/{n}
    POST /api/usecases/{name}/imports    an upload (multipart, field `file`: one
                                         .tar.gz or .zip of the use case folder)
                                         or JSON {"git": {"url", "ref", "path"}}

An import answers 201 with the new version, 200 "unchanged" with the current
one, or 422 with every problem by file and field. No delete.
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from fastapi import Path as PathParam
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, ValidationError, model_validator
from starlette.concurrency import run_in_threadpool
from starlette.datastructures import UploadFile

from . import sources
from .problems import BadRequest, ImportRefused, NotFound, TooLarge
from .registry import Registry, check_name

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


def create_app(registry: Registry, *, allow_file_urls: bool = False) -> FastAPI:
    """*allow_file_urls* lets a git import read a `file://` repository; only the tests set it."""
    app = FastAPI(title="Agent Flywheel API")
    _add_error_handlers(app)

    @app.get("/healthz")
    def healthz() -> dict:
        return {"status": "ok"}

    @app.get("/api/usecases")
    def usecase_list() -> list[dict]:
        return registry.list()

    @app.get("/api/usecases/{name}")
    def usecase(name: str) -> dict:
        return registry.get(name)

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

    return app


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
