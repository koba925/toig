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

    def test_primary(self):
        self.assertEqual(self.go(None), None)
        self.assertEqual(self.go(5), 5)
        self.assertEqual(self.go(True), True)
        self.assertEqual(self.go(False), False)

    def test_quote(self):
        self.assertEqual(self.go(["q", 5]), 5)
        self.assertEqual(self.go(["q", ["add", 5, 6]]), ["add", 5, 6])

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

if __name__ == "__main__":
    unittest.main()