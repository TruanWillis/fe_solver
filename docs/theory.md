# Finite Element Analysis: Theory and Process

This document explains what FEsolver does at each step and why. It is written for
engineers who use FEA but may not remember the underlying theory. Equations appear in
marked blocks that can be skipped without losing the thread.

Code references point to `solver.py`, `direct_solver.py`, and `elements.py`.
A companion [worked example](worked_example.md) follows a two-element model from the
`.inp` file to final stresses with numbers at every step.

---

## Contents

1. [What Does FEA Actually Do?](#1-what-does-fea-actually-do)
2. [The Mesh: Elements and DOFs](#2-the-mesh-elements-and-dofs)
3. [Element Stiffness](#3-element-stiffness)
4. [Assembly](#4-assembly)
5. [Boundary Conditions and Loads](#5-boundary-conditions-and-loads)
6. [Reducing the System](#6-reducing-the-system)
7. [Solving for Displacements](#7-solving-for-displacements)
8. [Stresses](#8-stresses)
9. [Summary](#9-summary)

---

## 1. What Does FEA Actually Do?

### The governing equations

Elasticity theory describes how a loaded structure deforms. The governing equations are
the same for every linear elastic problem — what changes between problems is the
geometry, material properties, and boundary conditions.

The equations express a simple requirement: at every point inside the structure, the
internal stresses must be in equilibrium. Take a tiny element of material (a small
square in 2D, a cube in 3D). Stress acts on all its faces. The equilibrium equations say
that the stresses on opposite faces must balance — if they don't, that element of
material would accelerate, which cannot happen in a static problem.

Stress is rarely uniform across a structure. Near a hole it is higher, far from a load it
is lower. If stress varies from one side of the tiny element to the other, the rate of
that variation must be accounted for. The equilibrium equations govern exactly this: how
stress is allowed to vary spatially.

> **The maths.** In 2D, equilibrium in the x and y directions gives two equations:
>
> ```
> (rate of change of σxx in x) + (rate of change of τxy in y) + body force in x = 0
> (rate of change of τxy in x) + (rate of change of σyy in y) + body force in y = 0
> ```

These two equations contain three unknowns (σxx, σyy, τxy). To close the system, stress
is expressed in terms of strain (via the material law), and strain is expressed in terms
of displacement (strain is the change in displacement per unit length). After
substitution the only unknowns are the displacement functions u(x,y) and v(x,y).

The result is a **partial differential equation (PDE)**: the unknowns are continuous
functions of x and y, and the equations involve how those functions change in both
directions simultaneously. The solution must satisfy these equations at every point
inside the structure, on whatever geometry you give it.

For simple shapes — a uniform bar, a hole in an infinite plate, a thin beam — the PDEs
can be solved exactly. These are the textbook formulae engineers already know. For
anything with realistic geometry they cannot.

### How FEA converts the PDE into simultaneous equations

FEA makes two moves:

**Finite unknowns.** Instead of a continuous displacement function defined everywhere,
assume displacement varies linearly within each element and track values only at the
nodes. A 500-node mesh has 1000 unknowns (two DOFs per node) instead of infinitely many.

**Finite equations.** Instead of enforcing equilibrium at every point, enforce it at every
node. At each node the internal forces from the surrounding elements must balance the
applied external force. The internal force at a node comes from the stresses in its
connected elements, which come from strains (via `[D]`), which come from nodal
displacements (via `[B]`). So the internal force at each node is a linear combination of
the nodal displacements — which is exactly what one row of `[K]{u} = {F}` says.

One DOF, one equation, one row. The PDE has become a system of simultaneous equations:

```
[K]{u} = {F}
```

- **`[K]`** — the **stiffness matrix**. Encodes how stiff the structure is: push here,
  how much does it deflect there.
- **`{u}`** — the **displacement vector**. The unknown nodal displacements.
- **`{F}`** — the **force vector**. The applied loads.

The approximation improves as elements get smaller and nodes get closer together. With a
fine enough mesh the solution converges toward the exact PDE answer.

Everything the solver does is either building `[K]` and `{F}`, or solving for `{u}`.

### Force-driven vs displacement-driven

FEsolver supports both:

**Force-driven:** external forces applied at nodes, solver finds displacements.

**Displacement-driven:** known displacements prescribed at nodes, solver finds the
remaining free displacements. Common in displacement-controlled testing or when boundary
motion is known from another analysis.

---

## 2. The Mesh: Elements and DOFs

FEsolver uses the **S3 element** — a flat triangle defined by three corner nodes.

```
        k
       / \
      /   \
     /     \
    i-------j
```

Each node has two **degrees of freedom (DOFs)**: horizontal displacement `u` and
vertical displacement `v`. One element has `3 × 2 = 6` DOFs:
`{u_i, v_i, u_j, v_j, u_k, v_k}`.

For a mesh with n nodes the model has 2n DOFs total. In the code, DOFs are labelled by
node number and direction — node 3 has `3u` and `3v`:

```python
self.node_headings = [
    f"{n}{dof}" for n in range(1, node_count + 1) for dof in ["u", "v"]
]
```

### Displacement inside an element

The mesh only tracks displacements at the nodes. Displacement at any interior point is
**linearly interpolated** from the three corner values using **shape functions**
`N_i`, `N_j`, `N_k`:

- `N_i = 1` at node i, `0` at nodes j and k
- `N_j = 1` at node j, `0` at nodes i and k
- `N_k = 1` at node k, `0` at nodes i and j

At any interior point, `N_i + N_j + N_k = 1`.

### Constant strain

Because displacement varies linearly, strain — the change in displacement per unit
length — is **constant** within each element. The slope of a straight line is the same
everywhere. Stress is therefore also uniform within each element.

This is an approximation. Near stress concentrations (holes, notches, re-entrant
corners) the mesh needs to be fine enough to capture the gradient across multiple
elements.

---

## 3. Element Stiffness

### What `[Kᵉ]` represents

The element stiffness matrix is a `6 × 6` matrix relating nodal forces to nodal
displacements for one element. Entry `(i, j)` is the force at DOF i produced by a unit
displacement at DOF j with all other DOFs held fixed.

In FEsolver, element stiffness matrices are computed in `elements.py`:

```python
cst = elements.Element(
    element_data["type"],
    x_cord, y_cord, node_list,
    self.model["elasticity"][0],  # E
    self.model["elasticity"][1],  # v
    self.model["section"]["thickness"],
)
self.model["elements"][element_number]["K"] = cst
```

### `[B]` — the strain-displacement matrix

`[B]` maps the six nodal displacements to the three strain components inside the
element: εxx (horizontal stretch), εyy (vertical stretch), and γxy (shear). Its entries
come from the element geometry — the node positions determine how nodal displacements
translate into strain.

Because S3 shape functions are linear, `[B]` is constant across the element. It is a
`3 × 6` matrix.

> **The maths.** `{ε} = [B]{uᵉ}`. The entries of `[B]` are the spatial derivatives
> of the shape functions — constants determined by the node coordinates.

### `[D]` — the material matrix

`[D]` converts strain into stress. It is built from two material properties:

- **Young's modulus E** — material stiffness. Higher E means larger stresses for the
  same strain.
- **Poisson's ratio ν** — lateral coupling. Stretch a material in x and it contracts
  in y. ν controls how much. For steel, ν ≈ 0.3. If ν = 0 the axes are independent.

FEsolver uses the **plane stress** form of `[D]`, valid for thin plates where
out-of-plane stress is zero.

> **The maths.**
> ```
> [D] = E/(1-ν²) × | 1    ν        0     |
>                   | ν    1        0     |
>                   | 0    0    (1-ν)/2   |
> ```

### Computing `[Kᵉ]`

The stiffness matrix chains geometry and material together: displacement → strain
(via `[B]`) → stress (via `[D]`) → nodal forces. For an S3 element with area A and
thickness t:

```
[Kᵉ] = [B]ᵀ [D] [B] × A × t
```

Because `[B]` and `[D]` are both constant across the element, this reduces to a single
matrix multiplication:

```python
element_stiffness = np.matmul(Bt, np.matmul(self.D, self.B)) * self.area * self.t
```

The result is a `6 × 6` symmetric matrix.

---

## 4. Assembly

Each `[Kᵉ]` describes one element in isolation. The **global stiffness matrix** `[K]`
combines them into a single system representing the entire structure.

At shared nodes, contributions from every connected element are **added together**. This
enforces **compatibility** — the mesh deforms as one connected piece, not a collection
of independent triangles.

For a mesh with n nodes, `[K]` is `2n × 2n`, initialised to zero. Each element's
`6 × 6` entries are added at the rows and columns matching that element's DOFs:

```python
self.global_stiffness_matrix = pd.DataFrame(
    np.zeros((self.dof, self.dof)),
    columns=self.node_headings,
    index=self.node_headings,
)

for element_number, element_data in self.model["elements"].items():
    element_stiffness_matrix = element_data["K"].element_stiffness_matrix

    for col in element_stiffness_matrix.columns:
        for row in element_stiffness_matrix.index:
            self.global_stiffness_matrix.at[
                row, col
            ] += element_stiffness_matrix.at[row, col]
```

The element stiffness matrices carry DOF labels (`1u`, `1v`, `2u`, ...) matching the
global matrix, so assembly is a direct label-to-label addition with no index mapping.

### Stiffness matrix heatmap

When `save_matrix = True`, FEsolver records which elements contribute to each position
in `[K]`, producing the heatmap in the GUI. Dense diagonal blocks indicate nodes with
many element connections; off-diagonal entries show which nodes are linked through shared
elements.

---

## 5. Boundary Conditions and Loads

### Boundary conditions

Boundary conditions fix specific DOFs. A fully fixed node has both u and v set to 0. A
roller might fix v while leaving u free.

The displacement vector `{u}` starts with `"*"` at every DOF (unknown). Boundary
conditions overwrite specific entries with known values — typically `0.0` for fixed
supports, or a prescribed non-zero value for displacement-driven models.

### Loads

For force-driven models, applied forces are written into `{F}` at the relevant DOFs.

### Code

Both are applied by `assemble_dof_series()`, which reads definitions from the `.inp`
file and writes each value into the correct DOF:

```python
def assemble_dof_series(self, series, condition):
    for ident, dof_values in self.model[condition].items():
        if isinstance(ident, str) and ident in self.model["nodesets"]:
            node_list = self.model["nodesets"][ident]
        else:
            node_list = [int(ident)]

        for axis, value in dof_values.items():
            if axis == "1":
                direction = "u"
            elif axis == "2":
                direction = "v"
            for n in node_list:
                series.at[f"{n}{direction}"] = value
```

Axis `"1"` is x (u), `"2"` is y (v), following the Abaqus `.inp` convention. A
definition can name a single node or a node set.

If no loads are defined, the model is treated as displacement-driven and
`self.homogeneous_model` is set to `False`.

> **Known limitation.** Force-driven and displacement-driven are currently mutually
> exclusive — a model with both silently ignores the prescribed displacements. See items
> 4, 23 and 24 in [todo.md](todo.md).

---

## 6. Reducing the System

The full system `[K]{u} = {F}` includes both known (constrained) and unknown (free)
DOFs. Including the known DOFs makes the system overdetermined.

Without boundary conditions `[K]` is also **singular** — nothing prevents rigid body
motion, so no unique solution exists. Constraining enough DOFs eliminates this.

FEsolver identifies free DOFs using a boolean mask:

```python
mask = self.model["active_mask"]  # True = free, False = constrained
```

The free rows/columns of `[K]` and entries of `{F}` are extracted:

```python
self.global_stiffness_matrix_reduced = global_stiffness_matrix[np.ix_(mask, mask)]
forces_reduced = forces[mask]
```

### Displacement-driven reduction

For displacement-driven models, `{F}` is not given directly. The solver computes the
equivalent forces from the prescribed displacements:

```python
displacements = np.where(displacements == "*", 0.0, displacements).astype(np.float64)
forces = np.dot(stiffness_matrix, displacements)
```

The free DOFs are then extracted and solved as normal.

---

## 7. Solving for Displacements

The reduced system is:

```
[K_ff]{u_f} = {F_f}
```

A system of simultaneous equations — the same kind solved in school when two equations
share two unknowns, except here there may be hundreds or thousands. FEsolver provides
two methods, selectable via `fe_solver = True/False` in `config_user.json`.

### Method 1: Gaussian elimination (`fe_solver = True`)

Implemented in `direct_solver.py`. Works in two phases.

#### Forward elimination

Transforms the system into upper triangular form by eliminating entries below the
diagonal, column by column. For each column, a multiple of the current row is subtracted
from every row below it to zero out that column's entry:

```python
def forward_elimination(self):
    for i in range(len(self.force)):
        self.partial_pivot(i)
        pivot = self.stiffness[i, i]
        for j in range(i + 1, len(self.force)):
            factor = self.stiffness[j, i] / pivot
            self.stiffness[j, i:] = (
                self.stiffness[j, i:] - factor * self.stiffness[i, i:]
            )
            self.force[j] = self.force[j] - factor * self.force[i]
```

After elimination:

```
┌                    ┐ ┌    ┐   ┌      ┐
│ K₁₁   K₁₂   K₁₃  │ │ u₁ │   │  F₁  │
│  0    K'₂₂  K'₂₃  │ │ u₂ │ = │ F'₂  │
│  0     0    K''₃₃ │ │ u₃ │   │ F''₃ │
└                    ┘ └    ┘   └      ┘
```

#### Partial pivoting

The elimination divides by the diagonal entry. If it is zero the division fails; if it
is very small it amplifies rounding errors. Partial pivoting swaps the current row with
whichever row below has the largest absolute value in that column:

```python
def partial_pivot(self, i):
    max_row = np.argmax(np.abs(self.stiffness[i:, i])) + i
    if max_row != i:
        self.stiffness[[i, max_row]] = self.stiffness[[max_row, i]]
        self.force[[i, max_row]] = self.force[[max_row, i]]
```

Reordering equations does not change the solution.

#### Back substitution

Solves from the bottom up. The last equation has one unknown. Each equation above has
one more, resolved using the already-computed values below:

```python
def back_subtract(self):
    self.displacements = np.zeros(len(self.force))
    for i in range(len(self.force) - 1, -1, -1):
        sum_knowns = np.dot(self.stiffness[i, i + 1:], self.displacements[i + 1:])
        self.displacements[i] = (self.force[i] - sum_knowns) / self.stiffness[i, i]
```

### Method 2: NumPy (`fe_solver = False`)

```python
displacement_solution = np.linalg.solve(
    self.global_stiffness_matrix_reduced, self.forces_reduced
)
```

Uses LU decomposition — faster and more numerically stable for large systems, but
fundamentally the same approach: factor and back-substitute. It is the **reduced** matrix
that is passed; the full `[K]` is singular.

### Reassembling the full vector

Computed displacements are written back into the full displacement vector at the free DOF
positions. Constrained DOFs keep their prescribed values. For displacement-driven models
a sign correction is applied because the force vector was computed as `[K]{u_c}`:

```python
def apply_sign_correction(self, displacements):
    if self.homogeneous_model:
        return displacements
    return displacements * -1
```

```python
displacements_corrected = self.apply_sign_correction(displacement_solution)
displacements = pd.Series(displacements_corrected, index=self.index_reduced)

for index, displacement in displacements.items():
    self.displacements.at[index] = displacement
```

---

## 8. Stresses

With displacements known, stresses are recovered for each element in three stages.

### In-plane stresses

For each element, the six nodal displacements are extracted and stresses computed by
chaining `[B]` and `[D]`:

```python
for node in node_list:
    for disp in ["u", "v"]:
        u[count] = self.displacements[f"{node}{disp}"]

normal_stress = np.matmul(np.matmul(D, B), u)
```

This gives three components per element:

- **σxx** — normal stress in x. Positive = tension, negative = compression.
- **σyy** — normal stress in y.
- **τxy** — shear stress.

All three are uniform within the element (constant strain).

### Principal stresses

σxx, σyy, and τxy depend on the coordinate system. **Principal stresses** are
coordinate-independent — they are the maximum and minimum normal stresses at any
orientation, found at the angle where shear is zero.

The solver computes σ₁, σ₂, and the principal angle θ, then decomposes into x and y
components for plotting.

The principal angle calculation divides by `σxx - σyy`, which is zero under equal
biaxial stress. The solver uses `atan2` to handle this:

```python
angle = -0.5 * m.atan2(2 * Sxy, Sx - Sy)
opp = m.sin(angle) * s1
adj = m.cos(angle) * s1
```

> **The maths.**
> ```
> σ₁,₂ = (σxx + σyy)/2 ± √(((σxx - σyy)/2)² + τxy²)
> θ = -½ arctan(2τxy / (σxx - σyy))
> ```

### Von Mises stress

Collapses the full stress state into a single number for yield checking. If σ_vm reaches
the material's yield strength, yielding begins. Standard for ductile materials.

```python
mises = m.sqrt(sigma_1**2 - sigma_1 * sigma_2 + sigma_2**2 + 3 * sigma_12**2)
```

The formula includes all three in-plane components — including shear — without requiring
a coordinate transformation.

> **The maths.**
> ```
> σ_vm = √(σxx² - σxx·σyy + σyy² + 3τxy²)
> ```

### Stress accuracy

Stress is constant within each S3 element, so there are **discontinuities** at element
boundaries. Adjacent elements report different stresses at their shared edge.

The size of these jumps is a rough indicator of mesh convergence — small jumps mean the
mesh is adequate; large jumps (especially near geometric features) mean it needs
refining.

FEsolver reports raw element values without nodal averaging.

---

## 9. Summary

| Step | What happens | Code function |
|------|-------------|---------------|
| Build `[Kᵉ]` | Each element gets a 6×6 stiffness matrix from its geometry and material | `define_element_stiffness()` |
| Assemble `[K]` | Element matrices are summed into the global matrix | `define_global_stiffness()` |
| Apply BCs | Constrained DOFs set to known values | `define_boundary_conditions()` |
| Apply loads | Forces written into `{F}` | `assemble_dof_series()` |
| Reduce | Known DOFs removed, leaving a solvable system | `reduce_matrix()` |
| Solve | Reduced system solved for free displacements | `compute_displacements()` |
| In-plane stress | Displacements → strains → stresses per element | `compute_normal_stress()` |
| Principal stress | Coordinate-independent max/min stresses | `compute_principal_stress()` |
| Von Mises | Single yield-check scalar per element | `compute_mises_stress()` |

Geometry and material in at the top, displacements and stresses out at the bottom. Each
function in `solver.py` maps to one row. For a worked numerical example, see
[worked_example.md](worked_example.md).
