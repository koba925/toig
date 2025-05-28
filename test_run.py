import unittest
from unittest.mock import patch
from io import StringIO

from toig import init_env, stdlib, run

class TestEval(unittest.TestCase):
    def setUp(self):
        init_env()
        stdlib()

class TestCore(TestEval):
    def test_primitives(self):
        self.assertEqual(run("None"), None)
        self.assertEqual(run("5"), 5)
        self.assertEqual(run("True"), True)
        self.assertEqual(run("False"), False)