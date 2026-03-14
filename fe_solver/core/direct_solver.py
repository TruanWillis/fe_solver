import numpy as np


class GaussianElimination:
    def __init__(self, stiffness, force):
        """
        Initiates GaussianElimination class object.

        Args:
            stiffness (numpy array): Global stiffness matrix.
            force (numpy array): Applied nodal forces.
        """

        self.stiffness = stiffness.astype("float64")
        self.force = force.astype("float64")
        self.run()

    def forward_elimination(self):
        for i in range(len(self.force)):
            self.partial_pivot(i)
            pivot = self.stiffness[i, i]
            for j in range(i + 1, len(self.force)):
                factor = self.stiffness[j, i] / pivot
                # Update the row: Row_j = Row_j - (factor * Row_i)
                self.stiffness[j, i:] = (
                    self.stiffness[j, i:] - factor * self.stiffness[i, i:]
                )
                self.force[j] = self.force[j] - factor * self.force[i]

    def back_subtract(self):
        self.displacements = np.zeros(len(self.force))
        for i in range(len(self.force) - 1, -1, -1):
            # sum(K_ij * u_j) for all j > i
            sum_knowns = np.dot(self.stiffness[i, i + 1 :], self.displacements[i + 1 :])
            # u_i = (F_i - sum_knowns) / K_ii
            self.displacements[i] = (self.force[i] - sum_knowns) / self.stiffness[i, i]

    def partial_pivot(self, i):
        max_row = np.argmax(np.abs(self.stiffness[i:, i])) + i
        if max_row != i:
            self.stiffness[[i, max_row]] = self.stiffness[[max_row, i]]
            self.force[[i, max_row]] = self.force[[max_row, i]]

    def run(self):
        self.forward_elimination()
        self.back_subtract()

    # TODO: Add multi-proccess functionallity to forward_elimination


if __name__ == "__main__":
    """
    __main__ for development purposes.
    """

    matrix = [[3, 4, 2, 45], [6, 2, 3, 59], [2, 7, 4, 66]]

    stiffness = np.array([i[:-1] for i in matrix])
    force = np.array([i[-1] for i in matrix])

    ge = GaussianElimination(stiffness, force)
    print(ge.displacements)
    print(np.linalg.solve(stiffness, force))
