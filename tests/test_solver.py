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
    d = solved_model_1.odb["node"]["U"].data
    assert round(d.loc["n5", "u"], 2) == round(1.38778e-17, 2)
    assert round(d.loc["n6", "v"], 2) == round(0.943654, 2)
    assert round(d.loc["n6", "u"], 2) == round(-0.23529, 2)

def test_displacement_2(solved_model_2):
    d = solved_model_2.odb["node"]["U"].data
    assert round(d.loc["n5", "u"], 3) == round(2.74679e-34, 3)
    assert round(d.loc["n5", "v"], 3) == round(0.0149603, 3)

def test_displacement_3(solved_model_3):
    d = solved_model_3.odb["node"]["U"].data
    assert round(d.loc["n4", "u"], 2) == round(0.01117, 2)
    assert round(d.loc["n4", "v"], 2) == round(0.0119, 2)


# --- In-plane stress tests ---

def test_stress_inplane_1(solved_model_1):
    s = solved_model_1.odb["element"]["S"].data
    assert round(s.loc["e1"]["s1"], -1) == round(6923.08, -1)
    assert round(s.loc["e1"]["s2"], -1) == round(23076.9, -1)
    assert round(s.loc["e8"]["s1"], -1) == round(6923.08, -1)
    assert round(s.loc["e8"]["s2"], -1) == round(23076.9, -1)

def test_stress_inplane_2(solved_model_2):
    s = solved_model_2.odb["element"]["S"].data
    assert round(s.loc["e7"]["s1"], 0) == round(39.4538, 0)
    assert round(s.loc["e7"]["s2"], -1) == round(131.513, -1)

def test_stress_inplane_3(solved_model_3):
    s = solved_model_3.odb["element"]["S"].data
    assert round(s.loc["e2"]["s1"], 1) == round(162.464, 1)
    assert round(s.loc["e2"]["s2"], 1) == round(162.314, 1)


# --- Von Mises stress tests ---

def test_stress_mises_1(solved_model_1):
    s = solved_model_1.odb["element"]["SM"].data
    assert round(s.loc["e1", "s_mises"], -1) == round(20511.2, -1)
    assert round(s.loc["e8", "s_mises"], -1) == round(20511.2, -1)

def test_stress_mises_2(solved_model_2):
    s = solved_model_2.odb["element"]["SM"].data
    assert round(s.loc["e8", "s_mises"], -1) == round(170.328, -1)

def test_stress_mises_3(solved_model_3):
    s = solved_model_3.odb["element"]["SM"].data
    assert round(s.loc["e2", "s_mises"], 1) == round(174.972, 1)
