import unittest
from unittest.mock import patch
from io import StringIO

import sys
sys.setrecursionlimit(270000)

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
        self.assertEqual(run(["expand",
            ["while", ["<", "a", 5], ["do",
                ["assign", "b", ["+", "b", ["arr", "a"]]],
                ["assign", "a", ["+", "a", 1]]]]]),
            ["scope", ["do",
                ["define", "__stdlib_while_loop", ["func", [],
                    ["when", ["<", "a", 5],
                        ["do",
                            ["do",
                                ["assign", "b", ["+", "b", ["arr", "a"]]],
                                ["assign", "a", ["+", "a", 1]]],
                            ["__stdlib_while_loop"]]]]],
                ["__stdlib_while_loop"]]])

        run(["do",
                ["define", "a", 0],
                ["define", "b", ["arr"]],
                ["while", ["<", "a", 5], ["do",
                    ["assign", "b", ["+", "b", ["arr", "a"]]],
                    ["assign", "a", ["+", "a", 1]]]]])
        self.assertEqual(run("a"), 5)
        self.assertEqual(run("b"), [0, 1, 2, 3, 4])
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

    def test_for(self):
        self.assertEqual(run(["expand",
            ["for", "i", ["arr", 5, 6, 7], ["assign", "sum", ["+", "sum", "i"]]]]),
            ["scope", ["do",
                ["define", "__stdlib_for_index", 0],
                ["define", "i", None],
                ["while", ["<", "__stdlib_for_index", ["len", ["arr", 5, 6, 7]]], ["do",
                    ["assign", "i", ["getat", ["arr", 5, 6, 7], "__stdlib_for_index"]],
                    ["assign", "sum", ["+", "sum", "i"]],
                    ["assign", "__stdlib_for_index", ["inc", "__stdlib_for_index"]]]]]])

        self.assertEqual(run(["do",
            ["define", "sum", 0],
            ["for", "i", ["arr", 5, 6, 7], ["assign", "sum", ["+", "sum", "i"]]],
            "sum"]), 18)

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

class TestProblems(TestToig):
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

if __name__ == "__main__":
    unittest.main()
