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

    def extend(self, params, args):
        env = Environment(self)
        for param, arg in zip(params, args):
            env.define(param, arg)
        return env

class Evaluator:
    def __init__(self, env):
        self._env = env

    def eval(self, expr):
        match expr:
            case None | bool(_) | int(_):
                return expr
            case str(name):
                return self._env.get(name)
            case ["func", params, body]:
                return ["func", params, body, self._env]
            case ["define", name, val]:
                return self._env.define(name, self.eval(val))
            case ["assign", name, val]:
                return self._env.assign(name, self.eval(val))
            case ["seq", *exprs]:
                return self._eval_seq(exprs)
            case ["if", cnd, thn, els]:
                return self._eval_if(cnd, thn, els)
            case [func, *args]:
                return self._apply(
                    self.eval(func),
                    [self.eval(arg) for arg in args])
            case unexpected:
                assert False, f"Unexpected expression: {unexpected} @ eval"

    def _eval_seq(self, exprs):
        val = None
        for expr in exprs:
            val = self.eval(expr)
        return val

    def _eval_if(self, cnd, thn, els):
        if self.eval(cnd):
            return self.eval(thn)
        else:
            return self.eval(els)

    def _apply(self, f_val, args_val):
        if callable(f_val):
            return f_val(*args_val)
        _, params, body, env = f_val
        prev_env = self._env
        self._env =  env.extend(params, args_val)
        val = self.eval(body)
        self._env = prev_env
        return val

import operator

class Interpreter:
    def __init__(self):
        self._env = Environment()

        _builtins = {
            "__builtins__": None,
            "add": operator.add,
            "sub": operator.sub,
            "equal": operator.eq,
            "print": print,
        }

        for name, func in _builtins.items():
            self._env.define(name, func)

        self._env = Environment(self._env)

    def go(self, src):
        return Evaluator(self._env).eval(src)

if __name__ == "__main__":
    i = Interpreter()
    i.go(["define", "fib", ["func", ["n"],
            ["if", ["equal", "n", 0], 0,
            ["if", ["equal", "n", 1], 1,
            ["add", ["fib", ["sub", "n", 1]], ["fib", ["sub", "n", 2]]]]]]])
    i.go(["print", ["fib", 10]])
