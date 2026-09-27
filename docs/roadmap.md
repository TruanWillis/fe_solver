# Roadmap

Direction for the next 12 months or so. Written on 2026-07-31 against `develop` at
`60d8757`. Line references are to that commit.

References such as (item 3) point to numbered entries in [todo.md](todo.md).

---

## Decisions in this roadmap

| Decision | Choice | Consequence |
|---|---|---|
| Capability direction | Deepen teaching, broaden 2D elements, and add 3D | Done in sequence as one path |
| Coding skills to build | Numerical methods and performance; architecture and typing | Phases 1 to 3 are built around these |
| Audience | Mainly the author now; later self-guided training, with no live sessions | Diagnostics and error messages are core features |
| Abaqus fidelity | Familiar, not compatible | Keep the `.inp` format and output names; reject unsupported syntax with a clear error |

Deferred: modal, thermal and nonlinear analysis; GUI improvements; packaging and
standalone executables. Each could be added later, but none should come before the
element work. Each would also add code that Phases 1 and 2 would have to carry.

---

## What blocks progress

The 3 capability goals depend on each other. 3D needs the element library work, and both
need the typed architecture work.

These parts of the code block that work:

| Location | Blocker |
|---|---|
| `elements.py:21-43` | One element hardcoded as a literal dict, with a closed-form `B` and no numerical integration |
| `model.py:231` | `dof_suffixes = ['u', 'v']` hardcoded |
| `solver.py:88` | The `"*"` marker forces object dtype and mixes text with numbers |
| `solver.py:264-265` | DOFs stored as text (`"12u"`) and decoded by slicing |
| `solver.py:156-167` | Dense `dof × dof` assembly using Python `.at[]` loops |

This sets the order of work: generalise the element code first, then add quadrilateral
elements, then 3D. Adding 3D to the current structure would mean writing the same code
twice.

If time runs out, the end of Phase 2 is a good place to stop. The tool will already be
much better, and 3D can still be added to it later without a rewrite.

---

## Phase 0: stabilise

A short phase that must be finished before the others.

It covers the P0 and P1 items in [todo.md](todo.md).

Phase 2 rewrites the element code, and the residual check is meant to catch mistakes in
that rewrite. The check currently tests nothing (item 3) and one test fails (item 2), so
there is no way to know whether a rewrite is correct.

Exit criteria:

- [ ] `pytest` passes on both branches (items 1, 2, 5)
- [ ] The residual check is a real free-DOF norm (item 3)
- [ ] The static condensation rewrite is done (item 4)
- [ ] An analytical patch test is in place (item 18). Every later phase checks against it
- [ ] CI runs `pytest` on every push, so item 21 does not depend on remembering to run it

---

## Phase 1: typed model core

Skill focus: architecture and typing. Phases 2 and 4 depend on it.

Replace the model dictionary with dataclasses: `Node`, `Element`, `Material`, `Section`
and `Model`. Add a `DofMap` that maps nodes to indices. It takes the number of dimensions
as a parameter, instead of assuming 2 DOFs at each node.

This removes, in one step:

- the `"*"` marker (item 14)
- the `f"{node}{dof}"` text labels (item 15)
- the hardcoded `dof_suffixes`
- the separate `label_to_idx`, `node_headings` and `active_mask` structures

Item 11, where a second material is silently ignored, goes away once materials are
objects.

This also helps readability. `element.material.youngs_modulus` is clearer to a
non-developer than `model["elasticity"][0]`.

Separate calculation from display. Pandas currently does both, which is why assembly is
slow. Calculate in numpy, and build labelled DataFrames only for display. This keeps the
labelled DOF indices and removes the O(dof²) dense `.at[]` loop (item 13).

Exit criteria:

- [ ] No dictionary-based model access outside the parser
- [ ] `DofMap(dim=2)` works, and `dim=3` needs only a different parameter
- [ ] All existing tests still pass, with the same results
- [ ] Type hints throughout `core/`

---

## Phase 2: isoparametric element framework

Skill focus: numerical methods. This phase has the most teaching value.

Build the general code:

- shape functions `N(ξ)` and derivatives `dN/dξ` for each element type
- the Jacobian, and `B` evaluated at a Gauss point
- `K = Σ_gp Bᵀ D B · det(J) · w · t`

### Order of work

1. Reimplement S3 with the new code. The constant strain triangle (CST) is exact with a
   single Gauss point, so the results must match the current ones to machine precision.
   The test fixtures already exist.
2. Add CPS4. A quadrilateral then needs only a shape function table and an integration
   rule.
3. Optionally add CPS6 or CPS8 later.

### What it allows

With 2 element types, the training material can show:

- S3 and CPS4 on the same mesh, compared with a known stress concentration factor
- shear locking under full and reduced integration
- how integration order affects accuracy and run time
- mesh convergence studies where the element type matters as much as refinement

None of these are possible with one element type.

### Readability risk

An abstract base class with protocols is harder for a non-developer to follow than the
current dictionary. To limit this:

- keep each element class a short, readable table of shape functions
- keep the shared code in one place
- use no more than one level of inheritance

Exit criteria:

- [ ] S3 in the new framework matches the current results to machine precision
- [ ] CPS4 passes the patch test and an analytical benchmark
- [ ] A comparison page: S3 and CPS4 on the same mesh, against the textbook Kt

---

## Phase 3: performance and sparse matrices

Skill focus: numerical methods and performance. Must be finished before 3D.

3D models have many more DOFs, and dense assembly will not scale to them.

- Assemble in triplet (COO) form, then convert to CSR. This may also read more clearly than
  the current nested loop, because each element's contribution to the global matrix is
  listed directly.
- Use `scipy.sparse`, which is a new dependency.
- Profile the code as a planned exercise. Conditioning and solver stability belong in this
  phase.

Keep the hand-written Gaussian elimination as the teaching solver, and use the sparse
solver for larger models. This extends the existing `fe_solver` and numpy setting.

Exit criteria:

- [ ] `plate_hole_disp_refined_mesh.inp` solves in a reasonable time
- [ ] Memory use is no longer O(dof²)
- [ ] The user can still choose the solver, and the choice is documented

---

## Phase 4: 3D

Built on Phases 1 to 3, so it adds to the code instead of replacing it.

- C3D4 tetrahedron, using the Phase 2 framework
- `DofMap(dim=3)`
- `D` becomes a 6 × 6 matrix
- Parser: complete the `# TODO: Update to 3D when ready` markers at `model.py:83` and `:87`

Most of the work in this phase is plotting. `plot.py` is 2D throughout, and matplotlib's 3D
mesh support is poor. Plan for most of the phase to go on plotting, and expect to try an
alternative such as PyVista.

---

## Diagnostics throughout

Error messages are part of the training material. This work runs alongside every phase
from Phase 0.

Training is self-guided, so the software has to explain its own failures. This makes
items 6, 7 and 12 core features. Negative element area, unsupported `*Boundary` syntax and
singular systems must each give a message that names the FEA cause:

```
Model is under-constrained — the structure can still move as a rigid body.
Check that boundary conditions restrain all rigid-body modes.
```

Because FEsolver aims to be familiar, not compatible, it should reject unsupported Abaqus
syntax with a clear error and a link to [keywords.md](keywords.md). At present
`gen_boundary` ignores it silently (item 7).

Keep [theory.md](theory.md) up to date with the code as each phase is finished. It is
only useful while it is accurate.

---

## Main risk

Do not start 3D early. Phases 1 to 3 each reduce the work needed for 3D. Starting 3D first
would mean writing it again after Phase 2.
