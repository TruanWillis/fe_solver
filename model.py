import os
import pprint

wk_dir = os.path.dirname(os.path.realpath(__file__))

keywords = {
    "node":"gen_node", 
    "element":"gen_element", 
    "nset":"gen_node_set", 
    "elset":"gen_element_set", 
    "shell section":"gen_shell_section", 
    "material":"gen_material", 
    "elastic":"gen_material_elasticity", 
    "boundary":"gen_boundary", 
    "cload":"gen_load"
}


class generateModel:
    def __init__(self):
        self.model={}
        self.model["elements"] = {}
        self.model["nodes"] = {}
        self.model["nodesets"] = {}
        self.model["elementsets"] = {}
        self.model["section"] = {}
        self.model["material"] = {}
        self.model["elasticity"] = []
        self.model["boundary"] = {}
        self.model["load"] = {}


    def strip_input(self, input):
        output = [value.replace(" ", "") for value in input]
        return output


    def gen_element(self, input): 
        element_type = input[0].split("=")[1].lower()
        for line in input[1:]:
            split_line = line.split(",")
            element = int(split_line[0])
            self.model["elements"][element] = {}
            node_list = []
            for node in range(1, len(split_line)):
                node_list.append(int(split_line[node]))
            self.model["elements"][element]["nodes"] = node_list
            self.model["elements"][element]["type"] = element_type
        self.model["element count"] = int(len(self.model["elements"].keys()))
    

    def gen_node(self, input):
        for line in input[1:]:
            split_line = line.split(",")
            self.model["nodes"][int(split_line[0])] = [
                float(split_line[1]),
                float(split_line[2]),
            ]
        self.model["node count"] = int(len(self.model["nodes"].keys()))
        self.model["dof"] = int(len(self.model["nodes"].keys()) * 2)
        

    def gen_node_set(self, input):
        split_first_line = input[0].split(",")
        set_name = split_first_line[1].split("=")[1].strip()
        self.model["nodesets"][set_name] = []
        for line in input[1:]:
            nodes = line.split(",")
            if len(split_first_line) == 2:
                for node in nodes:
                    try:
                        node = int(node.strip())
                        self.model["nodesets"][set_name].append(node)
                    except:
                        pass
            elif len(split_first_line) == 3:
                start = int(nodes[0].strip()) 
                end = int(nodes[1].strip())
                inc = int(nodes[2].strip())
                for node in range(start, end+inc, inc):
                    self.model["nodesets"][set_name].append(node)


    def gen_element_set(self, input):
        split_first_line = input[0].split(",")
        set_name = split_first_line[1].split("=")[1].strip()
        self.model["elementsets"][set_name] = []
        for line in input[1:]:
            elements = line.split(",")
            if len(split_first_line) == 2:
                for element in elements:
                    try:
                        element = int(element.strip())
                        self.model["elementsets"][set_name].append(element)
                    except:
                        pass
            elif len(split_first_line) == 3:
                start = int(elements[0].strip()) 
                end = int(elements[1].strip())
                inc = int(elements[2].strip())
                for element in range(start, end+inc, inc):
                    self.model["elementsets"][set_name].append(element)
                

    def gen_shell_section(self, input):
        split_first_line = input[0].split(",")
        for item in split_first_line:
            if "elset" in item.lower():
                self.model["section"]["elementset"] = item.split("=")[1]
            elif "material" in item.lower():   
                self.model["section"]["material"] = item.split("=")[1]
        thickness = self.strip_input(input[1].split(","))[0]
        self.model["section"]["thickness"] = thickness


    def gen_material(self, input):
        materail_name = input[0].split("=")[1].strip("\n")
        self.model["material"][materail_name] = {}


    def gen_material_elasticity(self, input):
        for value in input[1].split(","):
            value = float(value.strip().strip("\n"))
            self.model["elasticity"].append(value)


    def gen_boundary(self, input):
        for line in input[1:]:
            values = line.split(",")
            values = self.strip_input(values)
            try:
                node = int(values[0])
            except:
                node = values[0]
            if node not in self.model["boundary"]:
                self.model["boundary"][node] = {}
            if values[1] == values[2]:
                if int(values[1]) < 3:
                    if len(values) == 3:
                        self.model["boundary"][node][values[1]] = 0.
                    elif len(values) == 4: 
                        self.model["boundary"][node][values[1]] = float(values[3])


    def gen_load(self, input):
        for line in input[1:]:
            values = line.split(",")
            values = self.strip_input(values)
            try:
                node = int(values[0])
            except:
                node = values[0]
            if node not in self.model["load"]:
                self.model["load"][node] = {}
            if int(values[1]) < 3:
                self.model["load"][node][values[1]] = float(values[2])
                

def call_gen_function(inp_file):
    model = generateModel()
    for line_count, line in enumerate(inp_file):
        if line[0] == '*' and line[1] != '*':
            keyword = line.split("*")[1].split(",")[0].strip("\n").lower()
            if keyword in keywords.keys():
                keyword_inputs = [line.strip('\n')]
                line_count_temp = line_count + 1
                while "*" not in inp_file[line_count_temp]:
                    keyword_inputs.append(inp_file[line_count_temp].strip('\n'))
                    line_count_temp += 1
                function = getattr(model, keywords[keyword])
                function(keyword_inputs)
    return model.__dict__["model"]


def load_input(file):
    with open(file) as input_file:
        input_lines = input_file.readlines()
    return input_lines


if __name__ == "__main__":
    input_file = load_input(wk_dir + "/inp/Job-3.inp")
    model = call_gen_function(input_file)
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(model)
