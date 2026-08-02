import json
import numpy as np
import pprint
import pickle
from pathlib import Path


keywords = {
    "node": "gen_node",
    "element": "gen_element",
    "nset": "gen_node_set",
    "elset": "gen_element_set",
    "shell section": "gen_shell_section",
    "material": "gen_material",
    "elastic": "gen_material_elasticity",
    "boundary": "gen_boundary",
    "cload": "gen_load",
}


class ModelBuilder:
    def __init__(self):
        """
        Initiates model class object.
        """

        self.model = {}
        self.model["elements"] = {}
        self.model["nodes"] = {}
        self.model["nodesets"] = {}
        self.model["elementsets"] = {}
        self.model["section"] = {}
        self.model["material"] = {}
        self.model["elasticity"] = []
        self.model["boundary"] = {}
        self.model["load"] = {}

    def strip_input(self, lines):
        """
        Strips white space from nested list of strings.

        Args:
            lines (list): Nested list of strings.
        """

        output = [value.replace(" ", "") for value in lines]
        return output

    def gen_element(self, lines):
        """
        Defines elements.

        Args:
            lines (list): Nested list of strings.
        """

        element_type = lines[0].split("=")[1].lower()
        for line in lines[1:]:
            split_line = line.split(",")
            element = int(split_line[0])
            self.model["elements"][element] = {}
            node_list = []
            for node in range(1, len(split_line)):
                node_list.append(int(split_line[node]))
            self.model["elements"][element]["nodes"] = node_list
            self.model["elements"][element]["type"] = element_type
        self.model["element count"] = int(len(self.model["elements"].keys()))

    def gen_node(self, lines):
        """
        Defines nodes.

        Args:
            lines (list): Nested list of strings.
        """

        for line in lines[1:]:
            split_line = line.split(",")
            self.model["nodes"][int(split_line[0])] = [
                float(split_line[1]),
                float(split_line[2]),
                # TODO: Update to 3D when ready
                # float(split_line[3]),
            ]
        self.model["node count"] = int(len(self.model["nodes"].keys()))
        # TODO: Update to 3D when ready
        self.model["dof"] = int(len(self.model["nodes"].keys()) * 2)

    def gen_node_set(self, lines):
        """
        Defines node set.

        Args:
            lines (list): Nested list of strings.
        """

        split_first_line = lines[0].split(",")
        set_name = split_first_line[1].split("=")[1].strip().lower()
        if set_name not in self.model["nodesets"]:
            self.model["nodesets"][set_name] = []
        for line in lines[1:]:
            nodes = line.split(",")
            if "generate" in lines[0]:
                start = int(nodes[0].strip())
                end = int(nodes[1].strip())
                inc = int(nodes[2].strip())
                for node in range(start, end + inc, inc):
                    if node not in self.model["nodesets"][set_name]:
                        self.model["nodesets"][set_name].append(node)
            else:
                for node in nodes:
                    try:
                        node = int(node.strip())
                        if node not in self.model["nodesets"][set_name]:
                            self.model["nodesets"][set_name].append(node)
                    except Exception:
                        pass

    def gen_element_set(self, lines):
        """
        Defines element set.

        Args:
            lines (list): Nested list of strings.
        """

        split_first_line = lines[0].split(",")
        set_name = split_first_line[1].split("=")[1].strip().lower()
        if set_name not in self.model["elementsets"]:
            self.model["elementsets"][set_name] = []
        for line in lines[1:]:
            elements = line.split(",")
            if "generate" in lines[0]:
                start = int(elements[0].strip())
                end = int(elements[1].strip())
                inc = int(elements[2].strip())
                for element in range(start, end + inc, inc):
                    if element not in self.model["elementsets"][set_name]:
                        self.model["elementsets"][set_name].append(element)
            else:
                for element in elements:
                    try:
                        element = int(element.strip())
                        if element not in self.model["elementsets"][set_name]:
                            self.model["elementsets"][set_name].append(element)
                    except Exception:
                        pass

    def gen_shell_section(self, lines):
        """
        Defines shell section properties.

        Args:
            lines (list): Nested list of strings.
        """

        split_first_line = lines[0].split(",")
        for item in split_first_line:
            if "elset" in item.lower():
                self.model["section"]["elementset"] = item.split("=")[1].strip().lower()
            elif "material" in item.lower():
                self.model["section"]["material"] = item.split("=")[1].strip().lower()
        thickness = float(self.strip_input(lines[1].split(","))[0])
        self.model["section"]["thickness"] = thickness

    def gen_material(self, lines):
        """
        Defines material name.

        Args:
            lines (list): Nested list of strings.
        """

        material_name = lines[0].split("=")[1].strip().lower()
        self.model["material"][material_name] = {}

    def gen_material_elasticity(self, lines):
        """
        Defines material properties.

        Args:
            lines (list): Nested list of strings.
        """

        for value in lines[1].split(","):
            value = float(value.strip().strip("\n"))
            self.model["elasticity"].append(value)

    def gen_boundary(self, lines):
        """
        Defines boundary condition.

        Args:
            lines (list): Nested list of strings.
        """

        for line in lines[1:]:
            values = line.split(",")
            values = self.strip_input(values)
            try:
                node = int(values[0])
            except Exception:
                node = values[0].lower()
            if node not in self.model["boundary"]:
                self.model["boundary"][node] = {}
            if values[1] == values[2]:
                if int(values[1]) < 3:
                    if len(values) == 3:
                        self.model["boundary"][node][values[1]] = 0.0
                    elif len(values) == 4:
                        self.model["boundary"][node][values[1]] = float(values[3])

    def gen_load(self, lines):
        """
        Defines applied load.

        Args:
            lines (list): Nested list of strings.
        """

        for line in lines[1:]:
            values = line.split(",")
            values = self.strip_input(values)
            try:
                node = int(values[0])
            except Exception:
                node = values[0].lower()
            if node not in self.model["load"]:
                self.model["load"][node] = {}
            if int(values[1]) < 3:
                self.model["load"][node][values[1]] = float(values[2])

    def gen_solver_maps(self):
        label_to_idx = {}
        #TODO:Update to 3D when ready
        dof_suffixes = ['u', 'v'] 
        # dof_suffixes = ['u', 'v', 'w'] 
        
        count = 0
        for node_id in sorted(self.model['nodes'].keys()):
            for suffix in dof_suffixes:
                label = f"{node_id}{suffix}"
                label_to_idx[label] = count
                count += 1
                
        active_mask = np.ones(self.model['dof'], dtype=bool)

        for key, constraints in self.model['boundary'].items():
            if key in self.model['nodesets']:
                node_list = self.model['nodesets'][key]
            else:
                try:
                    node_list = [int(key)]
                except ValueError:
                    print(f"Warning: Boundary key '{key}' not found in sets or nodes.")
                    continue
            
            for node_id in node_list:
                for dof_key, value in constraints.items():
                    dof_idx = int(dof_key) - 1 
                    suffix = dof_suffixes[dof_idx]
                    label = f"{node_id}{suffix}"
                    
                    if label in label_to_idx:
                        idx = label_to_idx[label]
                        active_mask[idx] = False

        self.model["label_to_idx"] = label_to_idx
        self.model["active_mask"] = active_mask.tolist()


def call_gen_function(inp_file):
    """
    Iterates through inp file lines and generates model.

    Args:
        inp_file (list): Nested list of inp file lines.

    Returns:
        dict: Model attributes.
    """

    model = ModelBuilder()
    for line_count, line in enumerate(inp_file):
        if line[0] == "*" and line[1] != "*":
            keyword = line.split("*")[1].split(",")[0].strip("\n").lower()
            if keyword in keywords.keys():
                keyword_inputs = [line.strip("\n")]
                line_count_temp = line_count + 1
                while "*" not in inp_file[line_count_temp]:
                    keyword_inputs.append(inp_file[line_count_temp].strip("\n"))
                    line_count_temp += 1
                function = getattr(model, keywords[keyword])
                function(keyword_inputs)
    model.gen_solver_maps()
    return model.model


def load_input(file):
    """
    Opens inp file and reads content.

    Args:
        file (.inp): Text file containing keyword arguments to define model.

    Returns:
        list: inp file text lines as list.
    """

    with open(file) as input_file:
        input_lines = input_file.readlines()
    return input_lines


if __name__ == "__main__":
    """
    __main__ used for development purposes.
    """

    test_no = 1
    create_fixture = True

    wk_dir = Path(__file__).resolve().parent.parent.parent
    fixtures_dir = wk_dir / "tests" / "fixtures"

    input_file = load_input(fixtures_dir / f"test_input_{test_no}.inp")
    model = call_gen_function(input_file)
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(model)

    if create_fixture:
        with open(fixtures_dir / f"test_model_{test_no}.json", "w") as outfile:
           json.dump(model, outfile, separators=(',', ':'))

        with open(fixtures_dir / f"test_model_{test_no}.pickle", "wb") as outfile:
           pickle.dump(model, outfile)
