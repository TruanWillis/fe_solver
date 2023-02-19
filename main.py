import load_inp
import solver
import numpy as np
from tabulate import tabulate


if __name__ == '__main__':
    inp = load_inp.load_inp("Job-1.inp")
    model = load_inp.call_gen_function(inp)
    s = solver.solver(model)
    s.define_boundary()
    s.define_load()
    s.define_element_stiffness()
    s.define_global_stiffness()
    global_matrix, headers, displacements = s.compute_dispalcements()
    print(tabulate(global_matrix, tablefmt="grid", stralign='center', headers=headers, showindex=headers))
    print(tabulate([list(displacements)], tablefmt="grid", stralign="center", headers=headers))    
    
