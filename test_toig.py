import unittest
from unittest.mock import patch
from io import StringIO

from toig import init_env, run

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
        self.assertEqual(run(["=", ["+", 5, 6], ["+", 6, 5]]), True)
        self.assertEqual(run(["=", ["+", 5, 6], ["+", 7, 8]]), False)
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

if __name__ == "__main__":
    unittest.main()