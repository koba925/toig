from commons import ToigStr
from parser import CustomRules, Parser
from stdlib import StdLib
from environment import Environment
from ici_evaluator import Expander, Compiler, VM
import builtin_functions

class Interpreter:
    def __init__(self):
        self._custom_rule = CustomRules()
        self._env = Environment()
        self._vm = VM(self._env)
        builtin_functions.load(self._env)
        self._vm.new_scope()
        StdLib(self).load()
        self._vm.new_scope()

    def __repr__(self) -> str:
        return f"Interpreter({self._vm})"

    def parse(self, src):
        return Parser(src, self._custom_rule).parse()

    def expand(self, expr):
        return Expander(self._vm).expand(expr)

    def compile(self, expr):
        return Compiler().compile(expr)

    def execute(self, code):
        self._vm.load(code)
        return self._vm.execute()

    def go(self, src):
        val = None
        for expr in Parser(src, self._custom_rule).parse_step():
            expanded = self.expand(expr)
            code = self.compile(expanded)
            val = self.execute(code)
        return str(val) if isinstance(val, ToigStr) else val

if __name__ == "__main__":

    i = Interpreter()

    def go_verbose(src):
        global i
        print(f"\nSource:\n{src}")
        expr = i.parse(src)
        print(f"AST:\n{expr}")
        expanded = i.expand(expr)
        print(f"Expanded AST:\n{expanded}")
        code = Compiler().compile(expanded)
        print("Compiled Code:")
        for addr, inst in enumerate(code):
            print(f"{addr:3}: {inst}")
        print("Output:")
        result = i.execute(code)
        print(f"Actual Result  : {result}")
        return result

    def go_test(src, expected):
        result = go_verbose(src)
        print(f"Expected Result: {expected}")
        assert expected == result

    print(go_verbose("""
        letcc cc do cc(5) + 6 end
    """))