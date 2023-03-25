import unittest
import json
import model
import os
import pickle
import solver


wk_dir = os.path.dirname(os.path.realpath(__file__)) + "/test_data/"


class Tests(unittest.TestCase):
    def test_model_1(self):
        with open(wk_dir + "test_model_1.pickle", "rb") as test_file:
            test_data = pickle.load(test_file)
        
        input = model.load_input(wk_dir + "test_input_1.inp")
        test_model = model.call_gen_function(input)                   
        
        self.assertEqual(
            test_model,
            test_data,
        )


    def test_model_2(self):
        with open(wk_dir + "test_model_2.pickle", "rb") as test_file:
            test_data = pickle.load(test_file)
        
        input = model.load_input(wk_dir + "test_input_2.inp")
        test_model = model.call_gen_function(input)                   
        
        self.assertEqual(
            test_model,
            test_data,
        )


    def test_model_3(self):
        with open(wk_dir + "test_model_3.pickle", "rb") as test_file:
            test_data = pickle.load(test_file)
        
        input = model.load_input(wk_dir + "test_input_3.inp")
        test_model = model.call_gen_function(input)                   
        
        self.assertEqual(
            test_model,
            test_data,
        )


    def test_solver_displacement_1(self):
        input = model.load_input(wk_dir + "test_input_1.inp")
        test_model = model.call_gen_function(input)            
        s = solver.solver(test_model, False, False, "")       
        
        self.assertEqual(
            round(s.__dict__['displacements']['5u'], 2),
            round(1.38778e-17, 2)
        )

        self.assertEqual(
            round(s.__dict__['displacements']['5v'], 2),
            round(1, 2)
        )

        self.assertEqual(
            round(s.__dict__['displacements']['6u'], 2),
            round(-0.23529, 2)
        )

        self.assertEqual(
            round(s.__dict__['displacements']['6v'], 2),
            round(0.943654, 2)
        )
    
    def test_solver_stress_inplane_1(self):
        input = model.load_input(wk_dir + "test_input_1.inp")
        test_model = model.call_gen_function(input)            
        s = solver.solver(test_model, False, False, "")       
        
        self.assertEqual(
            round(s.__dict__['stress_normal']['s1']['e1'], -1),
            round(6923.08, -1)
        )

        self.assertEqual(
            round(s.__dict__['stress_normal']['s2']['e1'], -1),
            round(23076.9, -1)
        )

        self.assertEqual(
            round(s.__dict__['stress_normal']['s1']['e8'], -1),
            round(6923.08, -1)
        )

        self.assertEqual(
            round(s.__dict__['stress_normal']['s2']['e8'], -1),
            round(23076.9, -1)
        )
    
    def test_solver_stress_mises_1(self):
        input = model.load_input(wk_dir + "test_input_1.inp")
        test_model = model.call_gen_function(input)            
        s = solver.solver(test_model, False, False, "")       
        
        self.assertEqual(
            round(s.__dict__['stress_mises']['s_mises']['e1'], -1),
            round(20511.2, -1)
        )

        self.assertEqual(
            round(s.__dict__['stress_mises']['s_mises']['e8'], -1),
            round(20511.2, -1)
        )

    def test_solver_displacement_2(self):
        input = model.load_input(wk_dir + "test_input_2.inp")
        test_model = model.call_gen_function(input)            
        s = solver.solver(test_model, False, False, "")       
        
        self.assertEqual(
            round(s.__dict__['displacements']['5u'], 3),
            round(2.74679e-34, 3)
        )

        self.assertEqual(
            round(s.__dict__['displacements']['5v'], 3),
            round(0.0149603, 3)
        )

    def test_solver_stress_inplane_2(self):
        input = model.load_input(wk_dir + "test_input_2.inp")
        test_model = model.call_gen_function(input)            
        s = solver.solver(test_model, False, False, "")       
        
        self.assertEqual(
            round(s.__dict__['stress_normal']['s1']['e7'], -1),
            round(39.4538, 0)
        )

        self.assertEqual(
            round(s.__dict__['stress_normal']['s2']['e7'], -1),
            round(131.513, -1)
        )

    def test_solver_stress_mises_2(self):
        input = model.load_input(wk_dir + "test_input_2.inp")
        test_model = model.call_gen_function(input)            
        s = solver.solver(test_model, False, False, "")       
        
        self.assertEqual(
            round(s.__dict__['stress_mises']['s_mises']['e8'], -1),
            round(170.328, -1)
        )
    
    def test_solver_displacement_3(self):
        input = model.load_input(wk_dir + "test_input_3.inp")
        test_model = model.call_gen_function(input)            
        s = solver.solver(test_model, False, False, "")       
        
        self.assertEqual(
            round(s.__dict__['displacements']['4u'], 2),
            round(0.729761, 2)
        )

        self.assertEqual(
            round(s.__dict__['displacements']['4v'], 2),
            round(2.0056, 2)
        )

    def test_solver_stress_inplane_3(self):
        input = model.load_input(wk_dir + "test_input_3.inp")
        test_model = model.call_gen_function(input)            
        s = solver.solver(test_model, False, False, "")       
        
        self.assertEqual(
            round(s.__dict__['stress_normal']['s1']['e2'], -1),
            round(-4294.07, -1)
        )

        self.assertEqual(
            round(s.__dict__['stress_normal']['s2']['e2'],-1),
            round(22679.5, -1)
        )

    def test_solver_stress_mises_3(self):
        input = model.load_input(wk_dir + "test_input_3.inp")
        test_model = model.call_gen_function(input)            
        s = solver.solver(test_model, False, False, "")       
        
        self.assertEqual(
            round(s.__dict__['stress_mises']['s_mises']['e2'], -1),
            round(29211.6, -1)
        )


if __name__ == "__main__":
    unittest.main()
