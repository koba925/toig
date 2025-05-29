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

    def test_define(self):
        self.assertEqual(run("x := 5"), 5)
        self.assertEqual(run("x"), 5)
        self.assertEqual(run("y := z := 6"), 6)
        self.assertEqual(run("y"), 6)
        self.assertEqual(run("z"), 6)
        self.assertTrue(fails("6 := 5"), 5)
