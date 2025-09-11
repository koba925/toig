from parser import CustomRules, Parser
from stdlib import StdLib
from stm_evaluator import Environment, Evaluator

# Builtin Functions

def _set_at(args):
    args[0][args[1]] = args[2]
    return args[2]

def _slice(args):
    arr, start, end, step = args
    return arr[slice(start, end, step)]

def _set_slice(args):
    arr, start, end, step, val = args
    arr[start:end:step] = val
    return val

def _error(args):
    assert False, f"{' '.join(map(str, args))}"

_builtins = {
    "__builtins__": None,
    "add": lambda args: args[0] + args[1],
    "sub": lambda args: args[0] - args[1],
    "mul": lambda args: args[0] * args[1],
    "div": lambda args: args[0] // args[1],
    "mod": lambda args: args[0] % args[1],
    "neg": lambda args: -args[0],

    "equal": lambda args: args[0] == args[1],
    "not_equal": lambda args: args[0] != args[1],
    "less": lambda args: args[0] < args[1],
    "greater": lambda args: args[0] > args[1],
    "less_equal": lambda args: args[0] <= args[1],
    "greater_equal": lambda args: args[0] >= args[1],
    "not": lambda args: not args[0],

    "array": lambda args: args,
    "is_array": lambda args: isinstance(args[0], list),
    "len": lambda args: len(args[0]),
    "get_at": lambda args: args[0][args[1]],
    "set_at": _set_at,
    "slice": _slice,
    "set_slice": _set_slice,

    "is_name": lambda args: isinstance(args[0], str),

    "print": lambda args: print(*args),
    "error": lambda args: _error(args)
}

class BuiltIns:
    @staticmethod
    def load(env):
        for name, func in _builtins.items():
            env.define(name, func)

class Interpreter:
    def __init__(self):
        self._custom_rule = CustomRules()
        self._env = Environment()
        BuiltIns.load(self._env)
        self._env = Environment(self._env)
        StdLib(self).load()
        self._env = Environment(self._env)

    def parse(self, src):
        return Parser(src, self._custom_rule).parse()

    def go(self, src):
        return Evaluator(self.parse(src), self._env, ["$halt"]).eval()

if __name__ == "__main__":
    i = Interpreter()

    src = """
        5 + 6
    """

    print(i.parse(src))
    print(i.go(src))
