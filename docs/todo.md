# FEsolver — Work Items

Findings from a full code review on 2026-07-31 (branch `develop`, commit `60d8757`).
Grouped by priority. Each item records **where**, **what's wrong**, and **how it was
verified**, so it can be picked up cold.

Legend: `[ ]` open · `[x]` done · `[~]` in progress

---

## P0 — Blocking

### [x] 1. `plot.py` / `gui.py` not migrated to `FieldOutputs`

**Closed 2026-08-02.** All three call sites now read `results`, and plotting works on
every example model. `gui.py:239` was given the same `.abs().max().max()` treatment.
Remaining pre-migration reads are tracked separately as item 28.

The "Plot results" button failed on every model on `develop`.

| File | Line | Broken reference | Should be |
|---|---|---|---|
| `fe_solver/gui/plot.py` | 19 | `solution.stress_mises` | `solution.results["element"]["SM"].data` |
| `fe_solver/gui/plot.py` | 61-63 | `solution.stress_principal` | `solution.results["element"]["SP"].data` |
| `fe_solver/gui/gui.py` | 238 | `float(DataFrame.max())` | `float(df.abs().max().max())` |

`plot.py:19` raised `AttributeError: 'Solver' object has no attribute 'stress_mises'` —
the Solver exposes only `results`, holding `element: [S, SP, SM]` and `node: [U, RF]`.
`gui.py:245` wraps the call in `except Exception`, so it surfaced as an "Error plotting
result" log line rather than a traceback.

Three points of detail:

- **`gui.py:239` did not fail.** `SM.data` is single-column, so `float(df.max())`
  received a one-element Series, which pandas 1.5.3 still converts. Deprecated, and would
  have broken on pandas 2.x — fixed alongside 238.
- **The `.abs()` change is latent.** Signed and absolute maxima are identical on all four
  current models, so nothing exercises it:

  ```
  tests/fixtures/test_input_1.inp  signed=+2.0000e+00  abs=2.0000e+00
  tests/fixtures/test_input_2.inp  signed=+1.4968e-02  abs=1.4968e-02
  tests/fixtures/test_input_3.inp  signed=+1.1921e-02  abs=1.1921e-02
  examples/worked_example.inp      signed=+4.7619e-03  abs=4.7619e-03
  ```

  A model in compression would report the wrong number.
- **The label disagrees with the plot** — see item 30.

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

### [~] 2. `test_stress_inplane_3` fails

**Narrowed 2026-08-02 by item 5, not closed.**

```
FAILED tests/test_solver.py::test_stress_inplane_3 - assert 162.3 == 162.5
```

Suite is now 1 failed, 11 passed. `test_stress_mises_3` went green with item 5.

The original cause was confirmed: `tests/fixtures/test_input_3.inp` defines both
`_PICKEDSET9` (nodes 2,3,6) and `_PickedSet9` (nodes 3,4,8), which Abaqus treats as one
set and `model.py` treated as two. Element `e2`, component `s1`, expected `162.464`:

| `_PickedSet9` resolved as | result |
|---|---|
| before item 5, `[3,4,8]` | `160.490` |
| first definition wins, `[2,3,6]` | `-18.177` |
| union, `[2,3,4,6,8]` — **now live** | `162.326` |

So the set collision accounted for most of the 1.2% error but not the last 0.08%. A
second cause remains and is **not yet identified**. It is no longer a parsing problem —
the model now matches what Abaqus would build.

Where to look next: whether `162.464` was itself produced by a solver with a known bug, or
whether the discrepancy is in the stress recovery. Items 4 and 6 are the nearest
candidates.

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

### [ ] 4. Prescribed displacements silently ignored when a load is present

`fe_solver/core/solver.py:183-187`, `220-230`, `272-278`

`define_boundary_conditions` treats "has a load" and "has prescribed displacement" as
mutually exclusive. Same model, 2.0 mm prescribed on the top edge:

```
no load:      n5 v = 1.000       correct
+ 1 N Cload:  n5 v = 1.97e-07    prescribed displacement vanished
```

`apply_sign_correction` is *correct* for the pure-displacement case — solving
`K_ff x = K_fc·d_c` and negating gives the right answer — but it is expressed as an
unexplained sign flip rather than the standard form.

**Fix** — the textbook form. No branch, no sign correction, handles mixed models:

```python
# K_ff · u_f = F_f − K_fc · d_c    (static condensation)
d_prescribed = np.where(displacements == "*", 0.0, displacements).astype(float)
rhs = forces[mask] - (stiffness_matrix @ d_prescribed)[mask]
```

- [ ] Delete `apply_sign_correction`
- [ ] Delete `homogeneous_model` (it currently means "has a load", the opposite of what
      *homogeneous* means in BC terminology)
- [ ] Cross-check `docs/theory.md` §5–6 still matches the code

### [x] 5. Case-sensitive set names diverge from Abaqus

**Closed 2026-08-02.** Set and material names are lowercased at parse time in
`gen_node_set`, `gen_element_set`, `gen_shell_section`, `gen_material`, `gen_boundary` and
`gen_load`, so both sides of every lookup agree.

Lowercase rather than Abaqus's uppercase: the fix only needs *a* canonical case, and the
parser already lowercases element types (`model.py:57`) and keywords (`:286`). Consistency
within the model won over fidelity to Abaqus's internal storage, which is not user-facing.

A second change was needed alongside it. `gen_node_set` and `gen_element_set` did
`self.model["nodesets"][set_name] = []` unconditionally, so once names collapsed the second
definition wiped the first. They now initialise only on first sight and append, matching
Abaqus's accumulate-on-repeat behaviour, with a duplicate guard:

```
_pickedset9 -> [2, 3, 6, 4, 8]        # was _PICKEDSET9 [2,3,6] + _PickedSet9 [3,4,8]
```

Test fixtures 1-3 were regenerated. Equivalence was checked first — each parsed model was
identical to the previously accepted fixture once case-folded, so nothing but case and the
intended merge changed.

Partially unblocked item 2: `test_stress_mises_3` now passes; `test_stress_inplane_3`
narrowed from 160.5 to 162.3 but still fails.

### [ ] 6. Clockwise elements produce a negative-definite stiffness matrix

`fe_solver/core/elements.py:57-63` — `calculate_area` uses `det/2` with no `abs`.

```
CCW: area = +0.5,  K diagonal = [148352, 148352, 109890]
CW:  area = -0.5,  K diagonal = [-148352, -148352, -38462]
```

Abaqus-exported meshes are consistently CCW so this does not bite today, but a
hand-written `.inp` silently yields garbage. Use `abs()`, and warn on a negative
determinant.

### [ ] 7. `*Boundary` parsing drops and crashes on valid Abaqus syntax

`fe_solver/core/model.py:201` — only handles `values[1] == values[2]`.

- `7, 1, 2` (constrain DOF 1 *through* 2) — **silently ignored**, model under-constrained
- `8, ENCASTRE` — `IndexError: list index out of range`
- `PINNED` likewise unsupported

### [ ] 8. Assembly swallows all exceptions

`fe_solver/core/solver.py:143-170` wraps the entire global assembly in
`try/except Exception: print(e)`, then continues with a partially-assembled matrix and
produces numbers. Let it raise.

### [ ] 9. Undefined variable leak in BC assembly

`fe_solver/core/solver.py:200-206` — if `axis` is neither `"1"` nor `"2"`, `direction`
retains its value from the previous loop iteration and the BC lands on the wrong DOF.
Add `else: continue` or raise.

### [x] 10. `plot.py` mutates the model

**Closed 2026-08-02.** `.copy()` on the connectivity list, so the subtraction writes into
a copy. Verified: three consecutive plots leave `model["elements"]` unchanged.

`fe_solver/gui/plot.py:42-44` did `element_nodes[i] = element_nodes[i] - 1` in place on
`model["elements"][e]["nodes"]`. Plot twice without regenerating and every element's
connectivity shifts by another one. Build a new list.

### [ ] 11. Multi-material models are silently wrong

`fe_solver/core/model.py:180-182` — `gen_material_elasticity` appends into one flat
`model["elasticity"]` list; the solver reads `[0]` and `[1]` for every element. A second
`*Material` block appends rather than registering separately, so all elements get
material 1. Material name is captured but never linked to section or elements.

### [ ] 12. No singularity check in the direct solver

`fe_solver/core/direct_solver.py:57` divides by `self.stiffness[i, i]` with no guard. An
under-constrained model yields `inf`/`nan` propagating silently into the stress results.

Wanted: a pivot-magnitude check with a clear message — "model is under-constrained, check
boundary conditions".

---

## P2 — Code quality

### [ ] 13. Vectorise the assembly accumulation

`fe_solver/core/solver.py:156-167` — a Python double loop doing `.at[]` on a dense
`dof × dof` DataFrame, per element. Memory is O(dof²) dense and label lookups dominate.
`examples/plate_hole_disp_refined_mesh.inp` will be slow.

Keep the pandas presentation but accumulate into a numpy array via the `label_to_idx` map
already built in `gen_solver_maps`, then wrap the result in a DataFrame.

### [ ] 14. Replace the `"*"` sentinel

`fe_solver/core/solver.py:88` — `["*"] * dof` makes the Series object-dtype and forces
string/float mixing throughout. Use `np.nan` in a float array, or lean on the existing
`active_mask`.

### [ ] 15. Consider `(node, dof)` tuple indices

`f"{node}{dof}"` → `"12u"`, decoded with `index[:-1]` / `index[-1]`
(`solver.py:264-265`). Works and reads well — which counts for a lot here — but a tuple
index would be equally readable and non-parsing. Low priority.

### [x] 16. Remove dead code

**Closed 2026-08-02.** `progress_bar.py` deleted and the unused `os` import removed from
`model.py`; no references remain and all modules still import. The commented-out
matplotlib import at `solver.py:11` was left as-is, which the CHANGELOG wording covers.

- `fe_solver/gui/progress_bar.py` — unwired prototype calling `tk.Tk()` and `mainloop()`
  at module scope; **importing it hangs**
- `fe_solver/core/solver.py:11` — commented-out matplotlib import
- `fe_solver/core/model.py` — `os` imported unused

### [ ] 28. Complete the `FieldOutputs` migration

Added 2026-08-02. Item 1 is the minimum fix — repoint the two broken call sites so the GUI
works. This item is the rest: make `results` the single way anything outside the solve
reads a result.

**Reporting reads that still use pre-migration attributes:**

| File | Line | Reads | Field output holding the same data |
|---|---|---|---|
| `fe_solver/gui/plot.py` | 20 | `solution.displacements.tolist()` | `results["node"]["U"]` |
| `fe_solver/core/solver.py` | 442 | `pp.pprint(s.displacements)` | `results["node"]["U"]` |
| `fe_solver/core/solver.py` | 444 | `s.stress_normal["s1"]["e8"]` | `results["element"]["S"]` |

`U.data.to_numpy(float).ravel()` reproduces `displacements.tolist()` exactly — verified on
`test_input_1` and `test_input_2` — and is genuine `float` rather than `object` dtype, so
it survives item 14.

**`self.stress_normal` and `results["element"]["S"].data` are the same object.**
`solver.py:312` passes the DataFrame into `FieldOutputs` without copying:

```bash
python -c "
from pathlib import Path
from fe_solver.core import model, solver
m = model.call_gen_function(model.load_input('tests/fixtures/test_input_1.inp'))
s = solver.Solver(m, True, False, False, Path(''))
print(s.results['element']['S'].data is s.stress_normal)   # True
s.stress_normal.loc['e1','s1'] = -999.0
print(s.results['element']['S'].data.loc['e1','s1'])       # -999.0
"
```

Writing through either name mutates the published result. `compute_principal_stress` and
`compute_mises_stress` then iterate `self.stress_normal` (`:369`, `:398`) to derive `SP`
and `SM`, so a stray write to `S` silently changes them too. Either copy on construction
or drop the attribute and read `results["element"]["S"].data`.

**Two things that are not in scope:**

- **`self.displacements` during the solve is legitimate working state**, not a duplicate.
  It is the vector boundary conditions are written into (`:178`), reduced (`:217`) and
  solved back into (`:257`) before `U` is built from it at `:262-268`. Only reads *after*
  the solve should move to `U`.
- **`direct_solver.py:56-57,82` has its own `self.displacements`** — a local solution
  vector on `DirectSolver`, unrelated to `Solver`. Leave it.

**Exit criteria:** nothing outside `fe_solver/core/solver.py` reads a result except through
`results`, and no field output aliases a mutable solver attribute.

### [ ] 30. "Max displacement" in the GUI log is a component, not a magnitude

Added 2026-08-02. `gui.py:238` logs "Max displacement" but reports the largest single
component of `U`. The contour plot it sits above is titled "U [Magnitude]" and shows
`√(u² + v²)` — built in `plot.py:23-25`. Two different quantities under one name.

The gap is not academic:

```
worked_example.inp                component=4.761905e-03  magnitude=4.971575e-03   4.2%
plate_simple_load.inp             component=4.335009e+00  magnitude=6.130628e+00  29.3%
plate_hole_disp_refined_mesh.inp  component=2.000000e+00  magnitude=2.005802e+00   0.3%
```

`plate_simple_load.inp` reports a number 29% below the peak displacement shown in the
plot beside it.

Decide which the log line means, then make it say so:

- **Magnitude**, to match the plot — `np.hypot(U[:,0], U[:,1]).max()` on
  `results["node"]["U"].data.to_numpy(float)`. `plot.py:22-25` already computes this list;
  the value wanted is its max.
- **Component**, if the intent is the largest DOF value — then rename the label, e.g.
  "Max nodal displacement (component)".

Separate from the `TypeError` at the same line (item 1), which is about `float()` on a
two-column DataFrame. Fixing that alone leaves this wrong.

### [ ] 29. `main.py` sits outside the installable package

Added 2026-08-02. `main.py` is at the repo root, so `pip install -e ".[dev]"` installs
`fe_solver` but not the launcher. Anyone installing the package without cloning gets the
solver with no way to start the GUI. It resolves today only because the working directory
is on `sys.path`:

```
fe_solver package: .../fe_solver/fe_solver/__init__.py
main module      : origin='.../fe_solver/main.py'
```

There is no `[project.scripts]` entry point, so `python main.py` from the repo root is the
only route.

**Conventional layout** — move the launcher into the package:

```
fe_solver/app.py          # load_user_config, APP_CONFIG, main()
```

```toml
[project.scripts]
fesolver = "fe_solver.app:main"
```

`fesolver` then works from anywhere. Adding `fe_solver/__main__.py` calling the same
`main()` also gives `python -m fe_solver`, matching the existing
`python -m fe_solver.core.solver` dev harness. A two-line `main.py` at the root that calls
`fe_solver.app.main()` keeps `python main.py` working if that stays the documented entry.

**Two decisions this forces:**

- **Where `config_user.json` lives.** `main.py:31` resolves it from `__file__`, so it
  currently lands at the repo root. Move the launcher into the package and the config
  follows it into `site-packages`, which is wrong for an installed tool. It wants the
  working directory or a platform config directory instead.
- **`os.path` vs pathlib.** The 0.2.1 CHANGELOG entry claims "File paths handled by
  pathlib" and the rest of the codebase does. `main.py` still uses `os.path` in both
  places.

Not blocking 0.2.3. The config path is the only real work; the rest is a move and four
lines of `pyproject.toml`.

### [ ] 17. Housekeeping

- [ ] **Version drift across four places.** Re-checked 2026-08-02:

      ```
      installed metadata   0.2.0     ← what version("fe_solver") returns
      pyproject.toml       0.2.1
      v0.2.2 tag           0.2.1     (bump missed at that release)
      CHANGELOG.md         0.2.3
      ```

      `main.py:24` passes `version("fe_solver")` into `app_config` and `gui.py:45` puts it
      in the window title, so **the GUI currently reads "FEsolver 0.2.0"**. Editable
      installs cache the metadata at install time — bumping `pyproject.toml` alone will
      not change what the window shows without a reinstall.
- [x] Add an MIT `LICENSE` file. Done 2026-08-02 — `LICENSE` added, `README.md` links to
      it again, and `pyproject.toml` declares `license = "MIT"` with
      `license-files = ["LICENSE"]`. Verified in a built wheel:
      `License-Expression: MIT`, `License-File: LICENSE`, file present in the archive.
- [ ] `solver.py:437` — `__main__` shadows the `model` module with the model dict

---

## P3 — Testing

### [ ] 18. Add an analytical patch test

A uniaxial plate under uniform tension where `σ = F/A` exactly.

**The model already exists and is verified.** `examples/worked_example.inp` is a 10×10×2 mm
plate under 2000 N, pinned at node 1 and rollered at node 2. The solver reproduces the
analytical answer exactly:

| Quantity | Analytical | FEsolver |
|---|---|---|
| σyy | 100 MPa | 100.0 |
| σxx, τxy | 0 | 0.0 |
| v at top edge | 0.00476190 mm | 0.004761904761904762 |
| u at right edge | −0.00142857 mm | −0.0014285714285714286 |
| Total reaction | −2000 N | −2000.0 |

Refining to four elements (centre node at 5,5) leaves the answer unchanged — 100.0 MPa in
every element, displacements identical to the last bit.

The test is now just asserting these values. Walkthrough in
[worked_example.md](worked_example.md).

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

Needs new derivation content — reactions as `{R} = [K]{u} - {F}`, why they are
recovered only at constrained DOFs, and what a residual check tests.

**Blocked on item 3.** Writing this now would document a residual check that validates
nothing. Do item 3 first.

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

### [ ] 26. Principal stress vectors are plotted 90° out

`solver.py:379-381` computes the principal direction used by the vector plot:

```python
angle = -0.5 * m.atan2(2 * Sxy, Sx - Sy)
opp = m.sin(angle) * s1
adj = m.cos(angle) * s1
```

`plot.py:98-105` then passes `opp` as the quiver **x** component and `adj` as the **y**
component. Two errors compound:

1. The sign on `angle` should be positive — the standard result is
   `θp = ½atan2(2τxy, σxx-σyy)`.
2. With the vector taken as `(x, y)`, the components should be `(cosθ, sinθ)`.
   The code supplies `(sinθ, cosθ)` — swapped.

Net effect is `(-sinθ, cosθ)` where `(cosθ, sinθ)` is wanted, which
is exactly a 90° rotation. Verified against the analytical principal direction across four
stress states:

| State | plotted vector | true vector | error |
|---|---|---|---|
| uniaxial y | (−100.0, 0.0) | (0.0, 100.0) | 90° |
| uniaxial x | (0.0, 100.0) | (100.0, 0.0) | 90° |
| pure shear | (−35.4, 35.4) | (35.4, 35.4) | 90° |
| general (80, 20, 30) | (−35.4, 85.4) | (85.4, 35.4) | 90° |

**`s_max`, `s_min` and `s_shear` are correct** — only the direction is wrong, so this
affects the "S [Max Principal]" quiver plot alone. Masked until now because that plot has
been broken since the `FieldOutputs` refactor (item 1).

Reproduce:

```bash
python -c "
import math as m
Sx, Sy, Sxy = 0, 100, 0
a = -0.5*m.atan2(2*Sxy, Sx-Sy); s1 = 100
print('plotted:', (m.sin(a)*s1, m.cos(a)*s1))
t = 0.5*m.atan2(2*Sxy, Sx-Sy)
print('true   :', (m.cos(t)*s1, m.sin(t)*s1))"
```

Documented as a limitation in [data_structures.md](data_structures.md) and
[worked_example.md](worked_example.md) until fixed.

### [ ] 27. Publish the documentation site

Added 2026-08-02. `mkdocs.yml` and `.github/workflows/docs.yml` are in place; a build has
been verified locally under `--strict` — 5 pages, no warnings. Remaining:

- [ ] **Enable Pages.** Settings → Pages → Source: **GitHub Actions**. Nothing publishes
      without it.
- [ ] **Get current docs onto `main`.** The workflow builds on push to `main`, which is
      behind `develop`. Either merge `develop` first, or use Actions → Run workflow
      against `develop` for the initial deploy.
- [ ] **Link the site from `README.md`** once live at
      `https://truanwillis.github.io/fe_solver/`.
- [ ] **Review the pin.** `mkdocs-material==9.7.7`. MkDocs 2.0 is a breaking release with
      no migration path, so an unpinned install would fail silently later.

`todo.md` and `roadmap.md` are excluded from the site. The workflow deletes them before
building and rewrites the 19 links pointing at them — 16 to `todo.md`, 2 to `roadmap.md`,
1 to `examples/worked_example.inp` — to GitHub blob URLs. **Any new link to either file
from a published doc needs the same treatment**, or `mkdocs build --strict` fails.

---

## Process

### [ ] 21. Green tests as a merge gate

Both branches currently ship failing tests, and the 0.2.3 CHANGELOG entry lists work that
isn't finished. Treat the suite as a gate rather than a record.

---

## Suggested order

Items **3, 4 and 7/12** change what the tool reports. Everything else is tidying.

1. Item 1 — unbreak `develop`
2. Item 3 — real residual check
3. Item 4 — static condensation rewrite
4. Items 6, 7, 11, 12 — input validation with clear messages (for a training tool, the
   error messages *are* the curriculum)
5. Item 5 — uppercase set names, then re-check item 2
6. Item 18 — patch test
7. Item 13 — vectorise assembly
