import load_inp
import numpy as np
import math as m
import pandas as pd
import pprint


class cst_element:
    def __init__(self, x_cord, y_cord, node_list, E, v, t):
        self.x_cord = [float(x) for x in x_cord]                                                
        self.y_cord = [float(y) for y in y_cord]
        self.node_list = node_list

        self.E = float(E)
        self.v = float(v)
        self.t = float(t)
        
        self.calculate_area()
        self.strain_displacement_matrix()
        self.stress_strain_matirx()
        self.stiffness_matrix() 


    def calculate_area(self):
        area = np.array([
            [1, self.x_cord[0], self.y_cord[0]],
            [1, self.x_cord[1], self.y_cord[1]],
            [1, self.x_cord[2], self.y_cord[2]]
        ])
        
        self.area = np.linalg.det(area) * 0.5


    def strain_displacement_matrix(self):
        b1 = self.y_cord[1] - self.y_cord[2]                                                
        b2 = self.y_cord[2] - self.y_cord[0]
        b3 = self.y_cord[0] - self.y_cord[1]
        c1 = self.x_cord[2] - self.x_cord[1]
        c2 = self.x_cord[0] - self.x_cord[2]
        c3 = self.x_cord[1] - self.x_cord[0]

        B = np.array([
            [b1, 0, b2, 0, b3, 0],
            [0, c1, 0, c2, 0, c3],
            [c1, b1, c2, b2, c3, b3]
        ])
        
        self.B = B * (1/(2*self.area))


    def stress_strain_matirx(self):
        D = np.array([
            [1, self.v, 0],
            [self.v, 1, 0],
            [0, 0, (1-self.v)/2]
        ])

        self.D = D * (self.E/(1-self.v**2))


    def stiffness_matrix(self):                                                                                                        
        Bt = self.B.transpose()
        eK = np.matmul(Bt, np.matmul(self.D, self.B)) * self.area * self.t 

        node_headings = []
        for node in self.node_list:
            for displacement in ['u', 'v']:
                node_headings.append(str(node) + displacement)

        self.eK_df = pd.DataFrame(
            eK,
            columns=node_headings,
            index=node_headings
        )


class solver:
    def __init__(self, model):
        self.model = model
        self.dof = len(self.model["nodes"].keys()) * 2
        self.u = ['*']*self.dof
        self.f = np.zeros(self.dof)
        self.homogeneous_model = True

        self.node_headings = []
        for n in range(1, int((self.dof/2)+1)):
            for disp in ['u', 'v']:
                self.node_headings.append(str(n) + disp)

        self.f_ds = pd.Series(
            self.f,
            index=self.node_headings
        )

        self.u_ds = pd.Series(
            self.u,
            index=self.node_headings
        )


    def define_boundary(self):
        for boundary in self.model["boundary"]:
            if isinstance(boundary, str):
                node_list = self.model["nodesets"][boundary]
                for axis in self.model["boundary"][boundary].keys():
                    for node in node_list:
                        if axis == "1":
                            disp = 'u'
                        elif axis == "2":
                            disp = 'v'
                        self.u_ds._set_value(str(node)+disp, self.model["boundary"][boundary][axis])
        

    def define_load(self):
        if bool(self.model['load']) is False:
            self.homogeneous_model = False
        else:
            for load in self.model["load"]:
                if isinstance(load, str):
                    node_list = self.model["nodesets"][load]
                    for axis in self.model["load"][load].keys():
                        for node in node_list:
                            if axis == "1":
                                disp = 'u'
                            elif axis == "2":
                                disp = 'v'
                            self.f_ds._set_value(str(node)+disp, self.model["load"][load][axis])


    def define_element_stiffness(self):
        for element in self.model["elements"]:
            node_list = self.model["elements"][element]["nodes"]
            x_cord = []
            y_cord = []
            for node in node_list:
                x_cord.append(self.model["nodes"][node][0])
                y_cord.append(self.model["nodes"][node][1])
            
            cst = cst_element(
                x_cord,
                y_cord,
                node_list,
                self.model["elasticity"][0],
                self.model["elasticity"][1],
                self.model["section"]["thickness"]
            )

            self.model["elements"][element]["K"] = cst

        
    def define_global_stiffness(self):
        self.gK_df = pd.DataFrame(
            np.zeros((self.dof, self.dof)),
            columns=self.node_headings,
            index=self.node_headings
        )

        for e in self.model["elements"]:
            eK_df = self.model["elements"][e]['K'].__dict__["eK_df"]

            for column in eK_df:
                for index, row in eK_df.iterrows():
                    value = self.gK_df._get_value(index, column) + eK_df._get_value(index, column)
                    self.gK_df._set_value(index, column, value)


    def reduce_matrix(self):
        self.gKr_df = self.gK_df.copy()
        u_temp_ds = self.u_ds.copy()

        for index , u in self.u_ds.items():
            if u == 0:
                self.gKr_df.drop(index=index, columns=index, inplace=True)
                self.f_ds.drop(labels=index, inplace=True)   
                u_temp_ds.drop(labels=index, inplace=True) 
            else:
                if u == '*':
                    u_temp_ds._set_value(index, 0.)
                else:
                    u_temp_ds._set_value(index, u)
    
        if not self.homogeneous_model:
            self.f_ds = self.gKr_df.dot(u_temp_ds)
            
            for index, u in u_temp_ds.items():
                if u != 0:
                    self.gKr_df.drop(index=index, columns=index, inplace=True)
                    self.f_ds.drop(labels=index, inplace=True)   
             

    def compute_dispalcements(self):
        gKr = self.gKr_df.to_numpy()
        f = self.f_ds.to_numpy()
        gKr = gKr.astype('float64')
        f = f.astype('float64')
        disp = np.linalg.solve(gKr, f)
        self.disp_ds = pd.Series(disp, index=self.f_ds.index)
        for index, u in self.disp_ds.items():
            self.u_ds._set_value(index, u*-1)

        
    def compute_normal_stress(self):
        elements = self.model["elements"].keys()
        index = ["e" + str(element) for element in elements]
        self.norm_stress_df = pd.DataFrame(
           index=index,
           columns=["s1", "s2", "s12"]
           )
        
        for element in elements:
            node_list = self.model["elements"][element]["nodes"]
            u = np.zeros(len(node_list)*2)
            count = 0
            for node in node_list:
                for disp in ["u", "v"]:
                    u[count] = self.u_ds[str(node)+disp]
                    count += 1

            D = self.model["elements"][element]["K"].__dict__["D"]
            B = self.model["elements"][element]["K"].__dict__["B"]
            
            normal_stress = np.matmul(np.matmul(D, B), u)
            self.norm_stress_df.loc["e" + str(element)] = [
                normal_stress[0],
                normal_stress[1],
                normal_stress[2],
                ]


    def compute_principal_stress(self): 
        index = ["e" + str(element) for element in self.model["elements"].keys()]
        self.princ_stress_df = pd.DataFrame(
           index=index,
           columns=["s_max", "s_min", "s_shear", "a", "opp", "adj"]
           )
        
        for index, row in self.norm_stress_df.iterrows():
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
            self.princ_stress_df.loc[index] = [s1, s2, s12, angle, opp, adj] 


    def compute_mises_stress(self):
        index = ["e" + str(element) for element in self.model["elements"].keys()]
        self.mises_stress_df = pd.DataFrame(
           index=index,
           columns=["s_mises"]
           )
        
        for index, row in self.norm_stress_df.iterrows():
            sigma_1 = row[0]
            sigma_2 = row[1]
            sigma_12 = row[2]

            mises = m.sqrt(sigma_1**2 - sigma_1 * sigma_2 + sigma_2**2 + 3 * sigma_12**2)
            self.mises_stress_df.loc[index] = mises


if __name__ == "__main__":
    pp = pprint.PrettyPrinter(indent=4)
    inp = load_inp.load_inp("Job-6.inp")
    model = load_inp.call_gen_function(inp)
    s = solver(model)
    
    s.define_element_stiffness()
    s.define_global_stiffness()
    s.define_boundary()
    s.define_load()
    s.reduce_matrix()
    s.compute_dispalcements()
    s.compute_normal_stress()
    s.compute_principal_stress()
    s.compute_mises_stress()

    #pp.pprint(s.__dict__.keys())
    #pp.pprint(s.__dict__['disp_ds'])