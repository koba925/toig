import unittest
from unittest.mock import patch
from io import StringIO

from toig import init_env, stdlib, run

def fails(src):
    try: run(src)
    except AssertionError: return True
    else: return False

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
        self.assertTrue(fails(["b"]))
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

    def test_builtins(self):
        self.assertEqual(run(["+", ["+", 5, 6], ["+", 7, 8]]), 26)
        self.assertEqual(run(["-", ["-", 26, 8], ["+", 5, 6]]), 7)
        self.assertEqual(run(["*", ["*", 5, 6], ["*", 7, 8]]), 1680)
        self.assertEqual(run(["/", ["/", 1680, 8], ["*", 5, 6]]), 7)

        self.assertEqual(run(["=", ["+", 5, 6], ["+", 6, 5]]), True)
        self.assertEqual(run(["=", ["+", 5, 6], ["+", 7, 8]]), False)
        self.assertEqual(run(["<", ["+", 5, 6], ["+", 3, 7]]), False)
        self.assertEqual(run(["<", ["+", 5, 6], ["+", 4, 7]]), False)
        self.assertEqual(run(["<", ["+", 5, 6], ["+", 4, 8]]), True)
        self.assertEqual(run([">", ["+", 5, 6], ["+", 3, 7]]), True)
        self.assertEqual(run([">", ["+", 5, 6], ["+", 4, 7]]), False)
        self.assertEqual(run([">", ["+", 5, 6], ["+", 4, 8]]), False)

        self.assertEqual(run(["not", ["=", ["+", 5, 6], ["+", 6, 5]]]), False)
        self.assertEqual(run(["not", ["=", ["+", 5, 6], ["+", 7, 8]]]), True)

        self.assertTrue(fails(["+", 5]))
        self.assertTrue(fails(["+", 5, 6, 7]))

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

    def test_adder(self):
        run(["define", "make_adder", ["func", ["n"],
                ["func", ["m"], ["+", "n", "m"]]]])
        self.assertEqual(run([["make_adder", 5], 6]), 11)

    def test_counter(self):
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

class TestStdlib(TestToig):

    def test_when(self):
        self.assertEqual(run(["expand",
                            ["when", ["not", ["=", "b", 0]], ["/", "a", "b"]]]),
                         ["if", ["not", ["=", "b", 0]], ["/", "a", "b"], None])
        run(["define", "a", 30])
        run(["define", "b", 5])
        self.assertEqual(run(["when", ["not", ["=", "b", 0]], ["/", "a", "b"]]), 6)
        run(["assign", "b", 0])
        self.assertEqual(run(["when", ["not", ["=", "b", 0]], ["/", "a", "b"]]), None)

    def test_and_or(self):
        run(["define", "and", ["macro", ["a", "b"],
                ["arr", ["q", "if"], "a", "b", False]]])
        self.assertEqual(run(["expand", ["and", ["=", "a", 0], ["=", "b", 0]]]),
                         ["if", ["=", "a", 0], ["=", "b", 0], False])
        self.assertEqual(run(["and", False, "nosuchvariable"]), False)
        self.assertEqual(run(["and", False, "nosuchvariable"]), False)
        self.assertEqual(run(["and", True, False]), False)
        self.assertEqual(run(["and", True, True]), True)

        self.assertEqual(run(["expand", ["or", ["=", "a", 0], ["=", "b", 0]]]),
                         ["if", ["=", "a", 0], True, ["=", "b", 0]])
        self.assertEqual(run(["or", False, False]), False)
        self.assertEqual(run(["or", False, True]), True)
        self.assertEqual(run(["or", True, "nosuchvariable"]), True)
        self.assertEqual(run(["or", True, "nosuchvariable"]), True)

        self.assertEqual(
            run(["expand", ["and", ["or", ["=", 5, 6], ["=", 7, 7]], ["=", 8, 8]]]),
            ["if", ["or", ["=", 5, 6], ["=", 7, 7]], ["=", 8, 8], False])
        self.assertEqual(
            run(["and", ["or", ["=", 5, 6], ["=", 7, 7]], ["=", 8, 8]]),
            True)

    def test_while(self):
        self.assertEqual(run(["expand",
            ["while", ["<", "a", 5], ["do",
                ["assign", "b", ["+", "b", ["arr", "a"]]],
                ["assign", "a", ["+", "a", 1]]]]]),
            ["do",
                ["define", "loop", ["func", [],
                    ["when", ["<", "a", 5],
                        ["do",
                            ["do",
                                ["assign", "b", ["+", "b", ["arr", "a"]]],
                                ["assign", "a", ["+", "a", 1]]],
                            ["loop"]]]]],
                ["loop"]])
        run(["do",
                ["define", "a", 0],
                ["define", "b", ["arr"]],
                ["while", ["<", "a", 5], ["do",
                    ["assign", "b", ["+", "b", ["arr", "a"]]],
                    ["assign", "a", ["+", "a", 1]]]]])
        self.assertEqual(run("a"), 5)
        self.assertEqual(run("b"), [0, 1, 2, 3, 4])

if __name__ == "__main__":
    unittest.main()
