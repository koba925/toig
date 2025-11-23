from commons import ToigStr
from parser import CustomRules, Parser
from stdlib import StdLib
from stm_evaluator import Environment, Evaluator
import builtin_functions

class Interpreter:
    def __init__(self):
        self._custom_rule = CustomRules()
        self._env = Environment()
        builtin_functions.load(self._env)
        self._env = Environment(self._env)
        StdLib(self).load()
        self._env = Environment(self._env)

    def parse(self, src):
        return Parser(src, self._custom_rule).parse()

    def expand(self, expr):
        return Evaluator(["expand", expr], self._env, ["$halt"]).eval()

    def go(self, src):
        val = Evaluator(self.parse(src), self._env, ["$halt"]).eval()
        return str(val) if isinstance(val, ToigStr) else val

if __name__ == "__main__":
    i = Interpreter()

    i.go("""
        alias := macro (als, org) do qq
            !als := macro (*args) do qq
                (!org)(!q(!!args))
            end end
        end end;

        print(expand(alias(a, add)));
        alias(a, add);

        print(expand(a(5, 6)));
        print(a(5, 6))
    """)
