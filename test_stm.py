import unittest
from unittest.mock import patch
from io import StringIO

from toig import Interpreter
from test_core import TestCoreBase
from test_stdlib import TestStdlibBase
from test_problems import TestProblemsBase

class TestBase(unittest.TestCase):
    def setUp(self):
        self.i = Interpreter()

    def go(self, src):
        return self.i.go(src)

    def fails(self, src):
        try: self.i.go(src)
        except AssertionError: return True
        else: return False

    def expanded(self, src):
        return self.i.go(f"expand({src})")

    def printed(self, src):
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            val = self.i.go(src)
            return (val, mock_stdout.getvalue())

class TestCore(TestBase, TestCoreBase):
    pass

class TestStdlib(TestBase, TestStdlibBase):
    pass

class TestProblems(TestBase, TestProblemsBase):
    pass

if __name__ == "__main__":
    unittest.main()