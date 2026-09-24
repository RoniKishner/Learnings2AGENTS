"""Central defaults/constants for learnings2agents."""

from __future__ import annotations

# Env var names read by the CLI when the corresponding flag isn't passed explicitly.
GEMINI_API_KEY_ENV_VAR = "GEMINI_API_KEY"
GEMINI_MODEL_ENV_VAR = "GEMINI_MODEL"

# Preferred Gemini model candidates tried in order when neither --model nor
# the GEMINI_MODEL env var is set.  The first model that responds successfully
# to a lightweight probe is used for the entire run.
# Precedence: --model > GEMINI_MODEL env var > this chain (auto-detected).
DEFAULT_GEMINI_MODEL_CHAIN = [
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.6-flash",
]

# Single-model fallback kept for backwards-compatibility (e.g. tests that
# import this constant directly).  Points at the head of the chain.
DEFAULT_GEMINI_MODEL = DEFAULT_GEMINI_MODEL_CHAIN[0]

# difflib.SequenceMatcher similarity ratio above which two learning texts are
# considered near-duplicates in heuristic mode.
HEURISTIC_SIMILARITY_THRESHOLD = 0.75

# Name of the sentinel filename written into each qualifying directory.
AGENTS_FILENAME = "AGENTS.md"

# Marker comments used to delimit the generated section inside an AGENTS.md file,
# so hand-written content outside them is preserved on re-runs.
BEGIN_MARKER = "<!-- BEGIN CODERABBIT LEARNINGS -->"
END_MARKER = "<!-- END CODERABBIT LEARNINGS -->"

# Directory (relative to the target repo) used to cache per-directory synthesis
# results, keyed by a hash of the directory's raw learning texts, to avoid
# redundant LLM calls (and redundant heuristic work) across re-runs.
DEFAULT_CACHE_DIRNAME = ".learnings2agents_cache"
