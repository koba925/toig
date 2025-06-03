import unittest
from unittest.mock import patch
from io import StringIO

from toig import init_env, stdlib, run

def fails(expr):
    try: run(expr)
    except AssertionError: return True
    else: return False

def printed(expr):
    with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
        val = run(expr)
        return (val, mock_stdout.getvalue())

class TestEval(unittest.TestCase):
    def setUp(self):
        init_env()
        stdlib()

class TestCore(TestEval):
    def test_primary(self):
        self.assertEqual(run("None"), None)
        self.assertEqual(run("5"), 5)
        self.assertEqual(run("True"), True)
        self.assertEqual(run("False"), False)

    def test_sequence(self):
        self.assertEqual(run("x := 5; y := 6; x + y"), 11)
        self.assertEqual(run("x"), 5)
        self.assertEqual(run("y"), 6)
        self.assertEqual(run("x = 6; y = 7; x * y"), 42)
        self.assertEqual(run("x"), 6)
        self.assertEqual(run("y"), 7)
        self.assertTrue(fails(";"))

    def test_define(self):
        self.assertEqual(run("x := 5"), 5)
        self.assertEqual(run("x"), 5)
        self.assertEqual(run("y := z := 6"), 6)
        self.assertEqual(run("y"), 6)
        self.assertEqual(run("z"), 6)
        self.assertTrue(fails("6 := 5"), 5)

    def test_assign(self):
        self.assertEqual(run("x := y := 5"), 5)
        self.assertEqual(run("x = 6"), 6)
        self.assertEqual(run("x"), 6)
        self.assertEqual(run("x = y = 7"), 7)
        self.assertEqual(run("x"), 7)
        self.assertEqual(run("y"), 7)
        self.assertTrue(fails("z = 5"))
        self.assertTrue(fails("6 = 5"))

    def test_or(self):
        self.assertTrue(run("5 == 5 or 5 == 5"))
        self.assertTrue(run("5 == 5 or 5 != 5"))
        self.assertTrue(run("5 != 5 or 5 == 5"))
        self.assertFalse(run("5 != 5 or 5 != 5"))

        self.assertEqual(run("5 or x"), 5)
        self.assertEqual(run("False or 5"), 5)

        self.assertTrue(run("False or False or True"))
        self.assertFalse(run("False or False or False"))

        self.assertEqual(run("x := True or False"), True)
        self.assertEqual(run("x"), True)

    def test_and(self):
        self.assertTrue(run("5 == 5 and 5 == 5"))
        self.assertFalse(run("5 == 5 and 5 != 5"))
        self.assertFalse(run("5 != 5 and 5 == 5"))
        self.assertFalse(run("5 != 5 and 5 != 5"))

        self.assertEqual(run("True and 5"), 5)
        self.assertEqual(run("0 and x"), 0)

        self.assertTrue(run("True or True and False"))
        self.assertFalse(run("(True or True) and False"))

    def test_not(self):
        self.assertFalse(run("not 5 == 5"))
        self.assertTrue(run("not 5 != 5"))

        self.assertFalse(run("not True and False"))
        self.assertTrue(run("not (True and False)"))

    def test_comparison(self):
        self.assertTrue(run("5 + 8 == 6 + 7"))
        self.assertFalse(run("5 + 6 == 6 + 7"))
        self.assertFalse(run("5 + 8 != 6 + 7"))
        self.assertTrue(run("5 + 6 != 6 + 7"))

        self.assertTrue(run("5 + 7 < 6 + 7"))
        self.assertFalse(run("5 + 8 < 6 + 7"))
        self.assertFalse(run("5 + 8 < 5 + 7"))
        self.assertFalse(run("5 + 7 > 6 + 7"))
        self.assertFalse(run("5 + 8 > 6 + 7"))
        self.assertTrue(run("5 + 8 > 5 + 7"))

        self.assertTrue(run("5 + 7 <= 6 + 7"))
        self.assertTrue(run("5 + 8 <= 6 + 7"))
        self.assertFalse(run("5 + 8 <= 5 + 7"))
        self.assertFalse(run("5 + 7 >= 6 + 7"))
        self.assertTrue(run("5 + 8 >= 6 + 7"))
        self.assertTrue(run("5 + 8 >= 5 + 7"))

        self.assertEqual(run("not 5 == 6"), True)
        self.assertEqual(run("(not 5) == 6"), False)

    def test_add_sub(self):
        self.assertEqual(run("5 + 6 + 7"), 18)
        self.assertEqual(run("18 - 6 - 7"), 5)
        self.assertEqual(run("x := 5 + 6"), 11)
        self.assertEqual(run("x"), 11)

    def test_mul_div_mod(self):
        self.assertEqual(run("5 * 6 * 7"), 210)
        self.assertEqual(run("210 / 6 / 7"), 5)
        self.assertEqual(run("216 / 6 % 7"), 1)
        self.assertEqual(run("5 + 6 * 7"), 47)
        self.assertEqual(run("5 * 6 + 7"), 37)

    def test_neg(self):
        self.assertEqual(run("-5"), -5)
        self.assertEqual(run("-5 * 6"), -30)
        self.assertEqual(run("5 * -6"), -30)

    def test_paren(self):
        self.assertEqual(run("(5; 6) * 7"), 42)
        self.assertEqual(run("5 * (6; 7)"), 35)
        self.assertEqual(run("(5) + 6"), 11)

        self.assertTrue(fails("(5"))

    def test_if(self):
        self.assertEqual(run("if 5; True then 6; 7 end"), 7)
        self.assertEqual(run("if 5; False then 6; 7 end"), None)
        self.assertEqual(run("if 5; True then 6; 7 else 8; 9 end"), 7)
        self.assertEqual(run("if 5; False then 6; 7 else 8; 9 end"), 9)
        self.assertEqual(run("if 5; True then 6; 7 elif 8; True then 9; 10 else 11; 12 end"), 7)
        self.assertEqual(run("if 5; False then 6; 7 elif 8; True then 9; 10 else 11; 12 end"), 10)
        self.assertEqual(run("if 5; False then 6; 7 elif 8; False then 9; 10 else 11; 12 end"), 12)

        self.assertEqual(run("-if 5; True then 6; 7 end"), -7)

        self.assertTrue(fails("if True end"))
        self.assertTrue(fails("if True then"))
        self.assertTrue(fails("if True then 5 else"))

    def test_while(self):
        self.assertEqual(run("""
            i := sum := 0;
            while i < 10 do
                sum = sum + i;
                i = i + 1;
                sum
            end
        """), 45)

    def test_break_continue(self):
        self.assertEqual(run("""
            i := sum := 0;
            while True do
                if i == 5 then i = i + 1; continue end;
                if i >= 10 then break sum end;
                sum = sum + i;
                i = i + 1
            end
        """), 40)

        self.assertTrue(fails("break 5"))
        self.assertTrue(fails("continue"))

    def test_call(self):
        self.assertEqual(run("add(5; 6, 7; 8)"), 14)
        self.assertEqual(run("inc(5; 6)"), 7)
        self.assertEqual(run("and(True, False)"), False)
        self.assertEqual(run("""
            i := sum := 0;
            awhile(True,
                if i == 5 then i = i + 1; continue end;
                if i >= 10 then break sum end;
                sum = sum + i;
                i = i + 1
            )
        """), 40)

        self.assertTrue(fails("inc(5"))
        self.assertTrue(fails("inc(5 6)"))

    def test_func(self):
        self.assertEqual(run("func (a, b) a + b end (5, 6)"), 11)
        self.assertEqual(run("func (*args) args end ()"), [])
        self.assertEqual(run("func (*args) args end (5)"), [5])
        self.assertEqual(run("func (*args) args end (5, 6)"), [5, 6])
        self.assertEqual(run("func (*(args)) args end (5, 6)"), [5, 6])

        self.assertTrue(fails("*a"))
        self.assertTrue(fails("func (a, b) a + b"))
        self.assertTrue(fails("func a, b) a + b end (5, 6)"))
        self.assertTrue(fails("func (a, b a + b end (5, 6)"))
        self.assertTrue(fails("func (a b) a + b end (5, 6)"))
        self.assertTrue(fails("func (a, b + c) a + b end (5, 6)"))
