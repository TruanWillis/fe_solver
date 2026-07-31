# Worked Example

A complete finite element analysis, worked through by hand from the input file to the
final stresses. Every number below is the actual value FEsolver computes — you can check
each stage as you go.

The model is deliberately tiny: **two elements, four nodes, eight degrees of freedom**.
Small enough to follow with a calculator, but large enough that two elements share nodes,
so the assembly step does something real.

Input file: [`examples/worked_example.inp`](../examples/worked_example.inp)

Read alongside [theory.md](theory.md), which explains *why* each step exists. This
document shows *what the numbers do*.

---

## Contents

1. [The problem](#1-the-problem)
2. [What the answer should be](#2-what-the-answer-should-be)
3. [Writing the input file](#3-writing-the-input-file)
4. [Parsing into the model](#4-parsing-into-the-model)
5. [Element geometry and area](#5-element-geometry-and-area)
6. [The strain-displacement matrix B](#6-the-strain-displacement-matrix-b)
7. [The material matrix D](#7-the-material-matrix-d)
8. [The element stiffness matrix](#8-the-element-stiffness-matrix)
9. [Assembling the global matrix](#9-assembling-the-global-matrix)
10. [Boundary conditions and loads](#10-boundary-conditions-and-loads)
11. [Reducing the system](#11-reducing-the-system)
12. [Solving by Gaussian elimination](#12-solving-by-gaussian-elimination)
13. [Recovering stresses](#13-recovering-stresses)
14. [Reactions and the equilibrium check](#14-reactions-and-the-equilibrium-check)
15. [Comparing against theory](#15-comparing-against-theory)
16. [Run it yourself](#16-run-it-yourself)

---

## 1. The problem

A square steel plate, 10 mm × 10 mm, 2 mm thick, pulled vertically in tension.

```
              1000 N          1000 N
                 ↑               ↑
       4 (0,10) ●───────────────● 3 (10,10)
                │ ╲             │
                │   ╲           │
                │     ╲   E1    │
                │  E2   ╲       │
                │         ╲     │
                │           ╲   │
       1 (0,0)  ●───────────────● 2 (10,0)
               ┃┃┃             ○○○
             pinned          roller
          (u = 0, v = 0)     (v = 0)
```

| Property | Value |
|---|---|
| Young's modulus, $E$ | 210 000 MPa |
| Poisson's ratio, $\nu$ | 0.3 |
| Thickness, $t$ | 2 mm |
| Applied load | 1000 N upward at nodes 3 and 4 (2000 N total) |

Units are **mm, N, MPa** throughout. FEsolver has no concept of units — it simply does the
arithmetic, so consistency is the user's responsibility. Millimetres and newtons give
stresses in MPa, which is what a mechanical engineer usually wants.

### Why these boundary conditions?

Node 1 is **pinned** — held in both x and y. Node 2 is a **roller** — held in y only, free
to slide in x.

This matters. Fixing both bottom nodes completely would prevent the plate from contracting
sideways as it stretches, introducing artificial stresses near the base. The roller lets
Poisson contraction happen freely, so the stress field stays uniform and we get an answer
we can check by hand. Choosing restraints that hold the part in space *without* fighting
its natural deformation is one of the core skills in FEA.

### Why two elements, and why this diagonal?

A quadrilateral region cannot be meshed with a single triangle, so the square is split
along the diagonal from node 1 to node 3. Element E1 is the lower-right triangle
(nodes 1, 2, 3); element E2 is the upper-left (nodes 1, 3, 4).

Both are listed **counter-clockwise**. This is not cosmetic: element area is computed from
a determinant, which comes out negative for clockwise ordering and produces a
negative-definite stiffness matrix. FEsolver does not currently detect this — see item 6
in [TODO.md](TODO.md).

---

## 2. What the answer should be

Work this out first. Knowing the expected answer before running the solver is a habit
worth building — it is the only way to notice when a model is wrong.

The plate is in **uniaxial tension**. The load is carried across a cross-section of
width 10 mm and thickness 2 mm:

$$A = 10 \times 2 = 20\ \text{mm}^2$$

$$\sigma_{yy} = \frac{F}{A} = \frac{2000}{20} = 100\ \text{MPa}$$

Strain follows from Hooke's law, and the extension from the plate height:

$$\epsilon_{yy} = \frac{\sigma_{yy}}{E} = \frac{100}{210000} = 4.7619 \times 10^{-4}$$

$$v_{\text{top}} = \epsilon_{yy} \times 10 = 4.7619 \times 10^{-3}\ \text{mm}$$

Poisson contraction gives the sideways movement:

$$\epsilon_{xx} = -\nu\,\epsilon_{yy} = -0.3 \times 4.7619\times10^{-4} = -1.42857\times10^{-4}$$

$$u_{x=10} = -1.42857\times10^{-3}\ \text{mm}$$

So we expect: **100 MPa everywhere**, the top edge rising by **0.0047619 mm**, and the
right edge drawing in by **0.00142857 mm**.

Because the stress field is uniform, a constant-strain element should reproduce this
**exactly** — not approximately. This is the classic *patch test*, and a solver that fails
it has a bug.

---

## 3. Writing the input file

FEsolver reads Abaqus-style `.inp` files. Full keyword reference in
[keywords.md](keywords.md). Here is the model built up block by block.

### Nodes

Node number, then coordinates. A third coordinate may be present and is ignored.

```
*Node
      1,           0.,           0.
      2,          10.,           0.
      3,          10.,          10.
      4,           0.,          10.
```

### Elements

Element number, then its three node numbers counter-clockwise. `S3` is the only element
type available.

```
*Element, type=S3
1, 1, 2, 3
2, 1, 3, 4
```

> Do **not** add `elset=` to this line — FEsolver would read the element type as
> `s3, elset` and fail. Define sets separately.

### Section and material

Thickness on the data line. The second value (integration points) is ignored.

```
*Shell Section, elset=AllElements, material=Steel
2., 5

*Material, name=Steel
*Elastic
210000., 0.3
```

### Boundary conditions

Node number, first DOF, last DOF. DOF `1` is x, DOF `2` is y. Only one DOF per line is
applied, so the two constraints on node 1 need two lines.

```
*Boundary
1, 1, 1
1, 2, 2
2, 2, 2
```

### Loads

Node number, DOF, magnitude.

```
*Cload
3, 2, 1000.
4, 2, 1000.
```

Note that the 2000 N total is applied as 1000 N at each of the two top nodes. FEsolver
applies loads at nodes only — there is no pressure or distributed load keyword — so
converting a real distributed load into equivalent nodal forces is the user's job.

---

## 4. Parsing into the model

`model.call_gen_function()` reads the file and returns a dictionary. Keywords it does not
recognise (`*Part`, `*Step`, `*Output` …) are skipped silently, which is why files
exported from Abaqus/CAE can be read unedited.

```python
{'nodes':    {1: [0.0, 0.0], 2: [10.0, 0.0], 3: [10.0, 10.0], 4: [0.0, 10.0]},
 'elements': {1: {'nodes': [1, 2, 3], 'type': 's3'},
              2: {'nodes': [1, 3, 4], 'type': 's3'}},
 'section':  {'elementset': 'AllElements', 'material': 'Steel', 'thickness': 2.0},
 'elasticity': [210000.0, 0.3],
 'boundary': {1: {'1': 0.0, '2': 0.0}, 2: {'2': 0.0}},
 'load':     {3: {'2': 1000.0}, 4: {'2': 1000.0}},
 'dof': 8,
 'active_mask': [False, False, True, False, True, True, True, True]}
```

The **active mask** is the important derived value. With 4 nodes × 2 DOF = 8 total, it
records which are free to move:

| DOF | `1u` | `1v` | `2u` | `2v` | `3u` | `3v` | `4u` | `4v` |
|---|---|---|---|---|---|---|---|---|
| Free? | ✗ | ✗ | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ |

Three constrained, **five free**. Those five are the unknowns.

See [data_structures.md](data_structures.md) for the full model dictionary reference.

---

## 5. Element geometry and area

Area comes from the determinant of the coordinate matrix, halved.

### Element 1 — nodes 1 (0,0), 2 (10,0), 3 (10,10)

$$A = \frac{1}{2}\det\begin{bmatrix} 1 & 0 & 0 \\ 1 & 10 & 0 \\ 1 & 10 & 10 \end{bmatrix}
= \frac{1}{2}\big(1(10\cdot10 - 0\cdot10)\big) = \frac{100}{2} = 50\ \text{mm}^2$$

A check: the square is 100 mm² and the diagonal halves it. Both elements are 50 mm². ✓

### Shape function coefficients

The $[B]$ matrix is built from six coefficients that are just coordinate differences:

$$b_1 = y_2 - y_3 \quad b_2 = y_3 - y_1 \quad b_3 = y_1 - y_2$$
$$c_1 = x_3 - x_2 \quad c_2 = x_1 - x_3 \quad c_3 = x_2 - x_1$$

For element 1:

| | $b_1$ | $b_2$ | $b_3$ | $c_1$ | $c_2$ | $c_3$ |
|---|---|---|---|---|---|---|
| value | −10 | 10 | 0 | 0 | −10 | 10 |

For element 2 — nodes 1 (0,0), 3 (10,10), 4 (0,10):

| | $b_1$ | $b_2$ | $b_3$ | $c_1$ | $c_2$ | $c_3$ |
|---|---|---|---|---|---|---|
| value | 0 | 10 | −10 | −10 | 0 | 10 |

---

## 6. The strain-displacement matrix B

$[B]$ converts nodal displacements into strains. It is assembled from the coefficients
above and scaled by $1/2A$:

$$[B] = \frac{1}{2A}\begin{bmatrix}
b_1 & 0 & b_2 & 0 & b_3 & 0 \\
0 & c_1 & 0 & c_2 & 0 & c_3 \\
c_1 & b_1 & c_2 & b_2 & c_3 & b_3
\end{bmatrix}$$

### Element 1

With $2A = 100$:

$$[B]_1 = \frac{1}{100}\begin{bmatrix}
-10 & 0 & 10 & 0 & 0 & 0 \\
0 & 0 & 0 & -10 & 0 & 10 \\
0 & -10 & -10 & 10 & 10 & 0
\end{bmatrix}
=\begin{bmatrix}
-0.1 & 0 & 0.1 & 0 & 0 & 0 \\
0 & 0 & 0 & -0.1 & 0 & 0.1 \\
0 & -0.1 & -0.1 & 0.1 & 0.1 & 0
\end{bmatrix}$$

The columns correspond to `1u`, `1v`, `2u`, `2v`, `3u`, `3v`, and the rows to
$\epsilon_{xx}$, $\epsilon_{yy}$, $\gamma_{xy}$.

Read the first row: $\epsilon_{xx} = -0.1\,u_1 + 0.1\,u_2$. Stretching node 2 away from
node 1 over a 10 mm span produces x-strain — exactly what you would write by hand. Note
there is no dependence on $u_3$, because nodes 2 and 3 sit at the same $x$.

**$[B]$ contains no variable** — it is constant across the element. That is what makes S3
a *constant strain* element, and it is why the stiffness integral collapses to a
multiplication later.

### Element 2

$$[B]_2 = \begin{bmatrix}
0 & 0 & 0.1 & 0 & -0.1 & 0 \\
0 & -0.1 & 0 & 0 & 0 & 0.1 \\
-0.1 & 0 & 0 & 0.1 & 0.1 & -0.1
\end{bmatrix}$$

Columns here are `1u`, `1v`, `3u`, `3v`, `4u`, `4v` — element 2's own nodes.

---

## 7. The material matrix D

$[D]$ converts strain into stress. For plane stress:

$$[D] = \frac{E}{1-\nu^2}\begin{bmatrix}
1 & \nu & 0 \\ \nu & 1 & 0 \\ 0 & 0 & \frac{1-\nu}{2}
\end{bmatrix}$$

The leading coefficient:

$$\frac{E}{1-\nu^2} = \frac{210000}{1-0.09} = \frac{210000}{0.91} = 230769.23$$

Multiplying through:

$$[D] = \begin{bmatrix}
230769.23 & 69230.77 & 0 \\
69230.77 & 230769.23 & 0 \\
0 & 0 & 80769.23
\end{bmatrix}$$

Checks: $230769.23 \times 0.3 = 69230.77$ ✓ and $230769.23 \times 0.35 = 80769.23$ ✓

$[D]$ is identical for both elements — same material, same section.

---

## 8. The element stiffness matrix

$$[K^e] = [B]^T[D][B] \cdot A \cdot t$$

With $A = 50$ and $t = 2$, the scaling factor is $50 \times 2 = 100$.

### Checking one entry by hand

Take the top-left entry of element 1, $K^e_{1u,1u}$. Column `1u` of $[B]_1$ is
$\{-0.1, 0, 0\}$.

$$[D]\{-0.1, 0, 0\}^T = \{-23076.92,\ -6923.08,\ 0\}^T$$

$$K^e_{1u,1u} = \{-0.1, 0, 0\} \cdot \{-23076.92, -6923.08, 0\} \times 100
= 2307.69 \times 100 = 230769.23$$

And $K^e_{1v,1v}$, where column `1v` is $\{0, 0, -0.1\}$:

$$[D]\{0,0,-0.1\}^T = \{0,\ 0,\ -8076.92\}^T \quad\Rightarrow\quad
807.69 \times 100 = 80769.23$$

### Element 1 — $[K^e]$

```
            1u         1v         2u         2v         3u         3v
1u   230769.23       0.00 -230769.23   69230.77       0.00  -69230.77
1v        0.00   80769.23   80769.23  -80769.23  -80769.23       0.00
2u  -230769.23   80769.23  311538.46 -150000.00  -80769.23   69230.77
2v    69230.77  -80769.23 -150000.00  311538.46   80769.23 -230769.23
3u        0.00  -80769.23  -80769.23   80769.23   80769.23       0.00
3v   -69230.77       0.00   69230.77 -230769.23       0.00  230769.23
```

### Element 2 — $[K^e]$

```
            1u         1v         3u         3v         4u         4v
1u    80769.23       0.00       0.00  -80769.23  -80769.23   80769.23
1v        0.00  230769.23  -69230.77       0.00   69230.77 -230769.23
3u        0.00  -69230.77  230769.23       0.00 -230769.23   69230.77
3v   -80769.23       0.00       0.00   80769.23   80769.23  -80769.23
4u   -80769.23   69230.77 -230769.23   80769.23  311538.46 -150000.00
4v    80769.23 -230769.23   69230.77  -80769.23 -150000.00  311538.46
```

Both matrices are **symmetric** — a consequence of $[B]^T[D][B]$ with symmetric $[D]$. If
yours is not symmetric, something is wrong.

Each row also **sums to zero**. That is rigid-body translation: move every node by the
same amount and no force is produced. This is why an unconstrained stiffness matrix is
singular.

---

## 9. Assembling the global matrix

The global matrix is 8 × 8, one row and column per DOF, initialised to zero. Each element
matrix is added into the positions matching its own DOF labels.

Element 1 touches `1u 1v 2u 2v 3u 3v`. Element 2 touches `1u 1v 3u 3v 4u 4v`. They
**overlap at `1u 1v 3u 3v`** — the two nodes on the shared diagonal. Those positions
receive contributions from both.

### Watching one entry assemble

Position `1u,1u` gets a contribution from each element:

$$K_{1u,1u} = 230769.23 \;+\; 80769.23 \;=\; 311538.46$$

Position `1u,3v` likewise:

$$K_{1u,3v} = (-69230.77) \;+\; (-80769.23) \;=\; -150000.00$$

Position `2u,4u` gets **nothing** — node 2 belongs only to element 1, node 4 only to
element 2, and no element connects them. It stays zero.

That last point is the whole idea behind sparsity: in a real mesh most node pairs share no
element, so most of the matrix is zero.

### The assembled global matrix

```
             1u         1v         2u         2v         3u         3v         4u         4v
1u   311538.46       0.00 -230769.23   69230.77       0.00 -150000.00  -80769.23   80769.23
1v        0.00  311538.46   80769.23  -80769.23 -150000.00       0.00   69230.77 -230769.23
2u  -230769.23   80769.23  311538.46 -150000.00  -80769.23   69230.77       0.00       0.00
2v    69230.77  -80769.23 -150000.00  311538.46   80769.23 -230769.23       0.00       0.00
3u        0.00 -150000.00  -80769.23   80769.23  311538.46       0.00 -230769.23   69230.77
3v  -150000.00       0.00   69230.77 -230769.23       0.00  311538.46   80769.23  -80769.23
4u   -80769.23   69230.77       0.00       0.00 -230769.23   80769.23  311538.46 -150000.00
4v    80769.23 -230769.23       0.00       0.00   69230.77  -80769.23 -150000.00  311538.46
```

Note the zero block at `2u,4u` / `2v,4v` and its mirror — nodes 2 and 4 are the two
corners *not* joined by the diagonal.

---

## 10. Boundary conditions and loads

The force vector is zero except where loads were applied:

```
      1u    1v    2u    2v    3u      3v    4u      4v
F = [  0     0     0     0     0    1000     0    1000 ]
```

The displacement vector starts as all unknowns (`*`), with prescribed values written in:

```
      1u    1v    2u    2v    3u    3v    4u    4v
u = [ 0.0   0.0    *    0.0    *     *     *     * ]
```

Five unknowns, matching the active mask from Step 4.

---

## 11. Reducing the system

Rows and columns for constrained DOFs are struck out, leaving the free-DOF system
$[K_{ff}]\{u_f\} = \{F_f\}$ over `2u, 3u, 3v, 4u, 4v`:

```
              2u          3u          3v          4u          4v
2u    311538.46   -80769.23    69230.77        0.00        0.00
3u    -80769.23   311538.46        0.00  -230769.23    69230.77
3v     69230.77        0.00   311538.46    80769.23   -80769.23
4u         0.00  -230769.23    80769.23   311538.46  -150000.00
4v         0.00    69230.77   -80769.23  -150000.00   311538.46
```

$$\{F_f\} = \{0,\ 0,\ 1000,\ 0,\ 1000\}$$

The 8 × 8 system is now 5 × 5, and — crucially — no longer singular. The constraints have
removed the rigid-body motions.

---

## 12. Solving by Gaussian elimination

`direct_solver.py` reduces the matrix to upper triangular, then back-substitutes.

### Forward elimination

Before each step the algorithm applies a **partial pivot**, swapping in the row with the
largest absolute value in the current column. Here the diagonal already dominates, so no
swaps occur — but on an ill-conditioned model they matter a great deal.

**Step 0**, pivot `2u` = 311538.46:

```
row 3u -= -0.259259 x row 2u
row 3v -= +0.222222 x row 2u
```

Check the first factor: $-80769.23 / 311538.46 = -0.259259$ ✓

**Step 1**, pivot `3u` = 290598.29 (already modified by step 0):

```
row 3v -= +0.061765 x row 3u
row 4u -= -0.794118 x row 3u
row 4v -= +0.238235 x row 3u
```

**Step 2**, pivot `3v` = 295045.25:

```
row 4u -= +0.322061 x row 3v
row 4v -= -0.288245 x row 3v
```

**Step 3**, pivot `4u` = 97677.44:

```
row 4v -= -0.692410 x row 4u
```

### The upper triangular system

```
              2u          3u          3v          4u          4v          F
2u    311538.46   -80769.23    69230.77        0.00        0.00        0.00
3u          0.00   290598.29    17948.72  -230769.23    69230.77        0.00
3v          0.00        0.00   295045.25    95022.62   -85045.25     1000.00
4u          0.00        0.00        0.00    97677.44   -67632.85     -322.06
4v          0.00        0.00        0.00        0.00   223701.73     1065.25
```

### Back substitution

The last row now has a single unknown. Work upward:

$$v_4 = \frac{1065.2463}{223701.73} = 0.00476190$$

$$u_4 = \frac{-322.0612 - (-322.0612)}{97677.44} = 0.00000000$$

$$v_3 = \frac{1000 - (-404.9774)}{295045.25} = 0.00476190$$

$$u_3 = \frac{0 - 415.1404}{290598.29} = -0.00142857$$

$$u_2 = \frac{0 - 445.0549}{311538.46} = -0.00142857$$

### The displacement field

| Node | $u$ (mm) | $v$ (mm) |
|---|---|---|
| 1 | 0 | 0 |
| 2 | −0.00142857 | 0 |
| 3 | −0.00142857 | 0.00476190 |
| 4 | 0 | 0.00476190 |

Read this physically. Both top nodes rise by the same amount, so the top edge stays
horizontal. Both right-hand nodes draw inward by the same amount, so the right edge stays
vertical and parallel. Node 4 does not move sideways at all, because it sits on the same
vertical line as the pinned node 1. **The square has become a slightly taller, slightly
narrower rectangle** — precisely what uniaxial tension should do.

As exact fractions, $0.00476190 = 1/210$ and $-0.00142857 = -1/700$.

---

## 13. Recovering stresses

With displacements known, stress is recovered element by element:
$\{\sigma\} = [D][B]\{u^e\}$.

### Element 1 by hand

Its six DOFs, in element order `1u 1v 2u 2v 3u 3v`:

$$\{u^e\} = \{0,\ 0,\ -\tfrac{1}{700},\ 0,\ -\tfrac{1}{700},\ \tfrac{1}{210}\}$$

Strains, using $[B]_1$ from Step 6:

$$\epsilon_{xx} = -0.1(0) + 0.1\left(-\tfrac{1}{700}\right) = -1.42857\times10^{-4}$$

$$\epsilon_{yy} = -0.1(0) + 0.1\left(\tfrac{1}{210}\right) = 4.76190\times10^{-4}$$

$$\gamma_{xy} = -0.1(0) - 0.1\left(-\tfrac{1}{700}\right) + 0.1(0) + 0.1\left(-\tfrac{1}{700}\right) = 0$$

Then stress, $\{\sigma\} = [D]\{\epsilon\}$:

$$\sigma_{xx} = 230769.23(-1.42857\times10^{-4}) + 69230.77(4.76190\times10^{-4})
= -32.967 + 32.967 = 0$$

$$\sigma_{yy} = 69230.77(-1.42857\times10^{-4}) + 230769.23(4.76190\times10^{-4})
= -9.890 + 109.890 = 100$$

$$\tau_{xy} = 80769.23 \times 0 = 0$$

The two terms in $\sigma_{xx}$ cancel exactly. That is Poisson's ratio doing its job: the
plate contracts sideways by precisely the amount that leaves no lateral stress, because
nothing is restraining it.

### Both elements

| Element | `s1` ($\sigma_{xx}$) | `s2` ($\sigma_{yy}$) | `s12` ($\tau_{xy}$) |
|---|---|---|---|
| e1 | 0.0 | 100.0 | 0.0 |
| e2 | 0.0 | 100.0 | 0.0 |

Identical, as they must be for a uniform stress field.

> The column names `s1`, `s2`, `s12` hold $\sigma_{xx}$, $\sigma_{yy}$, $\tau_{xy}$ —
> they are **not** principal stresses despite the naming.

### Principal and von Mises

From Mohr's circle, centre $= (0+100)/2 = 50$ and radius $= \sqrt{50^2 + 0^2} = 50$:

| | $\sigma_{max}$ | $\sigma_{min}$ | $\tau_{max}$ |
|---|---|---|---|
| both elements | 100.0 | 0.0 | 50.0 |

Von Mises:

$$\sigma_{vm} = \sqrt{0^2 - 0(100) + 100^2 + 3(0)^2} = 100\ \text{MPa}$$

For a uniaxial stress state von Mises equals the applied stress exactly — a useful sanity
check whenever you see it.

> The `SP` columns `a`, `opp` and `adj` (the principal *direction*, used only for the
> vector plot) are currently computed 90° out. The magnitudes above are unaffected.
> See item 26 in [TODO.md](TODO.md).

---

## 14. Reactions and the equilibrium check

Reactions are recovered as $\{R\} = [K]\{u\} - \{F\}$:

| Node | $R_x$ (N) | $R_y$ (N) |
|---|---|---|
| 1 | 0 | −1000 |
| 2 | 0 | −1000 |
| 3 | 0 | 0 |
| 4 | 0 | 0 |

Three things to check, and they are the same three you should check on any model:

1. **Reactions appear only at constrained nodes.** Nodes 3 and 4 are free, so they carry
   none. ✓
2. **Vertical reactions balance the load.** $-1000 - 1000 = -2000$ N against the applied
   $+2000$ N. ✓
3. **Horizontal reactions are zero.** Nothing pushes sideways, and the roller lets the
   plate contract freely, so node 1 carries no x-reaction. If it did, the restraints would
   be fighting the deformation. ✓

Reaction forces are the most under-used check in FEA. If they do not balance the applied
load, the model is wrong — before you look at a single stress contour.

> FEsolver prints a residual line during the solve. That check is currently vacuous — it
> passes regardless of the answer. See item 3 in [TODO.md](TODO.md). Check the reactions
> by hand as above until it is fixed.

---

## 15. Comparing against theory

| Quantity | Hand calculation | FEsolver | Match |
|---|---|---|---|
| $\sigma_{yy}$ | 100 MPa | 100.0 MPa | exact |
| $\sigma_{xx}$ | 0 | 0.0 | exact |
| von Mises | 100 MPa | 100.0 MPa | exact |
| $v$ at top edge | 0.00476190 mm | 0.00476190 mm | exact |
| $u$ at right edge | −0.00142857 mm | −0.00142857 mm | exact |
| Total reaction | −2000 N | −2000 N | exact |

**Exact agreement, not approximate.** The true displacement field here is linear in $x$
and $y$, and a linear triangle can represent a linear field perfectly. There is no
discretisation error to have.

This will not happen on a real model. Refine a plate with a hole and the stress at the
hole edge will keep climbing as elements shrink, because the true field is not linear and
constant-strain triangles can only approximate it. The lesson to carry forward:

- **Uniform stress field** → S3 is exact, one element would do.
- **Varying stress field** → S3 is only as good as the mesh, and near a stress
  concentration it is poor. This is why real analyses use quadratic or quadrilateral
  elements, and why mesh convergence studies exist.

Because this model *should* be exact, it makes a good regression test — any future change
that breaks it has broken something real. That is item 18 in [TODO.md](TODO.md).

---

## 16. Run it yourself

Through the GUI: `python main.py`, select this repository as the working directory, then
`examples/worked_example.inp`.

Headlessly, to inspect the intermediate values yourself:

```python
from pathlib import Path
from fe_solver.core import model, solver

m = model.call_gen_function(model.load_input("examples/worked_example.inp"))
s = solver.Solver(m, True, False, False, Path(""))

# element matrices (Steps 5-8)
e1 = m["elements"][1]["K"]
print(e1.area)                       # 50.0
print(e1.B)                          # 3x6 strain-displacement
print(e1.D)                          # 3x3 material
print(e1.element_stiffness_matrix)   # 6x6 labelled by DOF

# global and reduced systems (Steps 9-11)
print(s.global_stiffness_matrix)     # 8x8 labelled
print(s.global_stiffness_matrix_reduced)   # 5x5
print(s.index_reduced)               # ['2u' '3u' '3v' '4u' '4v']

# results (Steps 12-14)
print(s.results["node"]["U"].data)
print(s.results["element"]["S"].data)
print(s.results["node"]["RF"].data)
```

### Things worth trying

Each of these has been run — the stated result is what actually happens.

- **Fix node 2 in x as well** (add `2, 1, 1` to `*Boundary`). The base can no longer
  contract, so the uniform field is destroyed: $\sigma_{yy}$ splits to **97.20** and
  **102.80** MPa in the two elements, and von Mises drops to 86.53 in one of them. A
  restraint that fights the natural deformation has polluted the answer — with no warning
  from the solver. This is the most common way real models go wrong.
- **Halve the thickness** to 1 mm. Stress doubles to exactly **200 MPa**, as $\sigma = F/A$
  demands.
- **Flip an element to clockwise** — change element 1 to `1, 1, 3, 2`. The area goes
  negative and $\sigma_{yy}$ becomes **1.25 × 10¹⁷** MPa. Complete nonsense, returned
  silently with no error (item 6 in [TODO.md](TODO.md)).
- **Refine the mesh.** Add a node at the centre (5, 5) and split into four triangles.
  The answer does **not** change: 100.0 MPa in all four elements, and displacements
  identical to the last floating-point bit (0.004761904761904764 against
  0.004761904761904762). That invariance is exactly what a patch test asserts — refining a
  mesh that is already exact must change nothing.
