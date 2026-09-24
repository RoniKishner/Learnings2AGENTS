from __future__ import annotations

from learnings2agents.cache import SynthesisCache
from learnings2agents.llm import LlmSynthesisError
from learnings2agents.models import DirGroup, Learning, SynthesizedBullet
from learnings2agents.synthesize import synthesize_all


def _group(path: str = "utilities") -> DirGroup:
    learning = Learning(
        text="Always do the thing.",
        repository="repo",
        file=f"{path}/foo.py" if path else "foo.py",
        pull_request="42",
        url="",
        created_by="x",
        usage=1,
    )
    return DirGroup(path=path, learnings=[learning])


class _FakeGeminiClient:
    def __init__(self, bullets=None, error: Exception | None = None):
        self.model = "fake-model"
        self._bullets = bullets
        self._error = error
        self.calls = 0

    def synthesize_directory(self, directory, learnings):
        self.calls += 1
        if self._error is not None:
            raise self._error
        return self._bullets


def test_synthesize_all_uses_heuristic_when_no_gemini_client():
    group = _group()
    synthesize_all([group], gemini_client=None, cache=None)
    assert group.mode_used == "heuristic"
    assert len(group.bullets) == 1


def test_synthesize_all_uses_llm_when_client_succeeds():
    group = _group()
    bullets = [SynthesizedBullet(text="Do the thing.", pull_requests=["42"])]
    client = _FakeGeminiClient(bullets=bullets)

    synthesize_all([group], gemini_client=client, cache=None)

    assert group.mode_used == "llm"
    assert group.bullets == bullets
    assert client.calls == 1


def test_synthesize_all_falls_back_to_heuristic_on_llm_error():
    group = _group()
    client = _FakeGeminiClient(error=LlmSynthesisError("boom"))

    synthesize_all([group], gemini_client=client, cache=None)

    assert group.mode_used == "heuristic"
    assert len(group.bullets) == 1
    assert client.calls == 1


def test_synthesize_all_uses_cache_on_second_run(tmp_path, monkeypatch):
    cache = SynthesisCache(tmp_path / "cache")
    call_count = {"n": 0}

    import learnings2agents.synthesize as synthesize_mod

    real_heuristic = synthesize_mod.synthesize_heuristic

    def counting_heuristic(learnings):
        call_count["n"] += 1
        return real_heuristic(learnings)

    monkeypatch.setattr(synthesize_mod, "synthesize_heuristic", counting_heuristic)

    group1 = _group()
    synthesize_all([group1], gemini_client=None, cache=cache)
    assert call_count["n"] == 1

    # Fresh DirGroup with identical learnings content -> should hit the cache.
    group2 = _group()
    synthesize_all([group2], gemini_client=None, cache=cache)
    assert call_count["n"] == 1  # not called again
    assert group2.bullets[0].text == group1.bullets[0].text
    assert group2.mode_used == "heuristic"
