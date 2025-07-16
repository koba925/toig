import unittest
from unittest.mock import patch
from io import StringIO

from toig import Interpreter

class TestToig(unittest.TestCase):

    def setUp(self):
        self.i = Interpreter()
        self.i.stdlib()

    def go(self, src):
        return self.i.run(src)

    def fails(self, src):
        try: self.i.run(src)
        except AssertionError: return True
        else: return False

    def expanded(self, src):
        return self.i.run(["expand", src])

    def printed(self, src):
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            val = self.i.run(src)
            return (val, mock_stdout.getvalue())

    def test_primary(self):
        self.assertEqual(self.go(None), None)
        self.assertEqual(self.go(5), 5)
        self.assertEqual(self.go(True), True)
        self.assertEqual(self.go(False), False)

    def test_quote(self):
        self.assertEqual(self.go(["q", 5]), 5)
        self.assertEqual(self.go(["q", ["add", 5, 6]]), ["add", 5, 6])

    def test_quasiquote(self):
        self.assertEqual(self.go(["qq", 5]), 5)
        self.assertEqual(self.go(["qq", ["add", 5, 6]]), ["add", 5, 6])
        self.assertEqual(self.go(["qq", ["mul", 4, ["add", 5, 6]]]), ["mul", 4, ["add", 5, 6]])
        self.assertEqual(self.go(["qq", ["mul", ["add", 5, 6], 7]]), ["mul", ["add", 5, 6], 7])

        self.assertEqual(self.go(["qq", ["!", ["add", 5, 6]]]), 11)
        self.assertEqual(self.go(["qq", ["mul", 4, ["!", ["add", 5, 6]]]]), ["mul", 4, 11])
        self.assertEqual(self.go(["qq", ["mul", ["!", ["add", 5, 6]], 7]]), ["mul", 11, 7])

        self.assertEqual(self.go(["qq", ["add", ["!!", ["arr", 5, 6]]]]), ["add", 5, 6])
        self.assertEqual(self.go(["qq", [
            ["!!", ["arr", 3]],
            4,
            ["!!", ["arr", 5]],
            6]]), [3, 4, 5, 6])
        self.assertTrue(self.fails(["qq", ["add", ["!!", 5]]]))

    def test_define(self):
        self.assertEqual(self.go(["define", "a", 5]), 5)
        self.assertEqual(self.go("a"), 5)
        self.assertEqual(self.go(["define", "a", ["add", 5, 6]]), 11)
        self.assertEqual(self.go("a"), 11)
        self.assertEqual(self.printed([["func", [], ["seq",
                            ["print", ["define", "a", 5]],
                            ["print", "a"]]]]), (None, "5\n5\n"))
        self.assertEqual(self.go("a"), 11)
        self.assertTrue(self.fails(["b"]))

    def test_assign(self):
        self.assertEqual(self.go(["define", "a", 5]), 5)
        self.assertEqual(self.go(["assign", "a", ["add", 5, 6]]), 11)
        self.assertEqual(self.go("a"), 11)
        self.assertEqual(self.printed([["func", [], ["seq",
                            ["print", ["assign", "a", 7]],
                            ["print", "a"]]]]), (None, "7\n7\n"))
        self.assertEqual(self.go("a"), 7)
        self.assertTrue(self.fails(["assign", "b", 6]))

    def test_seq(self):
        self.assertEqual(self.go(["seq"]), None)
        self.assertEqual(self.go(["seq", 5]), 5)
        self.assertEqual(self.go(["seq", 5, 6]), 6)
        self.assertEqual(self.printed(["seq", ["print", 5]]), (None, "5\n"))
        self.assertEqual(self.printed(["seq", ["print", 5], ["print", 6]]), (None, "5\n6\n"))

    def test_if(self):
        self.assertEqual(self.go(["if", ["equal", 5, 5], ["add", 7, 8], ["add", 9, 10]]), 15)
        self.assertEqual(self.go(["if", ["equal", 5, 6], ["add", 7, 8], ["add", 9, 10]]), 19)
        self.assertTrue(self.fails(["if", True, 5]))

    def test_builtin_arithmetic(self):
        self.assertEqual(self.go(["add", 5, 6]), 11)
        self.assertEqual(self.go(["add", ["add", 5, 6], ["add", 7, 8]]), 26)
        self.assertEqual(self.go(["sub", ["sub", 26, 8], ["add", 5, 6]]), 7)
        self.assertEqual(self.go(["mul", ["mul", 5, 6], ["mul", 7, 8]]), 1680)
        self.assertEqual(self.go(["div", ["div", 1680, 8], ["mul", 5, 6]]), 7)

    def test_builtin_equality(self):
        self.assertEqual(self.go(["equal", ["add", 5, 6], ["add", 6, 5]]), True)
        self.assertEqual(self.go(["equal", ["add", 5, 6], ["add", 7, 8]]), False)
        self.assertEqual(self.go(["not_equal", ["add", 5, 6], ["add", 6, 5]]), False)
        self.assertEqual(self.go(["not_equal", ["add", 5, 6], ["add", 7, 8]]), True)

    def test_builtin_comparison(self):
        self.assertEqual(self.go(["less", ["add", 5, 6], ["add", 3, 7]]), False)
        self.assertEqual(self.go(["less", ["add", 5, 6], ["add", 4, 7]]), False)
        self.assertEqual(self.go(["less", ["add", 5, 6], ["add", 4, 8]]), True)
        self.assertEqual(self.go(["greater", ["add", 5, 6], ["add", 3, 7]]), True)
        self.assertEqual(self.go(["greater", ["add", 5, 6], ["add", 4, 7]]), False)
        self.assertEqual(self.go(["greater", ["add", 5, 6], ["add", 4, 8]]), False)

        self.assertEqual(self.go(["less_equal", ["add", 5, 6], ["add", 3, 7]]), False)
        self.assertEqual(self.go(["less_equal", ["add", 5, 6], ["add", 4, 7]]), True)
        self.assertEqual(self.go(["less_equal", ["add", 5, 6], ["add", 4, 8]]), True)
        self.assertEqual(self.go(["greater_equal", ["add", 5, 6], ["add", 3, 7]]), True)
        self.assertEqual(self.go(["greater_equal", ["add", 5, 6], ["add", 4, 7]]), True)
        self.assertEqual(self.go(["greater_equal", ["add", 5, 6], ["add", 4, 8]]), False)

    def test_builtin_logic(self):
        self.assertEqual(self.go(["not", ["equal", ["add", 5, 6], ["add", 6, 5]]]), False)
        self.assertEqual(self.go(["not", ["equal", ["add", 5, 6], ["add", 7, 8]]]), True)

    def test_array(self):
        self.assertEqual(self.go(["arr"]), [])
        self.assertEqual(self.go(["arr", ["add", 5, 6]]), [11])

        self.go(["define", "a", ["arr", 5, 6, ["arr", 7, 8]]])
        self.assertEqual(self.go("a"), [5, 6, [7, 8]])

        self.assertEqual(self.go(["is_arr", 5]), False)
        self.assertEqual(self.go(["is_arr", ["arr"]]), True)
        self.assertEqual(self.go(["is_arr", "a"]), True)

        self.assertEqual(self.go(["len", ["arr"]]), 0)
        self.assertEqual(self.go(["len", "a"]), 3)

        self.assertEqual(self.go(["get_at", "a", 1]), 6)
        self.assertEqual(self.go(["get_at", "a", -1]), [7, 8])
        self.assertEqual(self.go(["get_at", ["get_at", "a", 2], 1]), 8)

        self.assertEqual(self.go(["set_at", "a", 1, 9]), 9)
        self.assertEqual(self.go("a"), [5, 9, [7, 8]])
        self.assertEqual(self.go(["set_at", ["get_at", "a", 2], -1, 10]), 10)
        self.assertEqual(self.go("a"), [5, 9, [7, 10]])

        self.assertEqual(self.go(["slice", "a", None, None, None]), [5, 9, [7, 10]])
        self.assertEqual(self.go(["slice", "a", 1, None, None]), [9, [7, 10]])
        self.assertEqual(self.go(["slice", "a", -2, None, None]), [9, [7, 10]])
        self.assertEqual(self.go(["slice", "a", 1, 2, None]), [9])
        self.assertEqual(self.go(["slice", "a", 1, -1, None]), [9])
        self.assertEqual(self.go(["slice", "a", 2, 0, -1]), [[7, 10],9])

        self.assertEqual(self.go(["add", ["arr", 5], ["arr", 6]]), [5, 6])

    def test_print(self):
        self.assertEqual(self.printed(["print", None]), (None, "None\n"))
        self.assertEqual(self.printed(["print", 5]), (None, "5\n"))
        self.assertEqual(self.printed(["print", True]), (None, "True\n"))
        self.assertEqual(self.printed(["print", False]), (None, "False\n"))
        self.assertEqual(self.printed(["print"]), (None, "\n"))
        self.assertEqual(self.printed(["print", 5, 6]), (None, "5 6\n"))

    def test_error(self):
        self.assertTrue(self.fails(["error"]))
        self.assertTrue(self.fails(["error", 5]))

    def test_func(self):
        self.assertEqual(self.go([["func", ["n"], ["add", 5, "n"]], 6]), 11)

    def test_macro(self):
        self.assertEqual(self.expanded([["macro", [], ["q", ["add", 5, 6]]]]), ["add", 5, 6])
        self.assertEqual(
            self.expanded([
                ["macro", ["a", "b"], ["qq", ["add", ["!", "a"], ["!","b"]]]],
                ["add", 5, 6], 7]), ["add", ["add", 5, 6], 7])

        # self.go(["define", "build_exp", ["macro", ["op", ["*", "r"]],
        #         ["add", ["arr", "op"], "r"]]])
        # self.assertEqual(self.expanded(["build_exp", "add"]), ["add"])
        # self.assertEqual(self.expanded(["build_exp", "add", 5]), ["add", 5])
        # self.assertEqual(self.expanded(["build_exp", "add", 5, 6]), ["add", 5, 6])

        # self.assertTrue(self.fails([["macro", [["*", "r"], "a"], 5]]))

    def test_fib(self):
        self.go(["define", "fib", ["func", ["n"],
                ["if", ["equal", "n", 0], 0,
                ["if", ["equal", "n", 1], 1,
                ["add", ["fib", ["sub", "n", 1]], ["fib", ["sub", "n", 2]]]]]]])
        self.assertEqual(self.go(["fib", 0]), 0)
        self.assertEqual(self.go(["fib", 1]), 1)
        self.assertEqual(self.go(["fib", 2]), 1)
        self.assertEqual(self.go(["fib", 3]), 2)
        self.assertEqual(self.go(["fib", 10]), 55)

    def test_adder(self):
        self.go(["define", "make_adder", ["func", ["n"],
                ["func", ["m"], ["add", "n", "m"]]]])
        self.assertEqual(self.go([["make_adder", 5], 6]), 11)

    def test_counter(self):
        self.go(["define", "make_counter", ["func", [], ["seq",
                ["define", "c", 0],
                ["func", [], ["assign", "c", ["add", "c", 1]]]]]])
        self.go(["define", "counter1", ["make_counter"]])
        self.go(["define", "counter2", ["make_counter"]])
        self.assertEqual(self.go(["counter1"]), 1)
        self.assertEqual(self.go(["counter1"]), 2)
        self.assertEqual(self.go(["counter2"]), 1)
        self.assertEqual(self.go(["counter2"]), 2)
        self.assertEqual(self.go(["counter1"]), 3)
        self.assertEqual(self.go(["counter2"]), 3)

class TestStdlib(TestToig):
    def test_id(self):
        self.assertEqual(self.go(["id", ["add", 5, 6]]), 11)

    def test_inc_dec(self):
        self.assertEqual(self.go(["inc", ["add", 5, 6]]), 12)
        self.assertEqual(self.go(["dec", ["add", 5, 6]]), 10)

    def test_first_rest_last(self):
        self.assertEqual(self.go(["first", ["arr", 5, 6, 7]]), 5)
        self.assertEqual(self.go(["rest", ["arr", 5, 6, 7]]), [6, 7])
        self.assertEqual(self.go(["last", ["arr", 5, 6, 7]]), 7)

    def test_append_prepend(self):
        self.assertEqual(self.go(["append", ["arr", 5, 6], ["inc", 7]]), [5, 6, 8])
        self.assertEqual(self.go(["prepend", ["inc", 5], ["arr", 7, 8]]), [6, 7, 8])

    def test_map(self):
        self.assertEqual(self.go(["map", ["arr"], "inc"]), [])
        self.assertEqual(self.go(["map", ["arr", 5, 6, 7], "inc"]), [6, 7, 8])

    def test_range(self):
        self.assertEqual(self.go(["range", 5, 5]), [])
        self.assertEqual(self.go(["range", 5, 8]), [5, 6, 7])

    def test_scope(self):
        self.assertEqual(self.expanded(["scope", ["seq", ["define", "a", 5]]]),
                         [["func", [], ["seq", ["define", "a", 5]]]])
        self.assertEqual(self.printed(["seq",
            ["define", "a", 5],
            ["scope", ["seq", ["define", "a", 6], ["print", "a"]]],
            ["print", "a"]]), (None, "6\n5\n"))

    def test_when(self):
        self.assertEqual(self.go(["expand",
                            ["when", ["not", ["equal", "b", 0]], ["div", "a", "b"]]]),
                         ["if", ["not", ["equal", "b", 0]], ["div", "a", "b"], None])
        self.go(["define", "a", 30])
        self.go(["define", "b", 5])
        self.assertEqual(self.go(["when", ["not", ["equal", "b", 0]], ["div", "a", "b"]]), 6)
        self.go(["assign", "b", 0])
        self.assertEqual(self.go(["when", ["not", ["equal", "b", 0]], ["div", "a", "b"]]), None)

    def test_aif(self):
        self.assertEqual(self.go(["aif", ["inc", 5], ["inc", "it"], 8]), 7)
        self.assertEqual(self.go(["aif", ["dec", 1], 5, "it"]), 0)

    def test_and_or(self):
        self.assertEqual(self.expanded(["and", ["equal", "a", 0], ["equal", "b", 0]]),
                         ["aif", ["equal", "a", 0], ["equal", "b", 0], "it"])
        self.assertEqual(self.go(["and", False, "nosuchvariable"]), False)
        self.assertEqual(self.go(["and", None, "nosuchvariable"]), None)
        self.assertEqual(self.go(["and", True, False]), False)
        self.assertEqual(self.go(["and", True, None]), None)
        self.assertEqual(self.go(["and", True, True]), True)
        self.assertEqual(self.go(["and", True, 5]), 5)

        self.assertEqual(self.expanded(["or", ["equal", "a", 0], ["equal", "b", 0]]),
                         ["aif", ["equal", "a", 0], "it", ["equal", "b", 0]])
        self.assertEqual(self.go(["or", False, False]), False)
        self.assertEqual(self.go(["or", False, None]), None)
        self.assertEqual(self.go(["or", False, True]), True)
        self.assertEqual(self.go(["or", False, 5]), 5)
        self.assertEqual(self.go(["or", True, "nosuchvariable"]), True)
        self.assertEqual(self.go(["or", 5, "nosuchvariable"]), 5)

        self.assertEqual(self.printed(["scope", ["seq",
            ["define", "foo", 5],
            ["print", ["or", "foo", ["q", "default"]]],
            ["assign", "foo", None],
            ["print", ["or", "foo", ["q", "default"]]]
        ]]), (None, "5\ndefault\n"))

        self.assertEqual(self.expanded(
            ["and", ["or", ["equal", 5, 6], ["equal", 7, 7]], ["equal", 8, 8]]),
            ["aif", ["or", ["equal", 5, 6], ["equal", 7, 7]], ["equal", 8, 8], "it"])
        self.assertEqual(
            self.go(["and", ["or", ["equal", 5, 6], ["equal", 7, 7]], ["equal", 8, 8]]),
            True)

    def test_while(self):
        self.assertEqual(self.go(["expand",
            ["while", ["less", "a", 5], ["seq",
                ["assign", "b", ["add", "b", ["arr", "a"]]],
                ["assign", "a", ["add", "a", 1]]]]]),
            ["scope", ["seq",
                ["define", "__stdlib_while_loop", ["func", [],
                    ["when", ["less", "a", 5],
                        ["seq",
                            ["seq",
                                ["assign", "b", ["add", "b", ["arr", "a"]]],
                                ["assign", "a", ["add", "a", 1]]],
                            ["__stdlib_while_loop"]]]]],
                ["__stdlib_while_loop"]]])

        self.go(["seq",
            ["define", "a", 0],
            ["define", "b", ["arr"]],
            ["while", ["less", "a", 5], ["seq",
                ["assign", "b", ["add", "b", ["arr", "a"]]],
                ["assign", "a", ["add", "a", 1]]]]])
        self.assertEqual(self.go("a"), 5)
        self.assertEqual(self.go("b"), [0, 1, 2, 3, 4])
        self.go(["seq",
            ["define", "r", ["arr"]],
            ["define", "c", ["arr"]],
            ["while", ["less", ["len", "r"], 3],
                ["seq",
                    ["assign", "c", ["arr"]],
                    ["while", ["less", ["len", "c"], 3],
                        ["assign", "c", ["add", "c", ["arr", 0]]]],
                    ["assign", "r", ["add", "r", ["arr", "c"]]]]]])
        self.assertEqual(self.go("r"), [[0, 0, 0], [0, 0, 0], [0, 0, 0]])

    def test_for(self):
        self.assertEqual(self.go(["expand",
            ["for", "i", ["arr", 5, 6, 7], ["assign", "sum", ["add", "sum", "i"]]]]),
            ["scope", ["seq",
                ["define", "__stdlib_for_index", 0],
                ["define", "i", None],
                ["while", ["less", "__stdlib_for_index", ["len", ["arr", 5, 6, 7]]], ["seq",
                    ["assign", "i", ["get_at", ["arr", 5, 6, 7], "__stdlib_for_index"]],
                    ["assign", "sum", ["add", "sum", "i"]],
                    ["assign", "__stdlib_for_index", ["inc", "__stdlib_for_index"]]]]]])

        self.assertEqual(self.go(["seq",
            ["define", "sum", 0],
            ["for", "i", ["arr", 5, 6, 7], ["assign", "sum", ["add", "sum", "i"]]],
            "sum"]), 18)

if __name__ == "__main__":
    unittest.main()