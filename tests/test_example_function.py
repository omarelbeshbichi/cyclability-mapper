from cmm import example_function

def test_example_function_adds_numbers():
    assert example_function(2, 3) == 5
    assert example_function(-1, 1) == 0