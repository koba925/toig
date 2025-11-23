import pytest

from test_commons import BaseTest
from ici import Interpreter as ICI
from stm import Interpreter as STM

@pytest.mark.parametrize(
    "set_interpreter",
    [STM], ids=["stm"],
    indirect=True)
class TestFirstClassMacroBase(BaseTest):
    def test_macro(self):
        assert self.expanded("macro () do q(abc) end ()") == "abc"

        assert self.expanded("""
            macro (a) do qq !a * !a end end (5 + 6)
        """) == ["mul", ["add", 5, 6], ["add", 5, 6]]

        self.go("build_exp := macro (op, *r) do qq (!op)(!!r) end end")
        assert self.expanded("build_exp(add)") == ["add"]
        assert self.expanded("build_exp(add, 5)") == ["add", 5]
        assert self.expanded("build_exp(add, 5, 6)") == ["add", 5, 6]

        assert self.go("macro (*a, b) do qq [q(!a), q(!b)] end end (5)") == [[], 5]
        assert self.go("macro (*a, b) do qq [q(!a), q(!b)] end end (5, 6)") == [[5], 6]
        assert self.go("macro (*a, b) do qq [q(!a), q(!b)] end end (5, 6, 7)") == [[5, 6], 7]
        assert self.go("macro (a, *b, c) do qq [q(!a), q(!b), q(!c)] end end (5, 6, 7)") == [5, [6], 7]

    def test_macro_defining_macro(self):
        self.go("""
        alias := macro (als, org) do qq
            !als := macro (*args) do qq
                (!org)(!q(!!args))
            end end
        end end;

        alias(a, add)
        """)

        assert self.expanded("a(5, 6)") == ["add", 5, 6]
        assert self.go("a(5, 6)") == 11

    def test_macro_firstclass(self):
        assert self.go("func(op, a, b) do op(a, b) end (and, True, False)") == False
        assert self.go("func(op, a, b) do op(a, b) end (or, True, False)") == True

        assert self.go("func() do and end ()(True, False)") == False
        assert self.go("func() do or end ()(True, False)") == True

        assert self.go("map([and, or], func(op) do op(True, False) end)") == [False, True]
