"""Versions: one per content change, never overwritten, each with its diff."""

from __future__ import annotations

import pytest
import yaml
from helpers import FIXTURE, tar_gz, write_folder, zip_bytes

from flywheel_api.files import read_folder
from flywheel_api.problems import BadRequest, ImportRefused, NotFound
from flywheel_api.sources import from_archive
from flywheel_api.versions import content_hash

UPLOAD = {"type": "upload", "file": "sample.tar.gz"}
NO_CHANGE = {"added": [], "removed": [], "changed": []}


def edit_task(files, path, **input_changes):
    data = yaml.safe_load(files[path])
    data["input"].update(input_changes)
    files[path] = yaml.safe_dump(data).encode()


def test_the_first_import_is_version_1(registry, files):
    result = registry.import_files("sample", files, UPLOAD)
    assert result.status == "created"
    record = result.version
    assert record["number"] == 1
    assert record["hash"] == content_hash(files)
    assert record["source"] == UPLOAD
    assert record["task_count"] == 3
    assert record["tasks_per_split"] == {"train": 1, "validation": 1}
    assert record["diff"]["from"] is None
    assert record["diff"]["tasks"]["added"] == ["export-data", "pricing", "reset-password"]
    assert "eval.yaml" in record["diff"]["files"]["added"]


def test_the_same_import_again_is_unchanged(registry, files):
    first = registry.import_files("sample", files, UPLOAD)
    again = registry.import_files("sample", dict(files), {"type": "upload", "file": "again.zip"})
    assert again.status == "unchanged"
    assert again.version == first.version
    assert registry.get("sample")["current"] == 1
    assert registry.store.keys("usecases/sample/versions/2/") == []


def test_a_changed_task_is_version_2_and_version_1_stays_readable(registry, files):
    registry.import_files("sample", files, UPLOAD)
    edit_task(files, "tasks/pricing.yaml", question="Is the Console free for five people?")
    result = registry.import_files("sample", files, UPLOAD)
    assert result.status == "created"
    assert result.version["number"] == 2
    assert result.version["diff"] == {"from": 1, "tasks": {**NO_CHANGE, "changed": ["pricing"]}, "files": NO_CHANGE}
    entry = registry.get("sample")
    assert entry["current"] == 2
    assert [v["number"] for v in entry["versions"]] == [1, 2]
    old = {t["id"]: t for t in registry.version("sample", 1)["tasks"]}
    new = {t["id"]: t for t in registry.version("sample", 2)["tasks"]}
    assert old["pricing"]["input"]["question"] == "Is the Console free for small teams?"
    assert new["pricing"]["input"]["question"] == "Is the Console free for five people?"


def test_added_and_removed_tasks_are_in_the_diff(registry, files):
    registry.import_files("sample", files, UPLOAD)
    files["tasks/refund.yaml"] = files.pop("tasks/pricing.yaml")
    diff = registry.import_files("sample", files, UPLOAD).version["diff"]
    assert diff["tasks"] == {"added": ["refund"], "removed": ["pricing"], "changed": []}


def test_a_task_files_bytes_change_the_task(registry, files):
    registry.import_files("sample", files, UPLOAD)
    files["tasks/export-data/screen.txt"] = b"[Reports] [Export: disabled, 20000 rows selected]\n"
    diff = registry.import_files("sample", files, UPLOAD).version["diff"]
    assert diff == {"from": 1, "tasks": {**NO_CHANGE, "changed": ["export-data"]}, "files": NO_CHANGE}


def test_a_judge_change_is_a_version_whose_diff_names_the_file(registry, files):
    registry.import_files("sample", files, UPLOAD)
    files["eval.yaml"] += b"\nthresholds:\n  must_mention: 0.9\n"
    files["resources/kb/003-billing.md"] = b"# KB-003\n"
    diff = registry.import_files("sample", files, UPLOAD).version["diff"]
    assert diff["tasks"] == NO_CHANGE
    assert diff["files"] == {"added": ["resources/kb/003-billing.md"], "removed": [], "changed": ["eval.yaml"]}


def test_a_version_shows_its_tasks_judges_and_files(registry, files):
    registry.import_files("sample", files, UPLOAD)
    version = registry.version("sample", 1)
    assert version["usecase"]["title"] == "Product questions"
    assert version["usecase"]["task"] == {"label": "question", "prompt": "question", "show": ["product"]}
    assert [j["name"] for j in version["judges"]] == ["must_mention", "style"]
    assert version["tasks"][0]["files"] == ["screen.txt"]
    assert "hidden/style.md" in version["files"]
    assert "version.json" not in version["files"]


def test_a_refused_import_writes_nothing(registry, files):
    files["tasks/pricing.yaml"] = b"input: [\n"
    with pytest.raises(ImportRefused):
        registry.import_files("sample", files, UPLOAD)
    assert registry.store.keys("usecases/") == []


def test_a_refused_import_leaves_the_current_version(registry, files):
    registry.import_files("sample", files, UPLOAD)
    files.pop("eval.yaml")
    with pytest.raises(ImportRefused):
        registry.import_files("sample", files, UPLOAD)
    assert registry.get("sample")["current"] == 1
    assert registry.store.keys("usecases/sample/versions/2/") == []


def test_what_an_interrupted_import_left_is_not_part_of_the_next_version(registry, files):
    registry.import_files("sample", files, UPLOAD)
    registry.store.put("usecases/sample/versions/2/tasks/stray.yaml", b"input: {question: q}\n")
    edit_task(files, "tasks/pricing.yaml", question="Changed?")
    registry.import_files("sample", files, UPLOAD)
    assert "tasks/stray.yaml" not in registry.version("sample", 2)["files"]


def test_a_version_is_never_overwritten(registry, files):
    registry.import_files("sample", files, UPLOAD)
    registry.store.put("usecases/sample/versions/2/version.json", b"{}")
    edit_task(files, "tasks/pricing.yaml", question="Changed?")
    with pytest.raises(RuntimeError, match="is a version already"):
        registry.import_files("sample", files, UPLOAD)
    assert registry.store.get("usecases/sample/versions/2/version.json") == b"{}"


def test_unknown_names_and_versions(registry, files):
    registry.import_files("sample", files, UPLOAD)
    with pytest.raises(NotFound):
        registry.get("other")
    with pytest.raises(NotFound):
        registry.version("sample", 2)
    with pytest.raises(NotFound):
        registry.get("../sample")
    with pytest.raises(BadRequest):
        registry.import_files("Sample_1", files, UPLOAD)


def test_the_list_holds_every_use_case(registry, files):
    registry.import_files("sample", files, UPLOAD)
    registry.import_files("sample-two", files, UPLOAD)
    entries = registry.list()
    assert [e["name"] for e in entries] == ["sample", "sample-two"]
    assert entries[0]["title"] == "Product questions"
    assert entries[0]["versions"][0]["task_count"] == 3


@pytest.mark.parametrize(
    "archive",
    [tar_gz, lambda f: tar_gz(f, top="sample/"), zip_bytes, lambda f: zip_bytes(f, top="sample/")],
    ids=["tar.gz", "tar.gz with its folder", "zip", "zip with its folder"],
)
def test_an_archive_and_the_folder_give_one_hash(registry, files, archive):
    fetched = from_archive("sample", archive(files))
    assert fetched.files == files
    assert content_hash(fetched.files) == content_hash(files)
    registry.import_files("sample", files, UPLOAD)
    assert registry.import_files("sample", fetched.files, fetched.source).status == "unchanged"


def test_the_hash_depends_on_paths_and_bytes_only(files):
    renamed = {("tasks/renamed.yaml" if p == "tasks/pricing.yaml" else p): d for p, d in files.items()}
    assert content_hash(renamed) != content_hash(files)
    assert content_hash({**files, "hidden/style.md": files["hidden/style.md"] + b" "}) != content_hash(files)
    assert content_hash(dict(reversed(list(files.items())))) == content_hash(files)


def test_a_folder_on_disk_reads_as_its_files(files, tmp_path):
    assert read_folder(write_folder(files, tmp_path / "copy")) == read_folder(FIXTURE)
