import model
import numpy as np
import pandas as pd
import os


class element:
    def __init__(self, element_type, x_cord, y_cord, node_list, E, v, t):
        """
        Initiates element class object.

        Args:
            x_cord (list): Element node x axis coordinates.
            y_cord (list): Element node y axis coordinates.
            node_list (list): Element node numbers.
            E (int): Young's Modulus .
            v (int): Poisson's ratio.
            t (int): Shell thickness.
        """

        x_cord += [0] * 30
        y_cord += [0] * 30

        element_library = {
            "s3": {
                "area": [
                    [1, x_cord[0], y_cord[0]],
                    [1, x_cord[1], y_cord[1]],
                    [1, x_cord[2], y_cord[2]],
                ],
                "shape_functions": {
                    "b1": y_cord[1] - y_cord[2],
                    "b2": y_cord[2] - y_cord[0],
                    "b3": y_cord[0] - y_cord[1],
                    "c1": x_cord[2] - x_cord[1],
                    "c2": x_cord[0] - x_cord[2],
                    "c3": x_cord[1] - x_cord[0],
                },
                "strain_displacement": [
                    ["b1", 0, "b2", 0, "b3", 0],
                    [0, "c1", 0, "c2", 0, "c3"],
                    ["c1", "b1", "c2", "b2", "c3", "b3"],
                ],
                "stress_strain": [[1, v, 0], [v, 1, 0], [0, 0, (1 - v) / 2]],
            }
        }

        self.element_structure = element_library[element_type]
        self.node_list = node_list

        self.E = float(E)
        self.v = float(v)
        self.t = float(t)

        self.calculate_area()
        self.strain_displacement_matrix()
        self.stress_strain_matrix()
        self.stiffness_matrix()

    def calculate_area(self):
        """
        Calculates element area.
        """

        area = np.array(self.element_structure["area"])
        self.area = np.linalg.det(area) * 0.5

    def strain_displacement_matrix(self):
        """
        Defines the strain-displacement matrix [B] as a numpy array.
        """

        B = self.element_structure["strain_displacement"]
        for row in range(0, len(B)):
            for col in range(0, len(B[row])):
                if B[row][col] != 0:
                    B[row][col] = self.element_structure["shape_functions"][B[row][col]]

        B = np.array(B)
        self.B = B * (1 / (2 * self.area))

    def stress_strain_matrix(self):
        """
        Defines stress-stain matrix [D] as numpy array.
        """

        D = np.array(self.element_structure["stress_strain"])
        self.D = D * (self.E / (1 - self.v**2))

    def stiffness_matrix(self):
        """
        Defines element stiffness matrix [K] as a pandas dataFrame
        """

        Bt = self.B.transpose()
        element_stiffness = (
            np.matmul(Bt, np.matmul(self.D, self.B)) * self.area * self.t
        )

        node_headings = []
        for n in self.node_list:
            for displacement in ["u", "v"]:
                node_headings.append(str(n) + displacement)

        self.element_stiffness_matrix = pd.DataFrame(
            element_stiffness, columns=node_headings, index=node_headings
        )


if __name__ == "__main__":
    """
    __main__ used for development purposes.
    """

    wk_dir = os.path.dirname(os.path.realpath(__file__))
    input = model.load_input(wk_dir + "/inp/plate_simple_disp.inp")
    test_model = model.call_gen_function(input)
    node_list = test_model["elements"][1]["nodes"]
    x_cord = []
    y_cord = []
    for node in node_list:
        x_cord.append(test_model["nodes"][node][0])
        y_cord.append(test_model["nodes"][node][1])

    cst = element(
        "s3",
        x_cord,
        y_cord,
        node_list,
        test_model["elasticity"][0],
        test_model["elasticity"][1],
        test_model["section"]["thickness"],
    )

    print(cst.area)

