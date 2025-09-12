from parser import CustomRules, Parser
from stdlib import StdLib
from environment import Environment
from ici_evaluator import Expander, Compiler, VM

# Builtins

def _get_at(_, s):
    arr = s.pop(); index = s.pop(); s.append(arr[index])

def _set_at(_, s):
    arr = s.pop(); index = s.pop(); val = s.pop()
    arr[index] = val
    s.append(val)

def _slice(_, s):
    arr = s.pop(); start = s.pop(); end = s.pop(); step = s.pop()
    s.append(arr[slice(start, end, step)])

def _set_slice(_, s):
    arr = s.pop(); start = s.pop(); end = s.pop(); step = s.pop(); val = s.pop()
    arr[start:end:step] = val
    s.append(val)

def _error(n, s):
    assert False, f"{' '.join(map(str, [s.pop() for _ in range(n)]))}"

_builtins = {
    "__builtins__": None,
    "add": lambda _, s: s.append(s.pop() + s.pop()),
    "sub": lambda _, s: s.append(s.pop() - s.pop()),
    "mul": lambda _, s: s.append(s.pop() * s.pop()),
    "div": lambda _, s: s.append(s.pop() // s.pop()),
    "mod": lambda _, s: s.append(s.pop() % s.pop()),
    "neg": lambda _, s: s.append(-s.pop()),

    "equal": lambda _, s: s.append(s.pop() == s.pop()),
    "not_equal": lambda _, s: s.append(s.pop() != s.pop()),
    "less": lambda _, s: s.append(s.pop() < s.pop()),
    "greater": lambda _, s: s.append(s.pop() > s.pop()),
    "less_equal": lambda _, s: s.append(s.pop() <= s.pop()),
    "greater_equal": lambda _, s: s.append(s.pop() >= s.pop()),
    "not": lambda _, s: s.append(not s.pop()),

    "array": lambda n, s: s.append([s.pop() for _ in range(n)]),
    "is_array": lambda _, s: s.append(isinstance(s.pop(), list)),
    "len": lambda _, s: s.append(len(s.pop())),
    "get_at": _get_at,
    "set_at": _set_at,
    "slice": _slice,
    "set_slice": _set_slice,

    "is_name": lambda _, s: s.append(isinstance(s.pop(), str)),

    "print": lambda n, s: s.append(print(*[s.pop() for _ in range(n)])),
    "error": _error
}

class Builtins:
    @staticmethod
    def load(env):
        for name, func in _builtins.items():
            env.define(name, func)

class Interpreter:
    def __init__(self):
        self._custom_rule = CustomRules()
        self._env = Environment()
        self._vm = VM(self._env)
        Builtins.load(self._env)
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
        return val

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

    i.go("""
        myadd := func (a, b) do a + b end;
        defmacro foo (a) do myadd([quote(array)], [a]) end;
        foo(5)
    """)


