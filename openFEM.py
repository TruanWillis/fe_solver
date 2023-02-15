import numpy as np

element = np.array([[0,0], [20,0], [0,30]])

class cst_element:
    def __init__(self, x1, x2, x3, y1, y2, y3, E, v, t):
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

        b = np.array([
            [b1, 0, b2, 0, b3, 0],
            [0, c1, 0, c2, 0, c3],
            [c1, b1, c2, b2, c3, b3]
        ])

        self.B = b * (1/(2*self.A))

        d = np.array([
            [1, v, 0],
            [v, 1, 0],
            [0, 0, (1-v)/2]
        ])

        self.D = d * (E/(1-v**2))

        Bt = self.B.transpose()
        k = np.matmul(Bt, self.D)
        self.K = np.matmul(k, self.B)
        self.K = self.K * self.A * t

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
        0.5
    )

    print(element.K)