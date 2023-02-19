import numpy as np


class cst_element:
    def __init__(self, x_cord, y_cord, node_list, E, v, t):
        self.x_cord = [float(x) for x in x_cord]                                                
        self.y_cord = [float(y) for y in y_cord]
        self.node_list = node_list
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
        

    def intialise_displacement(self):
        self.u = np.zeros(len(self.node_list))
        self.v = np.zeros(len(self.node_list))


class solver:
    def __init__(self, model):
        self.model = model
        self.dof = len(self.model["nodes"].keys()) * 2
        self.u = [1]*self.dof
        self.f = np.zeros(self.dof)
        
    def define_boundary(self):
        for boundary in self.model["boundary"]:
            if isinstance(boundary, str):
                node_list = self.model["nodesets"][boundary]
                for axis in self.model["boundary"][boundary].keys():
                    for node in node_list:
                        if axis == "1":
                            index = (node * 2 - 2)
                        elif axis == "2":
                            index = (node * 2 - 1)
                        self.u[index] = self.model["boundary"][boundary][axis]

        
    def define_load(self):
        for load in self.model["load"]:
            if isinstance(load, str):
                node_list = self.model["nodesets"][load]
                for axis in self.model["load"][load].keys():
                    for node in node_list:
                        if axis == "1":
                            index = (node * 2 - 2)
                        elif axis == "2":
                            index = (node * 2 - 1)
                        self.f[index] = self.model["load"][load][axis]
        
        for i in range(self.dof-1, -1, -1):
            if self.u[i] == 0:
                self.f = np.delete(self.f, i)        

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
                    

        self.gKr = self.gK
        self.matrix_headers_r = self.matrix_headers

        for i in range(len(self.u)-1, -1, -1):
            if self.u[i] == 0:
                del self.matrix_headers_r[i]
                self.gKr = np.delete(self.gKr, i, 0)
                self.gKr = np.delete(self.gKr, i, 1)


    def compute_dispalcements(self):
        self.displacements = np.linalg.solve(self.gKr, self.f)


if __name__ == "__main__":
    print("__main__")


