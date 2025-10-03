import pytest

from toig_on_toig import BaseToigOnToigTest
from ici import Interpreter as ICI
from stm import Interpreter as STM

@pytest.mark.parametrize(
    "set_interpreter",
    [ICI, STM], ids=["ici", "stm"],
    indirect=True)
class TestUtilities(BaseToigOnToigTest):
    def test_is_space(self):
        assert self.go(r""" is_space(" ") """) == True
        assert self.go(r""" is_space("\n") """) == True
        assert self.go(r""" is_space("a") """) == False

    def test_is_digit(self):
        assert self.go(r""" is_digit("0") """) == True
        assert self.go(r""" is_digit("1") """) == True
        assert self.go(r""" is_digit("9") """) == True
        assert self.go(r""" is_digit(" ") """) == False
        assert self.go(r""" is_digit("A") """) == False

    def test_is_alphabet(self):
        assert self.go(r""" is_alphabet("a") """) == True
        assert self.go(r""" is_alphabet("z") """) == True
        assert self.go(r""" is_alphabet("A") """) == True
        assert self.go(r""" is_alphabet("Z") """) == True
        assert self.go(r""" is_alphabet("_") """) == False
        assert self.go(r""" is_alphabet("0") """) == False
        assert self.go(r""" is_alphabet(" ") """) == False

    def test_is_name_first(self):
        assert self.go(r""" is_name_first("a") """) == True
        assert self.go(r""" is_name_first("z") """) == True
        assert self.go(r""" is_name_first("A") """) == True
        assert self.go(r""" is_name_first("Z") """) == True
        assert self.go(r""" is_name_first("_") """) == True
        assert self.go(r""" is_name_first("0") """) == False
        assert self.go(r""" is_name_first("#") """) == False
        assert self.go(r""" is_name_first(" ") """) == False

    def test_is_name_rest(self):
        assert self.go(r""" is_name_rest("a") """) == True
        assert self.go(r""" is_name_rest("z") """) == True
        assert self.go(r""" is_name_rest("A") """) == True
        assert self.go(r""" is_name_rest("Z") """) == True
        assert self.go(r""" is_name_rest("_") """) == True
        assert self.go(r""" is_name_rest("0") """) == True
        assert self.go(r""" is_name_rest("#") """) == False
        assert self.go(r""" is_name_rest(" ") """) == False

    def test_contains(self):
        assert self.go(r""" contains("a", []) """) == False
        assert self.go(r""" contains("a", [1, None, "b", False, []]) """) == False
        assert self.go(r""" contains("a", [1, None, "b", False, "a"]) """) == True

@pytest.mark.parametrize(
    "set_interpreter",
    [ICI, STM], ids=["ici", "stm"],
    indirect=True)
class TestScanner(BaseToigOnToigTest):
    def test_whitespace(self):
        assert self.go(r""" scan('') """) == ["$EOF"]
        assert self.go(r""" scan(' 5 ') """) == [5, "$EOF"]
        assert self.go(r""" scan('
            5
        ') """) == [5, "$EOF"]

    def test_primary(self):
        assert self.go(r""" scan('None True False 5 56') """) == [None, True, False, 5, 56, "$EOF"]

    def test_raw_string(self):
        assert self.go(r""" scan("''") """) == [["$STR", ""], "$EOF"]
        assert self.go(r""" scan("'abc'") """) == [["$STR", "abc"], "$EOF"]
        assert self.go(r""" scan("'\\'") """) == [["$STR", "\\"], "$EOF"]

    def test_string(self):
        assert self.go(r""" scan('""') """) == [["$STR", ""], "$EOF"]
        assert self.go(r""" scan('"abc"') """) == [["$STR", "abc"], "$EOF"]
        assert self.go(r""" scan('"\\\n\""') """) == [["$STR", "\\\n\""], "$EOF"]

@pytest.mark.parametrize(
    "set_interpreter",
    [ICI, STM], ids=["ici", "stm"],
    indirect=True)
class TestInterpreter(BaseToigOnToigTest):
    def test_primary(self):
        assert self.go(r""" go('None') """) == None
        assert self.go(r""" go('True') """) == True
        assert self.go(r""" go('False') """) == False
        assert self.go(r""" go('5') """) == 5

    def test_raw_string(self):
        assert self.go(r""" go("''") """) == ""
        assert self.go(r""" go("'abc'") """) == "abc"
        assert self.go(r""" go("'\\'") """) == "\\"

        with pytest.raises(AssertionError):
            assert self.go(r""" go("'abc") """)

    def test_string(self):
        assert self.go(r""" go('""') """) == ""
        assert self.go(r""" go('"abc"') """) == "abc"
        assert self.go(r""" go('"\\\n\""') """) == "\\\n\""

        with pytest.raises(AssertionError):
            assert self.go(r""" go('"abc') """)
        with pytest.raises(AssertionError):
            assert self.go(r""" go('"abc\"') """)

    def test_if(self):
        assert self.go(r""" go('if 1; True then 2; 5 else 3; 6 end') """) == 5
        assert self.go(r""" go('if 1; False then 2; 5 else 3; 6 end') """) == 6

        with pytest.raises(AssertionError):
            self.go(r""" go('if True end') """)
        with pytest.raises(AssertionError):
            self.go(r""" go('if True then 5') """)
        with pytest.raises(AssertionError):
            self.go(r""" go('if True then 5 else 6') """)

    def test_sequence(self):
        assert self.go(r""" go('5; 6') """) == 6

    def test_define(self, capsys):
        assert self.go(r""" go('a := 5') """) == 5
        assert self.go(r""" go('a') """) == 5
        assert self.go(r""" go('a := b := 6') """) == 6
        assert self.go(r""" go('a') """) == 6
        assert self.go(r""" go('b') """) == 6

    def test_assign(self):
        self.go(r""" a := b := 5 """)
        assert self.go(r""" a = 6 """) == 6
        assert self.go(r""" a """) == 6
        assert self.go(r""" a = b = 7 """) == 7
        assert self.go(r""" a """) == 7
        assert self.go(r""" b """) == 7

@pytest.mark.parametrize(
    "set_interpreter",
    [ICI, STM], ids=["ici", "stm"],
    indirect=True)
class TestEvaluator(BaseToigOnToigTest):
    def test_primary(self):
        assert self.go(r"""eval(None)""") == None
        assert self.go(r"""eval(True)""") == True
        assert self.go(r"""eval(False)""") == False
        assert self.go(r"""eval(5)""") == 5

    def test_if(self):
        assert self.go(r"""eval(["if", True, 5, 6])""") == 5
        assert self.go(r"""eval(["if", False, 5, 6])""") == 6
        assert self.go(r"""eval(["if", ["if", True, True, True], 5, 6])""") == 5
        assert self.go(r"""eval(["if", True, ["if", True, 5, 6], 6])""") == 5
        assert self.go(r"""eval(["if", False, 5, ["if", False, 5, 6]])""") == 6

        with pytest.raises(AssertionError):
            self.go(r"""eval(["unexpected case"])""")

    def test_define(self):
        assert self.go(r"""eval(["define", "a", 5])""") == 5
        assert self.go(r"""eval("a")""") == 5
        assert self.go(r"""eval(["define", "b", 6])""") == 6
        assert self.go(r"""eval("b")""") == 6
        assert self.go(r"""eval(["define", "b", 7])""") == 7
        assert self.go(r"""eval("b")""") == 7

        with pytest.raises(AssertionError):
            self.go(r"""eval("c")""")

    def test_primitives(self):
        assert self.go(r"""eval(["add", 5, 6])""") == 11
        assert self.go(r"""eval(["sub", 11, 6])""") == 5
        assert self.go(r"""eval(["equal", 5, 5])""") == True
        assert self.go(r"""eval(["equal", 5, 6])""") == False

    def test_function(self):
        assert self.go(r"""eval([["func", ["n"], ["add", "n", 5]], 6])""") == 11

    def test_fib(self):
        self.go(r"""eval(
            ["define", "fib", ["func", ["n"],
                ["if", ["equal", "n", 0], 0,
                ["if", ["equal", "n", 1], 1,
                ["add", ["fib", ["sub", "n", 1]], ["fib", ["sub", "n", 2]]]]]]]
        )""")
        assert self.go(r"""eval(["fib", 0])""") == 0
        assert self.go(r"""eval(["fib", 1])""") == 1
        assert self.go(r"""eval(["fib", 2])""") == 1
        assert self.go(r"""eval(["fib", 3])""") == 2
        assert self.go(r"""eval(["fib", 6])""") == 8

    def test_adder(self):
        self.go(r"""eval(
            ["define", "make_adder", ["func", ["n"],
                ["func", ["m"], ["add", "n", "m"]]
            ]]
        )""")
        assert self.go(r"""eval([["make_adder", 5], 6])""") == 11

    def test_counter(self):
        self.go(r"""eval(["seq",
            ["define", "make_counter", ["func", [], ["seq",
                ["define", "c", 0],
                ["func", [], ["assign", "c", ["add", "c", 1]]]
            ]]],
            ["define", "counter1", ["make_counter"]],
            ["define", "counter2", ["make_counter"]]
        ])""")

        assert self.go(r"""eval(["counter1"])""") == 1
        assert self.go(r"""eval(["counter1"])""") == 2
        assert self.go(r"""eval(["counter2"])""") == 1
        assert self.go(r"""eval(["counter2"])""") == 2
        assert self.go(r"""eval(["counter1"])""") == 3
        assert self.go(r"""eval(["counter2"])""") == 3
