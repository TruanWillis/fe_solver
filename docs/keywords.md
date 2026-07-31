# Keywords

Reference for the `.inp` keywords FEsolver understands. The format follows Simulia
Abaqus so that models are familiar to anyone who has used it, but FEsolver implements
only the subset listed here — it is **not** Abaqus-compatible. See
[theory.md](theory.md) for what the solver does with these inputs.

### How the input file is read

- Lines beginning with a single `*` are keywords. Lines beginning with `**` are comments
  and are ignored.
- A keyword's data lines are every line following it up to the next `*`.
- **Keywords not in the list below are skipped silently.** An `.inp` exported from
  Abaqus/CAE will contain many of these (`*Part`, `*Assembly`, `*Step`, `*Output` and so
  on) — they are ignored rather than rejected, which is why CAE files can be read
  directly.
- Keyword names are matched case-insensitively. **Set names are currently
  case-sensitive**, so `_PickedSet9` and `_PICKEDSET9` are treated as two different sets.
  Abaqus treats them as one. See item 5 in [TODO.md](TODO.md).

### Supported keywords

| Keyword | Purpose |
|---|---|
| [\*BOUNDARY](#-boundary) | Prescribe displacement constraints at nodes |
| [\*CLOAD](#-cload) | Apply concentrated forces at nodes |
| [\*ELASTIC](#-elastic) | Define linear elastic material moduli |
| [\*ELEMENT](#-element) | Define elements by their nodes |
| [\*ELSET](#-elset) | Assign elements to an element set |
| [\*MATERIAL](#-material) | Begin a material definition |
| [\*NODE](#-node) | Define nodes by their coordinates |
| [\*NSET](#-nset) | Assign nodes to a node set |
| [\*SHELL SECTION](#-shell-section) | Define section thickness and material |

---

#### \* BOUNDARY

Specify boundary conditions. This option is used to prescribe boundary
conditions at nodes

**Required parameters:**

    None

**Optional parameters:**

    None

**Data lines to define boundary:**

First line:

    Node number or node set label.
    First degree of freedom constrained.
    Last degree of freedom constrained.
    Boundary value, only required for nonzero boundary condition.

Degree of freedom `1` is translation in x, `2` is translation in y.

Repeat this data line as often as necessary to specify boundary conditions at
different nodes and degrees of freedom.

**Current limitations:**

- Only a **single** degree of freedom per data line is applied — the first and last
  fields must be equal. A range such as `7, 1, 2` is accepted by the parser but
  **silently ignored**, leaving the model under-constrained.
- Only degrees of freedom `1` and `2` exist in a 2D plane-stress model. Higher values
  written by Abaqus/CAE (`3` to `6` — rotations and out-of-plane translation) are
  ignored, which is why CAE decks can be read unedited.
- The `ENCASTRE` and `PINNED` shortcuts are **not supported** and raise an error.
  Constrain each degree of freedom explicitly instead.

See item 7 in [TODO.md](TODO.md).

[Back To The Top](#keywords)

#### \* CLOAD

Specify concentrated force. This option is used to apply concentrated forces at
any node in the model.

**Required parameters:**

    None

**Optional parameters:**

    None

**Data lines to define concentrated loads for specific degrees of freedom:**

First line:

    Node number or node set label.
    Degree of freedom.
    Load magnitude.

Degree of freedom `1` is force in x, `2` is force in y.

Repeat this data line as often as necessary to define concentrated loads.

If a node set is named, the given magnitude is applied to **every node in the set** —
it is not divided between them.

[Back To The Top](#keywords)

#### \* ELASTIC

Specify elastic material properties.  This option is used to define linear
elastic moduli.

**Required parameters:**

    None

**Optional parameters:**

    None

**Data lines to define isotropic elasticity:**

First line:

    Young's modulus, E.
    Poisson's ratio.

[Back To The Top](#keywords)

#### \* ELEMENT

Define elements by giving their nodes. This option is used to define an element
directly by specifying its nodes.

**Required parameter:**

    TYPE

Set this parameter equal to the element type, currently only **S3** element
type is available.

**Optional parameters:**

    None

> **`ELSET` is not supported on this keyword.** Writing
> `*Element, type=S3, elset=PLATE` causes the element type to be read as
> `s3, elset`, which fails with `KeyError: 's3, elset'` when the element stiffness
> matrix is built. Define the element set separately with [\*ELSET](#-elset).

**Data lines to define the elements:**

First line:

    Element number.
    First node number forming the element.
    Second node number forming the element.
    Third node number forming the element.

Repeat this set of data lines as often as necessary.

[Back To The Top](#keywords)

#### \* ELSET

Assign elements to an element set.  This option is used to assign elements to
an element set.

**Required parameter:**

    ELSET

Set this parameter equal to the name of the element set to which the elements
will be assigned.

**Optional parameters:**

    GENERATE

If this parameter is included, each data line should give a first element,
_e1_, a last element, _e2_, and the increment in element numbers between these
elements, _i_. Then, all elements going from _e1_ to _e2_ in steps of _i_ will
be added to the set. _i_ must be an integer.

**Data lines if the GENERATE parameter is omitted:**

First line:

    List of elements to be assigned to this element set.

Repeat this data line as often as necessary.

> **Nested sets are not supported.** Naming a previously defined element set inside
> another set's data line is **silently ignored** — only the numeric entries are kept.
> The same applies to [\*NSET](#-nset).

**Data lines if the GENERATE parameter is included:**

First line:

    First element in set.
    Last element in set.
    Increment in element numbers between elements in the set. The default is 1.

Repeat this data line as often as necessary.

[Back To The Top](#keywords)

#### \* MATERIAL

Begin the definition of a material. This option is used to indicate the start
of a material definition.

**Required parameter:**

    NAME

Set this parameter equal to a label that will be used to refer to the material
in the element property options. Material names in the same input file must be
unique.

**Optional parameters:**

    None

> **Only one material is supported.** The material name is recorded but never linked to
> a section or to elements, and the properties from every [\*ELASTIC](#-elastic) block
> are collected into a single list. If a second material is defined, **all elements
> silently use the first**. See item 11 in [TODO.md](TODO.md).

[Back To The Top](#keywords)

#### \* NODE

Specify nodal coordinates. This option is used to define a node directly by
specifying its coordinates.

**Optional parameters:**

    None

> **`NSET` is not supported on this keyword.** `*Node, nset=PLATE` is accepted but the
> parameter is **silently ignored** — no node set is created. Define the node set
> separately with [\*NSET](#-nset).

**Data lines to define the node:**

First line:

    Node number.
    First coordinate of the node.
    Second coordinate of the node.

Repeat this data line as often as necessary.

A third coordinate may be present — Abaqus/CAE writes one even for 2D models — and is
ignored. FEsolver is 2D plane-stress only.

[Back To The Top](#keywords)

#### \* NSET

Assign nodes to a node set. This option is used to assign nodes to a node set.
Node sets are how boundary conditions and loads are applied to groups of nodes.

**Required parameter:**

    NSET

Set this parameter equal to the name of the node set to which the nodes will be
assigned.

**Optional parameters:**

    GENERATE

If this parameter is included, each data line should give a first node, _n1_, a last
node, _n2_, and the increment in node numbers between these nodes, _i_. Then, all nodes
going from _n1_ to _n2_ in steps of _i_ will be added to the set. _i_ must be an integer.

**Data lines if the GENERATE parameter is omitted:**

First line:

    List of nodes to be assigned to this node set.

Repeat this data line as often as necessary.

**Data lines if the GENERATE parameter is included:**

First line:

    First node in set.
    Last node in set.
    Increment in node numbers between nodes in the set. The default is 1.

Repeat this data line as often as necessary.

> **Set names are case-sensitive.** `_PickedSet9` and `_PICKEDSET9` are treated as two
> separate sets; Abaqus treats them as one. See item 5 in [TODO.md](TODO.md).

[Back To The Top](#keywords)

#### \* SHELL SECTION

Specify a shell cross-section. This option is used to specify a shell
cross-section.

**Required parameter:**

    ELSET

Set this parameter equal to the name of the element set containing the shell
elements for which the section behavior is being defined.

> The element set name is recorded but **not currently acted on** — the thickness below
> is applied to *every* element in the model, not just those in the named set. Element
> sets defined with [\*ELSET](#-elset) are parsed but never read by the solver.

    MATERIAL

Set this parameter equal to the name of the material of which the shell is
made.

**Optional parameters:**

    None

**Data lines to define the section:**

First line:

    Shell thickness.

This data line is **required** — the thickness is used directly in the element stiffness
calculation, `[Kᵉ] = t · A · [B]ᵀ [D][B]`. Abaqus/CAE writes a second value on
this line (the number of integration points through the thickness); it is ignored.

[Back To The Top](#keywords)
