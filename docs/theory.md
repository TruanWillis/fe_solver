# Finite Element Analysis: Theory and Process

This document explains the theoretical basis of the finite element method (FEM) as implemented
in fe_solver. It is written for readers who are new to FEA and want to understand not just
what the solver does at each step, but why each step exists, how they connect, and how the
code implements them.

Where relevant, the implementation in `solver.py` and `direct_solver.py` is referenced
directly so the theory can be read alongside the code.

---

## Table of Contents

1. [What Problem Does FEA Solve?](#1-what-problem-does-fea-solve)
2. [The S3 Triangular Element](#2-the-s3-triangular-element)
3. [The Element Stiffness Matrix](#3-the-element-stiffness-matrix)
4. [Assembling the Global Stiffness Matrix](#4-assembling-the-global-stiffness-matrix)
5. [Applying Boundary Conditions and Loads](#5-applying-boundary-conditions-and-loads)
6. [Reducing the System](#6-reducing-the-system)
7. [Solving for Displacements](#7-solving-for-displacements)
8. [Computing Element Stresses](#8-computing-element-stresses)
9. [Summary](#9-summary)

---

## 1. What Problem Does FEA Solve?

When a structure is loaded — a plate pulled at one end, a bracket bolted to a wall — every
point in that structure moves and deforms. The governing equations for this behaviour come
from elasticity theory, but they are partial differential equations that have no closed-form
solution for anything other than the simplest shapes.

FEA sidesteps this by replacing the continuous structure with a mesh of small, simple shapes
called **elements**. Within each element, the displacement field is approximated by a simple
polynomial. This turns an unsolvable continuous problem into a large but solvable system of
linear equations:

$$[K]\{u\} = \{F\}$$

Where:
- $[K]$ is the **global stiffness matrix** — encodes how stiff the entire structure is
- $\{u\}$ is the **displacement vector** — the unknown nodal displacements we are solving for
- $\{F\}$ is the **force vector** — the applied nodal loads

Everything the solver does is either building $[K]$ and $\{F\}$, or solving for $\{u\}$.

### Force-driven vs displacement-driven models

fe_solver supports two loading types, which affects how the system is set up:

**Force-driven (homogeneous):** External forces are applied at nodes. $\{F\}$ is populated
directly from the load definitions in the `.inp` file and the system is solved for $\{u\}$.

**Displacement-driven (non-homogeneous):** Known displacements are prescribed at nodes
instead of forces. In this case $\{F\}$ is not known directly — it must be computed from
the prescribed displacements using $\{F\} = [K]\{u_c\}$ before the system can be solved
for the remaining free displacements. This is handled in `reduce_matrix_new()`.

---

## 2. The S3 Triangular Element

fe_solver uses the **S3 linear triangular element** — the simplest 2D solid element
available. Each element is defined by three nodes, and each node has two
**degrees of freedom (DOFs)**: displacement in the $x$ direction ($u$) and displacement
in the $y$ direction ($v$).

```
        k (x_k, y_k)
       / \
      /   \
     /     \
    i-------j
(x_i,y_i) (x_j,y_j)
```

Each element therefore has $3 \times 2 = 6$ DOFs total:
$\{u_i, v_i, u_j, v_j, u_k, v_k\}$

In the solver, DOFs are labelled using node number and direction — for example node 3 has
DOFs `3u` and `3v`. For a mesh with $n$ nodes the full displacement vector has $2n$ entries,
built in the solver as:

```python
for n in range(1, node_count + 1):
    for displacement in ["u", "v"]:
        self.node_headings.append(str(n) + displacement)
```

### Shape Functions

The displacement at any point inside the element is interpolated from the nodal
displacements using **shape functions** $N_i$, $N_j$, $N_k$. For the S3 element these
are linear — they vary linearly across the element and satisfy:

- $N_i = 1$ at node $i$, and $0$ at nodes $j$ and $k$
- $N_j = 1$ at node $j$, and $0$ at nodes $i$ and $k$
- $N_k = 1$ at node $k$, and $0$ at nodes $i$ and $j$

This means displacement varies linearly across each element, which is why S3 is called a
**constant strain element** — because strain is the derivative of displacement, and the
derivative of a linear function is constant. Stress is therefore also uniform within each
element. This is an approximation: a finer mesh gives a more accurate result, particularly
near stress concentrations.

---

## 3. The Element Stiffness Matrix

### Why do we need it?

The stiffness matrix for an element relates the forces at its nodes to the displacements
at its nodes — the same way a spring's stiffness $k$ relates force to displacement via
$F = ku$. For a 6-DOF element this relationship becomes a $6 \times 6$ matrix $[K^e]$.
Each entry $K^e_{ij}$ represents the force at DOF $i$ required to produce a unit
displacement at DOF $j$ while all other DOFs are held fixed.

In fe_solver, element stiffness matrices are computed in `elements.py` and stored on the
model in `define_element_stiffness()`:

```python
cst = elements.element(
    element_type, x_cord, y_cord, node_list,
    self.model["elasticity"][0],   # Young's modulus E
    self.model["elasticity"][1],   # Poisson's ratio ν
    self.model["section"]["thickness"],
)
self.model["elements"][element]["K"] = cst
```

### The strain-displacement matrix $[B]$

Strain is the spatial derivative of displacement. The $[B]$ matrix captures this
relationship — it maps nodal displacements $\{u\}$ to strains $\{\epsilon\}$:

$$\{\epsilon\} = [B]\{u\}$$

For plane stress there are three strain components —
$\{\epsilon\} = \{\epsilon_{xx},\ \epsilon_{yy},\ \gamma_{xy}\}$ — representing normal
strain in $x$, normal strain in $y$, and shear strain. The $[B]$ matrix is $3 \times 6$:

$$[B] = \begin{bmatrix}
\frac{\partial N_i}{\partial x} & 0 & \frac{\partial N_j}{\partial x} & 0 & \frac{\partial N_k}{\partial x} & 0 \\
0 & \frac{\partial N_i}{\partial y} & 0 & \frac{\partial N_j}{\partial y} & 0 & \frac{\partial N_k}{\partial y} \\
\frac{\partial N_i}{\partial y} & \frac{\partial N_i}{\partial x} & \frac{\partial N_j}{\partial y} & \frac{\partial N_j}{\partial x} & \frac{\partial N_k}{\partial y} & \frac{\partial N_k}{\partial x}
\end{bmatrix}$$

Because the S3 shape functions are linear, their derivatives are constant — so $[B]$ is
the same at every point in the element. This is what makes S3 a constant strain element
and simplifies the stiffness calculation significantly.

### The material stiffness matrix $[D]$

The $[D]$ matrix relates stress to strain through the material's elastic properties —
Young's modulus $E$ and Poisson's ratio $\nu$. For plane stress:

$$[D] = \frac{E}{1-\nu^2} \begin{bmatrix}
1 & \nu & 0 \\
\nu & 1 & 0 \\
0 & 0 & \frac{1-\nu}{2}
\end{bmatrix}$$

The **plane stress assumption** ($\sigma_{zz} = 0$) is valid for thin plates where the
thickness is small compared to the in-plane dimensions. It simplifies the full 3D
stress-strain relationship into a 2D one.

Poisson's ratio $\nu$ captures the coupling between normal strains — a material stretched
in $x$ will contract in $y$. The off-diagonal terms in $[D]$ encode this coupling. A
material with $\nu = 0$ would have no coupling between axes.

### Computing $[K^e]$

With $[B]$ and $[D]$ defined, the element stiffness matrix is:

$$[K^e] = t \cdot A \cdot [B]^T [D] [B]$$

Where $t$ is the element thickness and $A$ is the element area.

This formula comes from the **principle of virtual work**: $[K^e]$ is derived by
integrating the internal strain energy over the element volume. For S3 the integral
reduces to a simple multiplication because $[B]$ is constant throughout the element and
the thickness and area are uniform. The result is a $6 \times 6$ symmetric matrix.

---

## 4. Assembling the Global Stiffness Matrix

### Why assemble?

Each $[K^e]$ only describes the stiffness of one isolated element with no knowledge of
its neighbours. The global stiffness matrix $[K]$ assembles all elements into a single
system that describes the stiffness of the entire structure. Crucially, nodes shared
between elements receive contributions from all elements they belong to — this is what
enforces **compatibility**, ensuring the mesh deforms as a connected whole.

### The process

For a mesh with $n$ nodes, $[K]$ is a $2n \times 2n$ matrix initialised to zero. Each
element's $[K^e]$ is added into $[K]$ at the rows and columns that correspond to that
element's DOFs:

$$[K] = \sum_{e=1}^{n_{elem}} [K^e]$$

In fe_solver, the global stiffness matrix is a pandas DataFrame with DOF labels as both
row and column indices, making the mapping from element DOFs to global positions explicit:

```python
self.global_stiffness_matrix = pd.DataFrame(
    np.zeros((self.dof, self.dof)),
    columns=self.node_headings,
    index=self.node_headings,
)

for e in self.model["elements"]:
    element_stiffness_matrix = self.model["elements"][e]["K"].element_stiffness_matrix
    for column in element_stiffness_matrix:
        for index, row in element_stiffness_matrix.iterrows():
            value = self.global_stiffness_matrix._get_value(index, column) \
                  + element_stiffness_matrix._get_value(index, column)
            self.global_stiffness_matrix._set_value(index, column, value)
```

The element stiffness matrix already carries DOF labels (`1u`, `1v`, `2u`, etc.) matching
the global matrix — this means the assembly is a direct label-to-label addition with no
index mapping required.

### The stiffness matrix heatmap

When `save_matrix = True`, fe_solver also builds a second version of the global stiffness
matrix that records which elements contribute to each position. This produces the heatmap
visible in the GUI — a visual representation of the mesh connectivity. Dense diagonal
blocks indicate nodes with many element connections; off-diagonal entries indicate shared
nodes between elements.

---

## 5. Applying Boundary Conditions and Loads

Before the system can be solved, the known quantities must be populated. The displacement
vector $\{u\}$ is initialised with `"*"` for all unknown DOFs. Boundary conditions replace
the `"*"` with known values — typically `0.0` for fixed supports, or a prescribed
non-zero displacement for driven models. Applied forces populate the force vector $\{F\}$.

### Boundary conditions (`define_boundary`)

For each boundary condition defined in the `.inp` file, the corresponding DOFs in the
displacement vector are set to their prescribed values:

```python
self.displacements._set_value(str(n) + disp, self.model["boundary"][boundary][axis])
```

Axis `"1"` maps to the $u$ (x-direction) DOF and axis `"2"` maps to the $v$ (y-direction)
DOF, matching the Abaqus convention used in the `.inp` format.

### Loads (`define_load`)

Applied concentrated forces at nodes populate the force vector in the same way:

```python
self.forces._set_value(str(n) + disp, self.model["load"][load][axis])
```

If no loads are defined in the `.inp` file, the model is treated as displacement-driven
and `self.homogeneous_model` is set to `False`. This flag controls how the force vector
is computed during matrix reduction.

---

## 6. Reducing the System

### Why reduce?

The full system $[K]\{u\} = \{F\}$ includes both known and unknown DOFs. Constrained DOFs
do not need to be solved — including them would make the system overdetermined. More
importantly, without boundary conditions $[K]$ is **singular**: the structure is free to
undergo rigid body motion without any internal deformation, meaning there is no unique
solution. Removing the constrained DOFs eliminates this singularity.

### The active mask

fe_solver identifies which DOFs are free using a boolean mask stored on the model:

```python
mask = self.model["active_mask"]  # True = free DOF, False = constrained DOF
```

This mask is built during model generation and has one entry per DOF. `True` means the
displacement is unknown and must be solved for; `False` means it is prescribed.

### Reduction for force-driven models

For force-driven models the reduction is straightforward — extract the rows and columns
of $[K]$ and the entries of $\{F\}$ corresponding to free DOFs only:

```python
self.global_stiffness_matrix_reduced = global_stiffness_matrix[np.ix_(mask, mask)]
forces_reduced = forces[mask]
```

`np.ix_(mask, mask)` constructs an open mesh index that selects only the free DOF rows
and columns simultaneously, producing the reduced matrix $[K_{ff}]$.

### Reduction for displacement-driven models

For displacement-driven models the force vector is not known directly. Instead it is
computed from the prescribed displacements:

$$\{F\} = [K]\{u_c\}$$

Where $\{u_c\}$ is the full displacement vector with `"*"` entries replaced by `0.0`:

```python
displacements[displacements == "*"] = 0.0
forces = np.dot(global_stiffness_matrix, displacements)
```

This gives the equivalent nodal forces that would produce the prescribed displacements.
The free DOFs are then extracted and solved for as normal.

### The reduced system

After reduction, the system to be solved is:

$$[K_{ff}]\{u_f\} = \{F_f\}$$

Where $[K_{ff}]$ is the submatrix of $[K]$ corresponding only to the free DOFs, and
$\{F_f\}$ is the corresponding reduced force vector. This system is smaller, square,
and non-singular — ready to solve.

---

## 7. Solving for Displacements

The reduced system $[K_{ff}]\{u_f\} = \{F_f\}$ is a standard linear system $Ax = b$.
fe_solver provides two methods to solve it, selectable via `fe_solver = True/False` in
`config_user.json`.

### Method 1: Gaussian Elimination (fe_solver = True)

fe_solver's own solver in `direct_solver.py` implements **Gaussian elimination** — a
classical algorithm that reduces the system to upper triangular form and then
back-substitutes to find the solution. It operates in two phases.

#### Forward elimination

The goal is to transform $[K_{ff}]$ into an upper triangular matrix by systematically
eliminating the entries below the diagonal. Working column by column from left to right,
for each pivot row $i$:

1. Identify the **pivot** — the diagonal entry $K_{ii}$
2. For each row $j$ below the pivot, compute the elimination factor:

$$\text{factor} = \frac{K_{ji}}{K_{ii}}$$

3. Subtract `factor` $\times$ row $i$ from row $j$ to zero out $K_{ji}$:

$$\text{Row}_j \leftarrow \text{Row}_j - \text{factor} \times \text{Row}_i$$

4. Apply the same operation to the force vector to keep the system consistent:

$$F_j \leftarrow F_j - \text{factor} \times F_i$$

In code:

```python
def forward_elimination_new(self):
    for i in range(len(self.force)):
        pivot = self.stiffness[i, i]
        for j in range(i + 1, len(self.force)):
            factor = self.stiffness[j, i] / pivot
            self.stiffness[j, i:] = self.stiffness[j, i:] - factor * self.stiffness[i, i:]
            self.force[j] = self.force[j] - factor * self.force[i]
```

After forward elimination, the system looks like:

$$\begin{bmatrix} K_{11} & K_{12} & K_{13} \\ 0 & K'_{22} & K'_{23} \\ 0 & 0 & K''_{33} \end{bmatrix} \begin{Bmatrix} u_1 \\ u_2 \\ u_3 \end{Bmatrix} = \begin{Bmatrix} F_1 \\ F'_2 \\ F''_3 \end{Bmatrix}$$

Note the `TODO` comment in the code — a **partial pivot** (swapping rows to place the
largest value on the diagonal before each elimination step) would improve numerical
stability for ill-conditioned systems. This is a known limitation of the current
implementation.

#### Back substitution

With the upper triangular system established, displacements are solved from the bottom
up. The last equation has only one unknown and can be solved directly. Each subsequent
equation upward has one more unknown, which is resolved using the already-computed
displacements below it:

$$u_i = \frac{F_i - \sum_{j>i} K_{ij} u_j}{K_{ii}}$$

In code:

```python
def back_subtract_new(self):
    self.displacements = np.zeros(len(self.force))
    for i in range(len(self.force) - 1, -1, -1):
        sum_knowns = np.dot(self.stiffness[i, i + 1:], self.displacements[i + 1:])
        self.displacements[i] = (self.force[i] - sum_knowns) / self.stiffness[i, i]
```

The loop runs from the last row to the first. At each step, all displacements to the
right of $u_i$ are already known, so `np.dot` computes their contribution in a single
vectorised operation.

### Method 2: NumPy direct solve (fe_solver = False)

The fallback solver uses `numpy.linalg.solve`:

```python
displacement_solution = np.linalg.solve(global_stiffness_matrix, forces)
```

`numpy.linalg.solve` uses **LU decomposition** internally — a more numerically robust
and computationally efficient approach for large systems. LU decomposition factors
$[K_{ff}]$ into a lower triangular matrix $[L]$ and an upper triangular matrix $[U]$,
then solves the two resulting triangular systems. Partial pivoting is applied
automatically, which is the stability improvement noted as missing in the custom solver.

Directly inverting $[K_{ff}]$ with `numpy.linalg.inv` is avoided — while mathematically
equivalent, explicit inversion is slower and accumulates more floating point error than
solving the system directly.

### Assembling the full displacement vector

After solving, the computed free displacements $\{u_f\}$ are written back into the full
displacement vector at the positions corresponding to free DOFs. The constrained DOFs
retain their prescribed values. For displacement-driven models a sign correction of $-1$
is applied, since the force vector was computed as $[K]\{u_c\}$ and the solved
displacements represent the response to that loading:

```python
for index, displacement in displacements.items():
    self.displacements._set_value(index, displacement * homogeneous_correction)
```

---

## 8. Computing Element Stresses

With the full displacement vector $\{u\}$ known, stresses are recovered for each element
in three stages: in-plane stresses, principal stresses, and von Mises stress.

### In-plane stresses (`compute_normal_stress`)

For each element, the six nodal displacements $\{u^e\}$ are extracted from the global
displacement vector:

```python
for node in node_list:
    for disp in ["u", "v"]:
        u[count] = self.displacements[str(node) + disp]
```

The in-plane stresses are then computed directly:

$$\{\sigma\} = [D][B]\{u^e\}$$

Which in code is:

```python
normal_stress = np.matmul(np.matmul(D, B), u)
```

This gives three stress components per element:
- $\sigma_{xx}$ (`s1`) — normal stress in the $x$ direction
- $\sigma_{yy}$ (`s2`) — normal stress in the $y$ direction
- $\tau_{xy}$ (`s12`) — in-plane shear stress

### Principal stresses (`compute_principal_stress`)

The in-plane stresses depend on the coordinate system chosen. Principal stresses are
the coordinate-independent version — the maximum and minimum normal stresses found by
rotating to the angle where shear stress is zero. They are computed from the in-plane
components:

$$\sigma_{1,2} = \frac{\sigma_{xx} + \sigma_{yy}}{2} \pm \sqrt{\left(\frac{\sigma_{xx} - \sigma_{yy}}{2}\right)^2 + \tau_{xy}^2}$$

The angle of the principal stress plane relative to the $x$ axis is:

$$\theta = -\frac{1}{2} \arctan\left(\frac{2\tau_{xy}}{\sigma_{xx} - \sigma_{yy}}\right)$$

This angle is used to decompose the principal stress into $x$ and $y$ components for
plotting on the deformed mesh. The special case $\sigma_{xx} = \sigma_{yy}$ is handled
explicitly to avoid division by zero:

```python
if Sx == Sy:
    angle = 0
    opp = 0
    adj = s1
else:
    angle = -0.5 * m.atan((2 * Sxy) / (Sx - Sy))
```

### Von Mises stress (`compute_mises_stress`)

The von Mises stress is a scalar quantity used to predict whether a ductile material will
yield under a complex stress state. A material yields when $\sigma_{vm}$ reaches the
uniaxial yield strength $\sigma_y$.

fe_solver uses the full formulation that includes the shear stress contribution directly:

$$\sigma_{vm} = \sqrt{\sigma_{xx}^2 - \sigma_{xx}\sigma_{yy} + \sigma_{yy}^2 + 3\tau_{xy}^2}$$

In code:

```python
mises = m.sqrt(sigma_1**2 - sigma_1 * sigma_2 + sigma_2**2 + 3 * sigma_12**2)
```

The $3\tau_{xy}^2$ term accounts for shear stress directly without requiring a coordinate
transformation first. This is important because S3 elements can carry significant shear,
particularly near boundaries and load application points.

### A note on stress accuracy

Because S3 is a constant strain element, all stress quantities are uniform within each
element — there is no variation across the element area. This means stress discontinuities
exist at element boundaries, which is physically unrealistic. In practice, stresses are
often averaged at shared nodes or smoothed in post-processing. A finer mesh reduces these
discontinuities and improves accuracy, particularly at stress concentrations.

---

## 9. Summary

| Step | `solver.py` function | Key equation |
|---|---|---|
| Build $[K^e]$ for each element | `define_element_stiffness()` | $[K^e] = t \cdot A \cdot [B]^T[D][B]$ |
| Assemble $[K]$ | `define_global_stiffness()` | $[K] = \sum [K^e]$ |
| Apply boundary conditions | `define_boundary()` | Populate $\{u_c\}$ |
| Apply loads | `define_load()` | Populate $\{F\}$ |
| Reduce system | `reduce_matrix_new()` | Extract $[K_{ff}]$ and $\{F_f\}$ using active mask |
| Solve | `compute_displacements()` | $[K_{ff}]\{u_f\} = \{F_f\}$ |
| In-plane stress | `compute_normal_stress()` | $\{\sigma\} = [D][B]\{u^e\}$ |
| Principal stress | `compute_principal_stress()` | $\sigma_{1,2} = \frac{\sigma_{xx}+\sigma_{yy}}{2} \pm \sqrt{(\frac{\sigma_{xx}-\sigma_{yy}}{2})^2 + \tau_{xy}^2}$ |
| Von Mises stress | `compute_mises_stress()` | $\sigma_{vm} = \sqrt{\sigma_{xx}^2 - \sigma_{xx}\sigma_{yy} + \sigma_{yy}^2 + 3\tau_{xy}^2}$ |

The steps form a one-way pipeline: geometry and material properties go in at the top,
displacements and stresses come out at the bottom. Each function in `solver.py` corresponds
directly to one row in this table, making the code a direct implementation of the theory.
