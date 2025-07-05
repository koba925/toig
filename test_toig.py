import unittest
from unittest.mock import patch
from io import StringIO

from toig import Interpreter

class TestToig(unittest.TestCase):

    def setUp(self):
        self.i = Interpreter()

    def go(self, src):
        return self.i.run(src)

    def fails(self, src):
        try: self.i.run(src)
        except AssertionError: return True
        else: return False

    def printed(self, src):
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            val = self.i.run(src)
            return (val, mock_stdout.getvalue())

    def test_primitives(self):
        self.assertEqual(self.go(None), None)
        self.assertEqual(self.go(5), 5)
        self.assertEqual(self.go(True), True)
        self.assertEqual(self.go(False), False)

    def test_define(self):
        self.assertEqual(self.go(["define", "a", ["+", 5, 6]]), 11)
        self.assertEqual(self.go("a"), 11)
        self.assertEqual(self.go(["define", "a", 6]), 6)
        self.assertEqual(self.go("a"), 6)
        self.assertEqual(self.printed([["func", [], ["seq",
                            ["print", ["define", "a", 5]],
                            ["print", "a"]]]]), (None, "5\n5\n"))
        self.assertEqual(self.go("a"), 6)
        self.assertTrue(self.fails(["b"]))

    def test_assign(self):
        self.assertEqual(self.go(["define", "a", 5]), 5)
        self.assertEqual(self.go(["assign", "a", ["+", 5, 6]]), 11)
        self.assertEqual(self.go("a"), 11)
        self.assertEqual(self.go([["func", [], ["assign", "a", 6]]]), 6)
        self.assertEqual(self.printed([["func", [], ["seq",
                            ["print", ["assign", "a", 7]],
                            ["print", "a"]]]]), (None, "7\n7\n"))
        self.assertEqual(self.go("a"), 7)
        self.assertTrue(self.fails(["assign", "b", 6]))

    def test_do(self):
        self.assertEqual(self.go(["seq"]), None)
        self.assertEqual(self.go(["seq", 5]), 5)
        self.assertEqual(self.go(["seq", 5, 6]), 6)
        self.assertEqual(self.printed(["seq", ["print", 5]]), (None, "5\n"))
        self.assertEqual(self.printed(["seq", ["print", 5], ["print", 6]]), (None, "5\n6\n"))

    def test_if(self):
        self.assertEqual(self.go(["if", ["=", 5, 5], ["+", 7, 8], ["+", 9, 10]]), 15)
        self.assertEqual(self.go(["if", ["=", 5, 6], ["+", 7, 8], ["+", 9, 10]]), 19)
        self.assertTrue(self.fails(["if", True, 5]))

    def test_builtins(self):
        self.assertEqual(self.go(["+", ["+", 5, 6], ["+", 7, 8]]), 26)
        self.assertEqual(self.go(["-", ["-", 26, 8], ["+", 5, 6]]), 7)
        self.assertEqual(self.go(["=", ["+", 5, 6], ["+", 6, 5]]), True)
        self.assertEqual(self.go(["=", ["+", 5, 6], ["+", 7, 8]]), False)

    def test_print(self):
        self.assertEqual(self.printed(["print", None]), (None, "None\n"))
        self.assertEqual(self.printed(["print", 5]), (None, "5\n"))
        self.assertEqual(self.printed(["print", True]), (None, "True\n"))
        self.assertEqual(self.printed(["print", False]), (None, "False\n"))
        self.assertEqual(self.printed(["print"]), (None, "\n"))
        self.assertEqual(self.printed(["print", 5, 6]), (None, "5 6\n"))

    def test_func(self):
        self.assertEqual(self.go([["func", ["n"], ["+", 5, "n"]], 6]), 11)

    def test_fib(self):
        self.go(["define", "fib", ["func", ["n"],
                ["if", ["=", "n", 0], 0,
                ["if", ["=", "n", 1], 1,
                ["+", ["fib", ["-", "n", 1]], ["fib", ["-", "n", 2]]]]]]])
        self.assertEqual(self.go(["fib", 0]), 0)
        self.assertEqual(self.go(["fib", 1]), 1)
        self.assertEqual(self.go(["fib", 2]), 1)
        self.assertEqual(self.go(["fib", 3]), 2)
        self.assertEqual(self.go(["fib", 10]), 55)

    def test_adder(self):
        self.go(["define", "make_adder", ["func", ["n"],
                ["func", ["m"], ["+", "n", "m"]]]])
        self.assertEqual(self.go([["make_adder", 5], 6]), 11)

    def test_counter(self):
        self.go(["define", "make_counter", ["func", [], ["seq",
                ["define", "c", 0],
                ["func", [], ["assign", "c", ["+", "c", 1]]]]]])
        self.go(["define", "counter1", ["make_counter"]])
        self.go(["define", "counter2", ["make_counter"]])
        self.assertEqual(self.go(["counter1"]), 1)
        self.assertEqual(self.go(["counter1"]), 2)
        self.assertEqual(self.go(["counter2"]), 1)
        self.assertEqual(self.go(["counter2"]), 2)
        self.assertEqual(self.go(["counter1"]), 3)
        self.assertEqual(self.go(["counter2"]), 3)

if __name__ == "__main__":
    unittest.main()