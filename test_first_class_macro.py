from test_commons import Testable

class TestFirstClassMacroBase(Testable):
    def test_macro(self):
        self.assertEqual(self.expanded("macro () do quote(abc) end ()"), "abc")

        self.assertEqual(
            self.expanded("macro (a) do quasiquote unquote(a) * unquote(a) end end (5 + 6)"),
            ["mul", ["add", 5, 6], ["add", 5, 6]])

        self.go("build_exp := macro (op, *r) do quasiquote unquote(op)(unquote_splicing(r)) end end")
        self.assertEqual(self.expanded("build_exp(add)"), ["add"])
        self.assertEqual(self.expanded("build_exp(add, 5)"), ["add", 5])
        self.assertEqual(self.expanded("build_exp(add, 5, 6)"), ["add", 5, 6])

        self.assertEqual(self.go("macro (*a, b) do quasiquote [quote(unquote(a)), quote(unquote(b))] end end (5)"), [[], 5])
        self.assertEqual(self.go("macro (*a, b) do quasiquote [quote(unquote(a)), quote(unquote(b))] end end (5, 6)"), [[5], 6])
        self.assertEqual(self.go("macro (*a, b) do quasiquote [quote(unquote(a)), quote(unquote(b))] end end (5, 6, 7)"), [[5, 6], 7])
        self.assertEqual(self.go("macro (a, *b, c) do quasiquote [quote(unquote(a)), quote(unquote(b)), quote(unquote(c))] end end (5, 6, 7)"), [5, [6], 7])

    def test_macro_firstclass(self):
        self.assertEqual(self.go("func(op, a, b) do op(a, b) end (and, True, False)"), False)
        self.assertEqual(self.go("func(op, a, b) do op(a, b) end (or, True, False)"), True)

        self.assertEqual(self.go("func() do and end ()(True, False)"), False)
        self.assertEqual(self.go("func() do or end ()(True, False)"), True)

        self.assertEqual(self.go("map([and, or], func(op) do op(True, False) end)"), [False, True])

