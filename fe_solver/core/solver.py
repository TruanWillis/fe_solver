import math as m
import pprint
from pathlib import Path

import numpy as np
import pandas as pd
from tabulate import tabulate

from fe_solver.core import direct_solver, elements, model

# import matplotlib.pyplot as plt


class Solver:
    """
    The solver operates in two distinct phases:

    Assembly phase (pandas):
        Element and global stiffness matrices are assembled using
        pandas DataFrames with labelled DOF indices. Label-based
        indexing makes the assembly process explicit and traceable.

    Solve phase (numpy):
        The assembled system is converted to numpy arrays before being solved using
        numpy linear function or FEsolver's implementation of Guassian elimination.
    """

    def __init__(self, model, fe_solver, print_head, save_matrix, out_dir):
        """
        Initialises the solver and run through solution process.

        Args:
            model (dict): Model defined using keywords.
            fe_solver (bool): Uses direct solver/numpy if Ture/False.
            print_head (bool): Prints stress dataFrame head to terminal.
            save_matrix (bool): Saves global stiffness matrix as csv.
            out_dir (Path): Directory for output files.
        """

        self.model = model
        self.fe_solver = fe_solver
        self.save_matrix = save_matrix
        self.out_dir = out_dir / "outputs"
        if self.save_matrix:
            Path(self.out_dir).mkdir(parents=True, exist_ok=True)

        if self.fe_solver:
            print("Direct solver: FEsolver")
        else:
            print("Direct solver: Numpy")

        # Assumes model is loaded with a force by default
        self.homogeneous_model = True

        node_count = len(self.model["nodes"].keys())
        self.dof = node_count * 2

        self.node_headings = [
            f"{n}{dof}" for n in range(1, node_count + 1) for dof in ["u", "v"]
        ]

        self.element_index = [f"e{element}" for element in self.model["elements"]]

        self.forces = pd.Series(np.zeros(self.dof), index=self.node_headings)
        self.displacements = pd.Series(["*"] * self.dof, index=self.node_headings)

        self.run(print_head)

    def run(self, print_head):
        """
        Runs through FEsolver solution process. Pandas is used for assembly, numpy
        arrays used for solution.
        """
        self.define_element_stiffness()
        self.define_global_stiffness()
        self.define_boundary_conditions()
        self.reduce_matrix()
        self.compute_displacements()
        self.compute_normal_stress()
        self.compute_principal_stress()
        self.compute_mises_stress()

        if print_head:
            self.print_results()

    def define_element_stiffness(self):
        """
        Defines element stiffness matrix for all model elements.
        """

        print("Generating element stiffness matricies")

        for element_number, element_data in self.model["elements"].items():
            node_list = element_data["nodes"]
            x_cord = [self.model["nodes"][node][0] for node in node_list]
            y_cord = [self.model["nodes"][node][1] for node in node_list]

            cst = elements.element(
                element_data["type"],
                x_cord,
                y_cord,
                node_list,
                self.model["elasticity"][0],  # Young's modulus E
                self.model["elasticity"][1],  # Poisson's ratio v
                self.model["section"]["thickness"],
            )

            self.model["elements"][element_number]["K"] = cst

    def define_global_stiffness(self):
        """
        Defines global stiffness matrix based on element stiffness matrices.
        """

        print("Generating global stiffness matrix")

        try:
            self.global_stiffness_matrix = pd.DataFrame(
                np.zeros((self.dof, self.dof)),
                columns=self.node_headings,
                index=self.node_headings,
            )

            if self.save_matrix:
                self.global_stiffness_matrix_save = self.global_stiffness_matrix.copy()

            for element_number, element_data in self.model["elements"].items():
                element_stiffness_matrix = element_data["K"].element_stiffness_matrix

                for col in element_stiffness_matrix.columns:
                    for row in element_stiffness_matrix.index:
                        self.global_stiffness_matrix.at[
                            row, col
                        ] += element_stiffness_matrix.at[row, col]

                        if self.save_matrix:
                            existing = self.global_stiffness_matrix_save.at[row, col]
                            label = f"e{element_number}"
                            self.global_stiffness_matrix_save.at[row, col] = (
                                label if existing == 0 else f"{existing}, {label}"
                            )

        except Exception as e:
            print(e)

        print(f"Global stiffness matrix: {self.dof}x{self.dof}")

    def define_boundary_conditions(self):
        """
        Updates displacement and forces dataSeries with known boundary conditions.
        """

        print(self.displacements)
        print(self.forces)

        self.assemble_dof_series(self.displacements, "boundary")

        if self.save_matrix:
            self.displacements.to_csv(self.out_dir / "displacements_matrix.csv")

        if bool(self.model["load"]) is False:
            # Model is displacement driven
            self.homogeneous_model = False
        else:
            self.assemble_dof_series(self.forces, "load")

        print(self.displacements)
        print(self.forces)

    def assemble_dof_series(self, series, condition):
        """
        Iterates through boundary conditions and assigns values to dataSeries.
        """

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

    def reduce_matrix(self):
        """
        Reduces global stiffness matrix by removing nodal DOF where a
        constrained boundary condition is defined.
        """

        print("Reducing global stiffness matix")

        stiffness_matrix = self.global_stiffness_matrix.to_numpy(dtype=np.float64)
        displacements = self.displacements.to_numpy()
        mask = self.model["active_mask"]

        if self.homogeneous_model:
            forces = self.forces.to_numpy(dtype=np.float64)
        else:
            displacements = np.where(
                displacements == "*",  0.0, displacements).astype(np.float64)
            forces = np.dot(stiffness_matrix, displacements)

        self.global_stiffness_matrix_reduced = stiffness_matrix[
            np.ix_(mask, mask)
        ]
        self.forces_reduced = forces[mask]
        self.forces = forces
        self.index_reduced = np.array(self.node_headings)[mask]

        print(f"System reduced from {self.dof} to {len(self.forces_reduced)} free DOFs")

    def compute_displacements(self):
        """
        Calculates nodal displacements as a function of global stiffness matrix
        and applied forces.
        """
        print("Computing displacements")

        if self.fe_solver:
            displacement_solution = direct_solver.GaussianElimination(
                self.global_stiffness_matrix_reduced, self.forces_reduced
            ).displacements

        else:
            displacement_solution = np.linalg.solve(
                self.global_stiffness_matrix_reduced, self.forces_reduced)

        displacements = pd.Series(displacement_solution, index=self.index_reduced)
        displacements_corrected = self.apply_sign_correction(displacements)

        for index, displacement in displacements_corrected.items():
            self.displacements.at[index] = displacement

    def apply_sign_correction(self, displacements):
        """
        Reverse displacement sign for displacement driven models (non-homogeneous).
        """
        if self.homogeneous_model:
            return displacements
        return displacements * -1

    def compute_normal_stress(self):
        """
        Calculates element in-plane stresses.
        """

        print("Computing normal stress")

        elements = self.model["elements"].keys()
        self.stress_normal = pd.DataFrame(
            index=self.element_index, columns=["s1", "s2", "s12"]
        )

        for element in elements:
            node_list = self.model["elements"][element]["nodes"]
            u = np.zeros(len(node_list) * 2)
            count = 0
            for node in node_list:
                for disp in ["u", "v"]:
                    u[count] = self.displacements[f"{node}{disp}"]
                    count += 1

            D = self.model["elements"][element]["K"].D
            B = self.model["elements"][element]["K"].B

            normal_stress = np.matmul(np.matmul(D, B), u)
            self.stress_normal.loc[f"e{element}"] = [
                normal_stress[0],
                normal_stress[1],
                normal_stress[2],
            ]

    def compute_principal_stress(self):
        """
        Calculates element principal stresses.
        """

        print("Computing principal stress")

        self.stress_principal = pd.DataFrame(
            index=self.element_index,
            columns=["s_max", "s_min", "s_shear", "a", "opp", "adj"],
        )

        for index, row in self.stress_normal.iterrows():
            Sx, Sy, Sxy = row[0], row[1], row[2]

            radius = m.sqrt(((Sx - Sy) / 2) ** 2 + Sxy**2)
            centre = (Sx + Sy) / 2

            s1 = centre + radius
            s2 = centre - radius
            s12 = radius

            angle = -0.5 * m.atan2(2 * Sxy, Sx - Sy)
            opp = m.sin(angle) * s1
            adj = m.cos(angle) * s1

            self.stress_principal.loc[index] = [s1, s2, s12, angle, opp, adj]

    def compute_mises_stress(self):
        """
        Calculates element von Mises stress
        """

        print("Computing von Mises stress")

        self.stress_mises = pd.DataFrame(index=self.element_index, columns=["s_mises"])

        for index, row in self.stress_normal.iterrows():
            sigma_1 = row[0]
            sigma_2 = row[1]
            sigma_12 = row[2]

            mises = m.sqrt(
                sigma_1**2 - sigma_1 * sigma_2 + sigma_2**2 + 3 * sigma_12**2
            )
            self.stress_mises.loc[index] = mises

    def print_results(self):
        """
        Prints in-plane, principal and mises stress dataFrame heads to
        terminal.
        """

        print("In-plane stress...")
        print(
            tabulate(
                self.stress_normal.head(),
                tablefmt="grid",
                numalign="right",
                headers=self.stress_normal.columns,
            )
        )
        print("Principal stress...")
        print(
            tabulate(
                self.stress_principal.iloc[:, :3].head(),
                tablefmt="grid",
                numalign="right",
                headers=self.stress_principal.columns[:3],
            )
        )
        print("Mises stress...")
        print(
            tabulate(
                self.stress_mises.head(),
                tablefmt="grid",
                numalign="right",
                headers=self.stress_mises.columns,
            )
        )


if __name__ == "__main__":
    """
    __main__ for development purposes.
    """

    test_model = "test_input_1"

    wk_dir = Path(__file__).resolve().parent.parent.parent
    input = model.load_input(wk_dir / "tests" / "fixtures" / f"{test_model}.inp")
    model = model.call_gen_function(input)
    s = Solver(model, False, True, False, wk_dir)

    pp = pprint.PrettyPrinter(indent=4)
    # pp.pprint(s.__dict__.keys())
    pp.pprint(s.displacements)
    pp.pprint(s.forces)
    pp.pprint(s.stress_normal["s1"]["e8"])

    """
    sm = s.global_stiffness_matrix
    print(sm.head())

    x = np.repeat(np.arange(0.5, s.dof + 0.5, 1), s.dof)
    y = np.arange(0.5, s.dof + 0.5, 1)
    y = np.tile(y, s.dof)

    v = []
    max_value = sm.max()
    max_value = max_value.max()
    for index, row in sm.iterrows():
        v_row = [abs(i)/max_value for i in list(row)]
        v.extend(v_row)

    marker_size = 3600 / s.dof

    fig, ax = plt.subplots()
    print(fig, ax)
    ax.scatter(x, y, marker='s', alpha=v, s=marker_size)

    if s.dof < 300:
        ax.grid(True, linewidth=0.5)

    ticks = np.arange(0, s.dof + 2, 2)
    ax.set_xticks(ticks)
    ax.set_yticks(ticks)

    ax.xaxis.tick_top()
    ax.set_xlim(0, s.dof)
    ax.set_ylim(0, s.dof)
    ax.set_aspect('equal', adjustable='box')
    ax.invert_yaxis()
    ax.tick_params(left=False, right=False, labelleft=False, labeltop=False, top=False)

    plt.tight_layout()
    plt.show()
    """
