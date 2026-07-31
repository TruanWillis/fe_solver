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

```
[K]{u} = {F}
```

Where:
- `[K]` is the **global stiffness matrix** — encodes how stiff the entire structure is
- `{u}` is the **displacement vector** — the unknown nodal displacements we are solving for
- `{F}` is the **force vector** — the applied nodal loads

Everything the solver does is either building `[K]` and `{F}`, or solving for `{u}`.

### The governing equations

The sentence above skips over *why* the problem is hard. It is worth being precise about
what the underlying equations actually are, because every later step in the solver is a
consequence of them.

A loaded solid must satisfy three conditions at **every point** inside it.

**1. Equilibrium.** The internal stresses must balance any applied body force. In 2D
this is two coupled equations:

```
∂σxx/∂x + ∂τxy/∂y + b_x = 0

∂τxy/∂x + ∂σyy/∂y + b_y = 0
```

These say that if stress varies from one side of an infinitesimal block to the other, the
imbalance must be carried by a body force b — otherwise the block would accelerate.

**2. Compatibility (strain–displacement).** Strain is defined as the spatial derivative
of displacement. For small strains:

```
εxx = ∂u/∂x

εyy = ∂v/∂y

γxy = ∂u/∂y + ∂v/∂x
```

**3. Constitution (stress–strain).** The material links the two, through E and ν:

```
{σ} = [D]{ε}
```

Substituting 3 into 1, and then 2 into that, eliminates stress and strain and leaves two
coupled second-order **partial differential equations** in the displacements `u(x,y)` and
`v(x,y)` alone. These are the Navier–Cauchy equations. They are *partial* differential
equations because the unknowns are functions of more than one variable (x and y), so
the derivatives are taken with respect to each direction separately.

### Why the PDEs cannot be solved directly

Written this way the problem looks complete — two equations, two unknown functions. The
difficulty is not the equations themselves but what is being asked of them:

- The solution is a **function**, not a set of numbers. `u(x,y)` must be known everywhere,
  and it must satisfy the equations at every one of infinitely many points.
- The **boundary conditions follow the geometry**. A closed-form solution has to satisfy
  the equations on the interior *and* match prescribed displacements or tractions along a
  boundary that may be an arbitrary shape — a fillet, a hole, a weld toe.

Closed-form solutions exist only for a handful of idealised cases: a uniform bar, a
circular hole in an infinite plate, a thin beam under simple loading. These are the
textbook formulae engineers already know, and they are useful precisely because they are
the rare cases where the PDEs happen to be tractable. For a real bracket they are not.

This is the **strong form** of the problem: satisfy the differential equations exactly, at
every point.

### From PDE to matrix equation: the weak form

FEA takes a different route. Rather than demanding the equations hold exactly at every
point, it demands that they hold *on average*, weighted across the structure. Multiplying
the equilibrium equations by an arbitrary virtual displacement δu and integrating
over the volume gives the **weak form** — equivalent to the principle of virtual work:

```
∫ᵥ {δε}ᵀ {σ} dV = ∫ᵥ {δu}ᵀ {b} dV + ∫ₛ {δu}ᵀ {t} dS
```

In words: for any small virtual displacement, the internal work done by the stresses
equals the external work done by the applied loads.

Two things are gained. First, the integration by parts used to reach this form moves one
derivative off the stress term and onto the virtual displacement — so the solution now
only needs to be differentiable **once**, not twice. That is a genuinely weaker
requirement, and it is what admits the simple piecewise-linear approximations used inside
elements. Second, an integral over the structure can be split into a sum of integrals over
small pieces — which is precisely what a mesh is.

Approximating the displacement inside each element as `{u} ≈ [N]{uᵉ}` using
shape functions (Section 2), so that `{ε} = [B]{uᵉ}`, and substituting into the
weak form gives, for one element:

```
( ∫ᵥ [B]ᵀ [D] [B] dV ) {uᵉ} = {fᵉ}
```

The bracketed integral is the element stiffness matrix. The unknown is no longer a
function — it is a finite list of nodal displacement values. **The PDE has become
algebra.**

### Where this lands in the code

For the S3 element `[B]` and `[D]` are constant throughout the element, so the integral
collapses to a multiplication by the volume `A · t`:

```
[Kᵉ] = ∫ᵥ [B]ᵀ [D] [B] dV = [B]ᵀ [D] [B] · A · t
```

which is exactly the line implemented in `elements.py`:

```python
element_stiffness = np.matmul(Bt, np.matmul(self.D, self.B)) * self.area * self.t
```

Every step that follows — assembling elements into a global system, applying boundary
conditions, solving, recovering stresses — is bookkeeping on top of that one
transformation from differential equation to matrix equation. Sections 2 to 8 follow it
through in order, and [worked_example.md](worked_example.md) works a two-element model by
hand from the `.inp` file to the final stresses.

### Force-driven vs displacement-driven models

fe_solver supports two loading types, which affects how the system is set up:

**Force-driven (homogeneous):** External forces are applied at nodes. `{F}` is populated
directly from the load definitions in the `.inp` file and the system is solved for `{u}`.

**Displacement-driven (non-homogeneous):** Known displacements are prescribed at nodes
instead of forces. In this case `{F}` is not known directly — it must be computed from
the prescribed displacements using `{F} = [K]{u_c}` before the system can be solved
for the remaining free displacements. This is handled in `reduce_matrix()`.

---

## 2. The S3 Triangular Element

fe_solver uses the **S3 linear triangular element** — the simplest 2D solid element
available. Each element is defined by three nodes, and each node has two
**degrees of freedom (DOFs)**: displacement in the x direction (u) and displacement
in the y direction (v).

```
        k (x_k, y_k)
       / \
      /   \
     /     \
    i-------j
(x_i,y_i) (x_j,y_j)
```

Each element therefore has `3 × 2 = 6` DOFs total:
`{u_i, v_i, u_j, v_j, u_k, v_k}`

In the solver, DOFs are labelled using node number and direction — for example node 3 has
DOFs `3u` and `3v`. For a mesh with n nodes the full displacement vector has 2n entries,
built in the solver as:

```python
self.node_headings = [
    f"{n}{dof}" for n in range(1, node_count + 1) for dof in ["u", "v"]
]
```

### Shape Functions

The displacement at any point inside the element is interpolated from the nodal
displacements using **shape functions** `N_i`, `N_j`, `N_k`. For the S3 element these
are linear — they vary linearly across the element and satisfy:

- `N_i = 1` at node i, and 0 at nodes j and k
- `N_j = 1` at node j, and 0 at nodes i and k
- `N_k = 1` at node k, and 0 at nodes i and j

This means displacement varies linearly across each element, which is why S3 is called a
**constant strain element** — because strain is the derivative of displacement, and the
derivative of a linear function is constant. Stress is therefore also uniform within each
element. This is an approximation: a finer mesh gives a more accurate result, particularly
near stress concentrations.

---

## 3. The Element Stiffness Matrix

### Why do we need it?

The stiffness matrix for an element relates the forces at its nodes to the displacements
at its nodes — the same way a spring's stiffness k relates force to displacement via
`F = ku`. For a 6-DOF element this relationship becomes a `6 × 6` matrix `[Kᵉ]`.
Each entry `Kᵉ_ij` represents the force at DOF i required to produce a unit
displacement at DOF j while all other DOFs are held fixed.

In fe_solver, element stiffness matrices are computed in `elements.py` and stored on the
model in `define_element_stiffness()`:

```python
cst = elements.Element(
    element_data["type"],
    x_cord,
    y_cord,
    node_list,
    self.model["elasticity"][0],  # Young's modulus E
    self.model["elasticity"][1],  # Poisson's ratio v
    self.model["section"]["thickness"],
)

self.model["elements"][element_number]["K"] = cst
```

### The strain-displacement matrix `[B]`

Strain is the spatial derivative of displacement. The `[B]` matrix captures this
relationship — it maps nodal displacements `{u}` to strains `{ε}`:

```
{ε} = [B]{u}
```

For plane stress there are three strain components —
`{ε} = {εxx, εyy, γxy}` — representing normal
strain in x, normal strain in y, and shear strain. The `[B]` matrix is `3 × 6`:

```
[B] =
∂N_i/∂x             0   ∂N_j/∂x             0   ∂N_k/∂x             0
          0   ∂N_i/∂y             0   ∂N_j/∂y             0   ∂N_k/∂y
∂N_i/∂y   ∂N_i/∂x   ∂N_j/∂y   ∂N_j/∂x   ∂N_k/∂y   ∂N_k/∂x
```

Because the S3 shape functions are linear, their derivatives are constant — so `[B]` is
the same at every point in the element. This is what makes S3 a constant strain element
and simplifies the stiffness calculation significantly.

### The material stiffness matrix `[D]`

The `[D]` matrix relates stress to strain through the material's elastic properties —
Young's modulus E and Poisson's ratio ν. For plane stress:

```
[D] = E/(1-ν²)
1   ν         0
ν   1         0
0   0   (1-ν)/2
```

The **plane stress assumption** (`σzz = 0`) is valid for thin plates where the
thickness is small compared to the in-plane dimensions. It simplifies the full 3D
stress-strain relationship into a 2D one.

Poisson's ratio ν captures the coupling between normal strains — a material stretched
in x will contract in y. The off-diagonal terms in `[D]` encode this coupling. A
material with `ν = 0` would have no coupling between axes.

### Computing `[Kᵉ]`

With `[B]` and `[D]` defined, the element stiffness matrix is:

```
[Kᵉ] = t · A · [B]ᵀ [D] [B]
```

Where t is the element thickness and A is the element area.

This formula comes from the **principle of virtual work**: `[Kᵉ]` is derived by
integrating the internal strain energy over the element volume. For S3 the integral
reduces to a simple multiplication because `[B]` is constant throughout the element and
the thickness and area are uniform. The result is a `6 × 6` symmetric matrix.

---

## 4. Assembling the Global Stiffness Matrix

### Why assemble?

Each `[Kᵉ]` only describes the stiffness of one isolated element with no knowledge of
its neighbours. The global stiffness matrix `[K]` assembles all elements into a single
system that describes the stiffness of the entire structure. Crucially, nodes shared
between elements receive contributions from all elements they belong to — this is what
enforces **compatibility**, ensuring the mesh deforms as a connected whole.

### The process

For a mesh with n nodes, `[K]` is a `2n × 2n` matrix initialised to zero. Each
element's `[Kᵉ]` is added into `[K]` at the rows and columns that correspond to that
element's DOFs:

```
[K] = ∑ [Kᵉ]
```

In fe_solver, the global stiffness matrix is a pandas DataFrame with DOF labels as both
row and column indices, making the mapping from element DOFs to global positions explicit:

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
vector `{u}` is initialised with `"*"` for all unknown DOFs. Boundary conditions replace
the `"*"` with known values — typically `0.0` for fixed supports, or a prescribed
non-zero displacement for driven models. Applied forces populate the force vector `{F}`.

### Boundary conditions and loads (`define_boundary_conditions`)

Both boundary conditions and loads are applied by the same helper,
`assemble_dof_series()`, which walks the definitions parsed from the `.inp` file and
writes each value into the matching DOF of the target series — `self.displacements` for
boundary conditions, `self.forces` for loads:

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

Axis `"1"` maps to the u (x-direction) DOF and axis `"2"` maps to the v (y-direction)
DOF, matching the Abaqus convention used in the `.inp` format. A definition may name
either a single node or a node set, which is why the lookup checks `nodesets` first.

If no loads are defined in the `.inp` file, the model is treated as displacement-driven
and `self.homogeneous_model` is set to `False`. This flag controls how the force vector
is computed during matrix reduction.

> **Known limitation.** Treating "has a load" and "has a prescribed displacement" as
> mutually exclusive means a model with *both* silently ignores its prescribed
> displacements. See items 4, 23 and 24 in [TODO.md](TODO.md) — this section will be
> rewritten around static condensation when that lands.

---

## 6. Reducing the System

### Why reduce?

The full system `[K]{u} = {F}` includes both known and unknown DOFs. Constrained DOFs
do not need to be solved — including them would make the system overdetermined. More
importantly, without boundary conditions `[K]` is **singular**: the structure is free to
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
of `[K]` and the entries of `{F}` corresponding to free DOFs only:

```python
self.global_stiffness_matrix_reduced = global_stiffness_matrix[np.ix_(mask, mask)]
forces_reduced = forces[mask]
```

`np.ix_(mask, mask)` constructs an open mesh index that selects only the free DOF rows
and columns simultaneously, producing the reduced matrix `[K_ff]`.

### Reduction for displacement-driven models

For displacement-driven models the force vector is not known directly. Instead it is
computed from the prescribed displacements:

```
{F} = [K]{u_c}
```

Where `{u_c}` is the full displacement vector with `"*"` entries replaced by `0.0`:

```python
displacements = np.where(displacements == "*", 0.0, displacements).astype(
    np.float64
)
forces = np.dot(stiffness_matrix, displacements)
```

This gives the equivalent nodal forces that would produce the prescribed displacements.
The free DOFs are then extracted and solved for as normal.

### The reduced system

After reduction, the system to be solved is:

```
[K_ff]{u_f} = {F_f}
```

Where `[K_ff]` is the submatrix of `[K]` corresponding only to the free DOFs, and
`{F_f}` is the corresponding reduced force vector. This system is smaller, square,
and non-singular — ready to solve.

---

## 7. Solving for Displacements

The reduced system `[K_ff]{u_f} = {F_f}` is a standard linear system `Ax = b`.
fe_solver provides two methods to solve it, selectable via `fe_solver = True/False` in
`config_user.json`.

### Method 1: Gaussian Elimination (fe_solver = True)

fe_solver's own solver in `direct_solver.py` implements **Gaussian elimination** — a
classical algorithm that reduces the system to upper triangular form and then
back-substitutes to find the solution. It operates in two phases.

#### Forward elimination

The goal is to transform `[K_ff]` into an upper triangular matrix by systematically
eliminating the entries below the diagonal. Working column by column from left to right,
for each pivot row i:

1. Apply a **partial pivot** (see below), then identify the **pivot** — the diagonal
   entry `K_ii`
2. For each row j below the pivot, compute the elimination factor:

```
factor = K_ji/K_ii
```

3. Subtract `factor` `×` row i from row j to zero out `K_ji`:

```
Row_j <- Row_j - factor × Row_i
```

4. Apply the same operation to the force vector to keep the system consistent:

```
F_j <- F_j - factor × F_i
```

In code:

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

After forward elimination, the system looks like:

```
┌                  ┐ ┌    ┐   ┌      ┐
│ K₁₁   K₁₂   K₁₃  │ │ u₁ │   │  F₁  │
│  0   K'₂₂  K'₂₃  │ │ u₂ │ = │ F'₂  │
│  0     0   K''₃₃ │ │ u₃ │   │ F''₃ │
└                  ┘ └    ┘   └      ┘
```

#### Partial pivoting

The elimination factor divides by the pivot `K_ii`. If that diagonal entry is zero the
division fails outright, and if it is merely very small the factor becomes large and
amplifies rounding error through every subsequent row — a system that is perfectly
solvable in exact arithmetic can return nonsense in floating point.

**Partial pivoting** avoids this by swapping row i with whichever row below it has the
largest absolute value in column i, so the division is always by the largest available
number. The force vector is swapped alongside the stiffness matrix to keep the system
consistent:

```python
def partial_pivot(self, i):
    max_row = np.argmax(np.abs(self.stiffness[i:, i])) + i
    if max_row != i:
        self.stiffness[[i, max_row]] = self.stiffness[[max_row, i]]
        self.force[[i, max_row]] = self.force[[max_row, i]]
```

Row swapping does not change the solution — it only reorders the equations, which the
system is indifferent to.

#### Back substitution

With the upper triangular system established, displacements are solved from the bottom
up. The last equation has only one unknown and can be solved directly. Each subsequent
equation upward has one more unknown, which is resolved using the already-computed
displacements below it:

```
u_i = (F_i - ∑(j>i) K_ij u_j)/K_ii
```

In code:

```python
def back_subtract(self):
    self.displacements = np.zeros(len(self.force))
    for i in range(len(self.force) - 1, -1, -1):
        sum_knowns = np.dot(self.stiffness[i, i + 1:], self.displacements[i + 1:])
        self.displacements[i] = (self.force[i] - sum_knowns) / self.stiffness[i, i]
```

The loop runs from the last row to the first. At each step, all displacements to the
right of `u_i` are already known, so `np.dot` computes their contribution in a single
vectorised operation.

### Method 2: NumPy direct solve (fe_solver = False)

The fallback solver uses `numpy.linalg.solve`:

```python
displacement_solution = np.linalg.solve(
    self.global_stiffness_matrix_reduced, self.forces_reduced
)
```

Note that it is the **reduced** matrix and force vector that are passed. The full
`[K]` is singular, as explained in Section 6, and cannot be solved by either method.

`numpy.linalg.solve` uses **LU decomposition** internally — a more numerically robust
and computationally efficient approach for large systems. LU decomposition factors
`[K_ff]` into a lower triangular matrix `[L]` and an upper triangular matrix `[U]`,
then solves the two resulting triangular systems. It applies partial pivoting
automatically, for the same reasons set out above.

Directly inverting `[K_ff]` with `numpy.linalg.inv` is avoided — while mathematically
equivalent, explicit inversion is slower and accumulates more floating point error than
solving the system directly.

### Assembling the full displacement vector

After solving, the computed free displacements `{u_f}` are written back into the full
displacement vector at the positions corresponding to free DOFs. The constrained DOFs
retain their prescribed values. For displacement-driven models a sign correction of -1
is applied, since the force vector was computed as `[K]{u_c}` and the solved
displacements represent the response to that loading:

```python
def apply_sign_correction(self, displacements):
    if self.homogeneous_model:
        return displacements
    return displacements * -1
```

The corrected values are then written back into the full displacement vector:

```python
displacements_corrected = self.apply_sign_correction(displacement_solution)
displacements = pd.Series(displacements_corrected, index=self.index_reduced)

for index, displacement in displacements.items():
    self.displacements.at[index] = displacement
```

---

## 8. Computing Element Stresses

With the full displacement vector `{u}` known, stresses are recovered for each element
in three stages: in-plane stresses, principal stresses, and von Mises stress.

### In-plane stresses (`compute_normal_stress`)

For each element, the six nodal displacements `{uᵉ}` are extracted from the global
displacement vector:

```python
for node in node_list:
    for disp in ["u", "v"]:
        u[count] = self.displacements[f"{node}{disp}"]
```

The in-plane stresses are then computed directly:

```
{σ} = [D][B]{uᵉ}
```

Which in code is:

```python
normal_stress = np.matmul(np.matmul(D, B), u)
```

This gives three stress components per element:
- σxx (`s1`) — normal stress in the x direction
- σyy (`s2`) — normal stress in the y direction
- τxy (`s12`) — in-plane shear stress

### Principal stresses (`compute_principal_stress`)

The in-plane stresses depend on the coordinate system chosen. Principal stresses are
the coordinate-independent version — the maximum and minimum normal stresses found by
rotating to the angle where shear stress is zero. They are computed from the in-plane
components:

```
σ₁,₂ = (σxx + σyy)/2 ± √(((σxx - σyy)/2)² + τxy²)
```

The angle of the principal stress plane relative to the x axis is:

```
θ = -½ arctan(2τxy/(σxx - σyy))
```

This angle is used to decompose the principal stress into x and y components for
plotting on the deformed mesh.

Written as a single-argument `arctan` the expression divides by
`σxx - σyy`, which is zero whenever the two normal stresses are equal —
a common state, not an exotic one. The solver uses the two-argument form `atan2`
instead, which takes numerator and denominator separately and so handles that case
natively, with no special-casing required:

```python
angle = -0.5 * m.atan2(2 * Sxy, Sx - Sy)
opp = m.sin(angle) * s1
adj = m.cos(angle) * s1
```

`atan2` also resolves the correct quadrant, which a single-argument `arctan` cannot —
it returns angles only in the range `± 90°` and so loses the sign information needed
to orient the principal stress vectors correctly.

### Von Mises stress (`compute_mises_stress`)

The von Mises stress is a scalar quantity used to predict whether a ductile material will
yield under a complex stress state. A material yields when σvm reaches the
uniaxial yield strength σy.

fe_solver uses the full formulation that includes the shear stress contribution directly:

```
σvm = √(σxx² - σxxσyy + σyy² + 3τxy²)
```

In code:

```python
mises = m.sqrt(sigma_1**2 - sigma_1 * sigma_2 + sigma_2**2 + 3 * sigma_12**2)
```

The `3τxy²` term accounts for shear stress directly without requiring a coordinate
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
| Build `[Kᵉ]` for each element | `define_element_stiffness()` | `[Kᵉ] = t · A · [B]ᵀ[D][B]` |
| Assemble `[K]` | `define_global_stiffness()` | `[K] = ∑ [Kᵉ]` |
| Apply boundary conditions | `define_boundary_conditions()` | Populate `{u_c}` |
| Apply loads | `assemble_dof_series()` | Populate `{F}` |
| Reduce system | `reduce_matrix()` | Extract `[K_ff]` and `{F_f}` using active mask |
| Solve | `compute_displacements()` | `[K_ff]{u_f} = {F_f}` |
| In-plane stress | `compute_normal_stress()` | `{σ} = [D][B]{uᵉ}` |
| Principal stress | `compute_principal_stress()` | `σ_1,2 = \frac{σxx+σyy}{2} ± \sqrt{(\frac{σxx-σyy}{2})² + τxy²}` |
| Von Mises stress | `compute_mises_stress()` | `σvm = \sqrt{σxx² - σxxσyy + σyy² + 3τxy²}` |

The steps form a one-way pipeline: geometry and material properties go in at the top,
displacements and stresses come out at the bottom. Each function in `solver.py` corresponds
directly to one row in this table, making the code a direct implementation of the theory.
