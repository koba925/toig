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

class TestCore(TestToig):
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
        self.assertEqual(self.go(["mod", ["div", 1704, 8], ["mul", 5, 6]]), 3)
        self.assertEqual(self.go(["neg", ["add", 5, 6]]), -11)

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

        self.assertEqual(self.go([["func", [["*", "rest"]], "rest"]]), [])
        self.assertEqual(self.go([["func", ["a", ["*", "rest"]], ["arr", "a", "rest"]], 5]), [5, []])
        self.assertEqual(self.go([["func", ["a", ["*", "rest"]], ["arr", "a", "rest"]], 5, 6]), [5, [6]])
        self.assertEqual(self.go([["func", ["a", ["*", "rest"]], ["arr", "a", "rest"]], 5, 6, 7]), [5, [6, 7]])

    def test_closure_adder(self):
        self.go(["define", "make_adder", ["func", ["n"],
                ["func", ["m"], ["add", "n", "m"]]]])
        self.assertEqual(self.go([["make_adder", 5], 6]), 11)

    def test_closure_counter(self):
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

    def test_macro(self):
        self.assertEqual(self.expanded([["macro", [], ["q", ["add", 5, 6]]]]), ["add", 5, 6])
        self.assertEqual(
            self.expanded([
                ["macro", ["a", "b"], ["qq", ["add", ["!", "a"], ["!","b"]]]],
                ["add", 5, 6], 7]), ["add", ["add", 5, 6], 7])

        self.go(["define", "build_exp", ["macro", ["op", ["*", "r"]],
                ["add", ["arr", "op"], "r"]]])
        self.assertEqual(self.expanded(["build_exp", "add"]), ["add"])
        self.assertEqual(self.expanded(["build_exp", "add", 5]), ["add", 5])
        self.assertEqual(self.expanded(["build_exp", "add", 5, 6]), ["add", 5, 6])

        self.assertTrue(self.fails([["macro", [["*", "r"], "a"], 5]]))

    def test_letcc(self):
        self.assertEqual(self.go(["letcc", "skip-to", ["add", 5, 6]]), 11)
        self.assertEqual(self.go(["letcc", "skip-to", ["add", ["skip-to", 5], 6]]), 5)
        self.assertEqual(self.go(["add", 5, ["letcc", "skip-to", ["skip-to", 6]]]), 11)
        self.assertEqual(self.go(["letcc", "skip1", ["add", ["skip1", ["letcc", "skip2", ["add", ["skip2", 5], 6]]], 7]]), 5)

        self.go(["define", "inner", ["func", ["raise"], ["raise", 5]]])
        self.go(["define", "outer", ["func", [],
                [ "letcc", "raise", ["add", ["inner", "raise"], 6]]]])
        self.assertEqual(self.go(["outer"]), 5)

    def test_letcc_reuse(self):
        self.go(["define", "add5", None])
        self.assertEqual(self.go(["add", 5, ["letcc", "cc", ["seq", ["assign", "add5", "cc"], 6]]]), 11)
        self.assertEqual(self.go(["add5", 7]), 12)
        self.assertEqual(self.go(["add5", 8]), 13)

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

    def test_awhile(self):
        self.go(["seq",
                ["define", "a", 0],
                ["define", "b", ["arr"]],
                ["awhile", ["less", "a", 10], ["seq",
                    ["when", ["equal", "a", 5], ["break", None]],
                    ["assign", "a", ["add", "a", 1]],
                    ["when", ["equal", "a", 3], ["continue"]],
                    ["assign", "b", ["add", "b", ["arr", "a"]]],
                    ]]])
        self.assertEqual(self.go("a"), 5)
        self.assertEqual(self.go("b"), [1, 2, 4, 5])

        self.go(["seq",
                ["define", "r", ["arr"]],
                ["define", "c", ["arr"]],
                ["awhile", ["less", ["len", "r"], 3],
                    ["seq",
                        ["assign", "c", ["arr"]],
                        ["awhile", ["less", ["len", "c"], 3],
                            ["assign", "c", ["add", "c", ["arr", 0]]]],
                        ["assign", "r", ["add", "r", ["arr", "c"]]]]]])
        self.assertEqual(self.go("r"), [[0, 0, 0], [0, 0, 0], [0, 0, 0]])

    def test_is_name(self):
        self.assertEqual(self.go(["is_name", "a"]), True)
        self.assertEqual(self.go(["is_name", 5]), False)
        self.assertEqual(self.go(["is_name", ["neg", 5]]), False)

    def test_for(self):
        self.assertEqual(self.go(["seq",
            ["define", "sum", 0],
            ["for", "i", ["arr", 5, 6, 7, 8, 9], ["seq",
                ["assign", "sum", ["add", "sum", "i"]]]],
            "sum"]), 35)

        self.assertEqual(self.go(["seq",
            ["define", "sum", 0],
            ["for", "i", ["arr", 5, 6, 7, 8, 9], ["seq",
                ["when", ["equal", "i", 8], ["break", None]],
                ["assign", "sum", ["add", "sum", "i"]]]],
            "sum"]), 18)

        self.assertEqual(self.go(["seq",
            ["define", "sum", 0],
            ["for", "i", ["arr", 5, 6, 7, 8, 9], ["seq",
                ["when", ["equal", "i", 7], ["continue"]],
                ["assign", "sum", ["add", "sum", "i"]]]],
            "sum"]), 28)

    # see https://zenn.dev/link/comments/ea605f282d4c97
    def test_letcc_generator(self):
        self.go(["define", "g3", ["gfunc", ["n"], ["seq",
                ["yield", "n"],
                ["assign", "n", ["add", "n", 1]],
                ["yield", "n"],
                ["assign", "n", ["add", "n", 1]],
                ["yield", "n"]]]])

        self.go(["define", "gsum", ["func", ["gen"],
                ["aif", ["gen"], ["add", "it", ["gsum", "gen"]], 0]]])
        self.assertEqual(self.go(["gsum", ["g3", 2]]), 9)
        self.assertEqual(self.go(["gsum", ["g3", 5]]), 18)

        self.go(["define", "walk", ["gfunc", ["tree"], ["seq",
                ["define", "_walk", ["func",["t"], ["seq",
                    ["if", ["is_arr", ["first", "t"]],
                        ["_walk", ["first", "t"]],
                        ["yield", ["first", "t"]]],
                    ["if", ["is_arr", ["last", "t"]],
                        ["_walk", ["last", "t"]],
                        ["yield", ["last", "t"]]]]]],
                ["_walk", "tree"]]]])

        self.go(["define", "gen", ["walk", ["q", [[[5, 6], 7], [8, [9, 10]]]]]])
        self.assertEqual(self.printed(["awhile", ["gen"], ["print", "it"]]),
                         (None, "5\n6\n7\n8\n9\n10\n"))

    def test_agen(self):
        self.go(["define", "gen", ["agen", ["q", [2, 3, 4]]]])
        self.assertEqual(self.go(["gen"]), 2)
        self.assertEqual(self.go(["gen"]), 3)
        self.assertEqual(self.go(["gen"]), 4)
        self.assertEqual(self.go(["gen"]), None)

        self.go(["define", "gen0", ["agen", ["q", []]]])
        self.assertEqual(self.go(["gen"]), None)

    def test_gfor(self):
        self.assertEqual(self.printed(["gfor", "n", ["agen", ["q", []]],
                                    ["print", "n"]]),
                         (None, ""))
        self.assertEqual(self.printed(["gfor", "n", ["agen", ["q", [2, 3, 4]]],
                                    ["print", "n"]]),
                         (None, "2\n3\n4\n"))
        self.assertEqual(self.printed(["gfor", "n", ["agen", ["q", [2, 3, 4, 5, 6]]],
                                    ["seq",
                                        ["when", ["equal", "n", 5], ["break", None]],
                                        ["when", ["equal", "n", 3], ["continue"]],
                                        ["print", "n"]]]),
                         (None, "2\n4\n"))

class TestProblems(TestToig):

    def test_factorial(self):
        self.go(["define", "factorial", ["func", ["n"],
                ["if", ["equal", "n", 1],
                    1,
                    ["mul", "n", ["factorial", ["sub", "n", 1]]]]]])
        self.assertEqual(self.go(["factorial", 1]), 1)
        self.assertEqual(self.go(["factorial", 10]), 3628800)
        # print(run(["factorial", 1500]))

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

    def test_macro_firstclass(self):
        self.assertEqual(self.go([["func", ["op", "a", "b"], ["op", "a", "b"]], "and", True, False]), False)
        self.assertEqual(self.go([["func", ["op", "a", "b"], ["op", "a", "b"]], "or", True, False]), True)

        self.assertEqual(self.go([[["func", [], "and"]], True, False]), False)
        self.assertEqual(self.go([[["func", [], "or"]], True, False]), True)

        self.assertEqual(self.go(["map",
                                ["arr", "and", "or"],
                                ["func", ["op"], ["op", True, False]]]),
                        [False, True])

    def test_sieve(self):
        self.go(["define", "n", 30])
        self.go(["define", "sieve", ["add",
                ["mul", ["arr", False], 2],
                ["mul", ["arr", True], ["sub", "n", 2]]]])
        self.go(["define", "j", None])
        self.go(["for", "i", ["range", 2, "n"],
                ["when", ["get_at", "sieve", "i"],
                    ["seq",
                        ["assign", "j", ["mul", "i", "i"]],
                        ["while", ["less", "j", "n"], ["seq",
                            ["set_at", "sieve", "j", False],
                            ["assign", "j", ["add", "j", "i"]]]]]]])
        self.go(["define", "primes", ["arr"]])
        self.go(["for", "i", ["range", 0, "n"],
                ["when", ["get_at", "sieve", "i"],
                    ["assign", "primes", ["append", "primes", "i"]]]])
        self.assertEqual(self.go("primes"), [2, 3, 5, 7, 11, 13, 17, 19, 23, 29])

    def test_let(self):
        self.go(["define", "let", ["macro", ["bindings", "body"], ["seq",
                ["define", "defines", ["func", ["bindings"],
                    ["map", "bindings", ["func", ["b"], ["qq",
                        ["define",
                         ["!", ["first", "b"]],
                         ["!", ["last", "b"]]]]]]]],
                ["qq", ["scope", ["seq",
                    ["!!", ["defines", "bindings"]],
                    ["!","body"]]]]]]])
        self.assertEqual(self.expanded(["let", [["a", 5], ["b", 6]], ["add", "a", "b"]]),
                         ["scope", ["seq",
                             ["define", "a", 5],
                             ["define", "b", 6],
                             ["add", "a", "b"]]])
        self.assertEqual(self.go(["let", [["a", 5], ["b", 6]], ["add", "a", "b"]]), 11)

    def test_cond(self):
        self.go(["define", "cond", ["macro", [["*", "clauses"]],
                ["seq",
                    ["define", "_cond", ["func", ["clauses"],
                        ["if", ["equal", "clauses", ["arr"]],
                            None,
                            ["seq",
                                ["define", "clause", ["first", "clauses"]],
                                ["define", "cnd", ["first", "clause"]],
                                ["define", "thn", ["last", "clause"]],
                                ["qq", ["if", ["!", "cnd"],
                                        ["!", "thn"],
                                        ["!", ["_cond", ["rest", "clauses"]]]]]]]]],
                    ["_cond", "clauses"]]]])
        self.assertEqual(self.expanded(
            ["cond",
                [["equal", "n", 0], 0],
                [["equal", "n", 1], 1],
                [True, ["add", ["fib", ["sub", "n", 1]], ["fib", ["sub", "n", 2]]]]]),
            ["if", ["equal", "n", 0], 0,
                ["if", ["equal", "n", 1], 1,
                    ["if", True,
                        ["add", ["fib", ["sub", "n", 1]], ["fib", ["sub", "n", 2]]],
                        None]]])
        self.go(["define", "fib", ["func", ["n"],
                ["cond",
                    [["equal", "n", 0], 0],
                    [["equal", "n", 1], 1],
                    [True, ["add", ["fib", ["sub", "n", 1]], ["fib", ["sub", "n", 2]]]]]]])
        self.assertEqual(self.go(["fib", 0]), 0)
        self.assertEqual(self.go(["fib", 1]), 1)
        self.assertEqual(self.go(["fib", 2]), 1)
        self.assertEqual(self.go(["fib", 3]), 2)
        self.assertEqual(self.go(["fib", 10]), 55)

    def test_letcc_return(self):
        self.go(["define", "early-return", ["func", ["n"],
                ["letcc", "return", ["seq",
                    ["if", ["equal", "n", 1], ["return", 5], 6],
                    7]]]])
        self.assertEqual(self.go(["early-return", 1]), 5)
        self.assertEqual(self.go(["early-return", 2]), 7)

        self.go(["define", "runc", ["macro", ["params", "body"], ["qq",
                ["func", ["!", "params"], ["letcc", "return", ["!", "body"]]]]]])
        self.go(["define", "early_return_runc", ["runc", ["n"], ["seq",
                ["if", ["equal", "n", 1], ["return", 5], 6],
                7]]])
        self.assertEqual(self.go(["early_return_runc", 1]), 5)
        self.assertEqual(self.go(["early_return_runc", 2]), 7)

        self.go(["define", "early_return_runc2", ["runc", ["n"], ["seq",
                ["if", ["equal", ["early_return_runc", "n"], 5], ["return", 6], 7],
                8]]])
        self.assertEqual(self.go(["early_return_runc2", 1]), 6)
        self.assertEqual(self.go(["early_return_runc2", 2]), 8)

    def test_letcc_escape(self):
        self.go(["define", "riskyfunc", ["func", ["n", "escape"], ["seq",
                ["if", ["equal", "n", 1], ["escape", 5], 6],
                7]]])
        self.go(["define", "middlefunc", ["func", ["n", "escape"], ["seq",
                ["riskyfunc", "n", "escape"],
                8]]])
        self.go(["define", "parentfunc", ["func", ["n"],
                ["letcc", "escape", ["middlefunc", "n", "escape"]]]])
        self.assertEqual(self.go(["parentfunc", 1]), 5)
        self.assertEqual(self.go(["parentfunc", 2]), 8)

    def test_letcc_except(self):
        self.go(["define", "raise", None])
        self.go(["define", "riskyfunc", ["func", ["n"], ["seq",
                ["if", ["equal", "n", 1], ["raise", 5], None],
                ["print", 6]]]])
        self.go(["define", "middlefunc", ["func", ["n"], ["seq",
                ["riskyfunc", "n"],
                ["print", 7]]]])
        self.go(["define", "parentfunc", ["func", ["n"], ["seq",
                ["letcc", "escape", ["seq",
                    ["assign", "raise", ["func", ["e"], ["escape", ["seq",
                        ["print", "e"]]]]],
                    ["middlefunc", "n"],
                    ["print", 8]]],
                ["print", 9]]]])
        self.assertEqual(self.printed(["parentfunc", 1]), (None, "5\n9\n"))
        self.assertEqual(self.printed(["parentfunc", 2]), (None, "6\n7\n8\n9\n"))

    def test_letcc_try(self):
        self.go(["define", "raise", ["func", ["e"], ["error", ["q", "Raised outside of try:"], "e"]]])
        self.go(["define", "try", ["macro", ["try-expr", "_", "exc-var", "exc-expr"], ["qq",
                ["scope", ["seq",
                    ["define", "prev-raise", "raise"],
                    ["letcc", "escape", ["seq",
                        ["assign", "raise", ["func", [["!", "exc-var"]],
                            ["escape", ["!", "exc-expr"]]]],
                        ["!", "try-expr"]]],
                    ["assign", "raise", "prev-raise"]]]]]])

        self.go(["define", "riskyfunc", ["func", ["n"], ["seq",
                ["if", ["equal", "n", 1], ["raise", 5], None],
                ["print", 6]]]])
        self.go(["define", "middlefunc", ["func", ["n"], ["seq",
                ["riskyfunc", "n"],
                ["print", 7]]]])
        self.go(["define", "parentfunc", ["func", ["n"], ["seq",
                ["try", ["seq",
                    ["middlefunc", "n"],
                    ["print", 8]],
                    "except", "e", ["seq",
                        ["print", "e"]]],
                ["print", 9]]]])

        self.assertEqual(self.printed(["parentfunc", 1]), (None, "5\n9\n"))
        self.assertEqual(self.printed(["parentfunc", 2]), (None, "6\n7\n8\n9\n"))

        self.go(["define", "nested", ["func", ["n"], ["seq",
                ["try", ["seq",
                    ["if", ["equal", "n", 1], ["raise", 5], None],
                    ["print", 6],
                    ["try", ["seq",
                        ["if", ["equal", "n", 2], ["raise", 7], None],
                        ["print", 8]],
                        "except", "e", ["seq",
                            ["print", ["q", "exception inner try:"], "e"]]],
                    ["if", ["equal", "n", 3], ["raise", 9], None],
                    ["print", 10]],
                    "except", "e", ["seq",
                        ["print", ["q", "exception outer try:"], "e"]]],
                ["print", 11]]]])

        self.assertEqual(self.printed(["nested", 1]), (None, "exception outer try: 5\n11\n"))
        self.assertEqual(self.printed(["nested", 2]), (None, "6\nexception inner try: 7\n10\n11\n"))
        self.assertEqual(self.printed(["nested", 3]), (None, "6\n8\nexception outer try: 9\n11\n"))
        self.assertEqual(self.printed(["nested", 4]), (None, "6\n8\n10\n11\n"))

        self.assertTrue(self.fails(["raise", 5]))

    def test_letcc_concurrent(self):
        self.go(["define", "tasks", ["arr"]])
        self.go(["define", "add-task", ["func", ["t"],
                ["assign", "tasks", ["append", "tasks", "t"]]]])
        self.go(["define", "start", ["func", [],
                ["while", ["not_equal", "tasks", ["arr"]], ["seq",
                    ["define", "next-task", ["first", "tasks"]],
                    ["assign", "tasks", ["rest", "tasks"]],
                    ["when", ["next-task"], ["add-task", "next-task"]]]]]])

        self.go(["define", "three-times", ["gfunc", ["n"], ["seq",
                ["print", "n"],
                ["yield", True],
                ["print", "n"],
                ["yield", True],
                ["print", "n"],
            ]]])

        self.go(["add-task", ["three-times", 5]])
        self.go(["add-task", ["three-times", 6]])
        self.go(["add-task", ["three-times", 7]])

        self.assertEqual(self.printed(["start"]), (None, "5\n6\n7\n5\n6\n7\n5\n6\n7\n"))

if __name__ == "__main__":
    unittest.main()