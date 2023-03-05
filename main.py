import gui

if __name__ == '__main__':
    version = "0.0.1"
    disclaimer = (
        "FEsolver is a non-commercial finite element solver. "
        "The program is distributed with no warranty."
    )
    solver_print_head = True
    
    gui.run(
        version,
        disclaimer,
        solver_print_head
        )
  
