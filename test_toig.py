import unittest
from unittest.mock import patch
from io import StringIO

from toig import init_env, stdlib, run

def fails(src):
    try: run(src)
    except AssertionError: return True
    else: return False

def expanded(src):
    return run(["expand", src])

def printed(src):
    with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
        val = run(src)
        return (val, mock_stdout.getvalue())

class TestToig(unittest.TestCase):
    def setUp(self):
        init_env()
        stdlib()

class TestCore(TestToig):
    def test_primitives(self):
        self.assertEqual(run(None), None)
        self.assertEqual(run(5), 5)
        self.assertEqual(run(True), True)
        self.assertEqual(run(False), False)

    def test_define(self):
        self.assertEqual(run(["define", "a", ["+", 5, 6]]), 11)
        self.assertEqual(run("a"), 11)
        self.assertTrue(fails(["define", "a", 6]))
        self.assertTrue(fails("b"))
        self.assertEqual(printed([["func", [], ["do",
                            ["print", ["define", "a", 5]],
                            ["print", "a"]]]]), (None, "5\n5\n"))
        self.assertEqual(run("a"), 11)

    def test_assign(self):
        self.assertEqual(run(["define", "a", 5]), 5)
        self.assertEqual(run(["assign", "a", ["+", 5, 6]]), 11)
        self.assertEqual(run("a"), 11)
        self.assertTrue(fails(["assign", "b", 6]))
        self.assertEqual(run([["func", [], ["assign", "a", 6]]]), 6)
        self.assertEqual(printed([["func", [], ["do",
                            ["print", ["assign", "a", 6]],
                            ["print", "a"]]]]), (None, "6\n6\n"))
        self.assertEqual(run("a"), 6)

    def test_do(self):
        self.assertEqual(run(["do"]), None)
        self.assertEqual(run(["do", 5]), 5)
        self.assertEqual(run(["do", 5, 6]), 6)
        self.assertEqual(printed(["do", ["print", 5]]), (None, "5\n"))
        self.assertEqual(printed(["do", ["print", 5], ["print", 6]]), (None, "5\n6\n"))

    def test_if(self):
        self.assertEqual(run(["if", ["=", 5, 5], ["+", 7, 8], ["+", 9, 10]]), 15)
        self.assertEqual(run(["if", ["=", 5, 6], ["+", 7, 8], ["+", 9, 10]]), 19)
        self.assertTrue(fails(["if", True, 5]))

    def test_builtin_math(self):
        self.assertEqual(run(["+", ["+", 5, 6], ["+", 7, 8]]), 26)
        self.assertEqual(run(["-", ["-", 26, 8], ["+", 5, 6]]), 7)
        self.assertEqual(run(["*", ["*", 5, 6], ["*", 7, 8]]), 1680)
        self.assertEqual(run(["/", ["/", 1680, 8], ["*", 5, 6]]), 7)
        self.assertTrue(fails(["+", 5]))
        self.assertTrue(fails(["+", 5, 6, 7]))

    def test_builtin_equality(self):
        self.assertEqual(run(["=", ["+", 5, 6], ["+", 6, 5]]), True)
        self.assertEqual(run(["=", ["+", 5, 6], ["+", 7, 8]]), False)
        self.assertEqual(run(["!=", ["+", 5, 6], ["+", 6, 5]]), False)
        self.assertEqual(run(["!=", ["+", 5, 6], ["+", 7, 8]]), True)

    def test_builtin_comparison(self):
        self.assertEqual(run(["<", ["+", 5, 6], ["+", 3, 7]]), False)
        self.assertEqual(run(["<", ["+", 5, 6], ["+", 4, 7]]), False)
        self.assertEqual(run(["<", ["+", 5, 6], ["+", 4, 8]]), True)
        self.assertEqual(run([">", ["+", 5, 6], ["+", 3, 7]]), True)
        self.assertEqual(run([">", ["+", 5, 6], ["+", 4, 7]]), False)
        self.assertEqual(run([">", ["+", 5, 6], ["+", 4, 8]]), False)

        self.assertEqual(run(["<=", ["+", 5, 6], ["+", 3, 7]]), False)
        self.assertEqual(run(["<=", ["+", 5, 6], ["+", 4, 7]]), True)
        self.assertEqual(run(["<=", ["+", 5, 6], ["+", 4, 8]]), True)
        self.assertEqual(run([">=", ["+", 5, 6], ["+", 3, 7]]), True)
        self.assertEqual(run([">=", ["+", 5, 6], ["+", 4, 7]]), True)
        self.assertEqual(run([">=", ["+", 5, 6], ["+", 4, 8]]), False)

    def test_builtin_logic(self):
        self.assertEqual(run(["not", ["=", ["+", 5, 6], ["+", 6, 5]]]), False)
        self.assertEqual(run(["not", ["=", ["+", 5, 6], ["+", 7, 8]]]), True)

    def test_print(self):
        self.assertEqual(printed(["print", None]), (None, "None\n"))
        self.assertEqual(printed(["print", 5]), (None, "5\n"))
        self.assertEqual(printed(["print", True]), (None, "True\n"))
        self.assertEqual(printed(["print", False]), (None, "False\n"))
        self.assertEqual(printed(["print"]), (None, "\n"))
        self.assertEqual(printed(["print", 5, 6]), (None, "5 6\n"))

    def test_func(self):
        self.assertEqual(run([["func", ["n"], ["+", 5, "n"]], 6]), 11)
        self.assertTrue(fails([["func", ["n"], ["+", 5, "n"]]]))
        self.assertTrue(fails([["func", ["n"], ["+", 5, "n"]], 6, 7]))

        self.assertEqual(run([["func", [["*", "rest"]], "rest"]]), [])
        self.assertEqual(run([["func", ["a", ["*", "rest"]], ["arr", "a", "rest"]], 5]), [5, []])
        self.assertEqual(run([["func", ["a", ["*", "rest"]], ["arr", "a", "rest"]], 5, 6]), [5, [6]])
        self.assertEqual(run([["func", ["a", ["*", "rest"]], ["arr", "a", "rest"]], 5, 6, 7]), [5, [6, 7]])
        self.assertTrue(fails([["func", [["*", "rest"], "a"], ["arr", "a", "rest"]], 5]))

    def test_closure_adder(self):
        run(["define", "make_adder", ["func", ["n"],
                ["func", ["m"], ["+", "n", "m"]]]])
        self.assertEqual(run([["make_adder", 5], 6]), 11)

    def test_closure_counter(self):
        run(["define", "make_counter", ["func", [], ["do",
                ["define", "c", 0],
                ["func", [], ["assign", "c", ["+", "c", 1]]]]]])
        run(["define", "counter1", ["make_counter"]])
        run(["define", "counter2", ["make_counter"]])
        self.assertEqual(run(["counter1"]), 1)
        self.assertEqual(run(["counter1"]), 2)
        self.assertEqual(run(["counter2"]), 1)
        self.assertEqual(run(["counter2"]), 2)
        self.assertEqual(run(["counter1"]), 3)
        self.assertEqual(run(["counter2"]), 3)

    def test_array(self):
        self.assertEqual(run(["arr"]), [])
        self.assertEqual(run(["arr", ["+", 5, 6]]), [11])

        run(["define", "a", ["arr", 5, 6, ["arr", 7, 8]]])
        self.assertEqual(run("a"), [5, 6, [7, 8]])

        self.assertEqual(run(["is_arr", 5]), False)
        self.assertEqual(run(["is_arr", ["arr"]]), True)
        self.assertEqual(run(["is_arr", "a"]), True)
        self.assertTrue(fails(["is_arr"]))
        self.assertTrue(fails(["is_arr", 5, 6]))

        self.assertEqual(run(["len", ["arr"]]), 0)
        self.assertEqual(run(["len", "a"]), 3)
        self.assertTrue(fails(["len"]))
        self.assertTrue(fails(["len", 5, 6]))

        self.assertEqual(run(["getat", "a", 1]), 6)
        self.assertEqual(run(["getat", "a", -1]), [7, 8])
        self.assertEqual(run(["getat", ["getat", "a", 2], 1]), 8)
        self.assertTrue(fails(["getat", "a"]))
        self.assertTrue(fails(["getat", "a", 5, 6]))

        self.assertEqual(run(["setat", "a", 1, 9]), [5, 9, [7, 8]])
        self.assertEqual(run("a"), [5, 9, [7, 8]])
        self.assertEqual(run(["setat", ["getat", "a", 2], -1, 10]), [7, 10])
        self.assertEqual(run("a"), [5, 9, [7, 10]])
        self.assertTrue(fails(["setat", "a", 1]))
        self.assertTrue(fails(["setat", "a", 1, 5, 6]))

        self.assertTrue(fails(["slice"]))
        self.assertEqual(run(["slice", "a"]), [5, 9, [7, 10]])
        self.assertEqual(run(["slice", "a", 1]), [9, [7, 10]])
        self.assertEqual(run(["slice", "a", -2]), [9, [7, 10]])
        self.assertEqual(run(["slice", "a", 1, 2]), [9])
        self.assertEqual(run(["slice", "a", 1, -1]), [9])
        self.assertTrue(fails(["slice", "a", 1, 2, 3]))

        self.assertEqual(run(["+", ["arr", 5], ["arr", 6]]), [5, 6])

    def test_quote(self):
        self.assertEqual(run(["q", 5]), 5)
        self.assertEqual(run(["q", ["+", 5, 6]]), ["+", 5, 6])

    def test_qq(self):
        self.assertEqual(run(["qq", 5]), 5)
        self.assertEqual(run(["qq", ["+", 5, 6]]), ["+", 5, 6])
        self.assertEqual(run(["qq", ["!", ["+", 5, 6]]]), 11)
        self.assertEqual(run(["qq", ["*", 4, ["!", ["+", 5, 6]]]]), ["*", 4, 11])
        self.assertEqual(run(["qq", ["+", ["!!", ["arr", 5, 6]]]]), ["+", 5, 6])
        self.assertTrue(fails(["qq", ["+", ["!!", 5]]]))

    def test_macro(self):
        self.assertEqual(expanded([["macro", [], ["q", "abc"]]]), "abc")
        self.assertEqual(
            expanded([["macro", ["a"], ["arr", ["q", "*"], "a", "a"]], ["+", 5, 6]]),
            ["*", ["+", 5, 6], ["+", 5, 6]])

        run(["define", "build_exp", ["macro", ["op", ["*", "r"]],
                ["+", ["arr", "op"], "r"]]])
        self.assertEqual(expanded(["build_exp", "+"]), ["+"])
        self.assertEqual(expanded(["build_exp", "+", 5]), ["+", 5])
        self.assertEqual(expanded(["build_exp", "+", 5, 6]), ["+", 5, 6])

        self.assertTrue(fails([["macro", [["*", "r"], "a"], 5]]))

    def test_letcc(self):
        self.assertEqual(run(["letcc", "skip-to", ["+", 5, 6]]), 11)
        self.assertEqual(run(["letcc", "skip-to", ["+", ["skip-to", 5], 6]]), 5)
        self.assertEqual(run(["+", 5, ["letcc", "skip-to", ["skip-to", 6]]]), 11)
        self.assertEqual(run(["letcc", "skip1", ["+", ["skip1", ["letcc", "skip2", ["+", ["skip2", 5], 6]]], 7]]), 5)

        run(["define", "inner", ["func", ["raise"], ["raise", 5]]])
        run(["define", "outer", ["func", [],
                [ "letcc", "raise", ["+", ["inner", "raise"], 6]]]])
        self.assertEqual(run(["outer"]), 5)

    def test_letcc_reuse(self):
        run(["define", "add5", None])
        self.assertEqual(run(["+", 5, ["letcc", "cc", ["do", ["assign", "add5", "cc"], 6]]]), 11)
        self.assertEqual(run(["add5", 7]), 12)
        self.assertEqual(run(["add5", 8]), 13)

class TestStdlib(TestToig):
    def test_id(self):
        self.assertEqual(run(["id", ["+", 5, 6]]), 11)

    def test_inc_dec(self):
        self.assertEqual(run(["inc", ["+", 5, 6]]), 12)
        self.assertEqual(run(["dec", ["+", 5, 6]]), 10)

    def test_first_rest_last(self):
        self.assertEqual(run(["first", ["arr", 5, 6, 7]]), 5)
        self.assertEqual(run(["rest", ["arr", 5, 6, 7]]), [6, 7])
        self.assertEqual(run(["last", ["arr", 5, 6, 7]]), 7)

    def test_append_prepend(self):
        self.assertEqual(run(["append", ["arr", 5, 6], ["inc", 7]]), [5, 6, 8])
        self.assertEqual(run(["prepend", ["inc", 5], ["arr", 7, 8]]), [6, 7, 8])

    def test_map(self):
        self.assertEqual(run(["map", ["arr"], "inc"]), [])
        self.assertEqual(run(["map", ["arr", 5, 6, 7], "inc"]), [6, 7, 8])

    def test_range(self):
        self.assertEqual(run(["range", 5, 5]), [])
        self.assertEqual(run(["range", 5, 8]), [5, 6, 7])

    def test_scope(self):
        self.assertEqual(expanded(["scope", ["do", ["define", "a", 5]]]),
                         [["func", [], ["do", ["define", "a", 5]]]])
        self.assertEqual(printed(["do",
            ["define", "a", 5],
            ["scope", ["do", ["define", "a", 6], ["print", "a"]]],
            ["print", "a"]]), (None, "6\n5\n"))

    def test_when(self):
        self.assertEqual(run(["expand",
                            ["when", ["not", ["=", "b", 0]], ["/", "a", "b"]]]),
                         ["if", ["not", ["=", "b", 0]], ["/", "a", "b"], None])
        run(["define", "a", 30])
        run(["define", "b", 5])
        self.assertEqual(run(["when", ["not", ["=", "b", 0]], ["/", "a", "b"]]), 6)
        run(["assign", "b", 0])
        self.assertEqual(run(["when", ["not", ["=", "b", 0]], ["/", "a", "b"]]), None)

    def test_aif(self):
        self.assertEqual(run(["aif", ["inc", 5], ["inc", "it"], 8]), 7)
        self.assertEqual(run(["aif", ["dec", 1], 5, "it"]), 0)

    def test_and_or(self):
        self.assertEqual(expanded(["and", ["=", "a", 0], ["=", "b", 0]]),
                         ["aif", ["=", "a", 0], ["=", "b", 0], "it"])
        self.assertEqual(run(["and", False, "nosuchvariable"]), False)
        self.assertEqual(run(["and", None, "nosuchvariable"]), None)
        self.assertEqual(run(["and", True, False]), False)
        self.assertEqual(run(["and", True, None]), None)
        self.assertEqual(run(["and", True, True]), True)
        self.assertEqual(run(["and", True, 5]), 5)

        self.assertEqual(expanded(["or", ["=", "a", 0], ["=", "b", 0]]),
                         ["aif", ["=", "a", 0], "it", ["=", "b", 0]])
        self.assertEqual(run(["or", False, False]), False)
        self.assertEqual(run(["or", False, None]), None)
        self.assertEqual(run(["or", False, True]), True)
        self.assertEqual(run(["or", False, 5]), 5)
        self.assertEqual(run(["or", True, "nosuchvariable"]), True)
        self.assertEqual(run(["or", 5, "nosuchvariable"]), 5)

        self.assertEqual(printed(["scope", ["do",
            ["define", "foo", 5],
            ["print", ["or", "foo", ["q", "default"]]],
            ["assign", "foo", None],
            ["print", ["or", "foo", ["q", "default"]]]
        ]]), (None, "5\ndefault\n"))

        self.assertEqual(
            expanded(["and", ["or", ["=", 5, 6], ["=", 7, 7]], ["=", 8, 8]]),
            ["aif", ["or", ["=", 5, 6], ["=", 7, 7]], ["=", 8, 8], "it"])
        self.assertEqual(
            run(["and", ["or", ["=", 5, 6], ["=", 7, 7]], ["=", 8, 8]]),
            True)

    def test_while(self):
        run(["do",
                ["define", "a", 0],
                ["define", "b", ["arr"]],
                ["while", ["<", "a", 10], ["do",
                    ["when", ["=", "a", 5], ["break", None]],
                    ["assign", "a", ["+", "a", 1]],
                    ["when", ["=", "a", 3], ["continue"]],
                    ["assign", "b", ["+", "b", ["arr", "a"]]],
                    ]]])
        self.assertEqual(run("a"), 5)
        self.assertEqual(run("b"), [1, 2, 4, 5])

        run(["do",
                ["define", "r", ["arr"]],
                ["define", "c", ["arr"]],
                ["while", ["<", ["len", "r"], 3],
                    ["do",
                        ["assign", "c", ["arr"]],
                        ["while", ["<", ["len", "c"], 3],
                            ["assign", "c", ["+", "c", ["arr", 0]]]],
                        ["assign", "r", ["+", "r", ["arr", "c"]]]]]])
        self.assertEqual(run("r"), [[0, 0, 0], [0, 0, 0], [0, 0, 0]])

    def test_awhile(self):
        run(["do",
                ["define", "a", 0],
                ["define", "b", ["arr"]],
                ["awhile", ["<", "a", 10], ["do",
                    ["when", ["=", "a", 5], ["break", None]],
                    ["assign", "a", ["+", "a", 1]],
                    ["when", ["=", "a", 3], ["continue"]],
                    ["assign", "b", ["+", "b", ["arr", "a"]]],
                    ]]])
        self.assertEqual(run("a"), 5)
        self.assertEqual(run("b"), [1, 2, 4, 5])

        run(["do",
                ["define", "r", ["arr"]],
                ["define", "c", ["arr"]],
                ["awhile", ["<", ["len", "r"], 3],
                    ["do",
                        ["assign", "c", ["arr"]],
                        ["awhile", ["<", ["len", "c"], 3],
                            ["assign", "c", ["+", "c", ["arr", 0]]]],
                        ["assign", "r", ["+", "r", ["arr", "c"]]]]]])
        self.assertEqual(run("r"), [[0, 0, 0], [0, 0, 0], [0, 0, 0]])

    def test_for(self):
        self.assertEqual(run(["do",
            ["define", "sum", 0],
            ["for", "i", ["arr", 5, 6, 7, 8, 9], ["do",
                ["when", ["=", "i", 7], ["continue"]],
                ["when", ["=", "i", 9], ["break", None]],
                ["assign", "sum", ["+", "sum", "i"]]]],
            "sum"]), 19)

    # see https://zenn.dev/link/comments/ea605f282d4c97
    def test_letcc_generator(self):
        run(["define", "g3", ["gfunc", ["n"], ["do",
                ["yield", "n"],
                ["assign", "n", ["+", "n", 1]],
                ["yield", "n"],
                ["assign", "n", ["+", "n", 1]],
                ["yield", "n"]]]])

        run(["define", "gsum", ["func", ["gen"],
                ["aif", ["gen"], ["+", "it", ["gsum", "gen"]], 0]]])
        self.assertEqual(run(["gsum", ["g3", 2]]), 9)
        self.assertEqual(run(["gsum", ["g3", 5]]), 18)

        run(["define", "walk", ["gfunc", ["tree"], ["do",
                ["define", "_walk", ["func",["t"], ["do",
                    ["if", ["is_arr", ["first", "t"]],
                        ["_walk", ["first", "t"]],
                        ["yield", ["first", "t"]]],
                    ["if", ["is_arr", ["last", "t"]],
                        ["_walk", ["last", "t"]],
                        ["yield", ["last", "t"]]]]]],
                ["_walk", "tree"]]]])

        run(["define", "gen", ["walk", ["q", [[[5, 6], 7], [8, [9, 10]]]]]])
        self.assertEqual(printed(["awhile", ["gen"], ["print", "it"]]),
                         (None, "5\n6\n7\n8\n9\n10\n"))

    def test_agen(self):
        run(["define", "gen", ["agen", ["q", [2, 3, 4]]]])
        self.assertEqual(run(["gen"]), 2)
        self.assertEqual(run(["gen"]), 3)
        self.assertEqual(run(["gen"]), 4)
        self.assertEqual(run(["gen"]), None)

        run(["define", "gen0", ["agen", ["q", []]]])
        self.assertEqual(run(["gen"]), None)

    def test_gfor(self):
        self.assertEqual(printed(["gfor", "n", ["agen", ["q", []]],
                                    ["print", "n"]]),
                         (None, ""))
        self.assertEqual(printed(["gfor", "n", ["agen", ["q", [2, 3, 4]]],
                                    ["print", "n"]]),
                         (None, "2\n3\n4\n"))
        self.assertEqual(printed(["gfor", "n", ["agen", ["q", [2, 3, 4, 5, 6]]],
                                    ["do",
                                        ["when", ["=", "n", 5], ["break", None]],
                                        ["when", ["=", "n", 3], ["continue"]],
                                        ["print", "n"]]]),
                         (None, "2\n4\n"))

class TestProblems(TestToig):
    def test_factorial(self):
        run(["define", "factorial", ["func", ["n"],
                ["if", ["=", "n", 1],
                    1,
                    ["*", "n", ["factorial", ["-", "n", 1]]]]]])
        self.assertEqual(run(["factorial", 1]), 1)
        self.assertEqual(run(["factorial", 10]), 3628800)
        # print(run(["factorial", 1500]))

    def test_fib(self):
        run(["define", "fib", ["func", ["n"],
                ["if", ["=", "n", 0], 0,
                ["if", ["=", "n", 1], 1,
                ["+", ["fib", ["-", "n", 1]], ["fib", ["-", "n", 2]]]]]]])
        self.assertEqual(run(["fib", 0]), 0)
        self.assertEqual(run(["fib", 1]), 1)
        self.assertEqual(run(["fib", 2]), 1)
        self.assertEqual(run(["fib", 3]), 2)
        self.assertEqual(run(["fib", 10]), 55)

    def test_macro_firstclass(self):
        self.assertEqual(run([["func", ["op", "a", "b"], ["op", "a", "b"]], "and", True, False]), False)
        self.assertEqual(run([["func", ["op", "a", "b"], ["op", "a", "b"]], "or", True, False]), True)

        self.assertEqual(run([[["func", [], "and"]], True, False]), False)
        self.assertEqual(run([[["func", [], "or"]], True, False]), True)

        self.assertEqual(run(["map",
                                ["arr", "and", "or"],
                                ["func", ["op"], ["op", True, False]]]),
                        [False, True])

    def test_sieve(self):
        run(["define", "sieve", ["+",
                ["*", ["arr", False], 2],
                ["*", ["arr", True], 28]]])
        run(["define", "j", None])
        run(["for", "i", ["range", 2, 30],
                ["when", ["getat", "sieve", "i"],
                    ["do",
                        ["assign", "j", ["*", "i", "i"]],
                        ["while", ["<", "j", 30], ["do",
                            ["setat", "sieve", "j", False],
                            ["assign", "j", ["+", "j", "i"]]]]]]])
        run(["define", "primes", ["arr"]])
        run(["for", "i", ["range", 0, 30],
                ["when", ["getat", "sieve", "i"],
                    ["assign", "primes", ["append", "primes", "i"]]]])
        self.assertEqual(run("primes"), [2, 3, 5, 7, 11, 13, 17, 19, 23, 29])

    def test_let(self):
        run(["define", "let", ["macro", ["bindings", "body"], ["do",
                ["define", "defines", ["func", ["bindings"],
                    ["map", "bindings", ["func", ["b"], ["qq",
                        ["define",
                         ["!", ["first", "b"]],
                         ["!", ["last", "b"]]]]]]]],
                ["qq", ["scope", ["do",
                    ["!!", ["defines", "bindings"]],
                    ["!","body"]]]]]]])
        self.assertEqual(expanded(["let", [["a", 5], ["b", 6]], ["+", "a", "b"]]),
                         ["scope", ["do",
                             ["define", "a", 5],
                             ["define", "b", 6],
                             ["+", "a", "b"]]])
        self.assertEqual(run(["let", [["a", 5], ["b", 6]], ["+", "a", "b"]]), 11)

    def test_cond(self):
        run(["define", "cond", ["macro", [["*", "clauses"]],
                ["do",
                    ["define", "_cond", ["func", ["clauses"],
                        ["if", ["=", "clauses", ["arr"]],
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
                [["=", "n", 0], 0],
                [["=", "n", 1], 1],
                [True, ["+", ["fib", ["-", "n", 1]], ["fib", ["-", "n", 2]]]]]),
            ["if", ["=", "n", 0], 0,
                ["if", ["=", "n", 1], 1,
                    ["if", True,
                        ["+", ["fib", ["-", "n", 1]], ["fib", ["-", "n", 2]]],
                        None]]])
        run(["define", "fib", ["func", ["n"],
                ["cond",
                    [["=", "n", 0], 0],
                    [["=", "n", 1], 1],
                    [True, ["+", ["fib", ["-", "n", 1]], ["fib", ["-", "n", 2]]]]]]])
        self.assertEqual(run(["fib", 0]), 0)
        self.assertEqual(run(["fib", 1]), 1)
        self.assertEqual(run(["fib", 2]), 1)
        self.assertEqual(run(["fib", 3]), 2)
        self.assertEqual(run(["fib", 10]), 55)

    def test_letcc_return(self):
        run(["define", "early-return", ["func", ["n"],
                ["letcc", "return", ["do",
                    ["if", ["=", "n", 1], ["return", 5], 6],
                    7]]]])
        self.assertEqual(run(["early-return", 1]), 5)
        self.assertEqual(run(["early-return", 2]), 7)

        run(["define", "runc", ["macro", ["params", "body"], ["qq",
                ["func", ["!", "params"], ["letcc", "return", ["!", "body"]]]]]])
        run(["define", "early_return_runc", ["runc", ["n"], ["do",
                ["if", ["=", "n", 1], ["return", 5], 6],
                7]]])
        self.assertEqual(run(["early_return_runc", 1]), 5)
        self.assertEqual(run(["early_return_runc", 2]), 7)

        run(["define", "early_return_runc2", ["runc", ["n"], ["do",
                ["if", ["=", ["early_return_runc", "n"], 5], ["return", 6], 7],
                8]]])
        self.assertEqual(run(["early_return_runc2", 1]), 6)
        self.assertEqual(run(["early_return_runc2", 2]), 8)

    def test_letcc_escape(self):
        run(["define", "riskyfunc", ["func", ["n", "escape"], ["do",
                ["if", ["=", "n", 1], ["escape", 5], 6],
                7]]])
        run(["define", "middlefunc", ["func", ["n", "escape"], ["do",
                ["riskyfunc", "n", "escape"],
                8]]])
        run(["define", "parentfunc", ["func", ["n"],
                ["letcc", "escape", ["middlefunc", "n", "escape"]]]])
        self.assertEqual(run(["parentfunc", 1]), 5)
        self.assertEqual(run(["parentfunc", 2]), 8)

    def test_letcc_except(self):
        run(["define", "raise", None])
        run(["define", "riskyfunc", ["func", ["n"], ["do",
                ["if", ["=", "n", 1], ["raise", 5], None],
                ["print", 6]]]])
        run(["define", "middlefunc", ["func", ["n"], ["do",
                ["riskyfunc", "n"],
                ["print", 7]]]])
        run(["define", "parentfunc", ["func", ["n"], ["do",
                ["letcc", "escape", ["do",
                    ["assign", "raise", ["func", ["e"], ["escape", ["do",
                        ["print", "e"]]]]],
                    ["middlefunc", "n"],
                    ["print", 8]]],
                ["print", 9]]]])
        self.assertEqual(printed(["parentfunc", 1]), (None, "5\n9\n"))
        self.assertEqual(printed(["parentfunc", 2]), (None, "6\n7\n8\n9\n"))

    def test_letcc_try(self):
        run(["define", "raise", ["func", ["e"],["error", ["q", "Raised outside of try:"], "e"]]])
        run(["define", "try", ["macro", ["try-expr", "_", "exc-var", "exc-expr"], ["qq",
                ["scope", ["do",
                    ["define", "prev-raise", "raise"],
                    ["letcc", "escape", ["do",
                        ["assign", "raise", ["func", [["!", "exc-var"]],
                            ["escape", ["!", "exc-expr"]]]],
                        ["!", "try-expr"]]],
                    ["assign", "raise", "prev-raise"]]]]]])

        run(["define", "riskyfunc", ["func", ["n"], ["do",
                ["if", ["=", "n", 1], ["raise", 5], None],
                ["print", 6]]]])
        run(["define", "middlefunc", ["func", ["n"], ["do",
                ["riskyfunc", "n"],
                ["print", 7]]]])
        run(["define", "parentfunc", ["func", ["n"], ["do",
                ["try", ["do",
                    ["middlefunc", "n"],
                    ["print", 8]],
                    "except", "e", ["do",
                        ["print", "e"]]],
                ["print", 9]]]])

        self.assertEqual(printed(["parentfunc", 1]), (None, "5\n9\n"))
        self.assertEqual(printed(["parentfunc", 2]), (None, "6\n7\n8\n9\n"))

        run(["define", "nested", ["func", ["n"], ["do",
                ["try", ["do",
                    ["if", ["=", "n", 1], ["raise", 5], None],
                    ["print", 6],
                    ["try", ["do",
                        ["if", ["=", "n", 2], ["raise", 7], None],
                        ["print", 8]],
                        "except", "e", ["do",
                            ["print", ["q", "exception inner try:"], "e"]]],
                    ["if", ["=", "n", 3], ["raise", 9], None],
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
        run(["define", "tasks", ["arr"]])
        run(["define", "add-task", ["func", ["t"],
                ["assign", "tasks", ["append", "tasks", "t"]]]])
        run(["define", "start", ["func", [],
                ["while", ["!=", "tasks", ["arr"]], ["do",
                    ["define", "next-task", ["first", "tasks"]],
                    ["assign", "tasks", ["rest", "tasks"]],
                    ["when", ["next-task"], ["add-task", "next-task"]]]]]])

        run(["define", "three-times", ["gfunc", ["n"], ["do",
                ["print", "n"],
                ["yield", True],
                ["print", "n"],
                ["yield", True],
                ["print", "n"],
            ]]])

        run(["add-task", ["three-times", 5]])
        run(["add-task", ["three-times", 6]])
        run(["add-task", ["three-times", 7]])

        self.assertEqual(printed(["start"]), (None, "5\n6\n7\n5\n6\n7\n5\n6\n7\n"))

if __name__ == "__main__":
    unittest.main()
