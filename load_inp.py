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
    "boundary":"gen_boundard", 
    "cload":"gen_load"
}


class gen_model:
    def __init__(self):
        self.model={}


    def gen_element(self, keyword):    
        print(keyword)
        self.model["elements"] = keyword
        

    def gen_node(self, keyword):
        print(keyword)
        self.model["nodes"] = keyword


    def gen_node_set(self, keyword):
        print(keyword)
        self.model["nodesets"] = keyword


    def gen_element_set(self, keyword):
        print(keyword)
        self.model["elementsets"] = keyword


    def gen_shell_section(self, keyword):
        print(keyword)
        self.model["section"] = keyword


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
            keyword = line.split("*")[1].split(",")[0].lower()
            if keyword in keywords.keys():
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
