import pytest

from test_commons import BaseTest
from ici import Interpreter as ICI
from stm import Interpreter as STM

@pytest.mark.parametrize(
    "set_interpreter",
    [ICI, STM], ids=["ici", "stm"],
    indirect=True)
class TestEval(BaseTest):
    def test_eval(self):
        self.go("""
            eval := func (expr) do
                if expr == None then
                    None
                elif is_bool(expr) or is_int(expr) or is_str(expr) then
                    expr
                elif expr[0] == 'if' then
                    if eval(expr[1]) then eval(expr[2]) else eval(expr[3]) end
                else
                    error('Unexpected expression: ', expr)
                end
            end
        """)

        assert self.go("eval(None)") == None
        assert self.go("eval(True)") == True
        assert self.go("eval(False)") == False
        assert self.go("eval(5)") == 5
        assert self.go("eval('hello')") == "hello"

        assert self.go("eval(['if', True, 5, 6])") == 5
        assert self.go("eval(['if', False, 5, 6])") == 6

        with pytest.raises(AssertionError):
            self.go("eval(['unexpected case'])")
