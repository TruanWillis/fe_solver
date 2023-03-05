import load_inp
import solver
import plot
from tabulate import tabulate

import gui

if __name__ == '__main__':
    #inp = load_inp.load_inp("inp/Job-7.inp")
    #model = load_inp.call_gen_function(inp)
    #s = solver.solver(model)
    #s.define_element_stiffness()
    #s.define_global_stiffness()
    #s.define_boundary()
    #s.define_load()
    #s.reduce_matrix()
    #s.compute_dispalcements()
    #s.compute_normal_stress()
    #s.compute_principal_stress()
    #s.compute_mises_stress()
    
    #print(tabulate(s.norm_stress_df.head(), tablefmt="grid", numalign="right", headers=s.norm_stress_df.columns))
    #print(tabulate(s.princ_stress_df.head(), tablefmt="grid", numalign="right", headers=s.princ_stress_df.columns))
    #print(tabulate(s.mises_stress_df.head(), tablefmt="grid", numalign="right", headers=s.mises_stress_df.columns))
    
    #plot.plot_results(model, s, 2)

    gui.run()
  
