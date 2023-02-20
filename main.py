import load_inp
import solver
import plot
from tabulate import tabulate


if __name__ == '__main__':
    inp = load_inp.load_inp("Job-2.inp")
    model = load_inp.call_gen_function(inp)
    s = solver.solver(model)
    s.define_boundary()
    s.define_load()
    s.define_element_stiffness()
    s.define_global_stiffness()
    s.compute_dispalcements()
    s.compute_principal_stress()
    s.compute_mises_stress()
    #print(tabulate(s.gKr, tablefmt="grid", stralign='center', headers=s.matrix_headers_r, showindex=s.matrix_headers_r))
    #print(tabulate([list(s.displacements)], tablefmt="grid", stralign="center", headers=s.matrix_headers_r))    
    #print(tabulate(s.principal_stress_results, tablefmt="grid", stralign="center", headers=["el", "s1", "s2", "s12"]))
    #print(tabulate(s.mises_stress_results, tablefmt="grid", stralign="center", headers=["el", "mises"]))
    plot.plot_mises(model, s.mises_stress_results, s.u, 2)
  
