import numpy as np
import math as m
import matplotlib.pyplot as plt

def plot_mises(model, mises, u, scale):
    print("Plotting results......")

    nodes = []
    for node in model["nodes"]:
        nodes.append(model["nodes"][node])

    for i in range(0, len(nodes)):
        index_1 = ((i+1)*2)-2
        index_2 = ((i+1)*2)-1
        nodes[i][0] = nodes[i][0] + (u[index_1]*scale)
        nodes[i][1] = nodes[i][1] + (u[index_2]*scale)

    elements = []
    for element in model["elements"]:
        node_list = model["elements"][element]["nodes"]
        for i in range(len(node_list)):
            node_list[i] = node_list[i]-1
        elements.append(node_list)

    #plt.rcParams["figure.figsize"] = [7.00, 3.50]
    #plt.rcParams["figure.autolayout"] = True

    values_s = []
    for value in mises:
        values_s.append(value[1]) 
    values_u = []
    for i in range(0, len(u), 2):
        value = m.sqrt(u[i]**2 + u[i+1]**2)
        values_u.append(value)

    '''
    max_value = max(values)
    min_value = min(values)
    inc_value = (max_value - min_value) / len(default_colours)

    contour_plot_range = []
    for i in range(len(default_colours)):
        colour_range = [min_value + (inc_value * i), min_value + (inc_value * i) + inc_value]
        contour_plot_range.append(colour_range)

    plot_colours = []

    for value in values:
        for i, v in enumerate(contour_plot_range):
            if value >= v[0] and value <= v[1]:
                plot_colours.append(default_colours[i])
    '''

    nodes = np.array(nodes)
    elements = np.array(elements)

    x, y = nodes.T

    fig, axs = plt.subplots(1, 2, num="openFEM 0.0.1")
    u_plot = axs[0].tripcolor(x, y, elements, values_u, edgecolors='k', cmap="rainbow")
    s_plot = axs[1].tripcolor(x, y, elements, values_s, edgecolors='k', cmap="rainbow")
    axs[0].axis('off')
    axs[1].axis('off')
    axs[0].set_title("Displacement", y = -0.07)
    axs[1].set_title("Stress (von Mises)", y = -0.07)
    #axs[0].set_xlabel("Displacement")
    #axs[1].set_xlabel("Stress (von Mises)")
    fig.colorbar(u_plot, ax=axs[0])
    fig.colorbar(s_plot, ax=axs[1])
    
    #plt.tripcolor(x, y, elements, values, edgecolors='k', cmap="rainbow")
    #plt.gca().set_aspect('equal', adjustable='box')
    #plt.colorbar()
    plt.show()