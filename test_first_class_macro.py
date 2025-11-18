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
        assert self.expanded("macro () do quote(abc) end ()") == "abc"

        assert self.expanded("""
            macro (a) do quasiquote unquote(a) * unquote(a) end end (5 + 6)
        """) == ["mul", ["add", 5, 6], ["add", 5, 6]]

        self.go("build_exp := macro (op, *r) do quasiquote unquote(op)(unquote_splicing(r)) end end")
        assert self.expanded("build_exp(add)") == ["add"]
        assert self.expanded("build_exp(add, 5)") == ["add", 5]
        assert self.expanded("build_exp(add, 5, 6)") == ["add", 5, 6]

        assert self.go("macro (*a, b) do quasiquote [quote(unquote(a)), quote(unquote(b))] end end (5)") == [[], 5]
        assert self.go("macro (*a, b) do quasiquote [quote(unquote(a)), quote(unquote(b))] end end (5, 6)") == [[5], 6]
        assert self.go("macro (*a, b) do quasiquote [quote(unquote(a)), quote(unquote(b))] end end (5, 6, 7)") == [[5, 6], 7]
        assert self.go("macro (a, *b, c) do quasiquote [quote(unquote(a)), quote(unquote(b)), quote(unquote(c))] end end (5, 6, 7)") == [5, [6], 7]

    def test_macro_defining_macro(self):
        self.go("""
        alias := macro (als, org) do quasiquote
            unquote(als) := macro (*args) do quasiquote
                unquote(org)(unquote(quote(unquote_splicing(args))))
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
