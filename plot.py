import numpy as np
import math as m
import matplotlib.pyplot as plt


def plot_results(model, solution, deformation_scale, window_name, plot_matrix):
    """
    Plots displacement, von Mises stress deformed contour plots,
    max principal stress vector plots and global stiffness matrix
    heat map.

    Args:
        model (dict): Model attributes defined using keywords.
        solution (object): Class object of model solution.
        deformation_scale (int): Contour plot deformation scale.
        window_name (string): Window title for gui and plots
        plot_matrix (boolean): Plots global stiffness matrix heat map.
    """

    print("\n" + "Plotting results...")

    stress_mises = solution.stress_mises["s_mises"].tolist()
    displacements = solution.displacements.tolist()

    displacement_mag = []
    for i in range(0, len(displacements), 2):
        value = m.sqrt(displacements[i] ** 2 + displacements[i + 1] ** 2)
        displacement_mag.append(value)

    node_list = []
    for node in model["nodes"]:
        node_list.append(model["nodes"][node])

    node_coordinates = []
    for i in range(0, len(node_list)):
        x_index = ((i + 1) * 2) - 2
        y_index = ((i + 1) * 2) - 1
        x = node_list[i][0] + (displacements[x_index] * deformation_scale)
        y = node_list[i][1] + (displacements[y_index] * deformation_scale)
        node_coordinates.append([x, y])

    element_list = []
    for element in model["elements"]:
        element_nodes = model["elements"][element]["nodes"]
        for i in range(len(element_nodes)):
            element_nodes[i] = element_nodes[i] - 1
        element_list.append(element_nodes)

    element_coordinates_x = []
    element_coordinates_y = []

    for element in element_list:
        node_positions_x = []
        node_positions_y = []

        for node in element:
            node_positions_x.append(node_coordinates[node][0])
            node_positions_y.append(node_coordinates[node][1])
        element_centre_x = sum(node_positions_x) / 3
        element_centre_y = sum(node_positions_y) / 3
        element_coordinates_x.append([element_centre_x])
        element_coordinates_y.append([element_centre_y])

    stress_principal = solution.stress_principal["s_max"].tolist()
    stress_principal_x = solution.stress_principal["opp"].tolist()
    stress_principal_y = solution.stress_principal["adj"].tolist()
    stress_principal_x_opp = [x * -1 for x in stress_principal_x]
    stress_principal_y_opp = [y * -1 for y in stress_principal_y]

    node_array = np.array(node_coordinates)
    node_coordinates_x, node_coordinates_y = node_array.T

    fig, axs = plt.subplots(1, 3, num=window_name + ": Results")

    displacement_plot = axs[0].tripcolor(
        node_coordinates_x,
        node_coordinates_y,
        element_list,
        displacement_mag,
        edgecolors="k",
        cmap="rainbow",
    )

    axs[0].axis("off")
    axs[0].set_title("U [Magnitude]", y=-0.07)
    fig.colorbar(displacement_plot, ax=axs[0], format="%.0e")

    stress_mises_plot = axs[1].tripcolor(
        node_coordinates_x,
        node_coordinates_y,
        element_list,
        stress_mises,
        edgecolors="k",
        cmap="rainbow",
    )

    axs[1].axis("off")
    axs[1].set_title("S [von Mises]", y=-0.07)
    fig.colorbar(stress_mises_plot, ax=axs[1], format="%.0e")

    stress_vector_plot = axs[2].quiver(
        element_coordinates_x,
        element_coordinates_y,
        stress_principal_x,
        stress_principal_y,
        stress_principal,
        cmap="rainbow",
    )

    axs[2].quiver(
        element_coordinates_x,
        element_coordinates_y,
        stress_principal_x_opp,
        stress_principal_y_opp,
        stress_principal,
        cmap="rainbow",
    )

    axs[2].triplot(
        node_coordinates_x,
        node_coordinates_y,
        element_list,
        linewidth=0.2,
        color="black",
    )

    axs[2].axis("off")
    axs[2].set_title("S [Max Principal]", y=-0.07)
    fig.colorbar(stress_vector_plot, ax=axs[2], format="%.0e")

    if plot_matrix:
        dof = solution.dof

        x = np.repeat(np.arange(0.5, dof + 0.5, 1), dof)
        y = np.arange(0.5, dof + 0.5, 1)
        y = np.tile(y, dof)

        v = []
        max_value = solution.global_stiffness_matrix.max()
        max_value = max_value.max()
        for index, row in solution.global_stiffness_matrix.iterrows():
            v_row = [abs(i) / max_value for i in list(row)]
            v.extend(v_row)

        marker_size = 3600 / dof

        fig2, ax2 = plt.subplots(num=window_name + ": Stiffness Matrix")
        ax2.scatter(x, y, marker="s", alpha=v, s=marker_size)

        if dof < 300:
            plt.grid(True, linewidth=0.5)

        ticks = np.arange(0, dof + 2, 2)
        ax2.set_xticks(ticks)
        ax2.set_yticks(ticks)

        ax2.xaxis.tick_top()
        # plt.xlim(0, dof)
        # plt.ylim(0, dof)
        ax2.set_xlim(0, dof)
        ax2.set_ylim(0, dof)
        ax2.set_aspect("equal", adjustable="box")
        ax2.invert_yaxis()
        ax2.tick_params(
            left=False, right=False, labelleft=False, labeltop=False, top=False
        )

    plt.tight_layout()
    plt.show()
