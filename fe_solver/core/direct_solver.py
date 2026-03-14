import pandas as pd
import numpy as np


class gaussianElimination:
    def __init__(self, stiffness, force):
        """
        Initiates gaussianElimination class object.

        Args:
            stiffness (dataframe): Global stiffness matrix.
            force (series): Applied nodal forces.
        """

        self.stiffness = stiffness
        self.force = force
        
        self.forward_elimination()
        self.back_subtract()

    def forward_elimination(self):
        for i in range(len(self.force)):
            # TODO: add partial pivot to avoid zero pivot failure
            pivot = self.stiffness[i, i]
            for j in range(i + 1, len(self.force)):
                factor = self.stiffness[j, i] / pivot
                # Update the row: Row_j = Row_j - (factor * Row_i)
                self.stiffness[j, i:] = self.stiffness[j, i:] - factor * self.stiffness[i, i:]
                self.force[j] = self.force[j] - factor * self.force[i]

    def back_subtract(self):
        self.displacements = np.zeros(len(self.force))

        for i in range(len(self.force) - 1, -1, -1):
            # sum(K_ij * u_j) for all j > i
            sum_knowns = np.dot(self.stiffness[i, i + 1:], self.displacements[i + 1:])
            # u_i = (F_i - sum_knowns) / K_ii
            self.displacements[i] = (self.force[i] - sum_knowns) / self.stiffness[i, i]

    # TODO: Add multi-proccess functionallity to forward_elimination


if __name__ == "__main__":
    """
    __main__ for development purposes.
    """

    matrix = [[3, 4, 2, 45], [6, 2, 3, 59], [2, 7, 4, 66]]

    stiffness = [i[:-1] for i in matrix]
    force = [i[-1] for i in matrix]

    index = ["x1", "x2", "x3"]

    stiffness_df = pd.DataFrame(stiffness, index=index, columns=index)
    force_df = pd.Series(force, index=index)
    gE = gaussianElimination(stiffness_df, force_df)
    print(gE.displacements.head())
