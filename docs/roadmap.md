# Roadmap

Direction for the next ~12 months. Written 2026-07-31 against `develop` @ `60d8757`.

References like *(item 3)* point at numbered entries in [todo.md](todo.md).

---

## Decisions this roadmap encodes

| Decision | Choice | Consequence |
|---|---|---|
| Capability direction | Deepen teaching **+** broaden 2D elements **+** 3D | Sequenced as one path, not three tracks |
| Coding skills to build | Numerical methods & performance; architecture & typing | Phases 1–3 are built around these |
| Audience | Mainly the author now; later **self-guided** training, no live sessions | Diagnostics and error messages become core product, not polish |
| Abaqus fidelity | Familiar, not compatible | Keep the `.inp` look and output naming; reject unsupported syntax loudly |

**Deferred:** modal, thermal and nonlinear analysis; GUI polish; packaging and standalone
executables. Each is defensible later, but none belongs ahead of the element
generalisation, and each adds surface area Phases 1–2 would have to carry.

---

## The core problem

The three capability goals collapse into one path. The element-library work is the
prerequisite for 3D, and the typed-architecture work makes both possible.

What blocks it today:

| Location | Blocker |
|---|---|
| `elements.py:21-43` | One element hardcoded as a literal dict, closed-form `B`, no numerical integration |
| `model.py:231` | `dof_suffixes = ['u', 'v']` hardcoded |
| `solver.py:88` | `"*"` sentinel forces object-dtype and string/float mixing |
| `solver.py:264-265` | DOFs encoded as strings (`"12u"`) and decoded by slicing |
| `solver.py:156-167` | Dense `dof × dof` assembly via Python `.at[]` loops |

The sequencing is therefore forced:

> **Generalise the element abstraction → quads fall out → 3D falls out.**

Attempting 3D on the current structure means writing the same code twice.

**Natural stopping point:** end of Phase 2. If time runs out there, the tool is already
substantially better and 3D remains an extension rather than a rewrite.

---

## Phase 0 — Stabilise

*Short. Blocks everything else.*

The P0/P1 items in [todo.md](todo.md).

Phase 2 reimplements the element formulation from scratch and the residual check is the
safety net for it. That check is vacuous (item 3) and two tests are red (item 2), so
there is currently no way to know whether a reimplementation is correct.

**Exit criteria:**

- [ ] `pytest` green on both branches (items 1, 2, 5)
- [ ] Residual check is a real free-DOF norm (item 3)
- [ ] Static condensation rewrite done (item 4)
- [ ] Analytical patch test in place (item 18) — the reference every later phase checks against
- [ ] CI running `pytest` on push (enforces item 21 mechanically rather than by discipline)

---

## Phase 1 — Typed model core

*Skill focus: architecture & typing. Prerequisite for Phases 2 and 4.*

Replace the dict-model with dataclasses — `Node`, `Element`, `Material`, `Section`,
`Model` — and introduce a `DofMap` that owns node→index mapping and is **parameterised by
dimension** rather than hardcoded to two DOFs per node.

Deleted in one pass: the `"*"` sentinel (item 14), the `f"{node}{dof}"` string encoding
(item 15), the `dof_suffixes` hardcode, and the scattered `label_to_idx` /
`node_headings` / `active_mask` juggling. Item 11 (multi-material silently wrong)
disappears once materials are real objects.

This serves readability rather than fighting it: `element.material.youngs_modulus` reads
better to a non-developer than `model["elasticity"][0]`.

**Separate the compute representation from the presentation representation.** Pandas
currently does both, which is why assembly is slow. Compute in numpy; render labelled
DataFrames for display. Labelled DOF indices are retained while the O(dof²) dense `.at[]`
loop goes away (item 13).

**Exit criteria:**

- [ ] No dict-based model access outside the parser
- [ ] `DofMap(dim=2)` works; `dim=3` is a parameter, not a rewrite
- [ ] All existing tests still pass unchanged in behaviour
- [ ] Type hints throughout `core/`

---

## Phase 2 — Isoparametric element framework

*Skill focus: numerical methods. The largest teaching payoff in the plan.*

Build the general machinery:

- Shape functions `N(ξ)` and derivatives `dN/dξ`, per element type
- Jacobian, and `B` evaluated at a Gauss point
- `K = Σ_gp Bᵀ D B · det(J) · w · t`

### Order of work

1. **Reimplement S3 through the new machinery.** CST is exact with a single Gauss point,
   so this must reproduce current results to machine precision. The fixtures already
   exist.
2. **Add CPS4.** A quad becomes a shape-function table and a quadrature rule, not a new
   solver.
3. Optionally CPS6 / CPS8 later.

### What it unlocks

With one element type, none of the following can be demonstrated. With both:

- Same mesh, S3 vs CPS4, against a known stress concentration factor
- Shear locking under full vs reduced integration
- Effect of integration order on accuracy and cost
- Mesh convergence studies showing element choice mattering as much as refinement

### Readability risk

An abstract base with protocols is harder for a non-developer to follow than the current
flat dict. Mitigate by keeping each concrete element class a short, readable table of
shape functions, putting the machinery in one place, and capping inheritance at one level.

**Exit criteria:**

- [ ] S3 via the framework matches pre-refactor results to machine precision
- [ ] CPS4 validated against the patch test and an analytical benchmark
- [ ] A worked comparison doc: S3 vs CPS4 on the same mesh vs textbook Kt

---

## Phase 3 — Performance and sparsity

*Skill focus: numerical methods & performance. Gate before 3D.*

Required before Phase 4 — 3D DOF counts explode and dense assembly walls immediately.

- Triplet (COO) assembly → CSR. Arguably reads better than the current nested loop:
  "each element contributes to these global positions" is what the triplet form states.
- `scipy.sparse` — a new dependency.
- Profiling as an explicit exercise. Conditioning and solver stability belong here.

Keep the hand-written Gaussian elimination as the teaching solver and sparse as the
production path — an extension of the existing `fe_solver` / numpy config toggle.

**Exit criteria:**

- [ ] `plate_hole_disp_refined_mesh.inp` solves in reasonable time
- [ ] Memory no longer O(dof²)
- [ ] Solver choice remains user-visible and documented

---

## Phase 4 — 3D

*An extension rather than a rewrite.*

- C3D4 tet through the Phase 2 framework
- `DofMap(dim=3)`
- `D` matrix becomes 6×6
- Parser: act on the `# TODO: Update to 3D when ready` markers at `model.py:83` and `:87`

**The real cost is plotting, not mechanics.** `plot.py` is 2D throughout and matplotlib's
3D mesh support is poor. Budget the majority of this phase there, and expect to evaluate
an alternative such as PyVista.

---

## Cross-cutting: diagnostics are the curriculum

Runs alongside everything from Phase 0 onward, not a phase of its own.

Training use is self-guided, so the software has to explain its own failures. That
promotes items 6, 7 and 12 from tidying to core product. Negative element area,
unsupported `*Boundary` syntax and singular systems must each produce a message that
names the FEA cause rather than merely refusing:

```
Model is under-constrained — the structure can still move as a rigid body.
Check that boundary conditions restrain all rigid-body modes.
```

The "familiar, not compatible" decision makes this cleaner: reject unsupported Abaqus
syntax loudly with a pointer to [keywords.md](keywords.md), rather than silently ignoring
it as `gen_boundary` does today (item 7).

Keep [theory.md](theory.md) in step with the code as each phase lands — its value depends
entirely on staying accurate.

---

## Principal risk

**Do not start 3D early.** Everything in Phases 1–3 makes 3D cheaper. Nothing about doing
3D first makes the rest cheaper.
