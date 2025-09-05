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

    def expanded(self, src):
        return self.i.run(f"expand({src})")

    def printed(self, src):
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            val = self.i.run(src)
            return (val, mock_stdout.getvalue())
