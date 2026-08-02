# Data Structures

How FEsolver represents a model internally, from the `.inp` file through to the results
object. A reference for reading the code — see [theory.md](theory.md) for what the solver
does with these structures, and [worked_example.md](worked_example.md) for them filled in
with real numbers.

---

## The three stages

```
  plate.inp                model dict                Solver                 results
 ─────────────  parse  ─────────────────  solve  ──────────────  store  ─────────────
  text file      ──▶     nested dicts      ──▶     DataFrames      ──▶     FieldOutputs
                         of plain Python           and arrays
```

| Stage | Produced by | Type |
|---|---|---|
| Input file | written by the user or Abaqus/CAE | text |
| Model | `model.call_gen_function()` | `dict` |
| Solution | `solver.Solver()` | object with DataFrame/array attributes |
| Results | `Solver.results` | `dict` of `FieldOutputs` |

---

## DOF labelling

Every degree of freedom is identified by a string label: node number followed by a
direction letter.

| Label | Meaning |
|---|---|
| `1u` | node 1, displacement in x |
| `1v` | node 1, displacement in y |
| `12v` | node 12, displacement in y |

Labels are ordered node-by-node, x before y, so a 4-node model has 8 DOFs in this order:

```
1u, 1v, 2u, 2v, 3u, 3v, 4u, 4v
```

This ordering is what makes assembly work: an element stiffness matrix carries the same
labels as the global matrix, so adding one into the other needs no index arithmetic.
`Solver.node_headings` holds the list.

Nodes must be numbered contiguously from 1, because the list is built with
`range(1, node_count + 1)`.

> The `.inp` file uses the Abaqus numeric convention instead — `1` for x, `2` for y. The
> translation happens in `assemble_dof_series()`.

---

## The model dictionary

Built by `ModelBuilder` in `model.py`, returned by `call_gen_function()`. Plain Python
types throughout — no numpy, no pandas — so it can be printed or serialised to JSON
directly.

| Key | Type | Contents |
|---|---|---|
| `nodes` | `{int: [float, float]}` | Node number → `[x, y]` coordinates |
| `elements` | `{int: dict}` | Element number → `{"nodes": [...], "type": str}`; the solver later adds `"K"` |
| `nodesets` | `{str: [int]}` | Set name → node numbers |
| `elementsets` | `{str: [int]}` | Set name → element numbers. **Parsed but never read** — item 25 in [todo.md](todo.md) |
| `section` | `dict` | `{"elementset": str, "material": str, "thickness": float}` |
| `material` | `{str: dict}` | Material name → empty dict. Name recorded only — item 11 in [todo.md](todo.md) |
| `elasticity` | `[float, float]` | `[E, ν]` — a flat list, so only one material is supported |
| `boundary` | `{int\|str: {str: float}}` | Node number *or* set name → `{dof: value}` |
| `load` | `{int\|str: {str: float}}` | Same shape as `boundary` |
| `node count` | `int` | Number of nodes |
| `element count` | `int` | Number of elements |
| `dof` | `int` | `node count × 2` |
| `label_to_idx` | `{str: int}` | DOF label → position in the global vector |
| `active_mask` | `[bool]` | One entry per DOF. `True` = free, `False` = constrained |

**`boundary` and `load` keys are mixed-type.** A key is an `int` when the `.inp` named a
node directly and a `str` when it named a set. `assemble_dof_series()` checks `nodesets`
first and falls back to `int()`.

**The inner DOF keys are strings.** `{"1": 0.0, "2": 0.0}` means DOF 1 and DOF 2, taken
verbatim from the input file text.

**`active_mask` is the single source of truth for what gets solved.** Built in
`gen_solver_maps()` by walking the boundary conditions and switching off every constrained
DOF. Matrix reduction, the reduced index list and reaction recovery all derive from it.

---

## The Element object

One per element, constructed in `define_element_stiffness()` and stored at
`model["elements"][n]["K"]`.

| Attribute | Type | Contents |
|---|---|---|
| `element_structure` | `dict` | Shape function coefficients and matrix templates for this element type |
| `node_list` | `[int]` | The element's node numbers, in input order |
| `E`, `v`, `t` | `float` | Young's modulus, Poisson's ratio, thickness |
| `area` | `float` | Element area. **Signed** — negative for clockwise nodes, item 6 in [todo.md](todo.md) |
| `B` | `ndarray` `(3, 6)` | Strain-displacement matrix |
| `D` | `ndarray` `(3, 3)` | Stress-strain matrix |
| `element_stiffness_matrix` | `DataFrame` `(6, 6)` | `[Kᵉ]`, indexed by DOF label |

`element_stiffness_matrix` is the only pandas object here, and is pandas specifically so
it can carry DOF labels into assembly.

---

## Inside the Solver

Working state during the solve — what a debugger shows when stepping through.

| Attribute | Type | Contents |
|---|---|---|
| `node_headings` | `[str]` | All DOF labels in order — `["1u", "1v", …]` |
| `node_index` / `element_index` | `[str]` | Row labels for results — `["n1", …]` / `["e1", …]` |
| `global_stiffness_matrix` | `DataFrame` `(dof, dof)` | `[K]`, labelled both axes |
| `global_stiffness_matrix_save` | `DataFrame` | Which elements contributed to each entry, as text. Only when `save_matrix` is on |
| `global_stiffness_matrix_reduced` | `ndarray` | `[K_ff]` — free DOFs only |
| `forces_reduced` | `ndarray` | `{F_f}` |
| `index_reduced` | `ndarray` of `str` | DOF labels surviving reduction |
| `displacements` | `Series` | Full displacement vector, indexed by DOF label |
| `forces` | `Series` → `ndarray` | Full force vector |
| `stress_normal` | `DataFrame` | Per-element `σxx, σyy, τxy` |
| `results` | `dict` | The output structure, below |

### Two traps

**`forces` changes type mid-solve.** It starts as a labelled `Series` and is replaced with
a plain `ndarray` inside `reduce_matrix()`. Code before reduction can use labels; code
after cannot.

**`displacements` has `object` dtype.** It is initialised with the string `"*"` in every
position to mean unknown, and those are replaced with floats as boundary conditions and
solved values arrive. Mixing strings and floats forces `object` dtype, which is why
`.astype(np.float64)` appears before any arithmetic on it. See item 14 in
[todo.md](todo.md).

---

## The results structure

`Solver.results` is keyed first by where the quantity lives, then by an Abaqus-style
output name:

```python
results = {
    "node":    {"U":  FieldOutputs, "RF": FieldOutputs},
    "element": {"S":  FieldOutputs, "SP": FieldOutputs, "SM": FieldOutputs},
}
```

| Key | Name | Quantity | Row index | Columns |
|---|---|---|---|---|
| `node` → `U` | Displacements | u, v per node | `n1`, `n2`, … | `u`, `v` |
| `node` → `RF` | Reaction Force | Nodal reactions | `n1`, `n2`, … | `u`, `v` |
| `element` → `S` | Normal Stress | In-plane stress | `e1`, `e2`, … | `s1`, `s2`, `s12` |
| `element` → `SP` | Stress Principal | Principal stress | `e1`, `e2`, … | `s_max`, `s_min`, `s_shear`, `a`, `opp`, `adj` |
| `element` → `SM` | Stress Mises | von Mises stress | `e1`, `e2`, … | `s_mises` |

Names mirror Abaqus field output identifiers. `S` columns are named `s1`/`s2`/`s12` but
hold σxx, σyy and τxy — they are *not* principal stresses. Principal values live under
`SP`.

### FieldOutputs

A wrapper defined at the top of `solver.py`:

| Attribute | Type | Contents |
|---|---|---|
| `name` | `str` | Short identifier — `"U"`, `"S"` |
| `description` | `str` | Human-readable name — `"Displacements"` |
| `field_type` | `str` | `"node"` or `"element"` |
| `data` | `DataFrame` | The values |
| `components` | `[str]` | Column names, derived from `data` |

Reading a single value:

```python
s.results["element"]["S"].data.loc["e1", "s1"]     # σxx in element 1
s.results["node"]["U"].data.loc["n3", "v"]         # y-displacement of node 3
```

`__repr__` gives a one-line summary:

```
FieldOutput(name='S', type='element', components=['s1', 's2', 's12'], size=2)
```

> **`SP` columns `a`, `opp` and `adj`** exist only to feed the principal stress vector
> plot. `a` is the principal angle in radians; `opp` and `adj` are its components. They are
> currently computed 90° from the true principal axis. `s_max`, `s_min` and `s_shear` are
> unaffected. See item 26 in [todo.md](todo.md).

---

## Planned changes

These structures are deliberately plain, which makes them easy to inspect but leaves the
meaning implicit — `model["elasticity"][0]` is Young's modulus only by convention.

Phase 1 of the [roadmap](roadmap.md) replaces the model dictionary with typed dataclasses
(`Node`, `Element`, `Material`, `Section`, `Model`) and a dimension-aware `DofMap` in
place of the string DOF labels. That work also removes the `"*"` sentinel and the
mid-solve type change above.
