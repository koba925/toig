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
        assert self.go("is_space(' ')") == True
        assert self.go("""is_space('
')""") == True
        assert self.go("is_space('a')") == False

    def test_is_digit(self):
        assert self.go("is_digit('0')") == True
        assert self.go("is_digit('1')") == True
        assert self.go("is_digit('9')") == True
        assert self.go("is_digit(' ')") == False
        assert self.go("is_digit('A')") == False

    def test_is_alphabet(self):
        assert self.go("is_alphabet('a')") == True
        assert self.go("is_alphabet('z')") == True
        assert self.go("is_alphabet('A')") == True
        assert self.go("is_alphabet('Z')") == True
        assert self.go("is_alphabet('_')") == False
        assert self.go("is_alphabet('0')") == False
        assert self.go("is_alphabet(' ')") == False

    def test_is_name_first(self):
        assert self.go("is_name_first('a')") == True
        assert self.go("is_name_first('z')") == True
        assert self.go("is_name_first('A')") == True
        assert self.go("is_name_first('Z')") == True
        assert self.go("is_name_first('_')") == True
        assert self.go("is_name_first('0')") == False
        assert self.go("is_name_first('#')") == False
        assert self.go("is_name_first(' ')") == False

    def test_is_name_rest(self):
        assert self.go("is_name_rest('a')") == True
        assert self.go("is_name_rest('z')") == True
        assert self.go("is_name_rest('A')") == True
        assert self.go("is_name_rest('Z')") == True
        assert self.go("is_name_rest('_')") == True
        assert self.go("is_name_rest('0')") == True
        assert self.go("is_name_rest('#')") == False
        assert self.go("is_name_rest(' ')") == False

    def test_contains(self):
        assert self.go("contains('a', [])") == False
        assert self.go("contains('a', [1, None, 'b', False, []])") == False
        assert self.go("contains('a', [1, None, 'b', False, 'a'])") == True

@pytest.mark.parametrize(
    "set_interpreter",
    [ICI, STM], ids=["ici", "stm"],
    indirect=True)
class TestScanner(BaseToigOnToigTest):
    def test_scan_whitespace(self):
        assert self.go("scan('')") == ["$EOF"]
        assert self.go("scan(' 5 ')") == [5, "$EOF"]
        assert self.go("scan('\n5\n')") == [5, "$EOF"]

    def test_scan_primary(self):
        assert self.go("scan('None True False 5 56')") == [None, True, False, 5, 56, '$EOF']

@pytest.mark.parametrize(
    "set_interpreter",
    [ICI, STM], ids=["ici", "stm"],
    indirect=True)
class TestInterpreter(BaseToigOnToigTest):
    def test_primary(self):
        assert self.go("go('None')") == None
        assert self.go("go('True')") == True
        assert self.go("go('False')") == False
        assert self.go("go('5')") == 5

@pytest.mark.parametrize(
    "set_interpreter",
    [ICI, STM], ids=["ici", "stm"],
    indirect=True)
class TestEvaluator(BaseToigOnToigTest):
    def test_eval_primary(self):
        assert self.go("eval(None)") == None
        assert self.go("eval(True)") == True
        assert self.go("eval(False)") == False
        assert self.go("eval(5)") == 5

    def test_eval_if(self):
        assert self.go("eval(['if', True, 5, 6])") == 5
        assert self.go("eval(['if', False, 5, 6])") == 6
        assert self.go("eval(['if', ['if', True, True, True], 5, 6])") == 5
        assert self.go("eval(['if', True, ['if', True, 5, 6], 6])") == 5
        assert self.go("eval(['if', False, 5, ['if', False, 5, 6]])") == 6

        with pytest.raises(AssertionError):
            self.go("eval(['unexpected case'])")

    def test_eval_define(self):
        assert self.go("eval(['define', 'a', 5])") == 5
        assert self.go("eval('a')") == 5
        assert self.go("eval(['define', 'b', 6])") == 6
        assert self.go("eval('b')") == 6
        assert self.go("eval(['define', 'b', 7])") == 7
        assert self.go("eval('b')") == 7

        with pytest.raises(AssertionError):
            self.go("eval('c')")

    def test_eval_primitives(self):
        assert self.go("eval(['add', 5, 6])") == 11
        assert self.go("eval(['sub', 11, 6])") == 5
        assert self.go("eval(['equal', 5, 5])") == True
        assert self.go("eval(['equal', 5, 6])") == False

    def test_eval_function(self):
        assert self.go("eval([['func', ['n'], ['add', 'n', 5]], 6])") == 11

    def test_eval_fib(self):
        self.go("""eval(
            ['define', 'fib', ['func', ['n'],
                ['if', ['equal', 'n', 0], 0,
                ['if', ['equal', 'n', 1], 1,
                ['add', ['fib', ['sub', 'n', 1]], ['fib', ['sub', 'n', 2]]]]]]]
        )""")
        assert self.go("eval(['fib', 0])") == 0
        assert self.go("eval(['fib', 1])") == 1
        assert self.go("eval(['fib', 2])") == 1
        assert self.go("eval(['fib', 3])") == 2
        assert self.go("eval(['fib', 6])") == 8

    def test_eval_adder(self):
        self.go("""eval(
            ['define', 'make_adder', ['func', ['n'],
                ['func', ['m'], ['add', 'n', 'm']]
            ]]
        )""")
        assert self.go("eval([['make_adder', 5], 6])") == 11

    def test_eval_counter(self):
        self.go("""eval(['seq',
            ['define', 'make_counter', ['func', [], ['seq',
                ['define', 'c', 0],
                ['func', [], ['assign', 'c', ['add', 'c', 1]]]
            ]]],
            ['define', 'counter1', ['make_counter']],
            ['define', 'counter2', ['make_counter']]
        ])""")

        assert self.go("eval(['counter1'])") == 1
        assert self.go("eval(['counter1'])") == 2
        assert self.go("eval(['counter2'])") == 1
        assert self.go("eval(['counter2'])") == 2
        assert self.go("eval(['counter1'])") == 3
        assert self.go("eval(['counter2'])") == 3

