# Worked example

This page solves a 2-element model by hand, from the input file to the stresses. Every
number is the value FEsolver calculates, so you can check each stage as you go.

Input file: [`examples/worked_example.inp`](../examples/worked_example.inp)

[theory.md](theory.md) explains each step.

---

## Contents

1. [The problem](#1-the-problem)
2. [Expected answer](#2-expected-answer)
3. [The input file](#3-the-input-file)
4. [The parsed model](#4-the-parsed-model)
5. [Element stiffness](#5-element-stiffness)
6. [Assembly](#6-assembly)
7. [Boundary conditions and loads](#7-boundary-conditions-and-loads)
8. [Reducing the system](#8-reducing-the-system)
9. [Solving](#9-solving)
10. [Stresses](#10-stresses)
11. [Reactions](#11-reactions)
12. [Comparison with theory](#12-comparison-with-theory)
13. [Run it yourself](#13-run-it-yourself)

---

## 1. The problem

A square steel plate, 10 mm × 10 mm and 2 mm thick, in vertical tension. Node 1 is pinned
and node 2 is on a roller.

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

Units are mm, N and MPa. FEsolver does not track units, so you must keep them consistent.

E1 is the lower-right triangle (nodes 1, 2, 3) and E2 is the upper-left (nodes 1, 3, 4).
Both list their nodes anticlockwise. Element area comes from a determinant, so clockwise
nodes give a negative area and a negative-definite stiffness matrix. FEsolver does not
check for this, see item 6 in [todo.md](todo.md).

---

## 2. Expected answer

```
A      = 10 × 2 = 20 mm²
σyy    = F/A = 2000/20              = 100 MPa
εyy    = σyy/E = 100/210000         = 4.7619 × 10⁻⁴
v_top  = εyy × 10                   = 4.7619 × 10⁻³ mm
εxx    = -ν εyy                     = -1.42857 × 10⁻⁴
u_x=10 = εxx × 10                   = -1.42857 × 10⁻³ mm
```

The stress field is uniform, and a constant-strain element can represent a uniform field
without error. FEsolver should match these values to rounding error. This check is called
a patch test.

---

## 3. The input file

FEsolver reads Abaqus-style `.inp` files. [keywords.md](keywords.md) lists every keyword.

### Nodes

Each line gives the node number, then its coordinates. FEsolver ignores a third
coordinate if there is one.

```
*Node
      1,           0.,           0.
      2,          10.,           0.
      3,          10.,          10.
      4,           0.,          10.
```

### Elements

Each line gives the element number, then its 3 nodes in anticlockwise order. `S3` is the
only element type.

```
*Element, type=S3
1, 1, 2, 3
2, 1, 3, 4
```

Do not add `elset=` to this line. FEsolver reads the element type as `s3, elset` and
stops with an error. Define sets separately.

### Section and material

The data line gives the thickness. FEsolver ignores the second value, the number of
integration points.

```
*Shell Section, elset=AllElements, material=Steel
2., 5

*Material, name=Steel
*Elastic
210000., 0.3
```

### Boundary conditions

Each line gives the node number, the first DOF and the last DOF. DOF 1 is x and DOF 2 is
y. FEsolver applies one DOF for each line, so node 1 needs 2 lines.

```
*Boundary
1, 1, 1
1, 2, 2
2, 2, 2
```

### Loads

Each line gives the node number, the DOF and the magnitude. FEsolver applies loads at
nodes only. It has no pressure or distributed load keyword.

```
*Cload
3, 2, 1000.
4, 2, 1000.
```

---

## 4. The parsed model

`model.call_gen_function()` returns a dictionary. FEsolver skips keywords it does not
recognise, such as `*Part`, `*Step` and `*Output`, so it can read Abaqus/CAE files
unedited. It changes set and material names to lower case.

```python
{'nodes':    {1: [0.0, 0.0], 2: [10.0, 0.0], 3: [10.0, 10.0], 4: [0.0, 10.0]},
 'elements': {1: {'nodes': [1, 2, 3], 'type': 's3'},
              2: {'nodes': [1, 3, 4], 'type': 's3'}},
 'section':  {'elementset': 'allelements', 'material': 'steel', 'thickness': 2.0},
 'elasticity': [210000.0, 0.3],
 'boundary': {1: {'1': 0.0, '2': 0.0}, 2: {'2': 0.0}},
 'load':     {3: {'2': 1000.0}, 4: {'2': 1000.0}},
 'dof': 8,
 'active_mask': [False, False, True, False, True, True, True, True]}
```

`active_mask` shows which of the 8 DOFs are free:

| DOF | `1u` | `1v` | `2u` | `2v` | `3u` | `3v` | `4u` | `4v` |
|---|---|---|---|---|---|---|---|---|
| Free? | ✗ | ✗ | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ |

That gives 5 free DOFs, so 5 unknowns. [data_structures.md](data_structures.md) describes
every key in the dictionary.

---

## 5. Element stiffness

### Area

Element 1, nodes 1 (0,0), 2 (10,0), 3 (10,10):

```
A = ½ det | 1    0    0 |
          | 1   10    0 |   = ½(1(10·10 - 0·10)) = 50 mm²
          | 1   10   10 |
```

Both elements are 50 mm².

### Shape function coefficients

```
b₁ = y₂ - y₃     b₂ = y₃ - y₁     b₃ = y₁ - y₂
c₁ = x₃ - x₂     c₂ = x₁ - x₃     c₃ = x₂ - x₁
```

| Element | b₁ | b₂ | b₃ | c₁ | c₂ | c₃ |
|---|---|---|---|---|---|---|
| 1 (nodes 1, 2, 3) | −10 | 10 | 0 | 0 | −10 | 10 |
| 2 (nodes 1, 3, 4) | 0 | 10 | −10 | −10 | 0 | 10 |

### `[B]`, strain-displacement

```
[B] = 1/(2A) × | b₁    0   b₂    0   b₃    0 |
               |  0   c₁    0   c₂    0   c₃ |
               | c₁   b₁   c₂   b₂   c₃   b₃ |
```

Element 1, with `2A = 100`. The columns are `1u 1v 2u 2v 3u 3v` and the rows are εxx, εyy,
γxy:

```
[B]₁ =  -0.1      0    0.1      0     0     0
           0      0      0   -0.1     0   0.1
           0   -0.1   -0.1    0.1   0.1     0
```

Element 2, with columns `1u 1v 3u 3v 4u 4v`:

```
[B]₂ =     0      0   0.1     0   -0.1      0
           0   -0.1     0     0      0    0.1
        -0.1      0     0   0.1    0.1   -0.1
```

### `[D]`, material

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

`[D]` is the same for both elements, because they share a material and section.

### `[Kᵉ]`

```
[Kᵉ] = [B]ᵀ[D][B] · A · t
```

With `A = 50` and `t = 2`, the scaling factor is 100. For the top-left entry of element 1,
column `1u` of `[B]₁` is `{-0.1, 0, 0}`:

```
[D]{-0.1, 0, 0}ᵀ = {-23076.92, -6923.08, 0}ᵀ
Kᵉ_1u,1u = {-0.1, 0, 0} · {-23076.92, -6923.08, 0} × 100 = 230769.23
```

For `Kᵉ_1v,1v`, column `1v` is `{0, 0, -0.1}`:

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

Both matrices are symmetric, and every row sums to zero.

---

## 6. Assembly

The global matrix is 8 × 8 and starts at zero. FEsolver adds each element matrix at the
positions that match its DOF labels.

Element 1 uses `1u 1v 2u 2v 3u 3v` and element 2 uses `1u 1v 3u 3v 4u 4v`. They share
`1u 1v 3u 3v`, so those positions get both contributions:

```
K_1u,1u = 230769.23 + 80769.23   = 311538.46
K_1u,3v = -69230.77 + -80769.23  = -150000.00
```

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

The zero block at `2u,4u` and `2v,4v`, and its mirror, is between nodes 2 and 4. No element
connects them.

---

## 7. Boundary conditions and loads

```
      1u    1v    2u    2v    3u      3v    4u      4v
F = [  0     0     0     0     0    1000     0    1000 ]
```

The displacement vector starts with every DOF unknown (`*`). FEsolver then writes in the
prescribed values:

```
      1u    1v    2u    2v    3u    3v    4u    4v
u = [ 0.0   0.0    *    0.0    *     *     *     * ]
```

---

## 8. Reducing the system

FEsolver removes the rows and columns of the constrained DOFs. This leaves
`[K_ff]{u_f} = {F_f}` over `2u, 3u, 3v, 4u, 4v`:

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

---

## 9. Solving

`direct_solver.py` reduces the matrix to upper triangular form, then solves it by back
substitution.

### Forward elimination

Each step starts with a partial pivot. Here the diagonal is already the largest entry in
each column, so no rows are swapped.

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

```
              2u          3u          3v          4u          4v          F
2u    311538.46   -80769.23    69230.77        0.00        0.00        0.00
3u          0.00   290598.29    17948.72  -230769.23    69230.77        0.00
3v          0.00        0.00   295045.25    95022.62   -85045.25     1000.00
4u          0.00        0.00        0.00    97677.44   -67632.85     -322.06
4v          0.00        0.00        0.00        0.00   223701.73     1065.25
```

### Back substitution

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

As fractions, `0.00476190 = 1/210` and `-0.00142857 = -1/700`.

---

## 10. Stresses

FEsolver calculates stress for each element as `{σ} = [D][B]{uᵉ}`. For element 1, with DOFs
in element order `1u 1v 2u 2v 3u 3v`:

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

| Element | `s1` (σxx) | `s2` (σyy) | `s12` (τxy) |
|---|---|---|---|
| e1 | 0.0 | 100.0 | 0.0 |
| e2 | 0.0 | 100.0 | 0.0 |

The columns `s1`, `s2` and `s12` hold σxx, σyy and τxy. They are not principal stresses.

### Principal and von Mises stress

Mohr's circle has its centre at `(0+100)/2 = 50` and a radius of `√(50² + 0²) = 50`:

| | `σ_max` | `σ_min` | `τ_max` |
|---|---|---|---|
| Both elements | 100.0 | 0.0 | 50.0 |

```
σvm = √(0² - 0(100) + 100² + 3(0)²) = 100 MPa
```

The `SP` columns `a`, `opp` and `adj` give the principal direction for the vector plot.
They are currently 90° out. The magnitudes are correct. See item 26 in
[todo.md](todo.md).

---

## 11. Reactions

FEsolver calculates reactions as `{R} = [K]{u} - {F}`:

| Node | `R_x` (N) | `R_y` (N) |
|---|---|---|
| 1 | 0 | −1000 |
| 2 | 0 | −1000 |
| 3 | 0 | 0 |
| 4 | 0 | 0 |

The reactions are non-zero only at the constrained nodes. The 2 vertical reactions balance
the 2000 N applied load. Both horizontal reactions are zero, so the roller does not resist
the Poisson contraction.

FEsolver prints a residual line during the solve. That check currently passes whatever
the answer is, see item 3 in [todo.md](todo.md). Check the reactions by hand until it is
fixed.

---

## 12. Comparison with theory

| Quantity | Hand calculation | FEsolver | Match |
|---|---|---|---|
| σyy | 100 MPa | 100.0 MPa | Exact |
| σxx | 0 | 0.0 | Exact |
| von Mises | 100 MPa | 100.0 MPa | Exact |
| v at top edge | 0.00476190 mm | 0.00476190 mm | Exact |
| u at right edge | −0.00142857 mm | −0.00142857 mm | Exact |
| Total reaction | −2000 N | −2000 N | Exact |

The results match because the true displacement field is linear, and a linear triangle
represents a linear field without discretisation error. When the stress is not uniform,
for example near a stress concentration, accuracy depends on the mesh.

Because the answer is known, this model is also a good regression test. See item 18 in
[todo.md](todo.md).

---

## 13. Run it yourself

In the GUI, run `python main.py`, select this repository as the working directory, then
select `examples/worked_example.inp`.

To run it without the GUI and inspect the values at each step:

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

Each of these changes has been run, and the result is what FEsolver gives.

| Change | Result |
|---|---|
| Fix node 2 in x as well (`2, 1, 1`) | The stress field is no longer uniform. σyy splits to 97.20 and 102.80 MPa, and von Mises drops to 86.53 MPa in one element. FEsolver gives no warning. |
| Halve the thickness to 1 mm | The stress doubles to 200 MPa. |
| Make element 1 clockwise (`1, 1, 3, 2`) | The area goes negative and σyy becomes 1.25 × 10¹⁷ MPa. FEsolver gives no warning, see item 6 in [todo.md](todo.md). |
| Refine: add a node at (5,5) and split into 4 elements | No change. Every element gives 100.0 MPa, and the displacements differ only in the last digits (0.004761904761904764 against 0.004761904761904762). |
