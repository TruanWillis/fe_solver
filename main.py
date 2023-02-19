import load_inp
import solver
import numpy as np
from tabulate import tabulate


if __name__ == '__main__':
    inp_file = load_inp.load_inp("Job-1.inp")
    model = load_inp.call_gen_function(inp_file)
    print(model)
    model = solver.define_element_stiffness(model)
    s = solver.solver(model)
    s.define_boundary()
    print(s.u)
    s.define_load()
    print(s.f)
    print(model["elements"])
    K = solver.global_stiffness_matrix(s.dof, model)
    gK, gKr, header = K.define()
    displacements = np.linalg.solve(gKr, s.f)


    print(tabulate(gKr, tablefmt="grid", stralign='center', headers=header, showindex=header))
    #print(tabulate(gK, tablefmt="grid", stralign='center'))
    print(tabulate(displacements))    
