import unittest
from unittest.mock import patch
from io import StringIO

from toig import Interpreter

class TestToig(unittest.TestCase):

    def setUp(self):
        self.i = Interpreter()

    def go(self, src):
        return self.i.go(src)

    def fails(self, src):
        try: self.i.go(src)
        except AssertionError: return True
        else: return False

    def printed(self, src):
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            val = self.i.go(src)
            return (val, mock_stdout.getvalue())

    def test_primitives(self):
        self.assertEqual(self.go("None"), None)
        self.assertEqual(self.go("5"), 5)
        self.assertEqual(self.go("True"), True)
        self.assertEqual(self.go("False"), False)

    def test_define(self):
        self.assertEqual(self.go("x := 5 == 5 "), True)
        self.assertEqual(self.go("x"), True)
        self.assertEqual(self.go("y := z := 6"), 6)
        self.assertEqual(self.go("y"), 6)
        self.assertEqual(self.go("z"), 6)

    def test_assign(self):
        self.assertEqual(self.go("x := y := 5"), 5)
        self.assertEqual(self.go("x"), 5)
        self.assertEqual(self.go("x = 5 == 5"), True)
        self.assertEqual(self.go("x"), True)
        self.assertEqual(self.go("x = y = 7"), 7)
        self.assertEqual(self.go("x"), 7)
        self.assertEqual(self.go("y"), 7)

    def test_sequence(self):
        self.assertEqual(self.go("x := 5; y := 6; x + y"), 11)
        self.assertEqual(self.go("x"), 5)
        self.assertEqual(self.go("y"), 6)
        self.assertTrue(self.fails(";"))

    def test_comparison(self):
        self.assertTrue(self.go("5 + 8 == 6 + 7"))
        self.assertFalse(self.go("5 + 6 == 6 + 7"))

    def test_add_sub(self):
        self.assertEqual(self.go("5 + 6 + 7"), 18)
        self.assertEqual(self.go("18 - 6 - 7"), 5)

    def test_paren(self):
        self.assertEqual(self.go("5 + 6; 7"), 7)
        self.assertEqual(self.go("5 + (6; 7)"), 12)
        self.assertEqual(self.go("(5) + 6"), 11)

    def test_call(self):
        self.assertEqual(self.go("add(5; 6, 7; 8)"), 14)

    def test_print(self):
        self.assertEqual(self.printed("print(None)"), (None, "None\n"))
        self.assertEqual(self.printed("print(5)"), (None, "5\n"))
        self.assertEqual(self.printed("print(True)"), (None, "True\n"))
        self.assertEqual(self.printed("print(False)"), (None, "False\n"))
        self.assertEqual(self.printed("print()"), (None, "\n"))
        self.assertEqual(self.printed("print(5, 6)"), (None, "5 6\n"))

    def test_func(self):
        self.assertEqual(self.go("func (a, b) do a + b end (5, 6)"), 11)

    def test_if(self):
        self.assertEqual(self.go("if 5; True then 6; 7 end"), 7)
        self.assertEqual(self.go("if 5; False then 6; 7 end"), None)
        self.assertEqual(self.go("if 5; True then 6; 7 else 8; 9 end"), 7)
        self.assertEqual(self.go("if 5; False then 6; 7 else 8; 9 end"), 9)
        self.assertEqual(self.go("if 5; True then 6; 7 elif 8; True then 9; 10 else 11; 12 end"), 7)
        self.assertEqual(self.go("if 5; False then 6; 7 elif 8; True then 9; 10 else 11; 12 end"), 10)
        self.assertEqual(self.go("if 5; False then 6; 7 elif 8; False then 9; 10 else 11; 12 end"), 12)

        self.assertTrue(self.fails("if True end"))
        self.assertTrue(self.fails("if True then"))
        self.assertTrue(self.fails("if True then 5 else"))

    def test_fib(self):
        self.go("""
            fib := func (n) do
                if n == 0 then 0
                elif n == 1 then 1
                else fib(n - 1) + fib(n - 2) end
            end
        """)
        self.assertEqual(self.go("fib(0)"), 0)
        self.assertEqual(self.go("fib(1)"), 1)
        self.assertEqual(self.go("fib(2)"), 1)
        self.assertEqual(self.go("fib(3)"), 2)
        self.assertEqual(self.go("fib(10)"), 55)

    def test_closure_adder(self):
        self.go("make_adder := func (n) do func (m) do n + m end end")
        self.assertEqual(self.go("make_adder(5)(6)"), 11)

    def test_closure_counter(self):
        self.go("""
            make_counter := func () do c := 0; func() do c = c + 1 end end;
            counter1 := make_counter();
            counter2 := make_counter()
        """)
        self.assertEqual(self.go("counter1()"), 1)
        self.assertEqual(self.go("counter1()"), 2)
        self.assertEqual(self.go("counter2()"), 1)
        self.assertEqual(self.go("counter2()"), 2)
        self.assertEqual(self.go("counter1()"), 3)
        self.assertEqual(self.go("counter2()"), 3)

if __name__ == "__main__":
    unittest.main()