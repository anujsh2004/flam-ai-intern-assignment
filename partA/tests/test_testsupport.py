"""Fresh-clone behaviour: tests needing ungitted resources skip with an
instruction instead of failing (FLORES text is not committed, D-11)."""


def test_given_empty_prepared_dir_when_checked_then_reason_says_how_to_fix(tmp_path):
    from testsupport import missing_flores

    reason = missing_flores(tmp_path)
    assert reason is not None and "partA/corpus/prep.py" in reason


def test_given_all_eight_flores_files_when_checked_then_nothing_missing(tmp_path):
    from testsupport import FLORES_FILES, missing_flores

    assert len(FLORES_FILES) == 8
    for name in FLORES_FILES:
        (tmp_path / name).write_text("x\n", encoding="utf-8")
    assert missing_flores(tmp_path) is None


def test_given_one_flores_file_missing_when_checked_then_it_is_named(tmp_path):
    from testsupport import FLORES_FILES, missing_flores

    for name in FLORES_FILES[1:]:
        (tmp_path / name).write_text("x\n", encoding="utf-8")
    assert FLORES_FILES[0] in missing_flores(tmp_path)


def test_given_gated_llama_unavailable_when_checked_then_reason_says_how_to_get_access(monkeypatch):
    import fertility_v1 as v1

    from testsupport import missing_llama

    def denied(spec):
        raise OSError("You are trying to access a gated repo.")

    monkeypatch.setattr(v1, "load_tokenizer", denied)
    reason = missing_llama()
    assert "meta-llama/Llama-3.2-3B" in reason and "hf auth login" in reason


def test_given_tiktoken_failure_when_checked_then_gpt2_reason_is_returned(monkeypatch):
    import tiktoken

    from testsupport import missing_gpt2

    def boom(name):
        raise ConnectionError("offline")

    monkeypatch.setattr(tiktoken, "get_encoding", boom)
    assert "network" in missing_gpt2()
