import load_inp


if __name__ == '__main__':
    inp_file = load_inp.load_inp("Job-1.inp")
    model = load_inp.call_gen_function(inp_file)
    print(model)
