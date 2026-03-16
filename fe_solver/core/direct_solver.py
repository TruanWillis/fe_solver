import numpy as np


class GaussianElimination:
    """
    Solves displacements using Gaussian elimination with partial pivoting.

    See: docs/theory.md — Section 7.
    """

    def __init__(self, stiffness, force):
        """
        Args:
            stiffness (np.ndarray): Stiffness matrix.
            force (np.ndarray): Applied nodal forces.
        """
        self.stiffness = stiffness.astype("float64")
        self.force = force.astype("float64")
        self.run()

    def run(self):
        """
        Implements Gaussian elimination via forward elimination and back subtraction.
        Partial pivots are applied before each elimination step.
        """
        self.forward_elimination()
        self.back_subtract()

    def forward_elimination(self):
        """
        Forward elimination reduces stiffness matrix to upper triangular. For each 
        pivot row eliminates all entries below diagonal by subtracting scaled multiple
        for each row.
        """
        for i in range(len(self.force)):
            self.partial_pivot(i)
            pivot = self.stiffness[i, i]
            # TODO: Add multi-process option to inner loop
            for j in range(i + 1, len(self.force)):
                factor = self.stiffness[j, i] / pivot
                self.stiffness[j, i:] = (
                    self.stiffness[j, i:] - factor * self.stiffness[i, i:]
                )
                self.force[j] = self.force[j] - factor * self.force[i]

    def back_subtract(self):
        """
        Solves upper triangular system from the bottom up. Each displacement is
        computed using the solved values for the previously solved values.
        """
        self.displacements = np.zeros(len(self.force))
        for i in range(len(self.force) - 1, -1, -1):
            sum_knowns = np.dot(self.stiffness[i, i + 1 :], self.displacements[i + 1 :])
            self.displacements[i] = (self.force[i] - sum_knowns) / self.stiffness[i, i]

    def partial_pivot(self, i):
        """
        Swaps row i with row containing absolute value in column i. Zeros or very small
        values on the diagonal causes zero division error of numerical amplification.
        """
        max_row = np.argmax(np.abs(self.stiffness[i:, i])) + i
        if max_row != i:
            self.stiffness[[i, max_row]] = self.stiffness[[max_row, i]]
            self.force[[i, max_row]] = self.force[[max_row, i]]




if __name__ == "__main__":
    # __main__ for development purposes.

    matrix = [[3, 4, 2, 45], [6, 2, 3, 59], [2, 7, 4, 66]]
    stiffness = np.array([i[:-1] for i in matrix])
    force = np.array([i[-1] for i in matrix])

    ge = GaussianElimination(stiffness, force)
    np_solution = np.linalg.solve(stiffness.astype('float64'), force.astype('float64'))
    
    print(f"Gaussian elimination: {ge.displacements}")
    print(f"numpy.linalg.solve: {np_solution}") 
