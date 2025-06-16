import unittest
from unittest.mock import patch
from io import StringIO

from toig import init_env, stdlib, eval

def fails(expr):
    try: eval(expr)
    except AssertionError: return True
    else: return False

def expanded(expr):
    return eval(["expand", expr])

def printed(expr):
    with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
        val = eval(expr)
        return (val, mock_stdout.getvalue())

class TestToig(unittest.TestCase):
    def setUp(self):
        init_env()
        stdlib()

class TestCore(TestToig):
    def test_primary(self):
        self.assertEqual(eval(None), None)
        self.assertEqual(eval(5), 5)
        self.assertEqual(eval(True), True)
        self.assertEqual(eval(False), False)

    def test_define(self):
        self.assertEqual(eval(["define", "a", ["add", 5, 6]]), 11)
        self.assertEqual(eval("a"), 11)
        # self.assertTrue(fails(["define", "a", 6]))
        self.assertEqual(eval(["define", "a", 6]), 6)
        self.assertEqual(eval("a"), 6)
        self.assertTrue(fails("b"))
        self.assertEqual(printed([["func", [], ["do",
                            ["print", ["define", "a", 5]],
                            ["print", "a"]]]]), (None, "5\n5\n"))
        self.assertEqual(eval("a"), 6)

    def test_assign(self):
        self.assertEqual(eval(["define", "a", 5]), 5)
        self.assertEqual(eval(["assign", "a", ["add", 5, 6]]), 11)
        self.assertEqual(eval("a"), 11)
        self.assertTrue(fails(["assign", "b", 6]))
        self.assertEqual(eval([["func", [], ["assign", "a", 6]]]), 6)
        self.assertEqual(printed([["func", [], ["do",
                            ["print", ["assign", "a", 6]],
                            ["print", "a"]]]]), (None, "6\n6\n"))
        self.assertEqual(eval("a"), 6)

    def test_do(self):
        self.assertEqual(eval(["do"]), None)
        self.assertEqual(eval(["do", 5]), 5)
        self.assertEqual(eval(["do", 5, 6]), 6)
        self.assertEqual(printed(["do", ["print", 5]]), (None, "5\n"))
        self.assertEqual(printed(["do", ["print", 5], ["print", 6]]), (None, "5\n6\n"))

    def test_if(self):
        self.assertEqual(eval(["if", ["equal", 5, 5], ["add", 7, 8], ["add", 9, 10]]), 15)
        self.assertEqual(eval(["if", ["equal", 5, 6], ["add", 7, 8], ["add", 9, 10]]), 19)
        self.assertTrue(fails(["if", True, 5]))

    def test_builtin_math(self):
        self.assertEqual(eval(["add", ["add", 5, 6], ["add", 7, 8]]), 26)
        self.assertEqual(eval(["sub", ["sub", 26, 8], ["add", 5, 6]]), 7)
        self.assertEqual(eval(["mul", ["mul", 5, 6], ["mul", 7, 8]]), 1680)
        self.assertEqual(eval(["div", ["div", 1680, 8], ["mul", 5, 6]]), 7)
        self.assertEqual(eval(["mod", ["div", 1704, 8], ["mul", 5, 6]]), 3)
        self.assertEqual(eval(["neg", ["add", 5, 6]]), -11)
        self.assertTrue(fails(["add", 5]))
        self.assertTrue(fails(["add", 5, 6, 7]))

    def test_builtin_equality(self):
        self.assertEqual(eval(["equal", ["add", 5, 6], ["add", 6, 5]]), True)
        self.assertEqual(eval(["equal", ["add", 5, 6], ["add", 7, 8]]), False)
        self.assertEqual(eval(["not_equal", ["add", 5, 6], ["add", 6, 5]]), False)
        self.assertEqual(eval(["not_equal", ["add", 5, 6], ["add", 7, 8]]), True)

    def test_builtin_comparison(self):
        self.assertEqual(eval(["less", ["add", 5, 6], ["add", 3, 7]]), False)
        self.assertEqual(eval(["less", ["add", 5, 6], ["add", 4, 7]]), False)
        self.assertEqual(eval(["less", ["add", 5, 6], ["add", 4, 8]]), True)
        self.assertEqual(eval(["greater", ["add", 5, 6], ["add", 3, 7]]), True)
        self.assertEqual(eval(["greater", ["add", 5, 6], ["add", 4, 7]]), False)
        self.assertEqual(eval(["greater", ["add", 5, 6], ["add", 4, 8]]), False)

        self.assertEqual(eval(["less_equal", ["add", 5, 6], ["add", 3, 7]]), False)
        self.assertEqual(eval(["less_equal", ["add", 5, 6], ["add", 4, 7]]), True)
        self.assertEqual(eval(["less_equal", ["add", 5, 6], ["add", 4, 8]]), True)
        self.assertEqual(eval(["greater_equal", ["add", 5, 6], ["add", 3, 7]]), True)
        self.assertEqual(eval(["greater_equal", ["add", 5, 6], ["add", 4, 7]]), True)
        self.assertEqual(eval(["greater_equal", ["add", 5, 6], ["add", 4, 8]]), False)

    def test_builtin_logic(self):
        self.assertEqual(eval(["not", ["equal", ["add", 5, 6], ["add", 6, 5]]]), False)
        self.assertEqual(eval(["not", ["equal", ["add", 5, 6], ["add", 7, 8]]]), True)

    def test_print(self):
        self.assertEqual(printed(["print", None]), (None, "None\n"))
        self.assertEqual(printed(["print", 5]), (None, "5\n"))
        self.assertEqual(printed(["print", True]), (None, "True\n"))
        self.assertEqual(printed(["print", False]), (None, "False\n"))
        self.assertEqual(printed(["print"]), (None, "\n"))
        self.assertEqual(printed(["print", 5, 6]), (None, "5 6\n"))

    def test_array(self):
        self.assertEqual(eval(["arr"]), [])
        self.assertEqual(eval(["arr", ["add", 5, 6]]), [11])

        eval(["define", "a", ["arr", 5, 6, ["arr", 7, 8]]])
        self.assertEqual(eval("a"), [5, 6, [7, 8]])

        self.assertEqual(eval(["is_arr", 5]), False)
        self.assertEqual(eval(["is_arr", ["arr"]]), True)
        self.assertEqual(eval(["is_arr", "a"]), True)
        self.assertTrue(fails(["is_arr"]))
        self.assertTrue(fails(["is_arr", 5, 6]))

        self.assertEqual(eval(["len", ["arr"]]), 0)
        self.assertEqual(eval(["len", "a"]), 3)
        self.assertTrue(fails(["len"]))
        self.assertTrue(fails(["len", 5, 6]))

        self.assertEqual(eval(["getat", "a", 1]), 6)
        self.assertEqual(eval(["getat", "a", -1]), [7, 8])
        self.assertEqual(eval(["getat", ["getat", "a", 2], 1]), 8)
        self.assertTrue(fails(["getat", "a"]))
        self.assertTrue(fails(["getat", "a", 5, 6]))

        self.assertEqual(eval(["setat", "a", 1, 9]), 9)
        self.assertEqual(eval("a"), [5, 9, [7, 8]])
        self.assertEqual(eval(["setat", ["getat", "a", 2], -1, 10]), 10)
        self.assertEqual(eval("a"), [5, 9, [7, 10]])
        self.assertTrue(fails(["setat", "a", 1]))
        self.assertTrue(fails(["setat", "a", 1, 5, 6]))

        self.assertTrue(fails(["slice"]))
        self.assertEqual(eval(["slice", "a"]), [5, 9, [7, 10]])
        self.assertEqual(eval(["slice", "a", 1]), [9, [7, 10]])
        self.assertEqual(eval(["slice", "a", -2]), [9, [7, 10]])
        self.assertEqual(eval(["slice", "a", 1, 2]), [9])
        self.assertEqual(eval(["slice", "a", 1, -1]), [9])
        self.assertEqual(eval(["slice", "a", 2, 0, -1]), [[7, 10], 9])
        self.assertTrue(fails(["slice", "a", 1, 2, 3, 4]))

        self.assertEqual(eval(["add", ["arr", 5], ["arr", 6]]), [5, 6])

    def test_func(self):
        self.assertEqual(eval([["func", ["n"], ["add", 5, "n"]], 6]), 11)
        self.assertTrue(fails([["func", ["n"], ["add", 5, "n"]]]))
        self.assertTrue(fails([["func", ["n"], ["add", 5, "n"]], 6, 7]))

        self.assertEqual(eval([["func", [["*", "rest"]], "rest"]]), [])
        self.assertEqual(eval([["func", ["a", ["*", "rest"]], ["arr", "a", "rest"]], 5]), [5, []])
        self.assertEqual(eval([["func", ["a", ["*", "rest"]], ["arr", "a", "rest"]], 5, 6]), [5, [6]])
        self.assertEqual(eval([["func", ["a", ["*", "rest"]], ["arr", "a", "rest"]], 5, 6, 7]), [5, [6, 7]])
        self.assertTrue(fails([["func", [["*", "rest"], "a"], ["arr", "a", "rest"]], 5]))

    def test_closure_adder(self):
        eval(["define", "make_adder", ["func", ["n"],
                ["func", ["m"], ["add", "n", "m"]]]])
        self.assertEqual(eval([["make_adder", 5], 6]), 11)

    def test_closure_counter(self):
        eval(["define", "make_counter", ["func", [], ["do",
                ["define", "c", 0],
                ["func", [], ["assign", "c", ["add", "c", 1]]]]]])
        eval(["define", "counter1", ["make_counter"]])
        eval(["define", "counter2", ["make_counter"]])
        self.assertEqual(eval(["counter1"]), 1)
        self.assertEqual(eval(["counter1"]), 2)
        self.assertEqual(eval(["counter2"]), 1)
        self.assertEqual(eval(["counter2"]), 2)
        self.assertEqual(eval(["counter1"]), 3)
        self.assertEqual(eval(["counter2"]), 3)

    def test_quote(self):
        self.assertEqual(eval(["q", 5]), 5)
        self.assertEqual(eval(["q", ["add", 5, 6]]), ["add", 5, 6])

    def test_qq(self):
        self.assertEqual(eval(["qq", 5]), 5)
        self.assertEqual(eval(["qq", ["add", 5, 6]]), ["add", 5, 6])
        self.assertEqual(eval(["qq", ["!", ["add", 5, 6]]]), 11)
        self.assertEqual(eval(["qq", ["mul", 4, ["!", ["add", 5, 6]]]]), ["mul", 4, 11])
        self.assertEqual(eval(["qq", ["add", ["!!", ["arr", 5, 6]]]]), ["add", 5, 6])
        self.assertTrue(fails(["qq", ["add", ["!!", 5]]]))

    def test_macro(self):
        self.assertEqual(expanded([["macro", [], ["q", "abc"]]]), "abc")
        self.assertEqual(
            expanded([["macro", ["a"], ["arr", ["q", "mul"], "a", "a"]], ["add", 5, 6]]),
            ["mul", ["add", 5, 6], ["add", 5, 6]])

        eval(["define", "build_exp", ["macro", ["op", ["*", "r"]],
                ["add", ["arr", "op"], "r"]]])
        self.assertEqual(expanded(["build_exp", "add"]), ["add"])
        self.assertEqual(expanded(["build_exp", "add", 5]), ["add", 5])
        self.assertEqual(expanded(["build_exp", "add", 5, 6]), ["add", 5, 6])

        self.assertTrue(fails([["macro", [["*", "r"], "a"], 5]]))

    def test_letcc(self):
        self.assertEqual(eval(["letcc", "skip-to", ["add", 5, 6]]), 11)
        self.assertEqual(eval(["letcc", "skip-to", ["add", ["skip-to", 5], 6]]), 5)
        self.assertEqual(eval(["add", 5, ["letcc", "skip-to", ["skip-to", 6]]]), 11)
        self.assertEqual(eval(["letcc", "skip1", ["add", ["skip1", ["letcc", "skip2", ["add", ["skip2", 5], 6]]], 7]]), 5)

        eval(["define", "inner", ["func", ["raise"], ["raise", 5]]])
        eval(["define", "outer", ["func", [],
                [ "letcc", "raise", ["add", ["inner", "raise"], 6]]]])
        self.assertEqual(eval(["outer"]), 5)

    def test_letcc_reuse(self):
        eval(["define", "add5", None])
        self.assertEqual(eval(["add", 5, ["letcc", "cc", ["do", ["assign", "add5", "cc"], 6]]]), 11)
        self.assertEqual(eval(["add5", 7]), 12)
        self.assertEqual(eval(["add5", 8]), 13)

class TestStdlib(TestToig):
    def test_id(self):
        self.assertEqual(eval(["id", ["add", 5, 6]]), 11)

    def test_inc_dec(self):
        self.assertEqual(eval(["inc", ["add", 5, 6]]), 12)
        self.assertEqual(eval(["dec", ["add", 5, 6]]), 10)

    def test_first_rest_last(self):
        self.assertEqual(eval(["first", ["arr", 5, 6, 7]]), 5)
        self.assertEqual(eval(["rest", ["arr", 5, 6, 7]]), [6, 7])
        self.assertEqual(eval(["last", ["arr", 5, 6, 7]]), 7)

    def test_append_prepend(self):
        self.assertEqual(eval(["append", ["arr", 5, 6], ["inc", 7]]), [5, 6, 8])
        self.assertEqual(eval(["prepend", ["inc", 5], ["arr", 7, 8]]), [6, 7, 8])

    def test_map(self):
        self.assertEqual(eval(["map", ["arr"], "inc"]), [])
        self.assertEqual(eval(["map", ["arr", 5, 6, 7], "inc"]), [6, 7, 8])

    def test_range(self):
        self.assertEqual(eval(["range", 5, 5]), [])
        self.assertEqual(eval(["range", 5, 8]), [5, 6, 7])

    def test_scope(self):
        self.assertEqual(expanded(["scope", ["do", ["define", "a", 5]]]),
                         [["func", [], ["do", ["define", "a", 5]]]])
        self.assertEqual(printed(["do",
            ["define", "a", 5],
            ["scope", ["do", ["define", "a", 6], ["print", "a"]]],
            ["print", "a"]]), (None, "6\n5\n"))

    def test_when(self):
        eval(["define", "a", 30])
        eval(["define", "b", 5])
        self.assertEqual(eval(["when", ["not", ["equal", "b", 0]], ["div", "a", "b"]]), 6)
        eval(["assign", "b", 0])
        self.assertEqual(eval(["when", ["not", ["equal", "b", 0]], ["div", "a", "b"]]), None)

    def test_aif(self):
        self.assertEqual(eval(["aif", ["inc", 5], ["inc", "it"], 8]), 7)
        self.assertEqual(eval(["aif", ["dec", 1], 5, "it"]), 0)

    def test_and_or(self):
        self.assertEqual(expanded(["and", ["equal", "a", 0], ["equal", "b", 0]]),
                         ["aif", ["equal", "a", 0], ["equal", "b", 0], "it"])
        self.assertEqual(eval(["and", False, "nosuchvariable"]), False)
        self.assertEqual(eval(["and", None, "nosuchvariable"]), None)
        self.assertEqual(eval(["and", True, False]), False)
        self.assertEqual(eval(["and", True, None]), None)
        self.assertEqual(eval(["and", True, True]), True)
        self.assertEqual(eval(["and", True, 5]), 5)

        self.assertEqual(expanded(["or", ["equal", "a", 0], ["equal", "b", 0]]),
                         ["aif", ["equal", "a", 0], "it", ["equal", "b", 0]])
        self.assertEqual(eval(["or", False, False]), False)
        self.assertEqual(eval(["or", False, None]), None)
        self.assertEqual(eval(["or", False, True]), True)
        self.assertEqual(eval(["or", False, 5]), 5)
        self.assertEqual(eval(["or", True, "nosuchvariable"]), True)
        self.assertEqual(eval(["or", 5, "nosuchvariable"]), 5)

        self.assertEqual(printed(["scope", ["do",
            ["define", "foo", 5],
            ["print", ["or", "foo", ["q", "default"]]],
            ["assign", "foo", None],
            ["print", ["or", "foo", ["q", "default"]]]
        ]]), (None, "5\ndefault\n"))

        self.assertEqual(
            expanded(["and", ["or", ["equal", 5, 6], ["equal", 7, 7]], ["equal", 8, 8]]),
            ["aif", ["or", ["equal", 5, 6], ["equal", 7, 7]], ["equal", 8, 8], "it"])
        self.assertEqual(
            eval(["and", ["or", ["equal", 5, 6], ["equal", 7, 7]], ["equal", 8, 8]]),
            True)

    def test_while(self):
        self.assertEqual(eval(["do",
            ["define", "i", 0],
            ["define", "sum", 0],
            ["while", ["less", "i", 10], ["do",
                ["assign", "sum", ["add", "sum", "i"]],
                ["assign", "i", ["add", "i", 1]],
                "sum"]]
        ]), 45)

        eval(["do",
                ["define", "a", 0],
                ["define", "b", ["arr"]],
                ["while", ["less", "a", 10], ["do",
                    ["when", ["equal", "a", 5], ["break", None]],
                    ["assign", "a", ["add", "a", 1]],
                    ["when", ["equal", "a", 3], ["continue"]],
                    ["assign", "b", ["add", "b", ["arr", "a"]]],
                    ]]])
        self.assertEqual(eval("a"), 5)
        self.assertEqual(eval("b"), [1, 2, 4, 5])

        eval(["do",
                ["define", "r", ["arr"]],
                ["define", "c", ["arr"]],
                ["while", ["less", ["len", "r"], 3],
                    ["do",
                        ["assign", "c", ["arr"]],
                        ["while", ["less", ["len", "c"], 3],
                            ["assign", "c", ["add", "c", ["arr", 0]]]],
                        ["assign", "r", ["add", "r", ["arr", "c"]]]]]])
        self.assertEqual(eval("r"), [[0, 0, 0], [0, 0, 0], [0, 0, 0]])

    def test_awhile(self):
        eval(["do",
                ["define", "a", 0],
                ["define", "b", ["arr"]],
                ["awhile", ["less", "a", 10], ["do",
                    ["when", ["equal", "a", 5], ["break", None]],
                    ["assign", "a", ["add", "a", 1]],
                    ["when", ["equal", "a", 3], ["continue"]],
                    ["assign", "b", ["add", "b", ["arr", "a"]]],
                    ]]])
        self.assertEqual(eval("a"), 5)
        self.assertEqual(eval("b"), [1, 2, 4, 5])

        eval(["do",
                ["define", "r", ["arr"]],
                ["define", "c", ["arr"]],
                ["awhile", ["less", ["len", "r"], 3],
                    ["do",
                        ["assign", "c", ["arr"]],
                        ["awhile", ["less", ["len", "c"], 3],
                            ["assign", "c", ["add", "c", ["arr", 0]]]],
                        ["assign", "r", ["add", "r", ["arr", "c"]]]]]])
        self.assertEqual(eval("r"), [[0, 0, 0], [0, 0, 0], [0, 0, 0]])

    def test_is_name(self):
        self.assertEqual(eval(["is_name", "a"]), True)
        self.assertEqual(eval(["is_name", 5]), False)
        self.assertEqual(eval(["is_name", ["neg", 5]]), False)

    def test_for(self):
        self.assertEqual(eval(["do",
            ["define", "sum", 0],
            ["for", "i", ["arr", 5, 6, 7, 8, 9], ["do",
                ["assign", "sum", ["add", "sum", "i"]]]],
            "sum"]), 35)

        self.assertEqual(eval(["do",
            ["define", "sum", 0],
            ["for", "i", ["arr", 5, 6, 7, 8, 9], ["do",
                ["when", ["equal", "i", 8], ["break", None]],
                ["assign", "sum", ["add", "sum", "i"]]]],
            "sum"]), 18)

        self.assertEqual(eval(["do",
            ["define", "sum", 0],
            ["for", "i", ["arr", 5, 6, 7, 8, 9], ["do",
                ["when", ["equal", "i", 7], ["continue"]],
                ["assign", "sum", ["add", "sum", "i"]]]],
            "sum"]), 28)


    # see https://zenn.dev/link/comments/ea605f282d4c97
    def test_letcc_generator(self):
        eval(["define", "g3", ["gfunc", "n", ["do",
                ["yield", "n"],
                ["assign", "n", ["add", "n", 1]],
                ["yield", "n"],
                ["assign", "n", ["add", "n", 1]],
                ["yield", "n"]]]])

        eval(["define", "gsum", ["func", ["gen"],
                ["aif", ["gen"], ["add", "it", ["gsum", "gen"]], 0]]])
        self.assertEqual(eval(["gsum", ["g3", 2]]), 9)
        self.assertEqual(eval(["gsum", ["g3", 5]]), 18)

        eval(["define", "walk", ["gfunc", "tree", ["do",
                ["define", "_walk", ["func",["t"], ["do",
                    ["if", ["is_arr", ["first", "t"]],
                        ["_walk", ["first", "t"]],
                        ["yield", ["first", "t"]]],
                    ["if", ["is_arr", ["last", "t"]],
                        ["_walk", ["last", "t"]],
                        ["yield", ["last", "t"]]]]]],
                ["_walk", "tree"]]]])

        eval(["define", "gen", ["walk", ["q", [[[5, 6], 7], [8, [9, 10]]]]]])
        self.assertEqual(printed(["awhile", ["gen"], ["print", "it"]]),
                         (None, "5\n6\n7\n8\n9\n10\n"))

    def test_agen(self):
        eval(["define", "gen", ["agen", ["q", [2, 3, 4]]]])
        self.assertEqual(eval(["gen"]), 2)
        self.assertEqual(eval(["gen"]), 3)
        self.assertEqual(eval(["gen"]), 4)
        self.assertEqual(eval(["gen"]), None)

        eval(["define", "gen0", ["agen", ["q", []]]])
        self.assertEqual(eval(["gen"]), None)

    def test_gfor(self):
        self.assertEqual(printed(["gfor", "n", ["agen", ["q", []]],
                                    ["print", "n"]]),
                         (None, ""))
        self.assertEqual(printed(["gfor", "n", ["agen", ["q", [2, 3, 4]]],
                                    ["print", "n"]]),
                         (None, "2\n3\n4\n"))
        self.assertEqual(printed(["gfor", "n", ["agen", ["q", [2, 3, 4, 5, 6]]],
                                    ["do",
                                        ["when", ["equal", "n", 5], ["break", None]],
                                        ["when", ["equal", "n", 3], ["continue"]],
                                        ["print", "n"]]]),
                         (None, "2\n4\n"))

class TestProblems(TestToig):
    def test_factorial(self):
        eval(["define", "factorial", ["func", ["n"],
                ["if", ["equal", "n", 1],
                    1,
                    ["mul", "n", ["factorial", ["sub", "n", 1]]]]]])
        self.assertEqual(eval(["factorial", 1]), 1)
        self.assertEqual(eval(["factorial", 10]), 3628800)
        # print(run(["factorial", 1500]))

    def test_fib(self):
        eval(["define", "fib", ["func", ["n"],
                ["if", ["equal", "n", 0], 0,
                ["if", ["equal", "n", 1], 1,
                ["add", ["fib", ["sub", "n", 1]], ["fib", ["sub", "n", 2]]]]]]])
        self.assertEqual(eval(["fib", 0]), 0)
        self.assertEqual(eval(["fib", 1]), 1)
        self.assertEqual(eval(["fib", 2]), 1)
        self.assertEqual(eval(["fib", 3]), 2)
        self.assertEqual(eval(["fib", 10]), 55)

    def test_macro_firstclass(self):
        self.assertEqual(eval([["func", ["op", "a", "b"], ["op", "a", "b"]], "and", True, False]), False)
        self.assertEqual(eval([["func", ["op", "a", "b"], ["op", "a", "b"]], "or", True, False]), True)

        self.assertEqual(eval([[["func", [], "and"]], True, False]), False)
        self.assertEqual(eval([[["func", [], "or"]], True, False]), True)

        self.assertEqual(eval(["map",
                                ["arr", "and", "or"],
                                ["func", ["op"], ["op", True, False]]]),
                        [False, True])

    def test_sieve(self):
        eval(["define", "n", 30])
        eval(["define", "sieve", ["add",
                ["mul", ["arr", False], 2],
                ["mul", ["arr", True], ["sub", "n", 2]]]])
        eval(["define", "j", None])
        eval(["for", "i", ["range", 2, "n"],
                ["when", ["getat", "sieve", "i"],
                    ["do",
                        ["assign", "j", ["mul", "i", "i"]],
                        ["while", ["less", "j", "n"], ["do",
                            ["setat", "sieve", "j", False],
                            ["assign", "j", ["add", "j", "i"]]]]]]])
        eval(["define", "primes", ["arr"]])
        eval(["for", "i", ["range", 0, "n"],
                ["when", ["getat", "sieve", "i"],
                    ["assign", "primes", ["append", "primes", "i"]]]])
        self.assertEqual(eval("primes"), [2, 3, 5, 7, 11, 13, 17, 19, 23, 29])

    def test_let(self):
        eval(["define", "let", ["macro", ["bindings", "body"], ["do",
                ["define", "defines", ["func", ["bindings"],
                    ["map", "bindings", ["func", ["b"], ["qq",
                        ["define",
                         ["!", ["first", "b"]],
                         ["!", ["last", "b"]]]]]]]],
                ["qq", ["scope", ["do",
                    ["!!", ["defines", "bindings"]],
                    ["!","body"]]]]]]])
        self.assertEqual(expanded(["let", [["a", 5], ["b", 6]], ["add", "a", "b"]]),
                         ["scope", ["do",
                             ["define", "a", 5],
                             ["define", "b", 6],
                             ["add", "a", "b"]]])
        self.assertEqual(eval(["let", [["a", 5], ["b", 6]], ["add", "a", "b"]]), 11)

    def test_cond(self):
        eval(["define", "cond", ["macro", [["*", "clauses"]],
                ["do",
                    ["define", "_cond", ["func", ["clauses"],
                        ["if", ["equal", "clauses", ["arr"]],
                            None,
                            ["do",
                                ["define", "clause", ["first", "clauses"]],
                                ["define", "cnd", ["first", "clause"]],
                                ["define", "thn", ["last", "clause"]],
                                ["qq", ["if", ["!", "cnd"],
                                        ["!", "thn"],
                                        ["!", ["_cond", ["rest", "clauses"]]]]]]]]],
                    ["_cond", "clauses"]]]])
        self.assertEqual(expanded(
            ["cond",
                [["equal", "n", 0], 0],
                [["equal", "n", 1], 1],
                [True, ["add", ["fib", ["sub", "n", 1]], ["fib", ["sub", "n", 2]]]]]),
            ["if", ["equal", "n", 0], 0,
                ["if", ["equal", "n", 1], 1,
                    ["if", True,
                        ["add", ["fib", ["sub", "n", 1]], ["fib", ["sub", "n", 2]]],
                        None]]])
        eval(["define", "fib", ["func", ["n"],
                ["cond",
                    [["equal", "n", 0], 0],
                    [["equal", "n", 1], 1],
                    [True, ["add", ["fib", ["sub", "n", 1]], ["fib", ["sub", "n", 2]]]]]]])
        self.assertEqual(eval(["fib", 0]), 0)
        self.assertEqual(eval(["fib", 1]), 1)
        self.assertEqual(eval(["fib", 2]), 1)
        self.assertEqual(eval(["fib", 3]), 2)
        self.assertEqual(eval(["fib", 10]), 55)

    def test_letcc_return(self):
        eval(["define", "early-return", ["func", ["n"],
                ["letcc", "return", ["do",
                    ["if", ["equal", "n", 1], ["return", 5], 6],
                    7]]]])
        self.assertEqual(eval(["early-return", 1]), 5)
        self.assertEqual(eval(["early-return", 2]), 7)

        eval(["define", "runc", ["macro", ["params", "body"], ["qq",
                ["func", ["!", "params"], ["letcc", "return", ["!", "body"]]]]]])
        eval(["define", "early_return_runc", ["runc", ["n"], ["do",
                ["if", ["equal", "n", 1], ["return", 5], 6],
                7]]])
        self.assertEqual(eval(["early_return_runc", 1]), 5)
        self.assertEqual(eval(["early_return_runc", 2]), 7)

        eval(["define", "early_return_runc2", ["runc", ["n"], ["do",
                ["if", ["equal", ["early_return_runc", "n"], 5], ["return", 6], 7],
                8]]])
        self.assertEqual(eval(["early_return_runc2", 1]), 6)
        self.assertEqual(eval(["early_return_runc2", 2]), 8)

    def test_letcc_escape(self):
        eval(["define", "riskyfunc", ["func", ["n", "escape"], ["do",
                ["if", ["equal", "n", 1], ["escape", 5], 6],
                7]]])
        eval(["define", "middlefunc", ["func", ["n", "escape"], ["do",
                ["riskyfunc", "n", "escape"],
                8]]])
        eval(["define", "parentfunc", ["func", ["n"],
                ["letcc", "escape", ["middlefunc", "n", "escape"]]]])
        self.assertEqual(eval(["parentfunc", 1]), 5)
        self.assertEqual(eval(["parentfunc", 2]), 8)

    def test_letcc_except(self):
        eval(["define", "raise", None])
        eval(["define", "riskyfunc", ["func", ["n"], ["do",
                ["if", ["equal", "n", 1], ["raise", 5], None],
                ["print", 6]]]])
        eval(["define", "middlefunc", ["func", ["n"], ["do",
                ["riskyfunc", "n"],
                ["print", 7]]]])
        eval(["define", "parentfunc", ["func", ["n"], ["do",
                ["letcc", "escape", ["do",
                    ["assign", "raise", ["func", ["e"], ["escape", ["do",
                        ["print", "e"]]]]],
                    ["middlefunc", "n"],
                    ["print", 8]]],
                ["print", 9]]]])
        self.assertEqual(printed(["parentfunc", 1]), (None, "5\n9\n"))
        self.assertEqual(printed(["parentfunc", 2]), (None, "6\n7\n8\n9\n"))

    def test_letcc_try(self):
        eval(["define", "raise", ["func", ["e"], ["error", ["q", "Raised outside of try:"], "e"]]])
        eval(["define", "try", ["macro", ["try-expr", "_", "exc-var", "exc-expr"], ["qq",
                ["scope", ["do",
                    ["define", "prev-raise", "raise"],
                    ["letcc", "escape", ["do",
                        ["assign", "raise", ["func", [["!", "exc-var"]],
                            ["escape", ["!", "exc-expr"]]]],
                        ["!", "try-expr"]]],
                    ["assign", "raise", "prev-raise"]]]]]])

        eval(["define", "riskyfunc", ["func", ["n"], ["do",
                ["if", ["equal", "n", 1], ["raise", 5], None],
                ["print", 6]]]])
        eval(["define", "middlefunc", ["func", ["n"], ["do",
                ["riskyfunc", "n"],
                ["print", 7]]]])
        eval(["define", "parentfunc", ["func", ["n"], ["do",
                ["try", ["do",
                    ["middlefunc", "n"],
                    ["print", 8]],
                    "except", "e", ["do",
                        ["print", "e"]]],
                ["print", 9]]]])

        self.assertEqual(printed(["parentfunc", 1]), (None, "5\n9\n"))
        self.assertEqual(printed(["parentfunc", 2]), (None, "6\n7\n8\n9\n"))

        eval(["define", "nested", ["func", ["n"], ["do",
                ["try", ["do",
                    ["if", ["equal", "n", 1], ["raise", 5], None],
                    ["print", 6],
                    ["try", ["do",
                        ["if", ["equal", "n", 2], ["raise", 7], None],
                        ["print", 8]],
                        "except", "e", ["do",
                            ["print", ["q", "exception inner try:"], "e"]]],
                    ["if", ["equal", "n", 3], ["raise", 9], None],
                    ["print", 10]],
                    "except", "e", ["do",
                        ["print", ["q", "exception outer try:"], "e"]]],
                ["print", 11]]]])

        self.assertEqual(printed(["nested", 1]), (None, "exception outer try: 5\n11\n"))
        self.assertEqual(printed(["nested", 2]), (None, "6\nexception inner try: 7\n10\n11\n"))
        self.assertEqual(printed(["nested", 3]), (None, "6\n8\nexception outer try: 9\n11\n"))
        self.assertEqual(printed(["nested", 4]), (None, "6\n8\n10\n11\n"))

        self.assertTrue(fails(["raise", 5]))

    def test_letcc_concurrent(self):
        eval(["define", "tasks", ["arr"]])
        eval(["define", "add-task", ["func", ["t"],
                ["assign", "tasks", ["append", "tasks", "t"]]]])
        eval(["define", "start", ["func", [],
                ["while", ["not_equal", "tasks", ["arr"]], ["do",
                    ["define", "next-task", ["first", "tasks"]],
                    ["assign", "tasks", ["rest", "tasks"]],
                    ["when", ["next-task"], ["add-task", "next-task"]]]]]])

        eval(["define", "three-times", ["gfunc", "n", ["do",
                ["print", "n"],
                ["yield", True],
                ["print", "n"],
                ["yield", True],
                ["print", "n"],
            ]]])

        eval(["add-task", ["three-times", 5]])
        eval(["add-task", ["three-times", 6]])
        eval(["add-task", ["three-times", 7]])

        self.assertEqual(printed(["start"]), (None, "5\n6\n7\n5\n6\n7\n5\n6\n7\n"))

if __name__ == "__main__":
    unittest.main()
