import pytest

from ici import Interpreter as ICI
from stm import Interpreter as STM

class BaseTest:
    @pytest.fixture(autouse=True)
    def set_interpreter(self, request):
        self.i = request.param()

    def parsed(self, src):
        return self.i.parse(src)

    def expanded(self, src):
        return self.i.expand(self.parsed(src))

    def go(self, src):
        return self.i.go(src)