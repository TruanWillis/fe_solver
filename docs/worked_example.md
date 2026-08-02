# Worked Example

A complete analysis worked by hand, from input file to stresses. Every number is the
value FEsolver computes, so each stage can be checked as you go.

The model is two elements, four nodes, eight DOFs — small enough for a calculator, large
enough that two elements share nodes so assembly does something real.

Input file: [`examples/worked_example.inp`](../examples/worked_example.inp)

[theory.md](theory.md) explains why each step exists. This document shows what the
numbers do.

---

## Contents

1. [The Problem](#1-the-problem)
2. [Expected Answer](#2-expected-answer)
3. [The Input File](#3-the-input-file)
4. [The Parsed Model](#4-the-parsed-model)
5. [Element Stiffness](#5-element-stiffness)
6. [Assembly](#6-assembly)
7. [Boundary Conditions and Loads](#7-boundary-conditions-and-loads)
8. [Reducing the System](#8-reducing-the-system)
9. [Solving](#9-solving)
10. [Stresses](#10-stresses)
11. [Reactions](#11-reactions)
12. [Comparison With Theory](#12-comparison-with-theory)
13. [Run It Yourself](#13-run-it-yourself)

---

## 1. The Problem

A square steel plate, 10 mm × 10 mm, 2 mm thick, in vertical tension.

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
| Young's modulus, E | 210 000 MPa |
| Poisson's ratio, ν | 0.3 |
| Thickness, t | 2 mm |
| Applied load | 1000 N up at nodes 3 and 4 (2000 N total) |

Units are mm, N, MPa. FEsolver has no concept of units — consistency is the user's
responsibility. Millimetres and newtons give stresses in MPa.

**Restraints.** Node 1 is pinned (u and v), node 2 is a roller (v only). Fixing both
bottom nodes in x would prevent the plate contracting sideways as it stretches,
introducing artificial stress near the base. The roller allows Poisson contraction, so
the stress field stays uniform and the answer can be checked by hand.

**Mesh.** A quadrilateral cannot be meshed with one triangle, so the square is split on
the diagonal from node 1 to node 3. E1 is the lower-right triangle (nodes 1, 2, 3), E2
the upper-left (nodes 1, 3, 4). Both are listed counter-clockwise — element area comes
from a determinant, which is negative for clockwise ordering and gives a
negative-definite stiffness matrix. FEsolver does not detect this; see item 6 in
[todo.md](todo.md).

---

## 2. Expected Answer

The plate is in uniaxial tension, carried across a section 10 mm wide and 2 mm thick.

```
A    = 10 × 2 = 20 mm²
σyy  = F/A = 2000/20 = 100 MPa
εyy  = σyy/E = 100/210000 = 4.7619 × 10⁻⁴
v_top = εyy × 10 = 4.7619 × 10⁻³ mm
εxx  = -ν εyy = -1.42857 × 10⁻⁴
u_x=10 = -1.42857 × 10⁻³ mm
```

Expect 100 MPa everywhere, the top edge rising 0.0047619 mm, the right edge drawing in
0.00142857 mm.

The stress field is uniform, so a constant-strain element reproduces this **exactly**,
not approximately. This is the standard *patch test*; a solver that fails it has a bug.

---

## 3. The Input File

FEsolver reads Abaqus-style `.inp` files. Full reference in [keywords.md](keywords.md).

### Nodes

Node number, then coordinates. A third coordinate is ignored if present.

```
*Node
      1,           0.,           0.
      2,          10.,           0.
      3,          10.,          10.
      4,           0.,          10.
```

### Elements

Element number, then its three nodes counter-clockwise. `S3` is the only type available.

```
*Element, type=S3
1, 1, 2, 3
2, 1, 3, 4
```

> Do not add `elset=` to this line — FEsolver reads the element type as `s3, elset` and
> fails. Define sets separately.

### Section and material

Thickness on the data line; the second value (integration points) is ignored.

```
*Shell Section, elset=AllElements, material=Steel
2., 5

*Material, name=Steel
*Elastic
210000., 0.3
```

### Boundary conditions

Node number, first DOF, last DOF. DOF `1` is x, `2` is y. Only one DOF per line is
applied, so node 1 needs two lines.

```
*Boundary
1, 1, 1
1, 2, 2
2, 2, 2
```

### Loads

Node number, DOF, magnitude. FEsolver applies loads at nodes only — there is no pressure
or distributed load keyword, so converting a distributed load to equivalent nodal forces
is the user's job.

```
*Cload
3, 2, 1000.
4, 2, 1000.
```

---

## 4. The Parsed Model

`model.call_gen_function()` returns a dictionary. Unrecognised keywords (`*Part`,
`*Step`, `*Output` …) are skipped silently, which is why Abaqus/CAE files can be read
unedited.

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

The **active mask** is the key derived value — which of the 8 DOFs are free to move:

| DOF | `1u` | `1v` | `2u` | `2v` | `3u` | `3v` | `4u` | `4v` |
|---|---|---|---|---|---|---|---|---|
| Free? | ✗ | ✗ | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ |

Three constrained, five free. Those five are the unknowns.

Full model dictionary reference in [data_structures.md](data_structures.md).

---

## 5. Element Stiffness

### Area

Area is the determinant of the coordinate matrix, halved. Element 1, nodes 1 (0,0),
2 (10,0), 3 (10,10):

```
A = ½ det | 1    0    0 |
          | 1   10    0 |   = ½(1(10·10 - 0·10)) = 100/2 = 50 mm²
          | 1   10   10 |
```

The square is 100 mm² and the diagonal halves it, so both elements are 50 mm².

### Shape function coefficients

`[B]` is built from six coordinate differences:

```
b₁ = y₂ - y₃     b₂ = y₃ - y₁     b₃ = y₁ - y₂
c₁ = x₃ - x₂     c₂ = x₁ - x₃     c₃ = x₂ - x₁
```

| Element | b₁ | b₂ | b₃ | c₁ | c₂ | c₃ |
|---|---|---|---|---|---|---|
| 1 — nodes 1, 2, 3 | −10 | 10 | 0 | 0 | −10 | 10 |
| 2 — nodes 1, 3, 4 | 0 | 10 | −10 | −10 | 0 | 10 |

### `[B]` — strain-displacement

```
[B] = 1/(2A) × | b₁    0   b₂    0   b₃    0 |
               |  0   c₁    0   c₂    0   c₃ |
               | c₁   b₁   c₂   b₂   c₃   b₃ |
```

Element 1, with `2A = 100`:

```
[B]₁ =  -0.1      0    0.1      0     0     0
           0      0      0   -0.1     0   0.1
           0   -0.1   -0.1    0.1   0.1     0
```

Columns are `1u 1v 2u 2v 3u 3v`; rows are εxx, εyy, γxy. The first row reads
`εxx = -0.1u₁ + 0.1u₂` — stretching node 2 away from node 1 over a 10 mm span produces
x-strain. There is no dependence on u₃ because nodes 2 and 3 share an x coordinate.

`[B]` contains no variable — it is constant across the element. That is what makes S3 a
constant-strain element, and why the stiffness integral collapses to a multiplication.

Element 2, columns `1u 1v 3u 3v 4u 4v`:

```
[B]₂ =     0      0   0.1     0   -0.1      0
           0   -0.1     0     0      0    0.1
        -0.1      0     0   0.1    0.1   -0.1
```

### `[D]` — material

For plane stress:

```
[D] = E/(1-ν²) × | 1   ν        0    |
                 | ν   1        0    |
                 | 0   0   (1-ν)/2   |
```

```
E/(1-ν²) = 210000/0.91 = 230769.23
```

```
[D] =  230769.23    69230.77          0
        69230.77   230769.23          0
               0           0   80769.23
```

Check: `230769.23 × 0.3 = 69230.77` and `230769.23 × 0.35 = 80769.23`. `[D]` is identical
for both elements — same material, same section.

### `[Kᵉ]`

```
[Kᵉ] = [B]ᵀ[D][B] · A · t
```

With `A = 50` and `t = 2` the scaling factor is 100. Checking the top-left entry of
element 1, where column `1u` of `[B]₁` is `{-0.1, 0, 0}`:

```
[D]{-0.1, 0, 0}ᵀ = {-23076.92, -6923.08, 0}ᵀ
Kᵉ_1u,1u = {-0.1, 0, 0} · {-23076.92, -6923.08, 0} × 100 = 230769.23
```

And `Kᵉ_1v,1v`, where column `1v` is `{0, 0, -0.1}`:

```
[D]{0, 0, -0.1}ᵀ = {0, 0, -8076.92}ᵀ  →  807.69 × 100 = 80769.23
```

Element 1:

```
            1u         1v         2u         2v         3u         3v
1u   230769.23       0.00 -230769.23   69230.77       0.00  -69230.77
1v        0.00   80769.23   80769.23  -80769.23  -80769.23       0.00
2u  -230769.23   80769.23  311538.46 -150000.00  -80769.23   69230.77
2v    69230.77  -80769.23 -150000.00  311538.46   80769.23 -230769.23
3u        0.00  -80769.23  -80769.23   80769.23   80769.23       0.00
3v   -69230.77       0.00   69230.77 -230769.23       0.00  230769.23
```

Element 2:

```
            1u         1v         3u         3v         4u         4v
1u    80769.23       0.00       0.00  -80769.23  -80769.23   80769.23
1v        0.00  230769.23  -69230.77       0.00   69230.77 -230769.23
3u        0.00  -69230.77  230769.23       0.00 -230769.23   69230.77
3v   -80769.23       0.00       0.00   80769.23   80769.23  -80769.23
4u   -80769.23   69230.77 -230769.23   80769.23  311538.46 -150000.00
4v    80769.23 -230769.23   69230.77  -80769.23 -150000.00  311538.46
```

Two properties to check on any element matrix:

- **Symmetric**, a consequence of `[B]ᵀ[D][B]` with symmetric `[D]`.
- **Every row sums to zero** — rigid-body translation produces no force. This is why an
  unconstrained stiffness matrix is singular.

---

## 6. Assembly

The global matrix is 8 × 8, one row and column per DOF, initialised to zero. Each element
matrix is added at the positions matching its own DOF labels.

Element 1 touches `1u 1v 2u 2v 3u 3v`, element 2 touches `1u 1v 3u 3v 4u 4v`. They
overlap at `1u 1v 3u 3v` — the two nodes on the shared diagonal — and those positions
receive both contributions:

```
K_1u,1u = 230769.23 + 80769.23 = 311538.46
K_1u,3v = (-69230.77) + (-80769.23) = -150000.00
```

Position `2u,4u` gets nothing. Node 2 belongs only to element 1, node 4 only to element
2, and no element connects them. In a real mesh most node pairs share no element, which
is why `[K]` is sparse.

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

The zero block at `2u,4u` / `2v,4v` and its mirror marks nodes 2 and 4 — the two corners
not joined by the diagonal.

---

## 7. Boundary Conditions and Loads

The force vector is zero except where loads were applied:

```
      1u    1v    2u    2v    3u      3v    4u      4v
F = [  0     0     0     0     0    1000     0    1000 ]
```

The displacement vector starts as all unknown (`*`), with prescribed values written in:

```
      1u    1v    2u    2v    3u    3v    4u    4v
u = [ 0.0   0.0    *    0.0    *     *     *     * ]
```

Five unknowns, matching the active mask from step 4.

---

## 8. Reducing the System

Rows and columns for constrained DOFs are struck out, leaving `[K_ff]{u_f} = {F_f}` over
`2u, 3u, 3v, 4u, 4v`:

```
              2u          3u          3v          4u          4v
2u    311538.46   -80769.23    69230.77        0.00        0.00
3u    -80769.23   311538.46        0.00  -230769.23    69230.77
3v     69230.77        0.00   311538.46    80769.23   -80769.23
4u         0.00  -230769.23    80769.23   311538.46  -150000.00
4v         0.00    69230.77   -80769.23  -150000.00   311538.46
```

```
{F_f} = {0, 0, 1000, 0, 1000}
```

The 8 × 8 system is now 5 × 5 and no longer singular — the constraints have removed the
rigid-body motions.

---

## 9. Solving

`direct_solver.py` reduces the matrix to upper triangular, then back-substitutes.

### Forward elimination

Each step applies a partial pivot, swapping in the row with the largest absolute value in
the current column. Here the diagonal already dominates so no swaps occur, but on an
ill-conditioned model they matter.

```
Step 0, pivot 2u = 311538.46
    row 3u -= -0.259259 × row 2u        check: -80769.23 / 311538.46 = -0.259259
    row 3v -= +0.222222 × row 2u

Step 1, pivot 3u = 290598.29
    row 3v -= +0.061765 × row 3u
    row 4u -= -0.794118 × row 3u
    row 4v -= +0.238235 × row 3u

Step 2, pivot 3v = 295045.25
    row 4u -= +0.322061 × row 3v
    row 4v -= -0.288245 × row 3v

Step 3, pivot 4u = 97677.44
    row 4v -= -0.692410 × row 4u
```

The upper triangular system:

```
              2u          3u          3v          4u          4v          F
2u    311538.46   -80769.23    69230.77        0.00        0.00        0.00
3u          0.00   290598.29    17948.72  -230769.23    69230.77        0.00
3v          0.00        0.00   295045.25    95022.62   -85045.25     1000.00
4u          0.00        0.00        0.00    97677.44   -67632.85     -322.06
4v          0.00        0.00        0.00        0.00   223701.73     1065.25
```

### Back substitution

The last row has a single unknown; work upward.

```
v₄ = 1065.2463 / 223701.73                    =  0.00476190
u₄ = (-322.0612 - (-322.0612)) / 97677.44     =  0.00000000
v₃ = (1000 - (-404.9774)) / 295045.25         =  0.00476190
u₃ = (0 - 415.1404) / 290598.29               = -0.00142857
u₂ = (0 - 445.0549) / 311538.46               = -0.00142857
```

| Node | u (mm) | v (mm) |
|---|---|---|
| 1 | 0 | 0 |
| 2 | −0.00142857 | 0 |
| 3 | −0.00142857 | 0.00476190 |
| 4 | 0 | 0.00476190 |

Both top nodes rise equally, so the top edge stays horizontal. Both right-hand nodes draw
in equally, so the right edge stays vertical. Node 4 does not move sideways because it
sits on the same vertical line as the pinned node 1. The square has become a taller,
narrower rectangle.

As exact fractions, `0.00476190 = 1/210` and `-0.00142857 = -1/700`.

---

## 10. Stresses

Stress is recovered element by element as `{σ} = [D][B]{uᵉ}`. Element 1, DOFs in element
order `1u 1v 2u 2v 3u 3v`:

```
{uᵉ} = {0, 0, -1/700, 0, -1/700, 1/210}
```

Strains, using `[B]₁`:

```
εxx = -0.1(0) + 0.1(-1/700)                        = -1.42857 × 10⁻⁴
εyy = -0.1(0) + 0.1(1/210)                         =  4.76190 × 10⁻⁴
γxy = -0.1(0) - 0.1(-1/700) + 0.1(0) + 0.1(-1/700) =  0
```

Stress, `{σ} = [D]{ε}`:

```
σxx = 230769.23(-1.42857×10⁻⁴) + 69230.77(4.76190×10⁻⁴) = -32.967 + 32.967 = 0
σyy =  69230.77(-1.42857×10⁻⁴) + 230769.23(4.76190×10⁻⁴) = -9.890 + 109.890 = 100
τxy =  80769.23 × 0                                       = 0
```

The two terms in σxx cancel exactly — the plate contracts sideways by precisely the
amount that leaves no lateral stress, because nothing restrains it.

| Element | `s1` (σxx) | `s2` (σyy) | `s12` (τxy) |
|---|---|---|---|
| e1 | 0.0 | 100.0 | 0.0 |
| e2 | 0.0 | 100.0 | 0.0 |

Identical, as required for a uniform stress field.

> Column names `s1`, `s2`, `s12` hold σxx, σyy, τxy. They are **not** principal stresses
> despite the naming.

### Principal and von Mises

From Mohr's circle, centre `(0+100)/2 = 50` and radius `√(50² + 0²) = 50`:

| | `σ_max` | `σ_min` | `τ_max` |
|---|---|---|---|
| both elements | 100.0 | 0.0 | 50.0 |

```
σvm = √(0² - 0(100) + 100² + 3(0)²) = 100 MPa
```

For a uniaxial stress state von Mises equals the applied stress exactly.

> The `SP` columns `a`, `opp` and `adj` — the principal *direction*, used only for the
> vector plot — are currently 90° out. Magnitudes are unaffected. See item 26 in
> [todo.md](todo.md).

---

## 11. Reactions

Reactions are recovered as `{R} = [K]{u} - {F}`:

| Node | `R_x` (N) | `R_y` (N) |
|---|---|---|
| 1 | 0 | −1000 |
| 2 | 0 | −1000 |
| 3 | 0 | 0 |
| 4 | 0 | 0 |

Three checks, applicable to any model:

1. **Reactions appear only at constrained nodes.** Nodes 3 and 4 are free and carry none.
2. **Vertical reactions balance the load.** `-1000 - 1000 = -2000` N against +2000 N
   applied.
3. **Horizontal reactions are zero.** The roller lets the plate contract freely, so node 1
   carries no x-reaction. A non-zero value means the restraints are fighting the
   deformation.

If reactions do not balance the applied load, the model is wrong — check this before
looking at stress contours.

> FEsolver prints a residual line during the solve. That check is currently vacuous and
> passes regardless of the answer (item 3 in [todo.md](todo.md)). Check reactions by hand
> until it is fixed.

---

## 12. Comparison With Theory

| Quantity | Hand calculation | FEsolver | Match |
|---|---|---|---|
| σyy | 100 MPa | 100.0 MPa | exact |
| σxx | 0 | 0.0 | exact |
| von Mises | 100 MPa | 100.0 MPa | exact |
| v at top edge | 0.00476190 mm | 0.00476190 mm | exact |
| u at right edge | −0.00142857 mm | −0.00142857 mm | exact |
| Total reaction | −2000 N | −2000 N | exact |

Exact, not approximate. The true displacement field is linear in x and y, and a linear
triangle represents a linear field perfectly, so there is no discretisation error.

This does not hold on a real model:

- **Uniform stress field** — S3 is exact; one element would do.
- **Varying stress field** — S3 is only as good as the mesh, and poor near a stress
  concentration. This is why real analyses use quadratic or quadrilateral elements, and
  why mesh convergence studies exist.

Because the result should be exact, this model makes a good regression test — item 18 in
[todo.md](todo.md).

---

## 13. Run It Yourself

GUI: `python main.py`, select this repository as the working directory, then
`examples/worked_example.inp`.

Headlessly, to inspect intermediate values:

```python
from pathlib import Path
from fe_solver.core import model, solver

m = model.call_gen_function(model.load_input("examples/worked_example.inp"))
s = solver.Solver(m, True, False, False, Path(""))

# element matrices (step 5)
e1 = m["elements"][1]["K"]
print(e1.area)                             # 50.0
print(e1.B)                                # 3x6 strain-displacement
print(e1.D)                                # 3x3 material
print(e1.element_stiffness_matrix)         # 6x6 labelled by DOF

# global and reduced systems (steps 6-8)
print(s.global_stiffness_matrix)           # 8x8 labelled
print(s.global_stiffness_matrix_reduced)   # 5x5
print(s.index_reduced)                     # ['2u' '3u' '3v' '4u' '4v']

# results (steps 9-11)
print(s.results["node"]["U"].data)
print(s.results["element"]["S"].data)
print(s.results["node"]["RF"].data)
```

### Variations

Each has been run; the stated result is what happens.

| Change | Result |
|---|---|
| Fix node 2 in x as well (`2, 1, 1`) | The base cannot contract, destroying the uniform field. σyy splits to **97.20** and **102.80** MPa; von Mises drops to 86.53 in one element. No warning is given. |
| Halve the thickness to 1 mm | Stress doubles to exactly **200 MPa**, as `σ = F/A` requires. |
| Flip element 1 to clockwise (`1, 1, 3, 2`) | Area goes negative, σyy becomes **1.25 × 10¹⁷** MPa. Returned silently with no error — item 6 in [todo.md](todo.md). |
| Refine — add a node at (5,5), split into four | Answer unchanged: 100.0 MPa in all four elements, displacements identical to the last bit (0.004761904761904764 against 0.004761904761904762). That invariance is what a patch test asserts. |
