import unittest
from unittest.mock import patch
from io import StringIO

from ici import Interpreter

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
        return self.i.expand(self.i.parse(src))

    def printed(self, src):
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            val = self.i.go(src)
            return (val, mock_stdout.getvalue())

from test_core import TestCoreBase
class TestCore(TestBase, TestCoreBase):
    pass

from test_stdlib import TestStdlibBase
class TestStdlib(TestBase, TestStdlibBase):
    pass

from test_problems import TestProblemsBase
class TestProblems(TestBase, TestProblemsBase):
    pass

from test_tail_call_optimization import TestTailCallOptimizationBase
class TestTailCallOptimization(TestBase, TestTailCallOptimizationBase):
    pass

if __name__ == "__main__":
    unittest.main()
