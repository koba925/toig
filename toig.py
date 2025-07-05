class Environment:
    def __init__(self, parent=None):
        self._parent = parent
        self._vals = {}

    def define(self, name, val):
        self._vals[name] = val

    def assign(self, name, val):
        if name in self._vals:
            self._vals[name] = val
        elif self._parent is not None:
            self._parent.assign(name, val)
        else:
            assert False, f"name '{name}' is not defined"

    def get(self, name):
        if name in self._vals:
            return self._vals[name]
        elif self._parent is not None:
            return self._parent.get(name)
        else:
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
            case ["$define", name, next_cont]:
                self._apply_define(name, next_cont)
            case ["$assign", name, next_cont]:
                self._apply_assign(name, next_cont)
            case ["$seq", exprs, next_cont]:
                self._apply_seq(exprs, next_cont)
            case ["$if", thn_expr, els_expr, next_cont]:
                self._apply_if(thn_expr, els_expr, next_cont)
            case ["$call", args_expr, call_env, next_cont]:
                self._apply_call(args_expr, call_env, next_cont)
            case ["$args",
                    func_val, args_expr, args_val,
                    call_env, next_cont]:
                self._apply_args(func_val, args_expr, args_val,
                                 call_env, next_cont)
            case ["$restore_env", env, next_cont]:
                self._env, self._cont = env, next_cont
            case _:
                assert False, f"Invalid continuation: {self._cont}"

    def _apply_define(self, name, next_cont):
        self._env.define(name, self._expr)
        self._cont = next_cont

    def _apply_assign(self, name, next_cont):
        self._env.assign(name, self._expr)
        self._cont = next_cont

    def _apply_seq(self, exprs, next_cont):
        if exprs == []:
            self._cont = next_cont
        else:
            self._expr, self._cont = exprs[0], ["$seq", exprs[1:], next_cont]

    def _apply_if(self, thn_expr, els_expr, next_cont):
        if self._expr:
            self._expr, self._cont = thn_expr, next_cont
        else:
            self._expr, self._cont = els_expr, next_cont

    def _apply_call(self, args_expr, call_env, next_cont):
        if args_expr == []:
            self._expr, self._env, self._cont  = [
                "$apply", self._expr, []
            ], call_env, next_cont
        else:
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
            case ["assign", name, val_expr]:
                self._expr, self._cont = val_expr, \
                    ["$assign", name, self._cont]
            case ["seq", *exprs]:
                self._expr, self._cont = None, \
                    ["$seq", exprs, self._cont]
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
            case f if callable(f):
                self._expr = func_val(args_val)
            case ["func", params, body_expr, closure_env]:
                closure_env = Environment(closure_env)
                for param, arg in zip(params, args_val):
                    closure_env.define(param, arg)
                self._expr, self._env, self._cont = body_expr, closure_env, \
                    ["$restore_env", self._env, self._cont]
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

def run(src): return i.run(src)

def fails(expr):
    try: i.run(expr)
    except AssertionError: return True
    else: return False

import sys
from io import StringIO

def printed(expr):
    stdout_bak = sys.stdout
    sys.stdout = captured = StringIO()
    try: val = i.run(expr)
    finally: sys.stdout = stdout_bak
    return val, captured.getvalue()

assert run(None) == None
assert run(5) == 5
assert run(True) == True
assert run(False) == False

assert run(["define", "a", 5]) == 5
assert run("a") == 5
assert run(["define", "a", 6]) == 6
assert run("a") == 6
assert printed([["func", [], ["seq",
                    ["print", ["define", "a", 7]],
                    ["print", "a"]]]]) == (None, "7\n7\n")
assert run("a") == 6
assert fails(["b"])

assert run(["assign", "a", 7]) == 7
assert run("a") == 7
assert run([["func", [], ["assign", "a", 8]]]) == 8
assert run("a") == 8
assert printed([["func", [], ["seq",
                    ["print", ["assign", "a", 9]],
                    ["print", "a"]]]]) == (None, "9\n9\n")
assert run("a") == 9
assert fails(["assign", "b", 6])

assert run(["seq"]) == None
assert run(["seq", 5]) == 5
assert run(["seq", 5, 6]) == 6
assert printed(["seq", ["print", 5]]) == (None, "5\n")
assert printed(["seq", ["print", 5], ["print", 6]]) == (None, "5\n6\n")

assert run(["if", True, 5, 6]) == 5
assert run(["if", False, 5, 6]) == 6
assert fails(["if", True, 5])

assert run(["+", 5, 6]) == 11
assert run(["-", 11, 5]) == 6
assert run(["=", 5, 5]) == True
assert run(["=", 5, 6]) == False
# assert fails(["+", 5])
# assert fails(["+", 5, 6, 7])

assert run([["func", ["n"], ["+", 5, "n"]], 6]) == 11
# assert fails([["func", ["n"], ["+", 5, "n"]]])
# assert fails([["func", ["n"], ["+", 5, "n"]], 6, 7])

run(["define", "fib", ["func", ["n"],
        ["if", ["=", "n", 0], 0,
        ["if", ["=", "n", 1], 1,
        ["+", ["fib", ["-", "n", 1]], ["fib", ["-", "n", 2]]]]]]])
assert run(["fib", 0]) == 0
assert run(["fib", 1]) == 1
assert run(["fib", 2]) == 1
assert run(["fib", 3]) == 2
assert run(["fib", 10]) == 55

run(["define", "make_adder", ["func", ["n"], ["func", ["m"], ["+", "n", "m"]]]])
assert run([["make_adder", 5], 6]) == 11

run(["define", "make_counter", ["func", [], ["seq",
        ["define", "c", 0],
        ["func", [], ["assign", "c", ["+", "c", 1]]]]]])
run(["define", "counter1", ["make_counter"]])
run(["define", "counter2", ["make_counter"]])
assert run(["counter1"]) == 1
assert run(["counter1"]) == 2
assert run(["counter2"]) == 1
assert run(["counter2"]) == 2
assert run(["counter1"]) == 3
assert run(["counter2"]) == 3

print("Success")
