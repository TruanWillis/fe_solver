import unittest
import json
import model
import os
import pickle


wk_dir = os.path.dirname(os.path.realpath(__file__))


class Tests(unittest.TestCase):
    def test_model_1(self):
        with open(wk_dir + "/test_data/test_model_1.pickle", "rb") as test_file:
            test_data = pickle.load(test_file)
        
        input = model.load_input(wk_dir + "/test_data/test_input_1.inp")
        test_model = model.call_gen_function(input)                   
        
        self.assertEqual(
            test_model,
            test_data,
        )


    def test_model_2(self):
        with open(wk_dir + "/test_data/test_model_2.pickle", "rb") as test_file:
            test_data = pickle.load(test_file)
        
        input = model.load_input(wk_dir + "/test_data/test_input_2.inp")
        test_model = model.call_gen_function(input)                   
        
        self.assertEqual(
            test_model,
            test_data,
        )


    def test_model_3(self):
        with open(wk_dir + "/test_data/test_model_3.pickle", "rb") as test_file:
            test_data = pickle.load(test_file)
        
        input = model.load_input(wk_dir + "/test_data/test_input_3.inp")
        test_model = model.call_gen_function(input)                   
        
        self.assertEqual(
            test_model,
            test_data,
        )

if __name__ == "__main__":
    unittest.main()
