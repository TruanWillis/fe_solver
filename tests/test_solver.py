import pytest
from pathlib import Path
from fe_solver.core import model, solver

FIXTURES = Path(__file__).parent / "fixtures"


# --- Fixtures ---

@pytest.fixture
def solved_model_1():
    inp = model.load_input(FIXTURES / "test_input_1.inp")
    m = model.call_gen_function(inp)
    return solver.Solver(m, True, False, False, Path(""))

@pytest.fixture
def solved_model_2():
    inp = model.load_input(FIXTURES / "test_input_2.inp")
    m = model.call_gen_function(inp)
    return solver.Solver(m, True, False, False, Path(""))

@pytest.fixture
def solved_model_3():
    inp = model.load_input(FIXTURES / "test_input_3.inp")
    m = model.call_gen_function(inp)
    return solver.Solver(m, True, False, False, Path(""))


# --- Model generation tests ---

def test_model_generation_1():
    import pickle
    with open(FIXTURES / "test_model_1.pickle", "rb") as f:
        expected = pickle.load(f)
    inp = model.load_input(FIXTURES / "test_input_1.inp")
    assert model.call_gen_function(inp) == expected

def test_model_generation_2():
    import pickle
    with open(FIXTURES / "test_model_2.pickle", "rb") as f:
        expected = pickle.load(f)
    inp = model.load_input(FIXTURES / "test_input_2.inp")
    assert model.call_gen_function(inp) == expected

def test_model_generation_3():
    import pickle
    with open(FIXTURES / "test_model_3.pickle", "rb") as f:
        expected = pickle.load(f)
    inp = model.load_input(FIXTURES / "test_input_3.inp")
    assert model.call_gen_function(inp) == expected


# --- Displacement tests ---

def test_displacement_1(solved_model_1):
    d = solved_model_1.displacements
    assert round(d["5u"], 2) == round(1.38778e-17, 2)
    assert round(d["6v"], 2) == round(0.943654, 2)
    assert round(d["6u"], 2) == round(-0.23529, 2)

def test_displacement_2(solved_model_2):
    d = solved_model_2.displacements
    assert round(d["5u"], 3) == round(2.74679e-34, 3)
    assert round(d["5v"], 3) == round(0.0149603, 3)

def test_displacement_3(solved_model_3):
    d = solved_model_3.displacements
    assert round(d["4u"], 2) == round(0.01117, 2)
    assert round(d["4v"], 2) == round(0.0119, 2)


# --- In-plane stress tests ---

def test_stress_inplane_1(solved_model_1):
    s = solved_model_1.stress_normal
    assert round(s["s1"]["e1"], -1) == round(6923.08, -1)
    assert round(s["s2"]["e1"], -1) == round(23076.9, -1)
    assert round(s["s1"]["e8"], -1) == round(6923.08, -1)
    assert round(s["s2"]["e8"], -1) == round(23076.9, -1)

def test_stress_inplane_2(solved_model_2):
    s = solved_model_2.stress_normal
    assert round(s["s1"]["e7"], 0) == round(39.4538, 0)
    assert round(s["s2"]["e7"], -1) == round(131.513, -1)

def test_stress_inplane_3(solved_model_3):
    s = solved_model_3.stress_normal
    assert round(s["s1"]["e2"], 1) == round(162.464, 1)
    assert round(s["s2"]["e2"], 1) == round(162.314, 1)


# --- Von Mises stress tests ---

def test_stress_mises_1(solved_model_1):
    s = solved_model_1.stress_mises
    assert round(s["s_mises"]["e1"], -1) == round(20511.2, -1)
    assert round(s["s_mises"]["e8"], -1) == round(20511.2, -1)

def test_stress_mises_2(solved_model_2):
    s = solved_model_2.stress_mises
    assert round(s["s_mises"]["e8"], -1) == round(170.328, -1)

def test_stress_mises_3(solved_model_3):
    s = solved_model_3.stress_mises
    assert round(s["s_mises"]["e2"], 1) == round(174.972, 1)
