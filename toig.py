class Environment:
    def __init__(self, parent=None):
        self._parent = parent
        self._vals = {}

    def define(self, name, val):
        self._vals[name] = val

    def get(self, name):
        if name in self._vals:
            return self._vals[name]
        elif self._parent is not None:
            return self._parent.get(name)
        assert False, f"name '{name}' is not defined"

def is_value(expr):
    match expr:
        case None | bool(_) | int(_): return True
        case ["func", _params, _body, _env]: return True
        case f if callable(f): return True
        case _: return False

class Evaluator:
    def __init__(self, expr, env, cont):
        self._expr = expr
        self._env = env
        self._cont = cont

    def eval(self):
        while True:
            if is_value(self._expr):
                if self._cont == ["$halt"]: return self._expr
                self._apply_val()
            else:
                self._eval_expr()

    def _apply_val(self):
        match self._cont:
            case ["$if", thn_expr, els_expr, next_cont]:
                self._apply_if(thn_expr, els_expr, next_cont)
            case ["$define", name, next_cont]:
                self._apply_define(name, next_cont)
            case ["$call", args_expr, call_env, next_cont]:
                self._apply_call(args_expr, call_env, next_cont)
            case ["$args",
                    func_val, args_expr, args_val,
                    call_env, next_cont]:
                self._apply_args(func_val, args_expr, args_val,
                                 call_env, next_cont)
            case _:
                assert False, f"Invalid continuation: {self._cont}"

    def _apply_if(self, thn_expr, els_expr, next_cont):
        if self._expr:
            self._expr, self._cont = thn_expr, next_cont
        else:
            self._expr, self._cont = els_expr, next_cont

    def _apply_define(self, name, next_cont):
        self._env.define(name, self._expr)
        self._cont = next_cont

    def _apply_call(self, args_expr, call_env, next_cont):
        self._expr, self._env, self._cont = args_expr[0], call_env, [
            "$args",
            self._expr, args_expr[1:], [],
            call_env, next_cont
        ]

    def _apply_args(self,
                    func_val, args_expr, args_val,
                    call_env, next_cont):
        args_val += [self._expr]
        if args_expr == []:
            self._expr, self._env, self._cont  = [
                "$apply", func_val, args_val
            ], call_env, next_cont
        else:
            self._expr, self._env, self._cont = args_expr[0], call_env, [
                "$args",
                func_val, args_expr[1:], args_val,
                call_env, next_cont
            ]

    def _eval_expr(self):
        match self._expr:
            case ["func", params, body]:
                self._expr = ["func", params, body, self._env]
            case str(name):
                self._expr = self._env.get(name)
            case ["define", name, val_expr]:
                self._expr, self._cont = val_expr, \
                    ["$define", name, self._cont]
            case ["if", cnd_expr, thn_expr, els_expr]:
                self._expr, self._cont = cnd_expr, \
                    ["$if", thn_expr, els_expr, self._cont]
            case ["$apply", func_val, args_val]:
                self._apply_func(func_val, args_val)
            case [func_expr, *args_expr]:
                self._expr, self._cont = func_expr, \
                    ["$call", args_expr, self._env, self._cont]
            case _:
                assert False, f"Invalid expression: {self._expr}"

    def _apply_func(self, func_val, args_val):
        match func_val:
            case None | bool(_) | int(_):
                self._expr = func_val
            case f if callable(f):
                self._expr = func_val(args_val)
            case ["func", params, body_expr, closure_env]:
                closure_env = Environment(closure_env)
                for param, arg in zip(params, args_val):
                    closure_env.define(param, arg)
                self._expr, self._env = body_expr, closure_env
            case _:
                assert False, f"Invalid function: {self._expr}"

class Interpreter:
    def __init__(self):
        self.env = Environment()

        builtins = {
            "+": lambda args_val: args_val[0] + args_val[1],
            "-": lambda args_val: args_val[0] - args_val[1],
            "=": lambda args_val: args_val[0] == args_val[1],
            "print": lambda args_val: print(*args_val),
        }

        for name in builtins:
            self.env.define(name, builtins[name])
        self.env = Environment(self.env)

    def run(self, src):
        return Evaluator(src, self.env, ["$halt"]).eval()

# tests

i = Interpreter()

assert i.run(None) == None
assert i.run(5) == 5
assert i.run(True) == True
assert i.run(False) == False

assert i.run(["define", "a", 5]) == 5
assert i.run("a") == 5

assert i.run(["if", True, 5, 6]) == 5
assert i.run(["if", False, 5, 6]) == 6

assert i.run(["+", 5, 6]) == 11
assert i.run(["-", 11, 5]) == 6
assert i.run(["=", 5, 5]) == True
assert i.run(["=", 5, 6]) == False

assert i.run([["func", ["n"], ["+", 5, "n"]], 6]) == 11

i.run(["define", "fib", ["func", ["n"],
        ["if", ["=", "n", 0], 0,
        ["if", ["=", "n", 1], 1,
        ["+", ["fib", ["-", "n", 1]], ["fib", ["-", "n", 2]]]]]]])
assert i.run(["fib", 0]) == 0
assert i.run(["fib", 1]) == 1
assert i.run(["fib", 2]) == 1
assert i.run(["fib", 3]) == 2
assert i.run(["fib", 10]) == 55

i.run(["define", "make_adder", ["func", ["n"], ["func", ["m"], ["+", "n", "m"]]]])
assert i.run([["make_adder", 5], 6]) == 11

print("Success")
