import model
import numpy as np
import pandas as pd
import os


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
        element_stiffness = np.matmul(Bt, np.matmul(self.D, self.B)) * self.area * self.t 

        node_headings = []
        for n in self.node_list:
            for displacement in ['u', 'v']:
                node_headings.append(str(n) + displacement)

        self.element_stiffness_matrix = pd.DataFrame(
            element_stiffness,
            columns=node_headings,
            index=node_headings
        )


if __name__ == "__main__":
    wk_dir = os.path.dirname(os.path.realpath(__file__))
    input = model.load_input(wk_dir + "/inp/Job-7.inp")
    test_model = model.call_gen_function(input)
    node_list = test_model["elements"][1]["nodes"]
    x_cord = []
    y_cord = []
    for node in node_list:
        x_cord.append(test_model["nodes"][node][0])
        y_cord.append(test_model["nodes"][node][1])
            
    cst = cst_element(
        x_cord,
        y_cord,
        node_list,
        test_model["elasticity"][0],
        test_model["elasticity"][1],
        test_model["section"]["thickness"]
    )
    
    print(cst.area)
    