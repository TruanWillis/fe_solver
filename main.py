import json
import os
from importlib.metadata import version
from fe_solver.gui import gui

def load_user_config(filepath: str) -> dict:
    defaults = {
        "print_head": True,
        "save_matrix": True,
        "fe_solver": True,
        "scale": 2,
    }
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            return json.load(f)
    with open(filepath, "w") as f:
        json.dump(defaults, f, indent=4)
    return defaults

APP_CONFIG = {
    "name": "FEsolver",
    "version": version("fe_solver"),
    "disclaimer": (
        "FEsolver is a non-commercial 2D plane-stress finite element solver. "
        "The program is distributed with no warranty."
    ),
}

if __name__ == "__main__":
    config_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "config_user.json")
    user_config = load_user_config(config_path)
    gui.run(app_config=APP_CONFIG, user_config=user_config)


