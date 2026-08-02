# Keywords

Reference for the `.inp` keywords FEsolver understands. The format follows Abaqus so that
models are familiar, but FEsolver implements only the subset below — it is **not**
Abaqus-compatible. See [theory.md](theory.md) for what the solver does with these inputs.

## How the input file is read

- Lines beginning with a single `*` are keywords. Lines beginning with `**` are comments.
- A keyword's data lines are every line following it up to the next `*`.
- **Keywords not listed below are skipped silently** — `*Part`, `*Assembly`, `*Step`,
  `*Output` and the rest of what Abaqus/CAE writes. This is why CAE files read directly.
- Keyword, set and material names are all matched case-insensitively. Names are
  lowercased when parsed, so `_PickedSet9` and `_PICKEDSET9` are one set, as in Abaqus.
  Defining the same name twice adds to the set rather than replacing it.

| Keyword | Purpose |
|---|---|
| [\*BOUNDARY](#boundary) | Prescribe displacement constraints at nodes |
| [\*CLOAD](#cload) | Apply concentrated forces at nodes |
| [\*ELASTIC](#elastic) | Define linear elastic moduli |
| [\*ELEMENT](#element) | Define elements by their nodes |
| [\*ELSET](#elset) | Assign elements to an element set |
| [\*MATERIAL](#material) | Begin a material definition |
| [\*NODE](#node) | Define nodes by their coordinates |
| [\*NSET](#nset) | Assign nodes to a node set |
| [\*SHELL SECTION](#shell-section) | Define section thickness and material |

---

## \*BOUNDARY

Prescribe boundary conditions at nodes. No parameters.

**Data lines** — repeat as necessary:

```
Node number or node set label
First degree of freedom constrained
Last degree of freedom constrained
Boundary value (only for a nonzero boundary condition)
```

DOF `1` is translation in x, `2` is translation in y.

**Limitations** — see item 7 in [todo.md](todo.md):

- Only a **single** DOF per data line is applied; the first and last fields must be equal.
  A range such as `7, 1, 2` is accepted by the parser but **silently ignored**, leaving
  the model under-constrained.
- Only DOFs `1` and `2` exist in a 2D plane-stress model. Higher values written by
  Abaqus/CAE (`3` to `6`) are ignored.
- `ENCASTRE` and `PINNED` are **not supported** and raise an error. Constrain each DOF
  explicitly.

[Back to top](#keywords)

## \*CLOAD

Apply concentrated forces at nodes. No parameters.

**Data lines** — repeat as necessary:

```
Node number or node set label
Degree of freedom
Load magnitude
```

DOF `1` is force in x, `2` is force in y.

If a node set is named, the magnitude is applied to **every node in the set** — it is not
divided between them.

[Back to top](#keywords)

## \*ELASTIC

Define linear elastic moduli. No parameters.

**Data line:**

```
Young's modulus, E
Poisson's ratio
```

[Back to top](#keywords)

## \*ELEMENT

Define elements by giving their nodes.

**Required parameter:** `TYPE` — the element type. Only **S3** is available.

**Data lines** — repeat as necessary:

```
Element number
First node number
Second node number
Third node number
```

> **`ELSET` is not supported on this keyword.** `*Element, type=S3, elset=PLATE` causes the
> type to be read as `s3, elset`, which fails with `KeyError: 's3, elset'` when the element
> stiffness matrix is built. Define the set separately with [\*ELSET](#elset).

[Back to top](#keywords)

## \*ELSET

Assign elements to an element set.

**Required parameter:** `ELSET` — the name of the set.

**Optional parameter:** `GENERATE` — data lines give a first element, a last element and an
integer increment; all elements from first to last in those steps are added.

**Data lines** without `GENERATE` — a list of elements, repeated as necessary.

**Data lines** with `GENERATE`:

```
First element in set
Last element in set
Increment (default 1)
```

> **Nested sets are not supported.** Naming a previously defined element set inside another
> set's data line is **silently ignored** — only numeric entries are kept. The same applies
> to [\*NSET](#nset).

[Back to top](#keywords)

## \*MATERIAL

Begin a material definition.

**Required parameter:** `NAME` — the label used to refer to the material. Names must be
unique.

> **Only one material is supported.** The name is recorded but never linked to a section or
> to elements, and the properties from every [\*ELASTIC](#elastic) block are collected into
> a single list. If a second material is defined, **all elements silently use the first**.
> See item 11 in [todo.md](todo.md).

[Back to top](#keywords)

## \*NODE

Define nodes by their coordinates. No parameters.

**Data lines** — repeat as necessary:

```
Node number
First coordinate
Second coordinate
```

A third coordinate may be present — Abaqus/CAE writes one even for 2D models — and is
ignored. FEsolver is 2D plane-stress only.

> **`NSET` is not supported on this keyword.** `*Node, nset=PLATE` is accepted but the
> parameter is **silently ignored** — no node set is created. Define the set separately
> with [\*NSET](#nset).

[Back to top](#keywords)

## \*NSET

Assign nodes to a node set. Node sets are how boundary conditions and loads are applied
to groups of nodes.

**Required parameter:** `NSET` — the name of the set.

**Optional parameter:** `GENERATE` — data lines give a first node, a last node and an
integer increment; all nodes from first to last in those steps are added.

**Data lines** without `GENERATE` — a list of nodes, repeated as necessary.

**Data lines** with `GENERATE`:

```
First node in set
Last node in set
Increment (default 1)
```

> **Set names are case-insensitive.** `_PickedSet9` and `_PICKEDSET9` are the same set, as
> in Abaqus. Repeating a name adds its nodes to the existing set rather than replacing it.

[Back to top](#keywords)

## \*SHELL SECTION

Define a shell cross-section.

**Required parameters:**

- `ELSET` — the element set the section applies to.
- `MATERIAL` — the material the shell is made of.

> The element set name is recorded but **not acted on** — the thickness below is applied to
> *every* element in the model, not just those in the named set. Sets defined with
> [\*ELSET](#elset) are parsed but never read by the solver.

**Data line** — required:

```
Shell thickness
```

Used directly in the element stiffness calculation, `[Kᵉ] = [B]ᵀ[D][B] · A · t`.
Abaqus/CAE writes a second value on this line (integration points through the thickness);
it is ignored.

[Back to top](#keywords)
