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
            eval := func (expr) do expr end
        """)

        assert self.go("eval(None)") == None
        assert self.go("eval(True)") == True
        assert self.go("eval(False)") == False
        assert self.go("eval(5)") == 5
        assert self.go("eval('hello')") == "hello"
