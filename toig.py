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
            return f_val(*args_val)

        _, params, body, env = f_val
        new_env = Environment(env)
        for param, arg in zip(params, args_val):
            new_env.define(param, arg)
        return self.eval(body, new_env)

class Interpreter:
    def __init__(self):
        self._env = Environment()
        self.init_builtins()

    def init_builtins(self):
        _builtins = {
            "add": lambda a, b: a + b,
            "sub": lambda a, b: a - b,
            "equal": lambda a, b: a == b,
            "print": print
        }

        for name, func in _builtins.items():
            self._env.define(name, func)

        self._env = Environment(self._env)

    def go(self, src):
        return Evaluator().eval(src, self._env)

if __name__ == "__main__":
    i = Interpreter()

    i.go(["define", "fib", ["func", ["n"],
            ["if", ["equal", "n", 0], 0,
            ["if", ["equal", "n", 1], 1,
            ["add", ["fib", ["sub", "n", 1]], ["fib", ["sub", "n", 2]]]]]]])
    i.go(["print", ["fib", 10]])

    i.go(["define", "make_counter", ["func", [], ["seq",
            ["define", "c", 0],
            ["func", [], ["assign", "c", ["add", "c", 1]]]]]])
    i.go(["define", "counter1", ["make_counter"]])
    i.go(["define", "counter2", ["make_counter"]])
    i.go(["print", ["counter1"]])
    i.go(["print", ["counter1"]])
    i.go(["print", ["counter2"]])
    i.go(["print", ["counter2"]])
    i.go(["print", ["counter1"]])
    i.go(["print", ["counter2"]])
