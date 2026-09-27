# Finite element analysis: theory and process

This page explains what FEsolver does at each step of the finite element method, and why.
The maths is in separate blocks that you can skip.

Code references are to `solver.py`, `direct_solver.py` and `elements.py`.
[worked_example.md](worked_example.md) follows a 2-element model from the `.inp` file to
the final stresses, with the numbers at every step.

---

## Contents

1. [How FEA works](#1-how-fea-works)
2. [The mesh: elements and DOFs](#2-the-mesh-elements-and-dofs)
3. [Element stiffness](#3-element-stiffness)
4. [Assembly](#4-assembly)
5. [Boundary conditions and loads](#5-boundary-conditions-and-loads)
6. [Reducing the system](#6-reducing-the-system)
7. [Solving for displacements](#7-solving-for-displacements)
8. [Stresses](#8-stresses)
9. [Summary](#9-summary)

---

## 1. How FEA works

### The governing equations

Elasticity theory describes how a loaded structure deforms. The governing equations are
the same for every linear elastic problem. Only the geometry, material properties and
boundary conditions change.

The equations require the internal stresses to be in equilibrium at every point in the
structure. Take a small element of material: a square in 2D, or a cube in 3D. Stress acts
on all its faces, and the stresses on opposite faces must balance. If they did not, the
element would accelerate, which cannot happen in a static problem.

Stress is not usually uniform. It is higher near a hole and lower far from a load. If
stress varies across the small element, the equilibrium equations must account for that
variation. They set how stress can vary from point to point.

> The maths: in 2D, equilibrium in the x and y directions gives 2 equations:
>
> ```
> (rate of change of σxx in x) + (rate of change of τxy in y) + body force in x = 0
> (rate of change of τxy in x) + (rate of change of σyy in y) + body force in y = 0
> ```

These 2 equations have 3 unknowns: σxx, σyy and τxy. To close the system, stress is
written in terms of strain through the material law. Strain is written in terms of
displacement, as the change in displacement per unit length. After substitution, the only
unknowns are the displacement functions u(x,y) and v(x,y).

The result is a partial differential equation (PDE). The unknowns are continuous functions
of x and y, and the equations involve how they change in both directions. The solution
must satisfy the equations at every point inside the structure.

For simple shapes, such as a uniform bar, a hole in an infinite plate or a thin beam, the
PDEs can be solved exactly. These solutions are the textbook formulae. For realistic
geometry, they cannot.

### From the PDE to simultaneous equations

FEA makes 2 approximations:

1. Finite unknowns: displacement is assumed to vary linearly within each element, and is
   tracked only at the nodes. A 500-node mesh has 1,000 unknowns, because each node has 2
   degrees of freedom (DOFs).
2. Finite equations: equilibrium is enforced at every node instead of at every point. At
   each node, the internal forces from the connected elements must balance the applied
   external force.

The internal force at a node comes from the stresses in the connected elements. The
stresses come from strains through `[D]`, and the strains come from nodal displacements
through `[B]`. So the internal force at each node is a linear combination of the nodal
displacements. Each row of `[K]{u} = {F}` states this for one DOF.

The PDE becomes a system of simultaneous equations:

```
[K]{u} = {F}
```

- `[K]` is the stiffness matrix. It relates the nodal forces to the nodal displacements.
- `{u}` is the displacement vector, the unknown nodal displacements.
- `{F}` is the force vector, the applied loads.

The approximation improves as the elements get smaller. With a fine enough mesh, the
solution converges towards the exact PDE solution.

### Force-driven and displacement-driven models

FEsolver supports 2 kinds of model:

- force-driven: external forces are applied at nodes, and the solver finds the
  displacements
- displacement-driven: displacements are prescribed at nodes, and the solver finds the
  remaining free displacements

Displacement-driven models are common in displacement-controlled testing, or when the
boundary motion is known from another analysis.

---

## 2. The mesh: elements and DOFs

FEsolver uses the S3 element, a flat triangle with 3 corner nodes.

```
        k
       / \
      /   \
     /     \
    i-------j
```

FEsolver treats S3 as a plane-stress constant strain triangle (CST). This is not the same
as the Abaqus S3, which is a shell element with 6 DOFs at each node. The Abaqus element that
matches FEsolver's S3 is CPS3.

Each node has 2 DOFs: horizontal displacement `u` and vertical displacement `v`. One
element has `3 × 2 = 6` DOFs: `{u_i, v_i, u_j, v_j, u_k, v_k}`.

A mesh with n nodes has 2n DOFs. In the code, each DOF is labelled with its node number and
direction, so node 3 has `3u` and `3v`:

```python
self.node_headings = [
    f"{n}{dof}" for n in range(1, node_count + 1) for dof in ["u", "v"]
]
```

### Displacement inside an element

The mesh tracks displacement only at the nodes. At any point inside an element,
displacement is linearly interpolated from the 3 corner values, using the shape functions
`N_i`, `N_j` and `N_k`:

- `N_i = 1` at node i, `0` at nodes j and k
- `N_j = 1` at node j, `0` at nodes i and k
- `N_k = 1` at node k, `0` at nodes i and j

At any point inside the element, `N_i + N_j + N_k = 1`.

### Constant strain

Displacement varies linearly, so strain, the change in displacement per unit length, is
constant within each element. Stress is therefore also uniform within each element.

This is an approximation. Near stress concentrations, such as holes, notches and
re-entrant corners, the mesh must be fine enough to capture the stress gradient across
several elements.

---

## 3. Element stiffness

### What `[Kᵉ]` is

The element stiffness matrix is a `6 × 6` matrix that relates nodal forces to nodal
displacements for one element. Entry `(i, j)` is the force at DOF i caused by a unit
displacement at DOF j, with all other DOFs held fixed.

`elements.py` calculates the element stiffness matrices:

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

### `[B]`, the strain-displacement matrix

`[B]` converts the 6 nodal displacements into the 3 strain components in the element: εxx
(horizontal stretch), εyy (vertical stretch) and γxy (shear). Its entries depend on the
element geometry.

The S3 shape functions are linear, so `[B]` is constant across the element. It is a
`3 × 6` matrix.

> The maths: `{ε} = [B]{uᵉ}`. The entries of `[B]` are the spatial derivatives of the
> shape functions. They are constants set by the node coordinates.

### `[D]`, the material matrix

`[D]` converts strain into stress. It uses 2 material properties:

- Young's modulus E, the material stiffness: a higher E gives more stress for the same
  strain
- Poisson's ratio ν, the lateral coupling: a material stretched in x contracts in y, and ν
  sets how much. For steel, ν ≈ 0.3. If ν = 0, the axes are independent

FEsolver uses the plane stress form of `[D]`. It applies to thin plates, where the
out-of-plane stress is zero.

> The maths:
> ```
> [D] = E/(1-ν²) × | 1    ν        0     |
>                   | ν    1        0     |
>                   | 0    0    (1-ν)/2   |
> ```

### Calculating `[Kᵉ]`

The stiffness matrix links geometry and material. Displacement gives strain through `[B]`,
strain gives stress through `[D]`, and stress gives nodal forces. For an S3 element with
area A and thickness t:

```
[Kᵉ] = [B]ᵀ [D] [B] × A × t
```

`[B]` and `[D]` are both constant across the element, so this is a single matrix
multiplication:

```python
element_stiffness = np.matmul(Bt, np.matmul(self.D, self.B)) * self.area * self.t
```

The result is a symmetric `6 × 6` matrix.

---

## 4. Assembly

Each `[Kᵉ]` describes one element on its own. The global stiffness matrix `[K]` combines
them into one system for the whole structure.

At a shared node, FEsolver adds together the contributions from every connected element.
This enforces compatibility: the mesh deforms as one connected piece, not as separate
triangles.

For a mesh with n nodes, `[K]` is `2n × 2n` and starts at zero. FEsolver adds each
element's `6 × 6` entries at the rows and columns for that element's DOFs:

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

The element stiffness matrices use the same DOF labels as the global matrix: `1u`, `1v`,
`2u` and so on. Assembly adds entries by label, with no index mapping.

### Stiffness matrix heatmap

When `save_matrix` is `true`, FEsolver records which elements contribute to each entry of
`[K]`. It also plots `[K]` as a heatmap in the GUI, shaded by the size of each entry. Dense
blocks on the diagonal show nodes with many element connections. Off-diagonal entries show
which nodes share an element.

---

## 5. Boundary conditions and loads

### Boundary conditions

Boundary conditions fix specific DOFs. A fully fixed node has u and v both set to 0. A
roller might fix v and leave u free.

The displacement vector `{u}` starts with `"*"` at every DOF to mark it as unknown.
Boundary conditions replace specific entries with known values. These are usually `0.0`
for fixed supports, or a prescribed non-zero value in a displacement-driven model.

### Loads

In a force-driven model, FEsolver writes the applied forces into `{F}` at the relevant
DOFs.

### Code

`assemble_dof_series()` applies both. It reads the definitions from the `.inp` file and
writes each value into the correct DOF:

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

Axis `"1"` is x (u) and `"2"` is y (v), as in Abaqus `.inp` files. A definition can name a
single node or a node set.

If there are no loads, FEsolver treats the model as displacement-driven and sets
`self.homogeneous_model` to `False`.

> Known limitation: a model cannot currently be both force-driven and displacement-driven.
> If a model has both, FEsolver ignores the prescribed displacements with no warning. See
> items 4, 23 and 24 in [todo.md](todo.md).

---

## 6. Reducing the system

The full system `[K]{u} = {F}` includes both known (constrained) and unknown (free) DOFs.
Each DOF has either a known displacement or a known force, not both. At a free DOF, the
displacement is unknown and the force is known. At a constrained DOF, the displacement is
known and the force, the reaction, is unknown. So the full system cannot be solved as
written.

Without boundary conditions, `[K]` is also singular. Nothing stops rigid body motion, so
there is no unique solution. Constraining enough DOFs removes this.

FEsolver finds the free DOFs with a boolean mask:

```python
mask = self.model["active_mask"]  # True = free, False = constrained
```

It then takes the free rows and columns of `[K]` and the free entries of `{F}`:

```python
self.global_stiffness_matrix_reduced = global_stiffness_matrix[np.ix_(mask, mask)]
forces_reduced = forces[mask]
```

### Displacement-driven reduction

In a displacement-driven model, `{F}` is not given directly. The solver calculates
equivalent forces from the prescribed displacements:

```python
displacements = np.where(displacements == "*", 0.0, displacements).astype(np.float64)
forces = np.dot(stiffness_matrix, displacements)
```

It then takes the free DOFs and solves as normal.

---

## 7. Solving for displacements

The reduced system is:

```
[K_ff]{u_f} = {F_f}
```

This is a set of simultaneous equations, with up to thousands of unknowns. FEsolver has 2
methods. Choose one with `fe_solver` in `config_user.json`.

### Method 1: Gaussian elimination (`fe_solver = True`)

`direct_solver.py` solves the system in 2 phases: forward elimination, then back
substitution.

#### Forward elimination

Forward elimination turns the system into upper triangular form, one column at a time.
For each column, it subtracts a multiple of the current row from every row below it. This
makes the entries below the diagonal zero:

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

Elimination divides by the diagonal entry. If that entry is zero, the division fails. If
it is very small, it amplifies rounding errors. Partial pivoting swaps the current row with
the row below that has the largest absolute value in that column:

```python
def partial_pivot(self, i):
    max_row = np.argmax(np.abs(self.stiffness[i:, i])) + i
    if max_row != i:
        self.stiffness[[i, max_row]] = self.stiffness[[max_row, i]]
        self.force[[i, max_row]] = self.force[[max_row, i]]
```

Reordering the equations does not change the solution.

#### Back substitution

Back substitution solves from the bottom up. The last equation has one unknown. Each
equation above it has one more, which is found from the values already calculated:

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

This uses LU decomposition, which is faster and more numerically stable for large
systems. It works in the same way: factorise, then back-substitute. It is given the
reduced matrix, because the full `[K]` is singular.

### Reassembling the full vector

FEsolver writes the calculated displacements back into the full displacement vector at the
free DOFs. Constrained DOFs keep their prescribed values. In a displacement-driven model,
FEsolver applies a sign correction, because it calculated the force vector as `[K]{u_c}`:

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

Once the displacements are known, FEsolver calculates the stresses in each element in 3
stages.

### In-plane stresses

For each element, FEsolver takes the 6 nodal displacements and calculates the stresses
using `[B]` and `[D]`:

```python
for node in node_list:
    for disp in ["u", "v"]:
        u[count] = self.displacements[f"{node}{disp}"]

normal_stress = np.matmul(np.matmul(D, B), u)
```

This gives 3 components for each element:

- σxx, normal stress in x, where positive is tension and negative is compression
- σyy, normal stress in y
- τxy, shear stress

All 3 are uniform within the element, because the strain is constant.

### Principal stresses

σxx, σyy and τxy depend on the coordinate system. Principal stresses do not. They are the
maximum and minimum normal stresses at any orientation, and act at the angle where the
shear stress is zero.

The solver calculates σ₁, σ₂ and the principal angle θ, then splits them into x and y
components for plotting.

The principal angle calculation divides by `σxx - σyy`, which is zero under equal biaxial
stress. The solver uses `atan2` to handle this:

```python
angle = -0.5 * m.atan2(2 * Sxy, Sx - Sy)
opp = m.sin(angle) * s1
adj = m.cos(angle) * s1
```

> The maths:
> ```
> σ₁,₂ = (σxx + σyy)/2 ± √(((σxx - σyy)/2)² + τxy²)
> θ = ½ arctan(2τxy / (σxx - σyy))
> ```

> Known limitation: the code above does not match this formula yet. It uses `-0.5` instead
> of `0.5`, which mirrors the angle about the x-axis whenever τxy is not zero. It also
> swaps sin and cos when it builds the plot vector, so the principal stress vector plot is
> 90° out. The magnitudes `s_max`, `s_min` and `s_shear` are correct. See item 26 in
> [todo.md](todo.md).

### Von Mises stress

Von Mises stress combines the full stress state into one number, for checking against
yield. Yielding starts when σ_vm reaches the material's yield strength. It is the standard
check for ductile materials.

```python
mises = m.sqrt(sigma_1**2 - sigma_1 * sigma_2 + sigma_2**2 + 3 * sigma_12**2)
```

The formula uses all 3 in-plane components, including shear, so no coordinate
transformation is needed.

> The maths:
> ```
> σ_vm = √(σxx² - σxx·σyy + σyy² + 3τxy²)
> ```

### Stress accuracy

Stress is constant within each S3 element, so it jumps at element boundaries. Adjacent
elements report different stresses at their shared edge.

The size of these jumps is a rough measure of mesh convergence. Small jumps suggest the
mesh is fine enough. Large jumps, especially near geometric features, suggest it needs
refining.

FEsolver reports the raw element values, without nodal averaging.

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

Each row matches a function in `solver.py`. [worked_example.md](worked_example.md) works
through a numerical example.
