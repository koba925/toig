import unittest

from toig import init_env, stdlib, run

def fails(expr):
    try: run(expr)
    except AssertionError: return True
    else: return False

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
        self.assertEqual(run("(5 + 6) * 7"), 77)
        self.assertEqual(run("5 * (6 + 7)"), 65)
        self.assertEqual(run("(5) + 6"), 11)


