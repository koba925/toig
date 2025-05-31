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
        self.assertEqual(run("(5 + 6) * 7"), 77)
        self.assertEqual(run("5 * (6 + 7)"), 65)
        self.assertEqual(run("(5) + 6"), 11)


