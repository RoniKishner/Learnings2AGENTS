"""Per-directory bullet synthesis: turn each DirGroup's raw learnings into a
final list of `SynthesizedBullet`s, using Gemini when available and falling
back to the offline heuristic otherwise.
"""

from __future__ import annotations

import logging

from learnings2agents.cache import SynthesisCache
from learnings2agents.heuristics import synthesize_heuristic
from learnings2agents.llm import GeminiClient, LlmSynthesisError
from learnings2agents.models import DirGroup

logger = logging.getLogger(__name__)


def synthesize_all(
    groups: list[DirGroup],
    gemini_client: GeminiClient | None,
    cache: SynthesisCache | None = None,
) -> None:
    """Fill in `bullets` and `mode_used` for every group, in place.

    If `gemini_client` is given, LLM mode is attempted first per directory;
    on any failure (network/auth/parsing) it logs a warning and falls back to
    heuristic mode for that directory only, rather than aborting the run.

    Logs an INFO progress line after each directory finishes (cache hit, LLM,
    or heuristic), so a long run isn't silent between the noisy per-request
    library logs (httpx, google-genai) — e.g.:
        [12/45 dirs, 87/233 learnings] 'tests/network/libs' -> 6 bullets (llm)
    """
    model_name = gemini_client.model if gemini_client else ""

    total_dirs = len(groups)
    total_learnings = sum(len(group.learnings) for group in groups)
    learnings_done = 0

    logger.info(
        "Synthesizing %d director%s covering %d learning(s) total…",
        total_dirs,
        "y" if total_dirs == 1 else "ies",
        total_learnings,
    )

    for dir_index, group in enumerate(groups, start=1):
        mode = "llm" if gemini_client else "heuristic"
        cache_hit = False

        if cache is not None:
            cached = cache.get(group.path, group.learnings, mode, model_name)
            if cached is not None:
                group.bullets = cached
                group.mode_used = mode
                cache_hit = True

        if not cache_hit:
            bullets = None
            if gemini_client is not None:
                try:
                    bullets = gemini_client.synthesize_directory(
                        group.path, group.learnings
                    )
                    mode = "llm"
                except LlmSynthesisError as exc:
                    logger.warning(
                        "LLM synthesis failed for '%s', falling back to heuristic mode: %s",
                        group.display_path,
                        exc,
                    )
                    bullets = None
                    mode = "heuristic"

            if bullets is None:
                bullets = synthesize_heuristic(group.learnings)
                mode = "heuristic"

            group.bullets = bullets
            group.mode_used = mode

            if cache is not None:
                cache.set(group.path, group.learnings, mode, model_name, bullets)

        learnings_done += len(group.learnings)
        logger.info(
            "[%d/%d dirs, %d/%d learnings] '%s' -> %d bullet(s) (%s mode%s)",
            dir_index,
            total_dirs,
            learnings_done,
            total_learnings,
            group.display_path,
            len(group.bullets),
            mode,
            ", cached" if cache_hit else "",
        )
