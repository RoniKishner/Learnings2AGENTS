"""Data models shared across the learnings2agents pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Learning:
    """A single row from a CodeRabbit "Learnings" CSV export."""

    text: str
    repository: str
    file: str  # normalized, e.g. "utilities/virt.py" or "" for repo-root learnings
    pull_request: str
    url: str
    created_by: str
    usage: int

    @property
    def directory(self) -> str:
        """Directory portion of `file`, "" for repo-root learnings."""
        if "/" not in self.file:
            return ""
        return self.file.rsplit("/", 1)[0]


@dataclass
class SynthesizedBullet:
    """One finished guideline bullet, ready to render into an AGENTS.md file."""

    text: str
    pull_requests: list[str] = field(default_factory=list)
    heading: str = ""  # optional thematic subheading, e.g. "Imports" (LLM mode only)


@dataclass
class DirGroup:
    """All learnings whose `File` column falls directly under `path`."""

    path: str  # "" == repository root, otherwise e.g. "tests/network/libs"
    learnings: list[Learning] = field(default_factory=list)

    # Filled in by the synthesis step.
    bullets: list[SynthesizedBullet] = field(default_factory=list)
    mode_used: str = ""  # "llm" or "heuristic"

    @property
    def display_path(self) -> str:
        return self.path if self.path else "(repository root)"
