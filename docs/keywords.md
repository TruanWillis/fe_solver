# Keywords

This page lists the `.inp` keywords FEsolver reads. The format follows Abaqus so the input
looks familiar, but FEsolver reads only the keywords below. It is not compatible with
Abaqus. [theory.md](theory.md) explains what the solver does with the input.

## How FEsolver reads the input file

A line that starts with one `*` is a keyword. A line that starts with `**` is a comment.
A keyword's data lines are all the lines after it, up to the next `*`.

FEsolver skips any keyword not listed on this page, with no warning. This includes
`*Part`, `*Assembly`, `*Step`, `*Output` and the other keywords Abaqus/CAE writes. This
is why FEsolver can read CAE files directly.

Keyword, set and material names are not case-sensitive. FEsolver changes them to lower
case when it reads them, so `_PickedSet9` and `_PICKEDSET9` are the same set, as in
Abaqus. If you define the same set name twice, FEsolver adds to the set instead of
replacing it.

| Keyword | Purpose |
|---|---|
| [\*BOUNDARY](#boundary) | Sets displacement constraints at nodes |
| [\*CLOAD](#cload) | Applies concentrated forces at nodes |
| [\*ELASTIC](#elastic) | Defines linear elastic properties |
| [\*ELEMENT](#element) | Defines elements by their nodes |
| [\*ELSET](#elset) | Assigns elements to an element set |
| [\*MATERIAL](#material) | Starts a material definition |
| [\*NODE](#node) | Defines nodes by their coordinates |
| [\*NSET](#nset) | Assigns nodes to a node set |
| [\*SHELL SECTION](#shell-section) | Defines section thickness and material |

---

## \*BOUNDARY

Sets displacement constraints at nodes. It has no parameters.

Data lines, repeated as needed:

```
Node number or node set label
First degree of freedom constrained
Last degree of freedom constrained
Boundary value (only for a nonzero boundary condition)
```

Degree of freedom (DOF) 1 is translation in x. DOF 2 is translation in y.

Each data line constrains one DOF, so the first and last DOF must be the same. If you give
a range, such as `7, 1, 2`, FEsolver ignores the line and gives no error. The model is then
under-constrained. See item 7 in [todo.md](todo.md).

You must give the last DOF. A line such as `7, 1` is valid in Abaqus, but FEsolver stops
with an `IndexError` that does not name the problem. See item 35.

A 2D plane-stress model has DOFs 1 and 2 only. FEsolver ignores DOFs 3 to 6, which
Abaqus/CAE writes.

FEsolver does not support `ENCASTRE` or `PINNED`, and stops with an error if you use them.
Constrain each DOF on its own line instead.

[Back to top](#keywords)

## \*CLOAD

Applies concentrated forces at nodes. It has no parameters.

Data lines, repeated as needed:

```
Node number or node set label
Degree of freedom
Load magnitude
```

DOF 1 is force in x. DOF 2 is force in y.

If you name a node set, FEsolver applies the full magnitude to every node in the set. It
does not divide the load between them.

If the node or set does not exist, FEsolver stops with an error that does not name the
problem. Check the spelling. See item 35 in [todo.md](todo.md).

[Back to top](#keywords)

## \*ELASTIC

Defines linear elastic properties. It has no parameters.

Data line:

```
Young's modulus, E
Poisson's ratio
```

[Back to top](#keywords)

## \*ELEMENT

Defines elements by their nodes.

Required parameter: `TYPE`, the element type. `S3` is the only type available.

Data lines, repeated as needed:

```
Element number
First node number
Second node number
Third node number
```

FEsolver treats `S3` as a plane-stress constant strain triangle (CST) with 2 DOFs at each
node. In Abaqus, S3 is a shell element with 6 DOFs at each node, and the plane-stress
triangle is CPS3. FEsolver does not read `CPS3`.

Do not add `ELSET` to this keyword. FEsolver reads `*Element, type=S3, elset=PLATE` as type
`s3, elset`, then stops with `KeyError: 's3, elset'` when it builds the element stiffness
matrix. Define the set separately with [\*ELSET](#elset).

[Back to top](#keywords)

## \*ELSET

Assigns elements to an element set.

Required parameter: `ELSET`, the name of the set.

Optional parameter: `GENERATE`. Each data line then gives a first element, a last element
and an increment, and FEsolver adds every element in that range.

Without `GENERATE`, each data line is a list of elements. Repeat the line as needed.

With `GENERATE`, each data line is:

```
First element in set
Last element in set
Increment (default 1)
```

Write `generate` in lower case. FEsolver does not recognise `GENERATE` in upper case. It
reads the line as a list instead, so `1, 8, 1` gives elements 1 and 8 only, with no
warning. See item 33 in [todo.md](todo.md).

FEsolver does not support nested sets. If a data line names another set, FEsolver ignores
the name with no warning and keeps only the element numbers. The same applies to
[\*NSET](#nset).

[Back to top](#keywords)

## \*MATERIAL

Starts a material definition.

Required parameter: `NAME`, the label for the material. Names must be unique.

FEsolver supports one material only. It records the name but does not link it to a section
or to elements. It collects the values from every [\*ELASTIC](#elastic) block into one
list. If you define a second material, every element uses the first one, with no warning.
See item 11 in [todo.md](todo.md).

[Back to top](#keywords)

## \*NODE

Defines nodes by their coordinates. It has no parameters.

Data lines, repeated as needed:

```
Node number
First coordinate
Second coordinate
```

Abaqus/CAE writes a third coordinate, even for 2D models. FEsolver ignores it, because it
is 2D plane-stress only.

Number the nodes from 1 with no gaps, and list them in order. If you do not, the solve
fails or the plot draws the mesh wrongly. See item 34 in [todo.md](todo.md).

FEsolver ignores the `NSET` parameter on this keyword, with no warning. `*Node, nset=PLATE`
creates no node set. Define the set separately with [\*NSET](#nset).

[Back to top](#keywords)

## \*NSET

Assigns nodes to a node set. Boundary conditions and loads use node sets to act on groups
of nodes.

Required parameter: `NSET`, the name of the set.

Optional parameter: `GENERATE`. Each data line then gives a first node, a last node and an
increment, and FEsolver adds every node in that range.

Without `GENERATE`, each data line is a list of nodes. Repeat the line as needed.

With `GENERATE`, each data line is:

```
First node in set
Last node in set
Increment (default 1)
```

Write `generate` in lower case. With `GENERATE` in upper case, `1, 9, 1` gives nodes 1 and
9 only, with no warning. See item 33 in [todo.md](todo.md).

Set names are not case-sensitive. `_PickedSet9` and `_PICKEDSET9` are the same set, as in
Abaqus. If you repeat a name, FEsolver adds the nodes to the existing set.

[Back to top](#keywords)

## \*SHELL SECTION

Defines a shell section.

Required parameters:

- `ELSET`: the element set the section applies to
- `MATERIAL`: the material the shell is made of

FEsolver records the element set name but does not use it. It applies the thickness to
every element in the model, not only the elements in the named set. Sets defined with
[\*ELSET](#elset) are read but never used by the solver.

Data line, required:

```
Shell thickness
```

FEsolver uses the thickness in the element stiffness calculation,
`[Kᵉ] = [B]ᵀ[D][B] · A · t`. Abaqus/CAE writes a second value on this line, the number of
integration points through the thickness. FEsolver ignores it.

[Back to top](#keywords)
