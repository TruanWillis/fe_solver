import numpy as np
import matplotlib.pyplot as plt

def plot_mises(model, mises):
    print("Plotting results......")

    nodes = []
    for node in model["nodes"]:
        nodes.append(model["nodes"][node])

    elements = []
    for element in model["elements"]:
        node_list = model["elements"][element]["nodes"]
        for i in range(len(node_list)):
            node_list[i] = node_list[i]-1
        elements.append(node_list)

    plt.rcParams["figure.figsize"] = [7.00, 3.50]
    plt.rcParams["figure.autolayout"] = True

    values = []
    for value in mises:
        values.append(value[1]) 

    nodes = np.array(nodes)
    elements = np.array(elements)

    print(nodes)
    print(elements)

    '''
    nodes = np.array([
    [0.0, 0.0],
    [1.0, 0.0],
    [2.0, 0.5],
    [0.0, 1.0],
    [1.0, 1.0],
    [1.7, 1.3],
    [1.0, 1.7]])

    elements = np.array([
    [1, 2, 5],
    [5, 4, 1],
    [2, 3, 6],
    [6, 5, 2],
    [4, 5, 7],
    [5, 6, 7]])

    values = [1, 2, 1, 2, 7, 4, 5]
    '''
    x, y = nodes.T

    plt.tricontourf(x, y, elements, values, 12, cmap='copper')
    #plt.triplot(x, y, elements)

    plt.show()