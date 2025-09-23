class Environment:
    def __init__(self, parent=None):
        self._parent = parent
        self._vals = {}

    def define(self, name, val):
        self._vals[name] = val
        return val

    def assign(self, name, val):
        if name in self._vals:
            self._vals[name] = val
            return val
        elif self._parent is not None:
            return self._parent.assign(name, val)
        else:
            assert False, f"Undefined variable: `{name}` @ assign."

    def get(self, name):
        if name in self._vals:
            return self._vals[name]
        elif self._parent is not None:
            return self._parent.get(name)
        else:
            assert False, f"Undefined variable: `{name}` @ get"

class Evaluator:
    def eval(self, expr, env):
        match expr:
            case None | bool(_) | int(_):
                return expr
            case str(name):
                return env.get(name)
            case ["func", params, body]:
                return ["func", params, body, env]
            case ["quote", expr]:
                return expr
            case ["define", name, val]:
                return env.define(name, self.eval(val, env))
            case ["assign", name, val]:
                return env.assign(name, self.eval(val, env))
            case ["seq", *exprs]:
                return self._eval_seq(exprs, env)
            case ["if", cnd, thn, els]:
                return self._eval_if(cnd, thn, els, env)
            case [func, *args]:
                return self._apply(
                    self.eval(func, env),
                    [self.eval(arg, env) for arg in args])
            case unexpected:
                assert False, f"Unexpected expression: {unexpected} @ eval"

    def _eval_seq(self, exprs, env):
        val = None
        for expr in exprs:
            val = self.eval(expr, env)
        return val

    def _eval_if(self, cnd, thn, els, env):
        if self.eval(cnd, env):
            return self.eval(thn, env)
        else:
            return self.eval(els, env)

    def _apply(self, f_val, args_val):
        if callable(f_val):
            return f_val(args_val)

        _, params, body, env = f_val
        new_env = Environment(env)
        for param, arg in zip(params, args_val):
            new_env.define(param, arg)
        return self.eval(body, new_env)

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
    "not": lambda args: not args[0],
    "equal": lambda args: args[0] == args[1],

    "array": lambda args: args,
    "get_at": lambda args: args[0][args[1]],
    "set_at": _set_at,
    "append": lambda args: args[0].append(args[1]),
    "slice": _slice,
    "set_slice": _set_slice,

    "is_bool": lambda args: type(args[0]) is bool,
    "is_int": lambda args: type(args[0]) is int,
    "is_array": lambda args: type(args[0]) is list,

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
        self._env = Environment()
        BuiltIns.load(self._env)
        self._env = Environment(self._env)

    def go(self, src):
        return Evaluator().eval(src, self._env)

if __name__ == "__main__":
    i = Interpreter()

    i.go(["define", "fib", ["func", ["n"],
            ["if", ["equal", "n", 0], 0,
            ["if", ["equal", "n", 1], 1,
            ["add", ["fib", ["sub", "n", 1]], ["fib", ["sub", "n", 2]]]]]]])
    assert i.go(["fib", 10]) == 55

    i.go(["define", "make_counter", ["func", [], ["seq",
            ["define", "c", 0],
            ["func", [], ["assign", "c", ["add", "c", 1]]]]]])
    i.go(["define", "counter1", ["make_counter"]])
    i.go(["define", "counter2", ["make_counter"]])
    assert i.go(["counter1"]) == 1
    assert i.go(["counter1"]) == 2
    assert i.go(["counter2"]) == 1
    assert i.go(["counter2"]) == 2
    assert i.go(["counter1"]) == 3
    assert i.go(["counter2"]) == 3

    # eval on eval

    i.go(["define", "define_", ["func", ["env", "name", "val"], ["seq",
        ["define", "_define_", ["func", ["pairs"],
            ["if", ["equal", "pairs", ["array"]],
                ["seq",
                    ["append", ["get_at", "env", 1], ["array", "name", "val"]],
                    "val"],
                ["seq",
                    ["define", "name_val", ["get_at", "pairs", 0]],
                    ["if", ["equal", ["get_at", "name_val", 0], "name"],
                        ["set_at", "name_val", 1, "val"],
                        ["_define_", ["slice", "pairs", 1, None, None]]]]]]],
        ["_define_", ["get_at", "env", 1]]
    ]]])

    i.go(["define", "assign_", ["func", ["env", "name", "val"], ["seq",
        ["define", "_assign_", ["func", ["pairs"],
            ["if", ["equal", "pairs", ["array"]],
                ["assign_", ["get_at", "env", 0], "name", "val"],
                ["seq",
                    ["define", "name_val", ["get_at", "pairs", 0]],
                    ["if", ["equal", ["get_at", "name_val", 0], "name"],
                        ["set_at", "name_val", 1, "val"],
                        ["_assign_", ["slice", "pairs", 1, None, None]]]]]]],
        ["if", ["equal", "env", None],
            ["error", "name"],
            ["_assign_", ["get_at", "env", 1]]]]]])

    i.go(["define", "get_", ["func", ["env", "name"], ["seq",
        ["define", "_get_", ["func", ["pairs"],
            ["if", ["equal", "pairs", ["array"]],
                ["get_", ["get_at", "env", 0], "name"],
                ["seq",
                    ["define", "name_val", ["get_at", "pairs", 0]],
                    ["if", ["equal", ["get_at", "name_val", 0], "name"],
                        ["get_at", "name_val", 1],
                        ["_get_", ["slice", "pairs", 1, None, None]]]]]]],
        ["if", ["equal", "env", None],
            ["error", "name"],
            ["_get_", ["get_at", "env", 1]]]]]])

    i.go(["define", "eval", ["func", ["expr", "env"],
        ["if", ["not", ["is_array", "expr"]],
            ["if", ["equal", "expr", None], None,
            ["if", ["is_bool", "expr"], "expr",
            ["if", ["is_int", "expr"], "expr",
            ["get_", "env", "expr"]]]],
            ["seq",
                ["define", "op", ["get_at", "expr", 0]],
                ["if", ["equal", "op", ["quote","quote"]],
                    ["eval", ["get_at", "expr", 1], "env"],
                ["if", ["equal", "op", ["quote", "define"]],
                    ["define_", "env",
                        ["get_at", "expr", 1],
                        ["eval", ["get_at", "expr", 2], "env"]],
                ["if", ["equal", "op", ["quote", "assign"]],
                    ["assign_", "env",
                        ["get_at", "expr", 1],
                        ["eval", ["get_at", "expr", 2], "env"]],
                ["if", ["equal", "op", ["quote", "if"]],
                    ["if", ["eval", ["get_at", "expr", 1], "env"],
                        ["eval", ["get_at", "expr", 2], "env"],
                        ["eval", ["get_at", "expr", 3], "env"]],
                ["error", "expr"]]]]]
            ]
        ]
    ]])

    i.go(["define", "global_env", ["array", None, ["array"]]])

    def eval(expr):
        return i.go(["eval", ["quote", expr], "global_env"])

    def fails(expr):
        try: eval(expr)
        except AssertionError: return True
        else: return False

    assert eval(None) == None
    assert eval(True) == True
    assert eval(False) == False
    assert eval(5) == 5

    assert eval(["if", True, 5, 6]) == 5
    assert eval(["if", False, 5, 6]) == 6
    assert eval(["if", ["if", True, True, True], 5, 6]) == 5
    assert eval(["if", True, ["if", True, 5, 6], 7]) == 5
    assert eval(["if", False, 5, ["if", False, 6, 7]]) == 7

    assert eval(["define", "a", 5]) == 5
    assert eval(["define", "b", 6]) == 6
    assert eval("a") == 5
    assert eval("b") == 6

    assert eval(["define", "b", 7]) == 7
    assert eval("a") == 5
    assert eval("b") == 7

    i.go(["define", "global_env", ["array", "global_env", ["array"]]])

    assert eval(["define", "a", 8]) == 8
    assert eval("a") == 8
    assert eval("b") == 7

    assert eval(["assign", "a", 9]) == 9
    assert eval("a") == 9
    assert eval("b") == 7

    assert eval(["assign", "b", 10]) == 10
    assert eval("a") == 9
    assert eval("b") == 10

    assert fails(["assign", "c", 11])
    assert fails("c")

    i.go(["define", "global_env", ["get_at", "global_env", 0]])

    assert eval("a") == 5
    assert eval("b") == 10


