import numpy as np

element = np.array([[0,0], [20,0], [0,30]])

class cst_element:
    def __init__(self, x1, x2, x3, y1, y2, y3, E, v, t, node_list):
        b1 = y2 - y3                                                
        b2 = y3 - y1
        b3 = y1 - y2
        c1 = x3 - x2
        c2 = x1 - x3
        c3 = x2 - x1

        a = np.array([
            [1, x1, y1],
            [1, x2, y2],
            [1, x3, y3]
        ])

        self.A = np.linalg.det(a) * 0.5

        self.b = np.array([
            [b1, 0, b2, 0, b3, 0],
            [0, c1, 0, c2, 0, c3],
            [c1, b1, c2, b2, c3, b3]
        ])

        self.B = self.b * (1/(2*self.A))

        d = np.array([
            [1, v, 0],
            [v, 1, 0],
            [0, 0, (1-v)/2]
        ])

        self.D = d * (E/(1-v**2))

        Bt = self.B.transpose()
        #k = np.matmul(Bt, self.D)
        #self.K = np.matmul(k, self.B)
        #self.K = self.K * self.A * t
        k = np.matmul(self.D, self.B)
        self.K = np.matmul(Bt, k)
        self.K = self.K * self.A * t
        
        
        self.K_pos = np.zeros((6, 6), dtype=object)
        count_1 = 0
        for n1 in node_list:
            count_2 = 0
            for n2 in node_list:
                self.K_pos[count_1][count_2] = str(n1) + str(n2)
                self.K_pos[count_1][count_2 + 1] = str(n1) + str(n2)
                self.K_pos[count_1 + 1][count_2] = str(n1) + str(n2)
                self.K_pos[count_1 + 1][count_2 + 1] = str(n1) + str(n2)
                count_2 += 2
            count_1 += 2

        self.gK_pos = np.zeros((6, 6), dtype=object)
        count_1 = 0
        for n1 in node_list:
            count_2 = 0
            for n2 in node_list:
                origin_row = (n1*2)-2
                origin_col = (n2*2)-2
                self.gK_pos[count_1][count_2] = str(origin_row) + '|' + str(origin_col)
                self.gK_pos[count_1][count_2 + 1] = str(origin_row) + '|' + str(origin_col+1)
                self.gK_pos[count_1 + 1][count_2] = str(origin_row+1) + '|' + str(origin_col)
                self.gK_pos[count_1 + 1][count_2 + 1] = str(origin_row+1) + '|' + str(origin_col+1)
                count_2 += 2
            count_1 += 2
        
        '''
        self.K_pos = np.zeros((6, 6), dtype=object)
        for n1 in node_list:
            for n2 in node_list:
                p1 = n1 * 2
                p2 = n2 * 2
                self.K_pos[p1-2][p2-2] = str(n1) + str(n2)
                self.K_pos[p1-1][p2-2] = str(n1) + str(n2)
                self.K_pos[p1-2][p2-1] = str(n1) + str(n2)
                self.K_pos[p1-1][p2-1] = str(n1) + str(n2)
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
    print(element.K)
    print(element.b)


node_list = []
for e in mesh:
    for n in mesh[e]['n']:
        if n not in node_list:
            node_list.append(n)

dof = len(node_list) * 2
#print(dof)
gK = np.zeros((dof, dof))
#print(gK)


for e in mesh:
    print(mesh[e]['data'].K)
    eK = mesh[e]['data'].K
    gK_pos = mesh[e]['data'].gK_pos 
    for i in range(eK.shape[0]):
        for j in range(eK.shape[1]):
            K_value = eK[i][j]
            K_pos = gK_pos[i][j]
            K_pos_row = int(K_pos.split('|')[0])
            K_pos_col = int(K_pos.split('|')[1])
            gK[K_pos_row][K_pos_col] = K_value + gK[K_pos_row][K_pos_col]

#print('gK')
#print(gK)

u = [1, 0, 1, 1, 0, 0, 0, 0]
for i in range(gK.shape[0]):
    for j in range(gK.shape[1]):
        gK[i][j] = gK[i][j] * u[i]    
        gK[i][j] = gK[i][j] * u[j]    

gKr = gK
print(len(u))
for i in range(len(u)-1, 0, -1):
    print(i)
    if u[i] == 0:
        gKr = np.delete(gKr, i, 0)
        gKr = np.delete(gKr, i, 1)


#print('gK')  
#print(gK)

print('gKr')  
print(gKr)

#k_new = np.dot(gK, u)
#k_new = np.matmul(gK, u)
#print('K_new')
#print(k_new)
f = np.array([[0], [0], [-1225]])
r = np.linalg.solve(gKr, f)
print(r)    

