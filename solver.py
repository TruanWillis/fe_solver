import model
import elements

import math as m
import numpy as np
import pandas as pd
import pprint
import os
from tabulate import tabulate

import matplotlib.pyplot as plt
#from sklearn.preprocessing import normalize


class solver:
    def __init__(self, model, print_head, save_matrix, out_dir):
        self.model = model
        self.dof = len(self.model["nodes"].keys()) * 2
                
        self.homogeneous_model = True
        self.save_matrix = save_matrix
        self.out_dir = out_dir

        self.node_headings = []
        for n in range(1, int((self.dof/2)+1)):
            for displacement in ['u', 'v']:
                self.node_headings.append(str(n) + displacement)

        self.forces = pd.Series(
            np.zeros(self.dof),
            index=self.node_headings
        )

        self.displacements = pd.Series(
            ['*']*self.dof,
            index=self.node_headings
        )

        self.define_element_stiffness()
        self.define_global_stiffness()
        self.define_boundary()
        self.define_load()
        self.reduce_matrix()
        self.compute_dispalcements()
        self.compute_normal_stress()
        self.compute_principal_stress()
        self.compute_mises_stress()

        if print_head:
            self.print_results()


    def define_boundary(self):
        for boundary in self.model["boundary"]:
            if isinstance(boundary, str):
                node_list = self.model["nodesets"][boundary]
                for axis in self.model["boundary"][boundary].keys():
                    for n in node_list:
                        if axis == "1":
                            disp = 'u'
                        elif axis == "2":
                            disp = 'v'
                        self.displacements._set_value(str(n)+disp, self.model["boundary"][boundary][axis])
        

    def define_load(self):
        if bool(self.model['load']) is False:
            self.homogeneous_model = False
        else:
            for load in self.model["load"]:
                if isinstance(load, str):
                    node_list = self.model["nodesets"][load]
                    for axis in self.model["load"][load].keys():
                        for n in node_list:
                            if axis == "1":
                                disp = 'u'
                            elif axis == "2":
                                disp = 'v'
                            self.forces._set_value(str(n)+disp, self.model["load"][load][axis])


    def define_element_stiffness(self):
        for element in self.model["elements"]:
            node_list = self.model["elements"][element]["nodes"]
            x_cord = []
            y_cord = []
            for node in node_list:
                x_cord.append(self.model["nodes"][node][0])
                y_cord.append(self.model["nodes"][node][1])
            
            
            cst = elements.cst_element(
                x_cord,
                y_cord,
                node_list,
                self.model["elasticity"][0],
                self.model["elasticity"][1],
                self.model["section"]["thickness"]
            )

            self.model["elements"][element]["K"] = cst

        
    def define_global_stiffness(self):
        self.global_stiffness_matrix = pd.DataFrame(
            np.zeros((self.dof, self.dof)),
            columns=self.node_headings,
            index=self.node_headings
        )

        if self.save_matrix:
            self.global_stiffness_matrix_save = self.global_stiffness_matrix.copy()

        for e in self.model["elements"]:
            element_stiffness_matrix = self.model["elements"][e]['K'].__dict__["element_stiffness_matrix"]

            for column in element_stiffness_matrix:
                for index, row in element_stiffness_matrix.iterrows():
                    value = self.global_stiffness_matrix._get_value(index, column) + element_stiffness_matrix._get_value(index, column)
                    self.global_stiffness_matrix._set_value(index, column, value)
                    
                    if self.save_matrix:
                        ident = self.global_stiffness_matrix_save._get_value(index, column)
                        if ident == 0:
                            ident = "e" + str(e)
                        else:
                            ident = ident + ", e" + str(e)    
                        self.global_stiffness_matrix_save._set_value(index, column, ident)

        if self.save_matrix:
            self.global_stiffness_matrix_save.to_csv(self.out_dir + "/stiffness_matrix.csv")


    def reduce_matrix(self):
        self.global_stiffness_matrix_reduced = self.global_stiffness_matrix.copy()
        displacements_temp = self.displacements.copy()

        for index , u in self.displacements.items():
            if u == 0:
                self.global_stiffness_matrix_reduced.drop(index=index, columns=index, inplace=True)
                self.forces.drop(labels=index, inplace=True)   
                displacements_temp.drop(labels=index, inplace=True) 
            else:
                if u == '*':
                    displacements_temp._set_value(index, 0.)
                else:
                    displacements_temp._set_value(index, u)
    
        if not self.homogeneous_model:
            self.forces = self.global_stiffness_matrix_reduced.dot(displacements_temp)
            
            for index, u in displacements_temp.items():
                if u != 0:
                    self.global_stiffness_matrix_reduced.drop(index=index, columns=index, inplace=True)
                    self.forces.drop(labels=index, inplace=True)   
             

    def compute_dispalcements(self):
        global_stiffness_matrix = self.global_stiffness_matrix_reduced.to_numpy()
        forces = self.forces.to_numpy()

        global_stiffness_matrix = global_stiffness_matrix.astype('float64')
        forces = forces.astype('float64')

        displacement_solution = np.linalg.solve(global_stiffness_matrix, forces)
        displacements = pd.Series(displacement_solution, index=self.forces.index)
        
        if self.homogeneous_model:
            homogeneous_correction = 1
        else:
            homogeneous_correction = -1

        for index, displacement in displacements.items():
            self.displacements._set_value(index, displacement*homogeneous_correction)
        
        
    def compute_normal_stress(self):
        elements = self.model["elements"].keys()
        index = ["e" + str(element) for element in elements]
        self.stress_normal = pd.DataFrame(
           index=index,
           columns=["s1", "s2", "s12"]
           )
        
        for element in elements:
            node_list = self.model["elements"][element]["nodes"]
            u = np.zeros(len(node_list)*2)
            count = 0
            for node in node_list:
                for disp in ["u", "v"]:
                    u[count] = self.displacements[str(node)+disp]
                    count += 1

            D = self.model["elements"][element]["K"].__dict__["D"]
            B = self.model["elements"][element]["K"].__dict__["B"]
            
            normal_stress = np.matmul(np.matmul(D, B), u)
            self.stress_normal.loc["e" + str(element)] = [
                normal_stress[0],
                normal_stress[1],
                normal_stress[2],
                ]


    def compute_principal_stress(self): 
        index = ["e" + str(element) for element in self.model["elements"].keys()]
        self.stress_principal = pd.DataFrame(
           index=index,
           columns=["s_max", "s_min", "s_shear", "a", "opp", "adj"]
           )
        
        for index, row in self.stress_normal.iterrows():
            Sx, Sy, Sxy = row[0], row[1], row[2]
            s1 = ((Sx + Sy)/2)+m.sqrt(((Sx-Sy)/2)**2+Sxy**2)
            s2 = ((Sx + Sy)/2)-m.sqrt(((Sx-Sy)/2)**2+Sxy**2)
            s12 = m.sqrt(((Sx-Sy)/2)**2+Sxy**2)
            if Sx == Sy:
                angle = 0
                opp = 0
                adj = s1
            else: 
                try:
                    angle = -0.5*m.atan((2*Sxy)/(Sx-Sy))
                    opp = m.sin(angle)*s1
                    adj = m.cos(angle)*s1
                except:
                    angle = 0
                    opp = 0
                    adj = s1
            self.stress_principal.loc[index] = [s1, s2, s12, angle, opp, adj] 


    def compute_mises_stress(self):
        index = ["e" + str(element) for element in self.model["elements"].keys()]
        self.stress_mises = pd.DataFrame(
           index=index,
           columns=["s_mises"]
           )
        
        for index, row in self.stress_normal.iterrows():
            sigma_1 = row[0]
            sigma_2 = row[1]
            sigma_12 = row[2]

            mises = m.sqrt(sigma_1**2 - sigma_1 * sigma_2 + sigma_2**2 + 3 * sigma_12**2)
            self.stress_mises.loc[index] = mises


    def print_results(self):
        print("\n" + "In-plane stress...")
        print(tabulate(self.stress_normal.head(), tablefmt="grid", numalign="right", headers=self.stress_normal.columns))
        print("\n" + "Principal stress...")
        print(tabulate(self.stress_principal.head(), tablefmt="grid", numalign="right", headers=self.stress_principal.columns))       
        print("\n" + "Mises stress...")
        print(tabulate(self.stress_mises.head(), tablefmt="grid", numalign="right", headers=self.stress_mises.columns))
        

if __name__ == "__main__":
    wk_dir = os.path.dirname(os.path.realpath(__file__))
    pp = pprint.PrettyPrinter(indent=4)
    input = model.load_input(wk_dir + "/test_data/test_input_1.inp")
    model = model.call_gen_function(input)
    s = solver(model, True, True, wk_dir + "/")

    #pp.pprint(s.__dict__.keys())
    pp.pprint(s.__dict__['displacements'])
    pp.pprint(s.__dict__['forces'])
    pp.pprint(s.__dict__['stress_normal']['s1']['e8'])

    '''
    sm = s.__dict__['global_stiffness_matrix']
    print(sm.head())

    print(s.__dict__['dof'])


    x = np.repeat(np.arange(0.5, s.__dict__['dof'] + 0.5, 1), s.__dict__['dof']) 
    y = np.arange(0.5, s.__dict__['dof'] + 0.5, 1)
    y = np.tile(y, s.__dict__['dof'])

    v = []
    max_value = sm.max()
    max_value = max_value.max()
    for index, row in sm.iterrows():
        v_row = [abs(i)/max_value for i in list(row)]
        v.extend(v_row)
    
    marker_size = 3600 / s.__dict__['dof'] 
    
    fig, ax = plt.subplots()
    print(fig, ax)
    ax.scatter(x, y, marker='s', alpha=v, s=marker_size)
    
    if s.__dict__['dof'] < 300:
        ax.grid(True, linewidth=0.5)

    ticks = np.arange(0, s.__dict__['dof'] + 2, 2)         
    ax.set_xticks(ticks)
    ax.set_yticks(ticks)

    ax.xaxis.tick_top()
    ax.set_xlim(0, s.__dict__['dof'])
    ax.set_ylim(0, s.__dict__['dof'])
    ax.set_aspect('equal', adjustable='box')
    ax.invert_yaxis()
    ax.tick_params(left=False, right=False, labelleft=False, labeltop=False, top=False)

    plt.tight_layout()
    plt.show()
    '''
    
    
    

    
