import pytest
from conftest import DEFINITION, change

from flywheel_loop import FlywheelError


def test_a_better_brain_is_kept_and_a_worse_one_reverted(opencode, make_training, mlflow):
    script = opencode(
        {"files": {"AGENTS.md": "Cite the articles. score: 0.8"}, "change": change("no citations", "AGENTS.md: cite")},
        {"files": {"AGENTS.md": "Be brief. score: 0.6"}, "change": change("too long", "AGENTS.md: brief")},
    )
    training, api = make_training(script)
    best = training.run()

    assert (best.number, best.train, best.validation) == (1, 0.8, 0.7)
    assert [it.decision for it in training.iterations] == ["baseline", "kept", "reverted"]
    # v0 runs bare; each later brain is scored from its own run's brain/ folder, on both splits.
    assert [(s["split"], s["brain"]) for s in api.starts[:2]] == [("train", None), ("validation", None)]
    v1 = mlflow.by_name("tr-1 v1")
    v1_id = next(run_id for run_id, run in mlflow.runs.items() if run is v1)
    assert {s["brain"] for s in api.starts[2:4]} == {f"runs:/{v1_id}/brain"}
    assert all(s["training"] == "tr-1" and s["version"] == 1 for s in api.starts)


def test_the_mlflow_records_of_a_training_run(opencode, make_training, mlflow):
    script = opencode(
        {"files": {"AGENTS.md": "score: 0.8"}, "change": change("no citations", "AGENTS.md: cite")},
        {"files": {"AGENTS.md": "score: 0.6"}, "change": change("too long", "AGENTS.md: brief")},
    )
    training, _ = make_training(script)
    training.run()

    parent = mlflow.by_name("training tr-1")
    assert mlflow.experiment_name == "agent-flywheel-support"
    assert parent["status"] == "FINISHED"
    assert {k: parent["tags"][k] for k in ("kind", "usecase", "usecase_version", "usecase_hash")} == {
        "kind": "training", "usecase": "support", "usecase_version": "1", "usecase_hash": "abc123",
    }
    assert parent["metrics"] == {"best/iteration": 1, "best/train/score": 0.8, "best/validation/score": 0.7}
    assert parent["files"] == {"brain/AGENTS.md": "score: 0.8"}
    assert parent["params"]["adjuster_model"] == "enmaas-glm-5-3"

    v0, v1, v2 = (mlflow.by_name(f"tr-1 v{n}") for n in range(3))
    assert all(run["tags"]["mlflow.parentRunId"] == next(i for i, r in mlflow.runs.items() if r is parent) for run in (v0, v1, v2))
    assert [run["tags"]["decision"] for run in (v0, v1, v2)] == ["baseline", "kept", "reverted"]
    assert v0["files"] == {}
    assert v1["metrics"]["train/score"] == 0.8 and v1["metrics"]["validation/score"] == 0.7
    assert v1["metrics"]["train/must_mention"] == 0.5 and v1["metrics"]["adjuster/tool_calls"] == 1
    assert v1["tags"]["adjuster_hypothesis"] == "no citations" and v1["tags"]["adjusted_files"] == "AGENTS.md"
    assert v1["tags"]["train_evaluation"] == "job3" and v1["tags"]["train_mlflow_run"] == "ml-job3"
    assert {"adjuster/failures.md", "adjuster/history.md", "adjuster/task.md", "adjuster/change.md", "adjuster/transcript.md"} <= set(v1["files"])
    # Step 2 starts from v1, the best: its report is v1's train failures, its history knows v1 was kept.
    assert "# Eval failures of brain v1" in v2["files"]["adjuster/failures.md"]
    assert "answer of t1 in job3" in v2["files"]["adjuster/failures.md"]
    assert "| v1 | v0 | AGENTS.md | 0.800 | +0.300 | kept |" in v2["files"]["adjuster/history.md"]
    assert "validation" not in v2["files"]["adjuster/history.md"].lower()


def test_a_step_with_no_change_is_retried_then_counts_as_a_miss(opencode, make_training, mlflow):
    script = opencode({}, {}, {}, {})
    training, api = make_training(script, iterations=3, patience=2)
    best = training.run()

    assert best.number == 0
    assert [it.decision for it in training.iterations] == ["baseline", "no change", "no change"]
    assert len(api.starts) == 2  # only v0 was scored
    assert mlflow.by_name("training tr-1")["tags"]["stop_reason"] == "2 steps in a row brought no better brain"
    assert "Your first session on this step ended without a change" in opencode.tasks()
    assert "adjuster/session-1/transcript.md" in mlflow.by_name("tr-1 v1")["files"]


def test_a_failed_evaluation_fails_the_training_run(opencode, make_training, mlflow):
    training, api = make_training(opencode())
    api.fail_split = "validation"
    with pytest.raises(FlywheelError, match="ended failed"):
        training.run()
    parent = mlflow.by_name("training tr-1")
    assert parent["status"] == "FAILED"
    assert "the pod died" in parent["tags"]["error"]


def test_a_use_case_without_an_adjuster_cannot_be_trained(opencode, make_training, mlflow):
    definition = {key: value for key, value in DEFINITION.items() if key != "adjuster"}
    training, api = make_training(opencode(), definition=definition)
    with pytest.raises(FlywheelError, match="no adjuster: block"):
        training.run()
    assert (mlflow.runs, api.starts) == ({}, [])
