"""Group learnings by directory (from the `File` column).

There is deliberately no parent/child tree or ancestor closure here: each
directory's AGENTS.md is synthesized independently from only the learnings
whose `File` falls directly under it (see the plan for the "several files
from the start" decision, as opposed to a single-file-then-split design).
"""

from __future__ import annotations

import logging
from pathlib import Path

from learnings2agents.models import DirGroup, Learning

logger = logging.getLogger(__name__)


def group_by_directory(learnings: list[Learning]) -> list[DirGroup]:
    """Group learnings into one `DirGroup` per unique directory, sorted by path."""
    groups: dict[str, DirGroup] = {}
    for learning in learnings:
        directory = learning.directory
        group = groups.setdefault(directory, DirGroup(path=directory))
        group.learnings.append(learning)
    return [groups[path] for path in sorted(groups)]


def filter_existing_directories(
    groups: list[DirGroup], target: str | Path, create_missing_dirs: bool = False
) -> list[DirGroup]:
    """Keep only groups whose directory exists under `target`.

    The repository root ("") always "exists" (it's `target` itself).
    Directories that don't exist are logged as warnings and dropped unless
    `create_missing_dirs` is set, in which case they are created (this can
    happen when a file referenced in the CSV was since renamed/moved/deleted).
    """
    target_path = Path(target)
    kept: list[DirGroup] = []
    for group in groups:
        dir_path = target_path / group.path if group.path else target_path
        if dir_path.is_dir():
            kept.append(group)
            continue

        if create_missing_dirs:
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.warning(
                "Directory '%s' did not exist under target; created it "
                "(--create-missing-dirs).",
                group.display_path,
            )
            kept.append(group)
            continue

        logger.warning(
            "Skipping '%s': directory does not exist under target %s "
            "(pass --create-missing-dirs to create it).",
            group.display_path,
            target_path,
        )
    return kept
