import os
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


class gen_model:
    def __init__(self):
        self.model={}
        self.model["elements"] = {}
        self.model["nodes"] = {}
        self.model["nodesets"] = {}
        self.model["elementsets"] = {}
        self.model["section"] = {}

    def gen_element(self, input):    
        element_type = input[0].split("=")[1].lower()
        self.model["elements"]["type"] = element_type
        for line in input[1:]:
            split_line = line.split(",")
            element = int(split_line[0])
            self.model["elements"][element] = []
            for node in range(1, len(split_line)):
                self.model["elements"][element].append(int(split_line[node]))


    def gen_node(self, input):
        for line in input[1:]:
            split_line = line.split(",")
            self.model["nodes"][int(split_line[0])] = [
                float(split_line[1]),
                float(split_line[2]),
            ]


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


    def gen_material(self, keyword):
        print(keyword)
        self.model["material"] = keyword


    def gen_material_elasticity(self, keyword):
        print(keyword)
        self.model["elasticity"] = keyword


    def gen_boundary(self, keyword):
        print(keyword)
        self.model["boundary"] = keyword


    def gen_load(self, keyword):
        print(keyword)
        self.model["load"] = keyword


def call_gen_function(model, inp_lines):
    line_count = 0
    for line in inp_lines:
        if line[0] == '*' and line[1] != '*':
            keyword = line.split("*")[1].split(",")[0].strip("\n").lower()
            #keyword = keyword.strip("\n")
            #print(keyword, len(keyword))
            if keyword in keywords.keys():
                #print(keyword)
                keyword_inputs = [line.strip('\n')]
                line_count_temp = line_count + 1
                while "*" not in inp_lines[line_count_temp]:
                    keyword_inputs.append(inp_lines[line_count_temp].strip('\n'))
                    line_count_temp += 1
                function = getattr(model, keywords[keyword])
                function(keyword_inputs)
        line_count += 1


def load_inp(file):
    with open(wk_dir + '/' + file) as inp_file:
        inp_lines = inp_file.readlines()
    return inp_lines


if __name__ == "__main__":
    model = gen_model()
    inp_file = load_inp("Job-1.inp")
    call_gen_function(model, inp_file)
    print(model.__dict__["model"])
