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
    s.compute_dispalcements()
    print(tabulate(s.gKr, tablefmt="grid", stralign='center', headers=s.matrix_headers_r, showindex=s.matrix_headers_r))
    print(tabulate([list(s.displacements)], tablefmt="grid", stralign="center", headers=s.matrix_headers_r))    
    
