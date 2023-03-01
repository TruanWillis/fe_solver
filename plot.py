import numpy as np
import math as m
import matplotlib.pyplot as plt
import matplotlib.cm as cm

def plot_results(model, s, scale):
    print("Plotting results......")

    mises = s.mises_stress_df['s_mises'].tolist()
    u = s.u_ds.tolist()

    nodes = []
    for node in model["nodes"]:
        nodes.append(model["nodes"][node])

    nodes_d = []
    for i in range(0, len(nodes)):
        index_1 = ((i+1)*2)-2
        index_2 = ((i+1)*2)-1
        x = nodes[i][0] + (u[index_1]*scale)
        y = nodes[i][1] + (u[index_2]*scale)
        nodes_d.append([x, y])

    elements = []
    for element in model["elements"]:
        node_list = model["elements"][element]["nodes"]
        for i in range(len(node_list)):
            node_list[i] = node_list[i]-1
        elements.append(node_list)

    values_s = mises
    values_u = []
    for i in range(0, len(u), 2):
        value = m.sqrt(u[i]**2 + u[i+1]**2)
        values_u.append(value)
    
    v_x = []
    v_y = []

    for element in elements:
        x = []
        y = []
        
        for node in element:
            x.append(nodes_d[node][0])
            y.append(nodes_d[node][1])
        x_ = sum(x)/3
        y_ = sum(y)/3
        v_x.append([x_])
        v_y.append([y_])

    v_s = s.princ_stress_df['s_max'].tolist()
    v_u = s.princ_stress_df['opp'].tolist()
    v_v = s.princ_stress_df['adj'].tolist()
    
    nodes = np.array(nodes)
    nodes_d = np.array(nodes_d)
    elements = np.array(elements)
    
    x, y = nodes.T
    x_d, y_d = nodes_d.T
    
    fig, axs = plt.subplots(1, 3, num="openFEM 0.0.1")
    u_plot = axs[0].tripcolor(x_d, y_d, elements, values_u, edgecolors='k', cmap="rainbow")
    s_plot = axs[1].tripcolor(x_d, y_d, elements, values_s, edgecolors='k', cmap="rainbow")
    v_plot = axs[2].quiver(v_x, v_y, v_u, v_v, v_s, cmap="rainbow")
    v_u_opp = [u*-1 for u in v_u]
    v_v_opp = [v*-1 for v in v_v]
    axs[2].quiver(v_x, v_y, v_u_opp, v_v_opp, v_s, cmap="rainbow")
    axs[2].triplot(x_d, y_d, elements, linewidth=0.4, color='black')
    axs[0].axis('off')
    axs[1].axis('off')
    axs[2].axis('off')
    axs[0].set_title("U [Magnitude]", y = -0.07)
    axs[1].set_title("S [von Mises]", y = -0.07)
    axs[2].set_title("S [Max Principal]", y = -0.07)
    fig.colorbar(u_plot, ax=axs[0])
    fig.colorbar(s_plot, ax=axs[1])
    fig.colorbar(v_plot, ax=axs[2])
    plt.show()