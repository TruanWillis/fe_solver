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

        self.node_headings = []
        for n in self.node_list:
            for disp in ['u', 'v']:
                self.node_headings.append(str(n) + disp)

        self.E = float(E)
        self.v = float(v)
        self.t = float(t)
        self.dof = len(node_list) * 2
        
        self.calculate_area()
        self.strain_displacement_matrix()
        self.stress_strain_matirx()
        self.stiffness_matrix()
        self.stiffness_matrix_index()
        self.intialise_displacement()    


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
        self.eK = np.matmul(Bt, np.matmul(self.D, self.B)) * self.area * self.t 

        #print(self.eK)
        self.eK_df = pd.DataFrame(
            self.eK,
            columns=self.node_headings,
            index=self.node_headings
        )

        #print(self.eK_df)


    def stiffness_matrix_index(self):
        self.eK_index = np.zeros((self.dof, self.dof), dtype=object)
        count_1 = 0
        for n1 in self.node_list:
            count_2 = 0
            for n2 in self.node_list:
                self.eK_index[count_1][count_2] = str(n1) + str(n2)
                self.eK_index[count_1][count_2 + 1] = str(n1) + str(n2)
                self.eK_index[count_1 + 1][count_2] = str(n1) + str(n2)
                self.eK_index[count_1 + 1][count_2 + 1] = str(n1) + str(n2)
                count_2 += 2
            count_1 += 2

        self.gK_index = np.zeros((self.dof, self.dof), dtype=object)
        count_1 = 0
        for n1 in self.node_list:
            count_2 = 0
            for n2 in self.node_list:
                origin_row = (n1*2)-2
                origin_col = (n2*2)-2
                self.gK_index[count_1][count_2] = str(origin_row) + '|' + str(origin_col)
                self.gK_index[count_1][count_2 + 1] = str(origin_row) + '|' + str(origin_col+1)
                self.gK_index[count_1 + 1][count_2] = str(origin_row+1) + '|' + str(origin_col)
                self.gK_index[count_1 + 1][count_2 + 1] = str(origin_row+1) + '|' + str(origin_col+1)
                count_2 += 2
            count_1 += 2
        #print(self.eK_index)
        #print(self.gK_index)
        

    def intialise_displacement(self):
        self.u = np.zeros(len(self.node_list))
        self.v = np.zeros(len(self.node_list))


class solver:
    def __init__(self, model):
        self.model = model
        self.dof = len(self.model["nodes"].keys()) * 2
        self.u = ['*']*self.dof
        #self.u = [-1e-99]*self.dof
        #self.u = [1]*self.dof
        self.f = np.zeros(self.dof)
        self.homogeneous_model = True

        self.node_headings = []
        for n in range(1, int((self.dof/2)+1)):
            for disp in ['u', 'v']:
                self.node_headings.append(str(n) + disp)

        self.f_df = pd.DataFrame(
            self.f,
            index=self.node_headings
        )
    
        self.u_df = pd.DataFrame(
            self.u,
            index=self.node_headings
        )

        self.f_ds = pd.Series(
            self.f,
            index=self.node_headings
        )

        self.u_ds = pd.Series(
            self.u,
            index=self.node_headings
        )

        #print(self.f_df)
        #print(self.f_ds)
        #print(self.u_df)
        #print(self.u_ds)

    def define_boundary(self):
        for boundary in self.model["boundary"]:
            if isinstance(boundary, str):
                node_list = self.model["nodesets"][boundary]
                for axis in self.model["boundary"][boundary].keys():
                    for node in node_list:
                        if axis == "1":
                            index = (node * 2 - 2)
                            disp = 'u'
                        elif axis == "2":
                            index = (node * 2 - 1)
                            disp = 'v'
                        self.u[index] = self.model["boundary"][boundary][axis]
                        self.u_ds._set_value(str(node)+disp, self.model["boundary"][boundary][axis])
        #print(self.u)
        #print(self.u_ds)
        
    def define_load(self):
        if bool(self.model['load']) is False:
            #self.f = np.matmul(self.gK, self.u)
            #pass
            self.homogeneous_model = False
        else:
            for load in self.model["load"]:
                if isinstance(load, str):
                    node_list = self.model["nodesets"][load]
                    for axis in self.model["load"][load].keys():
                        for node in node_list:
                            if axis == "1":
                                index = (node * 2 - 2)
                                disp = 'u'
                            elif axis == "2":
                                index = (node * 2 - 1)
                                disp = 'v'
                            self.f[index] = self.model["load"][load][axis]
                            self.f_ds._set_value(str(node)+disp, self.model["load"][load][axis])
        #print(self.f)
        #print(self.f_ds)
        '''
        for i in range(self.dof-1, -1, -1):
            if self.u[i] == 0:
                self.f = np.delete(self.f, i)        
        '''


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
        self.matrix_headers = []
        for n in range(1, int((self.dof/2)+1)):
            for displacement in ['u', 'v']:
                self.matrix_headers.append(displacement + str(n))

        self.gK = np.zeros((self.dof, self.dof))

        for e in self.model["elements"]:
            eK = self.model["elements"][e]['K'].__dict__["eK"]
            gK_index = self.model["elements"][e]['K'].__dict__["gK_index"]
            for i in range(eK.shape[0]):
                for j in range(eK.shape[1]):
                    K_value = eK[i][j]
                    K_index = gK_index[i][j]
                    K_index_row = int(K_index.split('|')[0])
                    K_index_col = int(K_index.split('|')[1])
                    self.gK[K_index_row][K_index_col] = K_value + self.gK[K_index_row][K_index_col]
                    
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

        #print(self.gK)
        #print(self.gK_df)
        
        '''
        self.gKr = self.gK
        self.matrix_headers_r = self.matrix_headers

        for i in range(len(self.u)-1, -1, -1):
            if self.u[i] == 0:
                del self.matrix_headers_r[i]
                self.gKr = np.delete(self.gKr, i, 0)
                self.gKr = np.delete(self.gKr, i, 1)
        '''


    def reduce_matrix(self):
        self.gKr = self.gK
        self.matrix_headers_r = self.matrix_headers

        u_temp = []
        for i in range(len(self.u)-1, -1, -1):
            if self.u[i] == 0:
                del self.matrix_headers_r[i]
                self.gKr = np.delete(self.gKr, i, 0)
                self.gKr = np.delete(self.gKr, i, 1)
                self.f = np.delete(self.f, i)   
            else:
                u_temp.insert(0, self.u[i])
    
        if not self.homogeneous_model:
            if np.sum(self.f) == 0:
                for i in range(len(u_temp)):
                    if u_temp[i] == '*':
                        u_temp[i] = 0
                self.f = np.matmul(self.gKr, u_temp)
                
                for i in range(len(u_temp)-1, -1, -1):
                    if u_temp[i] != 0:
                        del self.matrix_headers_r[i]
                        self.gKr = np.delete(self.gKr, i, 0)
                        self.gKr = np.delete(self.gKr, i, 1)
                        self.f = np.delete(self.f, i)   

        
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
        #print(self.gKr_df)
    
        if not self.homogeneous_model:
            #u_temp_ds.convert_dtypes()
            #print(u_temp_ds) 
            #f = self.gKr_df.dot(u_temp_ds)
            self.f_ds = self.gKr_df.dot(u_temp_ds)
            #self.f_ds.convert_dtypes()
            #print(f)
            
            for index, u in u_temp_ds.items():
                if u != 0:
                    self.gKr_df.drop(index=index, columns=index, inplace=True)
                    self.f_ds.drop(labels=index, inplace=True)   
        
        print(self.f)
        print(self.f_ds.dtypes)
            

    def compute_dispalcements(self):
        self.displacements = np.linalg.solve(self.gKr, self.f)
        for i in range(0, len(self.displacements)):
            result = self.displacements[i]
            direction = self.matrix_headers_r[i][0]
            node = int(self.matrix_headers_r[i][1:])

            if direction == "u":
                offset = 2
            if direction == "v":
                offset = 1

            index = (node * 2) - offset
            if self.homogeneous_model:
                self.u[index] = result
            elif not self.homogeneous_model:
                self.u[index] = result * -1

        gKr = self.gKr_df.to_numpy()
        f = self.f_ds.to_numpy()
        gKr = gKr.astype('float64')
        f = f.astype('float64')
        disp = np.linalg.solve(gKr, f)
        self.disp_ds = pd.Series(disp, index=self.f_ds.index)
        for index, u in self.disp_ds.items():
            self.u_ds._set_value(index, u*-1)

        
    def compute_normal_stress(self):
        self.normal_stress_results = []
        for element in self.model["elements"]:
            node_list = self.model["elements"][element]["nodes"]
            u = np.zeros(len(node_list)*2)
            count = 0
            for node in node_list:
                for offset in [2, 1]:
                    index = (node * 2) - offset
                    u[count] = self.u[index]
                    count += 1

            D = self.model["elements"][element]["K"].__dict__["D"]
            B = self.model["elements"][element]["K"].__dict__["B"]
            
            normal_stress = np.matmul(np.matmul(D, B), u)
            self.normal_stress_results.append([
                element, 
                normal_stress[0],
                normal_stress[1],
                normal_stress[2],
                ])
        
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
        self.principal_stress_results = []
        for s in self.normal_stress_results:
            Sx, Sy, Sxy = s[1], s[2], s[3]
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
            self.principal_stress_results.append([s[0], s1, s2, s12, angle, opp, adj]) 


         
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
        self.mises_stress_results = []
        for result in self.normal_stress_results:
            sigma_1 = result[1]
            sigma_2 = result[2]
            sigma_12 = result[3]

            mises = m.sqrt(sigma_1**2 - sigma_1 * sigma_2 + sigma_2**2 + 3 * sigma_12**2)
            self.mises_stress_results.append([result[0], mises])
        
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
    #pp.pprint(s.__dict__['u'])
    #pp.pprint(s.__dict__['f'])
    #pp.pprint(s.__dict__['gK'])
    s.reduce_matrix()
    #pp.pprint(s.__dict__['u'])
    #pp.pprint(s.__dict__['f'])
    #pp.pprint(s.__dict__['gKr'])
    
    s.compute_dispalcements()
    s.compute_normal_stress()
    s.compute_principal_stress()
    s.compute_mises_stress()

    #pp.pprint(s.__dict__.keys())
    #pp.pprint(s.__dict__['u'])
    #pp.pprint(s.__dict__['f'])
    #pp.pprint(s.__dict__['displacements'])
    #pp.pprint(s.__dict__['disp_ds'])

    #pp.pprint(s.__dict__['u'])
    #pp.pprint(s.__dict__['u_ds'])

    #test = np.matmul(s.__dict__['gK'], np.array(s.__dict__['u']))
    #dis = np.linalg.solve(s.__dict__['gK'], test)
    #print(test)
    #print(dis)
