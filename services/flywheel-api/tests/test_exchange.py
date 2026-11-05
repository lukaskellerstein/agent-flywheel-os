"""exchange.py: one task's files of the harness's run folder, as the page shows them."""

from flywheel_api.exchange import MAX_TEXT, answer_file, output_paths, steps_of


def test_a_long_answer_is_cut_and_a_binary_one_has_no_text():
    long = answer_file("output/answer.md", b"a" * (MAX_TEXT + 1))
    assert (long["size"], len(long["text"]), long["truncated"]) == (MAX_TEXT + 1, MAX_TEXT, True)
    assert answer_file("output/screen.png", b"\x89PNG\r\n\x1a\n\xff") == {
        "path": "output/screen.png",
        "size": 9,
        "text": None,
        "truncated": False,
    }


def test_only_relative_output_paths_are_read():
    config = {"outputs": [{"path": "output/"}, {"path": "../etc"}, {"path": "/"}, {"schema": "x"}, "answer.md"]}
    assert output_paths(config) == ["output"]
    assert output_paths({}) == []


def test_a_long_tool_input_is_cut_and_an_unknown_one_is_its_json():
    events = [
        {"type": "assistant", "tools": [{"name": "Bash", "id": "1", "input": {"command": "x" * 500}}]},
        {"type": "assistant", "tools": [{"name": "WebSearch", "id": "2", "input": {"q": "proxy"}}]},
        "not an event",
    ]
    long, unknown = steps_of(events, "t")
    assert (len(long["input"]), long["input"][-1]) == (401, "…")
    assert unknown["input"] == '{"q": "proxy"}'
