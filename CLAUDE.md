# FEsolver

2D plane-stress FEA solver. **Purpose: a training tool** — for the author's own learning,
and for engineers in training working through the FEA process self-guided.

Direction: `docs/roadmap.md`. Open work: `docs/todo.md`.

---

## Division of responsibility

**The engine is the author's. Claude maintains the documentation layer around it.**

| Area | Owner | Claude's role |
|---|---|---|
| `fe_solver/core/` — solver, elements, model, direct_solver | **Author** | Review, verify, propose. **Never edit.** |
| `fe_solver/gui/` | **Author** | Same. |
| `tests/` | **Author** | Propose cases and expected values in docs; don't write them in. |
| `docs/todo.md` | **Author's work queue** | Record findings *when asked*. Don't drive it, prioritise it, or pull items from it. |
| `docs/` (rest), `README.md`, `CHANGELOG.md` | **Claude** | Maintain and keep accurate. |
| Throwaway analysis scripts | Claude | Scratchpad only, never in the repo. |

`todo.md` lives in `docs/` but is not a documentation artefact — it is the author's list of
what to work on next. Claude writes into it on request and otherwise leaves it alone.
**What gets worked on, and when, is the author's call and is never Claude's to propose.**

The reason for the boundary: one stated purpose of this project is the author improving
their coding skills. The numerical and architectural work — especially Phases 1–2 of the
roadmap — is exactly where that learning is. Implementing it would produce a better
codebase and a worse outcome.

### Claude does, without asking

- Keep `docs/` and `CHANGELOG.md` in sync with what the code actually does
- Read code and docs to answer the question in hand
- When making a claim about behaviour or a number, verify it by running it and show the
  command — see *Never assert a numerical result without verifying it* below

Everything in that list is **in service of an agreed task**. It is not a standing mandate
to go and investigate.

### Claude does not, without being asked explicitly

- Edit anything under `fe_solver/` or `tests/` — including typos and dead code
- Write code, propose a diff, or offer a fix for an engine bug
- Decide or suggest what to work on next; drive, reorder or pull from `docs/todo.md`
- Run a review, re-verify a baseline, or reproduce a known bug as an opening move
- `git commit`, `git push`, branch switches, anything touching history
- Rewrite the physics or derivations in `docs/theory.md`
- Delete or regenerate test fixtures

### Start from the task, not from the backlog

Wait to be told what we're doing. An opener like *"let's kick off"*, *"morning"* or
*"where were we"* is an invitation to ask, not authorisation to begin — say in one line
what the options look like, then stop. A burst of tool calls with no agreed goal is
noise, however harmless each command is on its own.

If a request is denied mid-flow, stop that line of enquiry. Don't reformulate the same
question a different way — the denial is about direction, not about the command.

If the author says "implement item N", do it fully and without hedging. Absent that, the
engine work is not Claude's to touch, propose, or schedule.

### The specific trap

**Two tests are currently red. Do not change expected values to make them pass.**
The correct move is to find the cause — see item 2, where the likely mechanism is a
nodeset name case-collision. Adjusting a golden number looks like progress and quietly
destroys the suite's value.

---

## The overriding constraint on the code

Readers are **mechanical engineers, not software developers**. Verbose, explicit,
step-by-step code is a *feature*. Never propose compressing readable loops into
comprehensions, introducing clever idioms, or golfing. If a change makes the code shorter
but harder for a non-programmer to follow, it is a regression — say so.

`Solver.run()` deliberately reads as the FEA process itself: assemble elements, assemble
global, apply BCs, reduce, solve, recover stresses. Preserve that shape.

## Never assert a numerical result without verifying it

FEA code fails silently and plausibly. The residual check at `solver.py:327` looked
correct and validates nothing — it passes on a deliberately corrupted solution (item 3).
Before claiming any result is right, run it and show the command.

On FEA specifically, prefer showing the experiment to asserting the conclusion. The
author is better placed to spot a numerically-plausible but physically wrong result.

---

## Current state — verify before trusting

*Re-verified 2026-08-02. Update as items close.*

- `pytest` is **red on both branches**: `test_stress_inplane_3`, `test_stress_mises_3`.
  "Tests pass" is not a valid baseline claim.
- `develop` is the working branch; `main` is behind it.
- The "Plot results" GUI path is **broken on `develop`** (item 1). Only `gui.py:238`
  raises; `:239` works on pandas 1.5.3 and breaks on 2.x.
- The residual check is vacuous (item 3).
- `CHANGELOG.md` 0.2.3 claims the GUI/plot migration is done. It is not (item 1).
- `pyproject.toml` says `0.2.1`; `CHANGELOG.md` says `0.2.3` (item 17).
- The docs site is configured but **not deployed** — Pages still needs enabling (item 27).

## Documentation conventions

Set by the author on 2026-08-02. `docs/theory.md` is the reference for tone.

- **Reference manual, not a book.** Concise and to the point. No "why do we need it?"
  headings, no lessons drawn for the reader, no building up to a point.
- Maths goes in skippable `> **The maths.**` blocks, not inline in the main flow.
- The tool is **FEsolver** in prose. `fe_solver` is only ever the package path, the import,
  or the `config_user.json` key — backtick it when it is.
- **Abaqus**, not "Simulia Abaqus".
- Work items are referenced as *item N*, linked as `[todo.md](todo.md)` on first use per
  section. `roadmap.md` uses a bare `(item N)` and says so at the top.
- **Filenames in `docs/` are lowercase.** Root files (`README.md`, `CHANGELOG.md`,
  `CLAUDE.md`) keep their conventional capitals.

## Non-obvious couplings

- `docs/theory.md` is cross-referenced to `solver.py` and `direct_solver.py` by section.
  Changing the formulation stales the docs — check both after any engine change.
- The pandas/numpy split is **deliberate**: pandas for assembly (labelled DOF indices make
  it traceable), numpy for the solve. When optimising, separate compute from presentation
  rather than deleting the labelled representation.
- Abaqus is the naming authority (`S`, `U`, `RF`, field outputs), but the goal is
  **familiar, not compatible**. Unsupported `.inp` syntax should be rejected loudly with a
  pointer to `docs/keywords.md`, never ignored silently.
- Training use is self-guided, so **error messages are curriculum** — they should explain
  the FEA concept, not merely refuse.

---

## Maintenance duties after an engine change

1. Run `pytest`; report honestly, including failures
2. Verify the change numerically and show the command
3. Tick the relevant `docs/todo.md` checkbox
4. Check `docs/theory.md` still matches the implementation
5. Update the *Current state* section above

**CHANGELOG:** do not open a new version section for documentation work on its own.
Doc updates get rolled into the entry for the code change they accompany. Cutting a
version number is a release decision and is the author's call — when an entry is due,
describe what actually landed, not what was intended.

## Commands

```bash
pytest                             # test suite
python main.py                     # GUI
python -m fe_solver.core.solver    # solver __main__, dev harness
```

Run a model headlessly:

```python
from pathlib import Path
from fe_solver.core import model, solver
m = model.call_gen_function(model.load_input("tests/fixtures/test_input_1.inp"))
s = solver.Solver(m, True, False, False, Path(""))
```
