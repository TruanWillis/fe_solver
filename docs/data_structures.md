# Data structures

This page describes how FEsolver stores a model, from the `.inp` file to the results.
Use it as a reference when you read the code. [theory.md](theory.md) explains what the
solver does with these structures. [worked_example.md](worked_example.md) shows them
filled in with real numbers.

---

## From input file to results

| Stage | Produced by | Type |
|---|---|---|
| Input file | Written by the user or Abaqus/CAE | Text |
| Model | `model.call_gen_function()` | `dict` of plain Python types |
| Solution | `solver.Solver()` | Object with DataFrame and array attributes |
| Results | `Solver.results` | `dict` of `FieldOutputs` |

---

## DOF labels

Each degree of freedom (DOF) has a text label: the node number followed by a direction
letter.

| Label | Meaning |
|---|---|
| `1u` | Node 1, displacement in x |
| `1v` | Node 1, displacement in y |
| `12v` | Node 12, displacement in y |

Labels are in node order, with x before y. A 4-node model has 8 DOFs in this order:

```
1u, 1v, 2u, 2v, 3u, 3v, 4u, 4v
```

An element stiffness matrix uses the same labels as the global matrix, so assembly adds
entries by label with no index arithmetic. `Solver.node_headings` holds the list.

Nodes must be numbered from 1 with no gaps, because the list is built with
`range(1, node_count + 1)`. See item 34 in [todo.md](todo.md).

The `.inp` file uses the Abaqus numbers instead: 1 for x, 2 for y.
`assemble_dof_series()` converts them to `u` and `v`.

---

## The model dictionary

`ModelBuilder` in `model.py` builds the model, and `call_gen_function()` returns it. It
holds plain Python types only, with no numpy or pandas, so you can print it or save it as
JSON.

| Key | Type | Contents |
|---|---|---|
| `nodes` | `{int: [float, float]}` | Node number to `[x, y]` coordinates |
| `elements` | `{int: dict}` | Element number to `{"nodes": [...], "type": str}`. The solver adds `"K"` later |
| `nodesets` | `{str: [int]}` | Set name to node numbers |
| `elementsets` | `{str: [int]}` | Set name to element numbers. Read but never used, see item 25 in [todo.md](todo.md) |
| `section` | `dict` | `{"elementset": str, "material": str, "thickness": float}` |
| `material` | `{str: dict}` | Material name to an empty dict. Only the name is recorded, see item 11 |
| `elasticity` | `[float, float]` | `[E, ν]`. A single list, so only one material is supported |
| `boundary` | `{int\|str: {str: float}}` | Node number or set name to `{dof: value}` |
| `load` | `{int\|str: {str: float}}` | Same shape as `boundary` |
| `node count` | `int` | Number of nodes |
| `element count` | `int` | Number of elements |
| `dof` | `int` | `node count × 2` |
| `label_to_idx` | `{str: int}` | DOF label to position in the global vector |
| `active_mask` | `[bool]` | One entry for each DOF. `True` is free, `False` is constrained |

The keys of `boundary` and `load` can be `int` or `str`. A key is an `int` when the `.inp`
file names a node, and a `str` when it names a set. `assemble_dof_series()` checks
`nodesets` first, then tries `int()`.

The inner DOF keys are text. `{"1": 0.0, "2": 0.0}` means DOF 1 and DOF 2, as written in
the input file.

`active_mask` decides what gets solved. `gen_solver_maps()` builds it, and matrix reduction
and the reduced index list both come from it. Reaction forces do not use it: they are
reported at every node.

---

## The `Element` object

`define_element_stiffness()` creates one for each element and stores it at
`model["elements"][n]["K"]`.

| Attribute | Type | Contents |
|---|---|---|
| `element_structure` | `dict` | Shape function coefficients and matrix templates for the element type |
| `node_list` | `[int]` | The element's node numbers, in input order |
| `E`, `v`, `t` | `float` | Young's modulus, Poisson's ratio, thickness |
| `area` | `float` | Element area. Negative for clockwise nodes, see item 6 in [todo.md](todo.md) |
| `B` | `ndarray` `(3, 6)` | Strain-displacement matrix |
| `D` | `ndarray` `(3, 3)` | Stress-strain matrix |
| `element_stiffness_matrix` | `DataFrame` `(6, 6)` | `[Kᵉ]`, indexed by DOF label |

`element_stiffness_matrix` is the only pandas object here. It is a DataFrame so it can
carry DOF labels into assembly.

---

## Inside `Solver`

These attributes hold the working state during the solve.

| Attribute | Type | Contents |
|---|---|---|
| `node_headings` | `[str]` | All DOF labels in order: `["1u", "1v", …]` |
| `node_index`, `element_index` | `[str]` | Row labels for results: `["n1", …]`, `["e1", …]` |
| `global_stiffness_matrix` | `DataFrame` `(dof, dof)` | `[K]`, labelled on both axes |
| `global_stiffness_matrix_save` | `DataFrame` | Which elements contribute to each entry, as text. Only when `save_matrix` is on |
| `global_stiffness_matrix_reduced` | `ndarray` | `[K_ff]`, free DOFs only |
| `forces_reduced` | `ndarray` | `{F_f}` |
| `index_reduced` | `ndarray` of `str` | DOF labels left after reduction |
| `displacements` | `Series` | Full displacement vector, indexed by DOF label |
| `forces` | `Series`, then `ndarray` | Full force vector |
| `stress_normal` | `DataFrame` | `σxx, σyy, τxy` for each element |
| `results` | `dict` | The results, described below |

### How `forces` and `displacements` change during the solve

`forces` starts as a labelled `Series`. `reduce_matrix()` replaces it with a plain
`ndarray`, so code after reduction cannot use labels. In a model with no loads,
`reduce_matrix()` sets it to `[K]` multiplied by the prescribed displacements. This makes
the reaction forces wrong for those models, see item 32 in [todo.md](todo.md).

`displacements` starts with the text `"*"` at every DOF to mark it as unknown. Boundary
conditions and solved values then replace the `"*"` with numbers. The mix of text and
numbers gives the `Series` the `object` dtype, which is why `.astype(np.float64)` comes
before any arithmetic on it. Under pandas 3 the `Series` gets the `str` dtype instead, and
the solve fails. See items 14 and 31.

`stress_normal` is the same object as `results["element"]["S"].data`, not a copy. A change
to one changes the other. See item 28.

---

## The results structure

`Solver.results` is keyed first by where the quantity is stored, then by an Abaqus-style
output name:

```python
results = {
    "node":    {"U":  FieldOutputs, "RF": FieldOutputs},
    "element": {"S":  FieldOutputs, "SP": FieldOutputs, "SM": FieldOutputs},
}
```

| Key | Name | Quantity | Row index | Columns |
|---|---|---|---|---|
| `node`, `U` | Displacements | u and v at each node | `n1`, `n2`, … | `u`, `v` |
| `node`, `RF` | Reaction Force | Nodal reactions, at every node | `n1`, `n2`, … | `u`, `v` |
| `element`, `S` | Normal Stress | In-plane stress | `e1`, `e2`, … | `s1`, `s2`, `s12` |
| `element`, `SP` | Stress Principal | Principal stress | `e1`, `e2`, … | `s_max`, `s_min`, `s_shear`, `a`, `opp`, `adj` |
| `element`, `SM` | Stress Mises | von Mises stress | `e1`, `e2`, … | `s_mises` |

The names follow Abaqus field output names. The `S` columns are named `s1`, `s2` and `s12`
but hold σxx, σyy and τxy. They are not principal stresses. Principal values are in `SP`.

### FieldOutputs

`FieldOutputs` is defined at the top of `solver.py`.

| Attribute | Type | Contents |
|---|---|---|
| `name` | `str` | Short name: `"U"`, `"S"` |
| `description` | `str` | Readable name: `"Displacements"` |
| `field_type` | `str` | `"node"` or `"element"` |
| `data` | `DataFrame` | The values |
| `components` | `[str]` | Column names, taken from `data` |

To read a single value:

```python
s.results["element"]["S"].data.loc["e1", "s1"]     # σxx in element 1
s.results["node"]["U"].data.loc["n3", "v"]         # y-displacement of node 3
```

`__repr__` gives a one-line summary:

```
FieldOutput(name='S', type='element', components=['s1', 's2', 's12'], size=2)
```

The `SP` columns `a`, `opp` and `adj` are only used by the principal stress vector plot.
`a` is the principal angle in radians, and `opp` and `adj` are its components. They are
currently 90° from the true principal direction. `s_max`, `s_min` and `s_shear` are
correct. See item 26 in [todo.md](todo.md).

---

## Planned changes

These structures are plain dictionaries and lists, so their meaning is not stated in the
code. `model["elasticity"][0]` is Young's modulus only by convention.

Phase 1 of the [roadmap](roadmap.md) replaces the model dictionary with typed dataclasses
(`Node`, `Element`, `Material`, `Section`, `Model`). It also replaces the text DOF labels
with a `DofMap` that works in 2D or 3D. That work removes the `"*"` marker and the change of
type for `forces` during the solve.
