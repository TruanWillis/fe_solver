import json
import os

import gui

config = {
    "name": "FEsolver",
    "version": "0.1.0",
    "disclaimer": (
        "FEsolver is a non-commercial 2D plane-stress finite element solver. "
        "The program is distributed with no warranty."
    ),
    "history": {"0.0.1": "First release", "0.1.0": "FEsolver direct solver added"},
}

config_user = {
    "print_head": True,
    "save_matrix": True,
    "fe_solver": True,  # False dafults to numpy
    "scale": 2,
}

config_user_filepath = os.path.dirname(os.path.realpath(__file__)) + "/config_user.json"

if __name__ == "__main__":
    if os.path.exists(config_user_filepath):
        with open(config_user_filepath, "r") as config_user_file:
            config_user = json.load(config_user_file)

    else:
        with open(config_user_filepath, "w") as config_user_file:
            json.dump(config_user, config_user_file, indent=4)

    config.update(config_user)
    gui.run(config)
