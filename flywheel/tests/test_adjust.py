import pytest
from conftest import DEFINITION, change

from flywheel_loop import FlywheelError
from flywheel_loop.adjust import Adjuster, Words, change_lines, read_change, take_adjusted, task_text
from flywheel_loop.brain import write

WORDS = Words.of(DEFINITION)  # max_skills 1


def test_only_brain_files_the_adjuster_changed_are_taken(tmp_path):
    before = {"AGENTS.md": "old"}
    folder = write({"AGENTS.md": "new", "notes.txt": "not a brain file"}, tmp_path / "brain")
    assert take_adjusted(folder, before, WORDS) == {"AGENTS.md": "new"}


def test_a_skill_gets_its_frontmatter_and_a_second_one_is_dropped(tmp_path):
    folder = write(
        {
            ".agents/skills/ask-version/SKILL.md": "Ask for the version first.",
            ".agents/skills/zzz-extra/SKILL.md": "One skill too many.",
        },
        tmp_path / "brain",
    )
    updates = take_adjusted(folder, {}, WORDS)
    assert list(updates) == [".agents/skills/ask-version/SKILL.md"]
    assert updates[".agents/skills/ask-version/SKILL.md"].startswith(
        "---\nname: ask-version\ndescription: Use for tickets that need the ask version procedure.\n---\n\nAsk"
    )


def test_a_skill_with_its_own_frontmatter_stays_as_written(tmp_path):
    text = "---\nname: sev1\ndescription: Use when production is down.\n---\n\nPage on-call."
    folder = write({".agents/skills/sev1/SKILL.md": text}, tmp_path / "brain")
    assert take_adjusted(folder, {}, WORDS) == {".agents/skills/sev1/SKILL.md": text}


def test_an_emptied_brain_file_stops_the_step(tmp_path):
    folder = write({"AGENTS.md": "  "}, tmp_path / "brain")
    with pytest.raises(FlywheelError, match="left AGENTS.md empty"):
        take_adjusted(folder, {"AGENTS.md": "old"}, WORDS)


def test_the_change_comes_from_change_md_else_from_the_last_message(tmp_path):
    path = tmp_path / "change.md"
    path.write_text("**Hypothesis:** cites are missing\n")
    assert read_change(path, "Change: AGENTS.md now asks to cite") == ("cites are missing", "AGENTS.md now asks to cite")
    assert read_change(tmp_path / "none.md", "") == ("not written", "not written")


def test_a_change_line_goes_on_over_its_list():
    text = "Hypothesis: two causes\nChange:\n- AGENTS.md: cite\n- skill sev1: page\nThe end."
    assert change_lines(text) == {"hypothesis": "two causes", "change": "AGENTS.md: cite skill sev1: page"}


def test_the_task_names_the_use_cases_role_causes_and_what_is_hidden():
    text = task_text(WORDS, 2, 1)
    assert text.startswith("Adjust step 2: improve a support agent. `brain/` holds brain v1")
    assert "A case is a ticket here." in text and "up to 1 skills" in text
    assert "Group the failures by cause: missing citation." in text and "The policy is hidden." in text


def test_the_workspace_and_the_opencode_call(opencode, tmp_path):
    script = opencode({"files": {"AGENTS.md": "Cite."}, "change": change("h", "c")})
    adjuster = Adjuster("enmaas-glm-5-3", "http://gateway:4000/", 30, opencode=str(script))
    done = adjuster.adjust(tmp_path / "w", {"AGENTS.md": "Old."}, "# failures", "# history", WORDS, 1, 0)

    assert (done.updates, done.hypothesis, done.change) == ({"AGENTS.md": "Cite."}, "h", "c")
    assert done.metrics == {
        "adjuster/steps": 1, "adjuster/tool_calls": 1, "adjuster/tokens_in": 150,
        "adjuster/tokens_out": 20, "adjuster/cost_usd": 0.0, "adjuster/sessions": 1,
    }
    ws = tmp_path / "w" / "ws"
    assert (ws / ".opencode/agents/adjuster.md").read_text().startswith("---\ndescription: Adjuster")
    config = (ws / "opencode.json").read_text()
    assert '"baseURL": "{env:GATEWAY_URL}/v1"' in config and '"enmaas-glm-5-3"' in config
    assert sorted(p.name for p in (tmp_path / "w" / "logs").iterdir()) == [
        "change.md", "events.jsonl", "failures.md", "history.md", "opencode.stderr", "task.md", "transcript.md",
    ]


def test_an_opencode_failure_stops_the_step(opencode, tmp_path):
    script = opencode({"exit": 3})
    adjuster = Adjuster("enmaas-glm-5-3", "http://gateway:4000", 30, opencode=str(script))
    with pytest.raises(FlywheelError, match="opencode exited with 3"):
        adjuster.adjust(tmp_path / "w", {}, "", "", WORDS, 1, 0)
