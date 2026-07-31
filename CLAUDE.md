# FEsolver

2D plane-stress FEA solver. **Purpose: a training tool** — for the author's own learning,
and for engineers in training working through the FEA process self-guided.

Direction: `docs/ROADMAP.md`. Open work: `docs/TODO.md`.

---

## Division of responsibility

**The engine is the author's. Claude maintains the documentation layer around it.**

| Area | Owner | Claude's role |
|---|---|---|
| `fe_solver/core/` — solver, elements, model, direct_solver | **Author** | Review, verify, propose. **Never edit.** |
| `fe_solver/gui/` | **Author** | Same. |
| `tests/` | **Author** | Propose cases and expected values in docs; don't write them in. |
| `docs/`, `README.md`, `CHANGELOG.md` | **Claude** | Maintain and keep accurate. |
| Throwaway analysis scripts | Claude | Scratchpad only, never in the repo. |

The reason for the boundary: one stated purpose of this project is the author improving
their coding skills. The numerical and architectural work — especially Phases 1–2 of the
roadmap — is exactly where that learning is. Implementing it would produce a better
codebase and a worse outcome.

### Claude does, without asking

- Read, investigate, run tests, run models, profile
- **Verify** results numerically and show the command used
- Review changes and report findings
- Keep `docs/` and `CHANGELOG.md` in sync with what the code actually does
- Propose fixes in full — including the code, as a suggestion to apply or not

### Claude does not, without being asked explicitly

- Edit anything under `fe_solver/` or `tests/` — including typos and dead code
- `git commit`, `git push`, branch switches, anything touching history
- Rewrite the physics or derivations in `docs/theory.md`
- Delete or regenerate test fixtures

If the author says "implement item N", do it fully and without hedging. Absent that, the
default is propose-not-apply.

### The specific trap

**Two tests are currently red. Do not change expected values to make them pass.**
The correct move is to find the cause — see TODO 2, where the likely mechanism is a
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
correct and validates nothing — it passes on a deliberately corrupted solution (TODO 3).
Before claiming any result is right, run it and show the command.

On FEA specifically, prefer showing the experiment to asserting the conclusion. The
author is better placed to spot a numerically-plausible but physically wrong result.

---

## Current state — verify before trusting

*As of 2026-07-31. Update as items close.*

- `pytest` is **red on both branches**: `test_stress_inplane_3`, `test_stress_mises_3`.
  "Tests pass" is not a valid baseline claim.
- `develop` is the working branch; `main` is behind it.
- The "Plot results" GUI path is **broken on `develop`** (TODO 1).
- The residual check is vacuous (TODO 3).
- `CHANGELOG.md` 0.2.3 claims the GUI/plot migration is done. It is not (TODO 1).
- `pyproject.toml` says `0.2.1`; `CHANGELOG.md` says `0.2.3` (TODO 17).

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
3. Tick the relevant `docs/TODO.md` checkbox
4. Check `docs/theory.md` still matches the implementation
5. Add a `CHANGELOG.md` entry describing what actually landed, not what was intended
6. Update the *Current state* section above

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
