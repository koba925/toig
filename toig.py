class Environment:
    def __init__(self, parent=None):
        self._parent = parent
        self._vals = {}

    def __repr__(self):
        return f"{
            "builtins" if "__builtins__" in self._vals else self._vals
        } > {self._parent}"

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

from typing import Callable
from dataclasses import dataclass

ValueType = None | bool | int | Callable | list

@dataclass
class Expr:
    elems: ValueType

class Evaluator:
    def __init__(self, expr, env, cont):
        self._expr: Expr | ValueType = expr
        self._env = env
        self._cont = cont

    def eval(self):
        while True:
            if isinstance(self._expr, Expr):
                self._eval_expr()
            elif self._cont == ["$halt"]:
                return self._expr
            else:
                self._apply_val()

    def _eval_expr(self):
        assert isinstance(self._expr, Expr)
        match self._expr.elems:
            case bool(_) | int(_) | None:
                self._expr = self._expr.elems
            case f if callable(f):
                self._expr = f
            case ["func", params, body]:
                self._expr = ["closure", params, body, self._env]
            case str(name):
                self._expr = self._env.get(name)
            case ["q", expr]:
                self._expr = expr
            case ["qq", expr]:
                self._expr, self._cont = expr, ["$qq", self._cont]
            case ["define", name, val_expr]:
                self._expr, self._cont = Expr(val_expr), \
                    ["$define", name, self._cont]
            case ["assign", name, val_expr]:
                self._expr, self._cont = Expr(val_expr), \
                    ["$assign", name, self._cont]
            case ["seq", *exprs]:
                self._expr, self._cont = None, \
                    ["$seq", exprs, self._cont]
            case ["if", cnd_expr, thn_expr, els_expr]:
                self._expr, self._cont = Expr(cnd_expr), \
                    ["$if", thn_expr, els_expr, self._cont]
            case ["$apply", elems_val]:
                self._apply_func(elems_val)
            case [func_expr, *args_expr]:
                self._expr, self._cont = Expr(func_expr), \
                    ["$call", args_expr, [], self._env, self._cont]
            case _:
                assert False, f"Invalid expression: {self._expr}"

    def _apply_func(self, elems_val):
        func_val, args_val = elems_val[0], elems_val[1:]
        match func_val:
            case f if callable(f):
                self._expr = func_val(args_val)
            case ["closure", params, body_expr, closure_env]:
                closure_env = Environment(closure_env)
                for param, arg in zip(params, args_val):
                    closure_env.define(param, arg)
                self._expr, self._env, self._cont = Expr(body_expr), closure_env, \
                    ["$restore_env", self._env, self._cont]
            case _:
                assert False, f"Invalid function: {self._expr}"

    def _apply_val(self):
        match self._cont:
            case ["$qq", next_cont]:
                self._apply_quasiquote(next_cont)
            case ["$qq_elems", splicing, elems, elems_done, next_cont]:
                self._apply_qq_elems(splicing, elems, elems_done, next_cont)
            case ["$define", name, next_cont]:
                self._apply_define(name, next_cont)
            case ["$assign", name, next_cont]:
                self._apply_assign(name, next_cont)
            case ["$seq", exprs, next_cont]:
                self._apply_seq(exprs, next_cont)
            case ["$if", thn_expr, els_expr, next_cont]:
                self._apply_if(thn_expr, els_expr, next_cont)
            case ["$call", elems_expr, elems_val, call_env, next_cont]:
                self._apply_call(elems_expr, elems_val, call_env, next_cont)
            case ["$restore_env", env, next_cont]:
                self._env, self._cont = env, next_cont
            case _:
                assert False, f"Invalid continuation: {self._cont}"

    def _apply_quasiquote(self, next_cont):
        match self._expr:
            case ["!", expr]:
                self._expr = Expr(expr)
                self._cont = next_cont
            case [["!!", elem], *rest]:
                self._expr = Expr(elem)
                self._cont = ["$qq_elems", True, rest, [], next_cont]
            case [first, *rest]:
                self._expr = first
                self._cont = ["$qq", ["$qq_elems", False, rest, [], next_cont]]
            case _:
                self._cont = next_cont

    def _apply_qq_elems(self, splicing, elems, elems_done, next_cont):
        if splicing:
            assert isinstance(self._expr , list), f"Cannot splice: {self._expr}"
            elems_done += self._expr
        else:
            elems_done += [self._expr]
        match elems:
            case []:
                self._expr, self._cont  = elems_done, next_cont
            case [["!!", elem], *rest]:
                self._expr = Expr(elem)
                self._cont = ["$qq_elems", True, rest, elems_done, next_cont]
            case [first, *rest]:
                self._expr = first
                self._cont = ["$qq", ["$qq_elems", False, rest, elems_done, next_cont]]
            case _:
                assert False, f"Invalid quasiquote elements: {elems}"

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
            self._expr, self._cont = Expr(exprs[0]), \
                ["$seq", exprs[1:], next_cont]

    def _apply_if(self, thn_expr, els_expr, next_cont):
        if self._expr:
            self._expr, self._cont = Expr(thn_expr), next_cont
        else:
            self._expr, self._cont = Expr(els_expr), next_cont

    def _apply_call(self, elems_expr, elems_val, call_env, next_cont):
        elems_val += [self._expr]
        if elems_expr == []:
            self._expr, self._env, self._cont = (
                Expr(["$apply", elems_val]), call_env, next_cont
            )
        else:
            self._expr, self._env, self._cont = (
                Expr(elems_expr[0]),
                call_env,
                ["$call", elems_expr[1:], elems_val, call_env, next_cont]
            )

def is_name(val):
    return isinstance(val, str)

def setat(args):
    args[0][args[1]] = args[2]
    return args[2]

def slice_(args):
    arr, start, end, step = args
    return arr[slice(start, end, step)]

def set_slice(args):
    arr, start, end, step, val = args
    arr[start:end:step] = val
    return val

def error(args):
    assert False, f"{' '.join(map(str, args))}"

class Interpreter:

    builtins = {
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

        "arr": lambda args: args,
        "is_arr": lambda args: isinstance(args[0], list),
        "len": lambda args: len(args[0]),
        "get_at": lambda args: args[0][args[1]],
        "set_at": setat,
        "slice": slice_,
        "set_slice": set_slice,

        "is_name": lambda args: isinstance(args[0], str),

        "print": lambda args: print(*args),
        "error": lambda args: error(args)
    }

    def __init__(self):
        self.env = Environment()
        for name, func in Interpreter.builtins.items():
            self.env.define(name, func)
        self.env = Environment(self.env)

    def run(self, src):
        return Evaluator(Expr(src), self.env, ["$halt"]).eval()

if __name__ == "__main__":
    i = Interpreter()

    assert i.run(["qq", 5]) == 5
    assert i.run(["qq", ["add", 5, 6]]) == ["add", 5, 6]
    assert i.run(["qq", ["mul", 4, ["add", 5, 6]]]) == ["mul", 4, ["add", 5, 6]]
    assert i.run(["qq", ["mul", ["add", 5, 6], 7]]) == ["mul", ["add", 5, 6], 7]

    assert i.run(["qq", ["!", ["add", 5, 6]]]) == 11
    assert i.run(["qq", ["mul", 4, ["!", ["add", 5, 6]]]]) == ["mul", 4, 11]
    assert i.run(["qq", ["mul", ["!", ["add", 5, 6]], 7]]) == ["mul", 11, 7]

    assert i.run(["qq", ["add", ["!!", ["arr", 5, 6]]]]) == ["add", 5, 6]
    assert i.run(["qq", [
        ["!!", ["arr", 3]],
        4,
        ["!!", ["arr", 5, 6]],
        7]]) == [3, 4, 5, 6, 7]
