# learnings2agents

A tool to turn a CodeRabbit **Learnings** CSV export into scoped `AGENTS.md`
files, written directly into the folders of a target repository checkout.

Learnings are grouped by the directory of the file they were recorded
against (the CSV's `File` column) and one `AGENTS.md` is generated per
directory from the start — there is no single monolithic file that gets
split up afterwards. See [`## Design notes`](#design-notes) below for why.

The tool works fully offline out of the box (no API key required). If you
provide a Gemini API key, per-directory synthesis is upgraded to use the LLM
for higher-quality deduplication and rewriting — see
[`## What does a Gemini API key add?`](#what-does-a-gemini-api-key-add).

## Quick start

```bash
git clone <this repo> && cd Learnings2AGENTS
make run CSV=/path/to/learnings.csv TARGET=/path/to/checked-out/repo
```

That's it — `make run` creates a local virtualenv, installs dependencies,
and writes/merges `AGENTS.md` files into `TARGET`, mirroring the folder
structure referenced by the CSV.

Optional extras:

```bash
make run CSV=learnings.csv TARGET=/path/to/repo \
  REPOSITORY=my-org/my-repo \  # only needed if the CSV has multiple repos
  MODEL=gemini-2.5-flash       # optional: override the Gemini model (default: gemini-2.5-flash)
```

To enable LLM-mode synthesis, **export** `GEMINI_API_KEY` rather than passing
it as a `make` variable on the command line:

```bash
export GEMINI_API_KEY=xxxx
make run CSV=learnings.csv TARGET=/path/to/repo
```

See [`## Handling the Gemini API key safely`](#handling-the-gemini-api-key-safely)
for why, and how to wire this up in GitHub Actions.

Preview what would be written without touching disk:

```bash
make dry-run CSV=learnings.csv TARGET=/path/to/repo
```

Run the test suite:

```bash
make test
```

You can also invoke the CLI directly for the full set of flags:

```bash
python -m learnings2agents.cli --help
```

## What it does

1. Parses the CodeRabbit CSV export (`Learning, Repository, File, Pull Request,
   URL, Created By, Usage, Last Used, Created At, Updated At`).
2. Selects a single repository's rows (auto-detected if the CSV only has
   one; pass `--repository`/`REPOSITORY=` to disambiguate otherwise).
3. Groups learnings by the directory of their `File` column and verifies
   that directory exists under `--target`/`TARGET`.
4. For each directory, synthesizes a deduplicated, imperative-style bullet
   list — either via the Gemini API (if a key is given) or a fully offline
   heuristic (near-duplicate text clustering via `difflib`).
5. Writes/merges an `AGENTS.md` per directory, wrapping generated content in
   `<!-- BEGIN/END CODERABBIT LEARNINGS -->` markers so any hand-written
   content in an existing `AGENTS.md` is preserved across re-runs.

Results are cached (`<target>/.learnings2agents_cache/` by default, disable
with `--no-cache`) so re-running against an unchanged CSV/target skips
redundant LLM calls.

## What does a Gemini API key add?

Without a key, the tool is fully functional: it groups learnings by folder,
deduplicates near-identical text with `difflib`, and writes an `AGENTS.md`
per folder. A Gemini key upgrades the quality of that per-directory
synthesis step:

- **Semantic (not just textual) deduplication** — merges rows that express
  the same rule in different words, which plain text-similarity would miss.
- **Rewriting into clean, imperative guidance** — turns a review-comment
  style sentence into a short, direct AGENTS.md bullet.
- **Thematic grouping within a folder** — related bullets get grouped under
  short subheadings (e.g. "Imports", "Testing") instead of one flat list.
- **Generalizing repeated specific instances into one broader rule** within
  a folder (e.g. several "import X as a whole module" learnings for
  different modules become one general bullet).
- **Noise filtering** of very narrow, one-off learnings.

None of this is required to use the tool; it only affects how polished the
generated bullets are. The model used defaults to `gemini-2.5-flash`
(`DEFAULT_GEMINI_MODEL` in `config.py`) unless overridden by the
`GEMINI_MODEL` env var or the `--model`/`MODEL=` flag.

## Handling the Gemini API key safely

`GEMINI_API_KEY` is optional and is only ever read from the **environment**
(`--gemini-api-key` also exists as an explicit CLI flag if you need it, e.g.
for scripting, but prefer the environment variable). Concretely:

- The `Makefile`'s `run`/`dry-run` recipes never reference
  `$(GEMINI_API_KEY)` and are silenced (`@`), so no command line containing a
  secret is ever echoed to your terminal or CI logs. GNU Make automatically
  forwards environment/command-line variables into recipe subshells, so the
  key still reaches the Python process via `os.environ` without appearing in
  any printed command.
- Locally: `export GEMINI_API_KEY=...` before `make run`.
- In GitHub Actions: put the key in a **GitHub Environment** secret
  (Settings → Environments → your environment → Secrets), then reference it
  from a job that targets that environment:

  ```yaml
  jobs:
    generate:
      runs-on: ubuntu-latest
      environment: production   # <- makes secrets.GEMINI_API_KEY resolve to
                                 #    that Environment's secret
      steps:
        - uses: actions/checkout@v4
        - name: Generate AGENTS.md
          env:
            GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          run: make run CSV=learnings.csv TARGET=./target-repo
  ```

  A ready-to-customize version of this lives at
  [`.github/workflows/generate-agents-md.yml`](.github/workflows/generate-agents-md.yml)
  (manual `workflow_dispatch` trigger only).
- `tests/test_security.py` regression-tests that the key never shows up in
  logs, stdout/stderr, `--help` output, or the `Makefile` text itself.

## Design notes

The tool builds **several scoped `AGENTS.md` files from the start** rather
than generating one big file and splitting it afterwards: each directory's
`AGENTS.md` is synthesized independently from only the learnings whose
`File` falls under that directory. This maps directly onto the CSV's
existing per-file structure, is cheap to cache/re-run, and scales to CSVs
covering many repositories. The trade-off is that if the exact same
convention was learned separately in several different directories, it will
appear once (deduplicated) in each of those directories' files rather than
being consolidated into one parent/root file — cross-folder consolidation is
a possible future enhancement, not part of this tool.

## Repository layout

```
.github/workflows/
  generate-agents-md.yml  # example workflow_dispatch CI job (see above)
src/learnings2agents/
  cli.py           # argparse entrypoint, orchestrates the pipeline
  config.py         # defaults: model name, similarity threshold, cache dir
  models.py         # Learning / DirGroup / SynthesizedBullet dataclasses
  csv_loader.py      # parse the CSV, filter/auto-detect repository
  tree.py            # group learnings by directory, verify against target
  llm.py             # Gemini client wrapper (google-genai), used only with a key
  heuristics.py       # offline fallback: difflib-based near-duplicate clustering
  synthesize.py        # per-directory synthesis orchestration + cache lookup
  writer.py            # render Markdown, merge into existing AGENTS.md files
  cache.py             # on-disk content-hash cache for synthesis results
tests/
  fixtures/sample_learnings.csv
  test_security.py     # regression tests: API key is never printed/logged
  test_*.py
```
