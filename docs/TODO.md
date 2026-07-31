# FEsolver — Work Items

Findings from a full code review on 2026-07-31 (branch `develop`, commit `60d8757`).
Grouped by priority. Each item records **where**, **what's wrong**, and **how it was
verified**, so it can be picked up cold.

Legend: `[ ]` open · `[x]` done · `[~]` in progress

---

## P0 — Blocking

### [ ] 1. `plot.py` / `gui.py` not migrated to `FieldOutputs`

The "Plot results" button fails on every model on `develop`.

| File | Line | Broken reference | Should be |
|---|---|---|---|
| `fe_solver/gui/plot.py` | 19 | `solution.stress_mises` | `solution.results["element"]["SM"].data` |
| `fe_solver/gui/plot.py` | 61-63 | `solution.stress_principal` | `solution.results["element"]["SP"].data` |
| `fe_solver/gui/gui.py` | 238-239 | `float(DataFrame.max())` | `float(df.abs().max().max())` |

`gui.py:238` calls `.max()` on a 2-column DataFrame, which returns a Series —
`float()` on it raises `TypeError`. It also needs `.abs()`; as written it reports the
max *signed* displacement, not magnitude.

**Verify:**

```bash
python -c "
import matplotlib; matplotlib.use('Agg')
from pathlib import Path
from fe_solver.core import model, solver
from fe_solver.gui import plot
m = model.call_gen_function(model.load_input('tests/fixtures/test_input_1.inp'))
s = solver.Solver(m, True, False, False, Path(''))
plot.plot_results(m, s, 2, 'x', False)"
```

**Note:** the CHANGELOG entry for 0.2.3 already claims this is done. Correct the entry
or finish the work before release.

### [ ] 2. Two tests fail on **both** branches

```
FAILED tests/test_solver.py::test_stress_inplane_3 - assert 160.5 == 162.5
FAILED tests/test_solver.py::test_stress_mises_3   - assert 174.5 == 175.0
```

Not a `develop` regression — `main` fails identically. About 1.2% off.

**Leading hypothesis:** `tests/fixtures/test_input_3.inp` defines both `_PICKEDSET9`
(nodes 2,3,6) and `_PickedSet9` (nodes 3,4,8). Abaqus set names are case-insensitive;
`model.py` uses case-sensitive dict keys, so we get two sets where Abaqus has one.

Experiment run — element `e2`, component `s1` (expected `162.464`):

| `_PickedSet9` resolved as | result |
|---|---|
| current, `[3,4,8]` | `160.490` |
| first definition wins, `[2,3,6]` | `-18.177` |
| union, `[2,3,4,6,8]` | `162.326` |

Union closes most of the gap but not all of it — fix item 5 first, then re-check whether
a second cause remains.

---

## P1 — Correctness

### [ ] 3. The residual check validates nothing

`fe_solver/core/solver.py:327`

```python
residual = abs(reaction_forces.sum() + self.forces.sum())
```

Expands to `|sum(K@d)|`. Because the columns of K sum to zero (rigid-body translation),
this is **identically zero for any displacement vector**. It also sums u and v together,
so equal-and-opposite x/y errors would cancel even if the identity didn't already
guarantee zero.

**Proof it's vacuous** — a deliberately corrupted solution with error norm 85,597 still
reports `residual: 1.46e-11` / `PASS`:

```bash
python -c "
import numpy as np
from pathlib import Path
from fe_solver.core import model, solver
m = model.call_gen_function(model.load_input('tests/fixtures/test_input_2.inp'))
s = solver.Solver(m, True, False, False, Path(''))
K = s.global_stiffness_matrix.to_numpy(float)
d = s.displacements.to_numpy(float)
bad = d + np.random.default_rng(0).normal(0, d.std()*10, d.shape)
print('residual:', abs((K@bad - s.forces).sum() + s.forces.sum()))"
```

**Fix** — free-DOF residual norm, which is what Abaqus actually reports:

```python
r = K @ d - F
residual = np.linalg.norm(r[mask]) / max(np.linalg.norm(F), 1.0)
```

A check that always passes is worse than no check — it teaches false confidence.

### [ ] 4. Prescribed displacements silently ignored when a load is present

`fe_solver/core/solver.py:183-187`, `220-230`, `272-278`

`define_boundary_conditions` treats "has a load" and "has prescribed displacement" as
mutually exclusive. Same model, 2.0 mm prescribed on the top edge:

```
no load:      n5 v = 1.000       correct
+ 1 N Cload:  n5 v = 1.97e-07    prescribed displacement vanished
```

The maths in `apply_sign_correction` is *correct* for the pure-displacement case —
solving `K_ff x = K_fc·d_c` and negating gives the right answer — but it's expressed as
an unexplained sign flip rather than the standard form.

**Fix** — write it the textbook way. Fixes the bug and improves the teaching value:

```python
# K_ff · u_f = F_f − K_fc · d_c    (static condensation)
d_prescribed = np.where(displacements == "*", 0.0, displacements).astype(float)
rhs = forces[mask] - (stiffness_matrix @ d_prescribed)[mask]
```

One expression, no branch, no sign correction, handles mixed models.

- [ ] Delete `apply_sign_correction`
- [ ] Delete `homogeneous_model` (it currently means "has a load", the opposite of what
      *homogeneous* means in BC terminology)
- [ ] Cross-check `docs/theory.md` §5–6 still matches the code

### [ ] 5. Case-sensitive set names diverge from Abaqus

`fe_solver/core/model.py` — `gen_node_set`, `gen_element_set`, and the lookups in
`gen_solver_maps` / `solver.assemble_dof_series`.

Abaqus stores set names uppercase and matches case-insensitively. Uppercase set names at
parse time and at every lookup site. Blocks item 2.

### [ ] 6. Clockwise elements produce a negative-definite stiffness matrix

`fe_solver/core/elements.py:57-63` — `calculate_area` uses `det/2` with no `abs`.

```
CCW: area = +0.5,  K diagonal = [148352, 148352, 109890]
CW:  area = -0.5,  K diagonal = [-148352, -148352, -38462]
```

Abaqus-exported meshes happen to be consistently CCW so this doesn't bite today, but a
hand-written `.inp` — exactly what a trainee produces — silently yields garbage.
Use `abs()`, and warn on a negative determinant.

### [ ] 7. `*Boundary` parsing drops and crashes on valid Abaqus syntax

`fe_solver/core/model.py:201` — only handles `values[1] == values[2]`.

- `7, 1, 2` (constrain DOF 1 *through* 2) — **silently ignored**, model under-constrained
- `8, ENCASTRE` — `IndexError: list index out of range`
- `PINNED` likewise unsupported

Silently dropping a boundary condition is the most dangerous failure mode in the parser.

### [ ] 8. Assembly swallows all exceptions

`fe_solver/core/solver.py:143-170` wraps the entire global assembly in
`try/except Exception: print(e)`, then continues with a partially-assembled matrix and
produces numbers. Let it raise.

### [ ] 9. Undefined variable leak in BC assembly

`fe_solver/core/solver.py:200-206` — if `axis` is neither `"1"` nor `"2"`, `direction`
retains its value from the previous loop iteration and the BC lands on the wrong DOF.
Add `else: continue` or raise.

### [ ] 10. `plot.py` mutates the model

`fe_solver/gui/plot.py:42-44` does `element_nodes[i] = element_nodes[i] - 1` in place on
`model["elements"][e]["nodes"]`. Plot twice without regenerating and every element's
connectivity shifts by another one. Build a new list.

### [ ] 11. Multi-material models are silently wrong

`fe_solver/core/model.py:180-182` — `gen_material_elasticity` appends into one flat
`model["elasticity"]` list; the solver reads `[0]` and `[1]` for every element. A second
`*Material` block appends rather than registering separately, so all elements get
material 1. Material name is captured but never linked to section or elements.

### [ ] 12. No singularity check in the direct solver

`fe_solver/core/direct_solver.py:57` divides by `self.stiffness[i, i]` with no guard. An
under-constrained model — a common trainee mistake — yields `inf`/`nan` propagating
silently into the stress results.

A pivot-magnitude check with a clear message ("model is under-constrained, check
boundary conditions") would be one of the most educational additions in the codebase.

---

## P2 — Code quality

### [ ] 13. Vectorise the assembly accumulation

`fe_solver/core/solver.py:156-167` — a Python double loop doing `.at[]` on a dense
`dof × dof` DataFrame, per element. Memory is O(dof²) dense and label lookups dominate.
`examples/plate_hole_disp_refined_mesh.inp` will be slow.

Keep the pandas *presentation* (it's the clearest part of the code) but accumulate into a
numpy array via the `label_to_idx` map already built in `gen_solver_maps`, then wrap the
result in a DataFrame. Same readability, orders of magnitude faster.

### [ ] 14. Replace the `"*"` sentinel

`fe_solver/core/solver.py:88` — `["*"] * dof` makes the Series object-dtype and forces
string/float mixing throughout. Use `np.nan` in a float array, or lean on the existing
`active_mask`.

### [ ] 15. Consider `(node, dof)` tuple indices

`f"{node}{dof}"` → `"12u"`, decoded with `index[:-1]` / `index[-1]`
(`solver.py:264-265`). Works and reads well — which counts for a lot here — but a tuple
index would be equally readable and non-parsing. Low priority.

### [ ] 16. Remove dead code

- `fe_solver/gui/progress_bar.py` — unwired prototype calling `tk.Tk()` and `mainloop()`
  at module scope; **importing it hangs**
- `fe_solver/core/solver.py:11` — commented-out matplotlib import
- `fe_solver/core/model.py` — `os` imported unused

### [ ] 17. Housekeeping

- [ ] Version mismatch: `pyproject.toml` says `0.2.1`, `CHANGELOG.md` says `0.2.3`
- [ ] Add an MIT `LICENSE` file. The dead link has been removed from `README.md`, which
      now states the licence without linking — restore the link once the file exists.
      `pyproject.toml` declares no licence either.
- [ ] `solver.py:437` — `__main__` shadows the `model` module with the model dict

---

## P3 — Testing

### [ ] 18. Add an analytical patch test

A uniaxial plate under uniform tension where `σ = F/A` exactly. Worth more than all the
current golden-value tests combined, and directly teachable — it's the standard FEA
verification exercise.

### [ ] 19. Replace pickle fixtures with explicit assertions

`tests/test_solver.py:32-36` compares the parsed model against a pickled golden file.
That asserts "the parser produces what the parser produced" — a parsing bug gets frozen
in as expected behaviour — and pickles are opaque in diffs.

JSON equivalents are already written by `model.py:327-331`. Better still, assert on
specific values: `assert model["nodes"][5] == [10.0, 10.0]`.

### [ ] 20. Cover the gaps

No test currently asserts:

- reaction forces sum to the applied load
- a mixed load + prescribed-displacement model (item 4)
- a displacement-driven model's residual
- behaviour on a deliberately under-constrained model (item 12)

---

## Documentation

Raised by the documentation review on 2026-07-31. The mechanical fixes from that review
(stale function names, dead code snippets, the incorrect partial-pivoting claim, missing
`*NSET` entry, and so on) are **already applied**. These four are what was deferred
because they need a decision or depend on pending code changes.

### [ ] 22. Add a reaction force / residual section to `theory.md`

`compute_reaction_forces()` landed in 0.2.3 and `theory.md` has no section for it. It is
also absent from the Section 9 summary table, which otherwise maps one row per solver
function.

Needs new derivation content — reactions as $\{R\} = [K]\{u\} - \{F\}$, why they are
recovered only at constrained DOFs, and what a residual check is actually testing.

**Blocked on item 3.** Writing this now would document a residual check that validates
nothing. Do item 3 first, then document the corrected version — the *why* of a proper
residual norm is the teachable part.

### [ ] 23. Fix the homogeneous / non-homogeneous terminology

`theory.md` §1 labels force-driven models "homogeneous" and displacement-driven models
"non-homogeneous", inheriting the misnomer from `solver.py`. Homogeneous refers to a
boundary condition with a **zero prescribed value**, not to whether external loads exist.

**Tied to item 4**, which deletes `homogeneous_model` entirely. Cheaper to fix once, when
that lands, than to correct the docs twice.

### [ ] 24. Rewrite `theory.md` §1 and §5 around static condensation

Both sections present force-driven and displacement-driven loading as mutually exclusive.
That is accurate to the current code and the current code is wrong (item 4).

A `> **Known limitation**` note has been added to §5 pointing at items 4, 23 and 24, so
the doc no longer presents the bug as intended behaviour. Replace the note with the
proper treatment once item 4 lands.

### [ ] 25. Parser limitations surfaced by the documentation review

All three are now documented in `keywords.md` as limitations, but the underlying
behaviour is still worth fixing:

- **`ELSET` on `*Element` breaks the model.** `*Element, type=S3, elset=PLATE` parses the
  type as `s3, elset` and fails with `KeyError: 's3, elset'` when the element stiffness
  matrix is built. `gen_element` splits on `=` and takes index `[1]`, so any trailing
  parameter is swallowed into the type. Should either be supported or rejected clearly.
- **Nested sets are silently dropped.** Naming a previously defined set inside another
  set's data line is skipped by the bare `except Exception: pass` in `gen_node_set` and
  `gen_element_set`. Abaqus supports this.
- **`elementsets` is parsed but never read.** `model["elementsets"]` and
  `model["section"]["elementset"]` are both populated and neither is used — the shell
  section thickness is applied to every element regardless of the set named. Either wire
  it up or drop the dead parsing.

---

## Process

### [ ] 21. Green tests as a merge gate

Both branches currently ship failing tests, and the 0.2.3 CHANGELOG entry lists work that
isn't finished. Treating the suite as a gate rather than a record is the single biggest
coding-practice improvement available here, and the habit that transfers most directly to
professional work.

---

## Suggested order

Items **3, 4 and 7/12** change what the tool *teaches* — a training solver that is quietly
wrong, or that passes a meaningless self-check, is worse than one that refuses to run.
Everything else is tidying.

1. Item 1 — unbreak `develop`
2. Item 3 — real residual check
3. Item 4 — static condensation rewrite
4. Items 6, 7, 11, 12 — input validation with clear messages (for a training tool, the
   error messages *are* the curriculum)
5. Item 5 — uppercase set names, then re-check item 2
6. Item 18 — patch test
7. Item 13 — vectorise assembly
