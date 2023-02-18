import numpy as np
from tabulate import tabulate

element = np.array([[0,0], [20,0], [0,30]])


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
        

class global_stiffness_matrix:
    def __init__(self, dof, mesh):
        self.dof = dof
        self.mesh = mesh

        self.matrix_headers = []
        for n in range(1, int((dof/2)+1)):
            for displacement in ['u', 'v']:
                self.matrix_headers.append(displacement + str(n))


    def define(self):
        gK = np.zeros((dof, dof))

        for e in self.mesh:
            eK = mesh[e]['data'].eK
            gK_index = mesh[e]['data'].gK_index 
            for i in range(eK.shape[0]):
                for j in range(eK.shape[1]):
                    K_value = eK[i][j]
                    K_index = gK_index[i][j]
                    K_index_row = int(K_index.split('|')[0])
                    K_index_col = int(K_index.split('|')[1])
                    gK[K_index_row][K_index_col] = K_value + gK[K_index_row][K_index_col]

        gKr = gK
        matrix_headers_r = self.matrix_headers

        for i in range(len(u)-1, -1, -1):
            if u[i] == 0:
                del matrix_headers_r[i]
                gKr = np.delete(gKr, i, 0)
                gKr = np.delete(gKr, i, 1)

        return gKr, matrix_headers_r

'''
mesh = {
    'E1':
    {'n':[1, 2, 4],
    'x':[3, 3, 0],
    'y':[0, 2, 0]},
    'E2':
    {'n':[3, 4, 2],
    'x':[0, 0, 3],
    'y':[2, 0, 2]},
}

u = [1, 0, 1, 1, 0, 0, 0, 0]
f = np.array([[0], [0], [-1225]])
'''

mesh = {
    'E1':
    {'n':[1, 2, 5],
    'x':[0, 10, 10],
    'y':[0, 0, 10]},
    'E2':
    {'n':[4, 1, 5],
    'x':[0, 0, 10],
    'y':[10, 0, 10]},
    'E3':
    {'n':[2, 3, 6],
    'x':[10, 20, 20],
    'y':[0, 0, 10]},
    'E4':
    {'n':[5, 2, 6],
    'x':[10, 10, 20],
    'y':[10, 0, 10]},
    'E5':
    {'n':[4, 5, 8],
    'x':[0, 10, 10],
    'y':[10, 10, 20]},
    'E6':
    {'n':[7, 4, 8],
    'x':[0, 0, 10],
    'y':[20, 10, 20]},
    'E7':
    {'n':[5, 6, 9],
    'x':[10, 20, 20],
    'y':[10, 10, 20]},
    'E8':
    {'n':[8, 5, 9],
    'x':[10, 10, 20],
    'y':[20, 10, 20]},
}

u = [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1]
f = np.array([[0], [0], [0], [0], [0], [0], [50000], [50000]])

for e in mesh:
    print(e)
    element = cst_element(
        mesh[e]['x'],
        mesh[e]['y'],
        mesh[e]['n'],
        210000,
        0.3,
        0.1,
    )

    mesh[e]['data'] = element


node_list = []
for e in mesh:
    for n in mesh[e]['n']:
        if n not in node_list:
            node_list.append(n)

dof = len(node_list) * 2
gsm = global_stiffness_matrix(dof, mesh)
gKr, header = gsm.define()
#header = gsm.matrix_headers

print(header)


'''
for e in mesh:
    print(e)
    element = cst_element(
        mesh[e]['x'][0],
        mesh[e]['x'][1],
        mesh[e]['x'][2],
        mesh[e]['y'][0],
        mesh[e]['y'][1],
        mesh[e]['y'][2],
        30000000,
        0.25,
        0.5,
        mesh[e]['n']
    )

    mesh[e]['data'] = element
    #print(element.K_pos)
    #print(element.gK_pos)
    #print(element.K)
    #print(element.b)
'''

'''
dof = len(node_list) * 2
gK = np.zeros((dof, dof))

for e in mesh:
    eK = mesh[e]['data'].eK
    gK_index = mesh[e]['data'].gK_index 
    for i in range(eK.shape[0]):
        for j in range(eK.shape[1]):
            K_value = eK[i][j]
            K_index = gK_index[i][j]
            K_index_row = int(K_index.split('|')[0])
            K_index_col = int(K_index.split('|')[1])
            gK[K_index_row][K_index_col] = K_value + gK[K_index_row][K_index_col]




gKr = gK

for i in range(len(u)-1, -1, -1):
    if u[i] == 0:
        gKr = np.delete(gKr, i, 0)
        gKr = np.delete(gKr, i, 1)
'''
print('gKr')  
print(tabulate(gKr, tablefmt="grid", stralign='center', headers=header, showindex=header))

r = np.linalg.solve(gKr, f)
print(r)    

