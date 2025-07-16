class Environment:
    def __init__(self, parent=None):
        self._parent = parent
        self._vals = {}

    def __repr__(self):
        if "__builtins__" in self._vals:
            this_env = "builtins"
        elif "__stdlib__" in self._vals:
            this_env = "stdlib"
        else:
            this_env = self._vals
        return f"{this_env} > {self._parent}"

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

    def extend(self, params, args):
        def _extend(params, args):
            if params == [] and args == []: return {}
            assert len(params) > 0, \
                f"Argument count doesn't match: `{params}, {args}` @ extend"
            match params[0]:
                case str(param):
                    assert len(args) > 0, \
                        f"Argument count doesn't match: `{params}, {args}` @ extend"
                    env.define(param, args[0])
                    _extend(params[1:], args[1:])
                case ["*", rest]:
                    rest_len = len(args) - len(params) + 1
                    assert rest_len >= 0, \
                        f"Argument count doesn't match: `{params}, {args}` @ extend"
                    env.define(rest, args[:rest_len])
                    _extend(params[1:], args[rest_len:])
                case unexpected:
                    assert False, f"Unexpected param at extend: {unexpected}"

        env = Environment(self)
        _extend(params, args)
        return env

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
            case ["macro", params, body]:
                self._expr = ["mclosure", params, body, self._env]
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
            case ["expand", [op_expr, *args_expr]]:
                self._expr, self._cont = Expr(op_expr), \
                    ["$expand", args_expr, self._env, self._cont]
            case ["$apply", op_val, args_val]:
                self._apply_op(op_val, args_val)
            case [op_expr, *args_expr]:
                self._expr, self._cont = Expr(op_expr), \
                    ["$call", args_expr, self._env, self._cont]
            case _:
                assert False, f"Invalid expression: {self._expr}"

    def _apply_op(self, op_val, args_val):
        match op_val:
            case f if callable(f):
                self._expr = op_val(args_val)
            case ["closure", params, body_expr, closure_env]:
                closure_env = closure_env.extend(params, args_val)
                self._expr, self._env, self._cont = Expr(body_expr), closure_env, \
                    ["$restore_env", self._env, self._cont]
            case ["mclosure", params, body_expr, mclosure_env]:
                mclosure_env = mclosure_env.extend(params, args_val)
                self._expr, self._env, self._cont = Expr(body_expr), mclosure_env, \
                    ["$meval", self._env, self._cont]
            case _:
                assert False, f"Invalid function: {self._expr}"

    def _apply_val(self):
        assert not isinstance(self._expr, Expr), \
            f"Invalid value: {self._expr}"
        match self._cont:
            case ["$qq", next_cont]:
                self._apply_quasiquote(next_cont)
            case ["$qq_elems", splicing, elems, elems_done, next_cont]:
                elems_done = self._qq_add_element(elems_done,splicing)
                self._apply_qq_elems(elems, elems_done, next_cont)
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
            case ["$args", op_expr, args_expr, args_val, call_env, next_cont]:
                self._apply_args(op_expr, args_expr, args_val, call_env, next_cont)
            case ["$expand", args_expr, call_env, next_cont]:
                self._apply_expand(args_expr, call_env, next_cont)
            case ["$meval", mclosure_env, next_cont]:
                self._expr, self._env, self._cont = (
                    Expr(self._expr), mclosure_env, next_cont
                )
            case ["$restore_env", env, next_cont]:
                self._env, self._cont = env, next_cont
            case _:
                assert False, f"Invalid continuation: {self._cont}"

    def _apply_quasiquote(self, next_cont):
        match self._expr:
            case ["!", expr]:
                self._expr = Expr(expr)
                self._cont = next_cont
            case [*elems]:
                self._apply_qq_elems(elems, [], next_cont)
            case _:
                self._cont = next_cont

    def _qq_add_element(self, elems_done, splicing):
        if splicing:
            assert isinstance(self._expr , list), f"Cannot splice: {self._expr}"
            return elems_done + self._expr
        else:
            return elems_done + [self._expr]

    def _apply_qq_elems(self, elems, elems_done, next_cont):
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

    def _apply_call(self, args_expr, call_env, next_cont):
        match self._expr:
            case ["mclosure", _params, _body_expr, _mclosure_env]:
                self._expr, self._env, self._cont = (
                    Expr(["$apply", self._expr, args_expr]), call_env, next_cont
                )
            case op_val:
                self._apply_arg(op_val, args_expr, [], call_env, next_cont)

    def _apply_args(self, op_val, args_expr, args_val, call_env, next_cont):
        args_val += [self._expr]
        self._apply_arg(op_val, args_expr, args_val, call_env, next_cont)

    def _apply_arg(self, op_val, args_expr, args_val, call_env, next_cont):
        if args_expr == []:
            self._expr, self._env, self._cont = (
                Expr(["$apply", op_val, args_val]), call_env, next_cont
            )
        else:
            self._expr, self._env, self._cont = (
                Expr(args_expr[0]),
                call_env,
                ["$args", op_val, args_expr[1:], args_val, call_env, next_cont]
            )

    def _apply_expand(self, args_expr, call_env, next_cont):
        match self._expr:
            case ["mclosure", params, body_expr, mclosure_env]:
                mclosure_env = mclosure_env.extend(params, args_expr)
                self._expr, self._env, self._cont = (
                    Expr(body_expr), mclosure_env,
                    ["$restore_env", call_env, next_cont]
                )
            case unexpected:
                assert False, f"Cannot expand: {unexpected}"

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

    def stdlib(self):
        self.run(["define", "__stdlib__", None])

        self.run(["define", "id", ["func", ["x"], "x"]])

        self.run(["define", "inc", ["func", ["x"], ["add", "x", 1]]])
        self.run(["define", "dec", ["func", ["x"], ["sub", "x", 1]]])

        self.run(["define", "first", ["func", ["l"], ["get_at", "l", 0]]])
        self.run(["define", "rest", ["func", ["l"], ["slice", "l", 1, None, None]]])
        self.run(["define", "last", ["func", ["l"], ["get_at", "l", -1]]])
        self.run(["define", "append", ["func", ["l", "a"], ["add", "l", ["arr", "a"]]]])
        self.run(["define", "prepend", ["func", ["a", "l"], ["add", ["arr", "a"], "l"]]])

        self.run(["define", "foldl", ["func", ["l", "f", "init"],
                ["if", ["equal", "l", ["arr"]],
                    "init",
                    ["foldl", ["rest", "l"], "f", ["f", "init", ["first", "l"]]]]]])
        self.run(["define", "unfoldl", ["func", ["x", "p", "h", "t"], ["seq",
                ["define", "_unfoldl", ["func", ["x", "b"],
                    ["if", ["p", "x"],
                        "b",
                        ["_unfoldl", ["t", "x"], ["add", "b", ["arr", ["h", "x"]]]]]]],
                ["_unfoldl", "x", ["arr"]]]]])

        self.run(["define", "map", ["func", ["l", "f"],
                ["foldl", "l", ["func", ["acc", "e"], ["append", "acc", ["f", "e"]]], ["arr"]]]])
        self.run(["define", "range", ["func", ["s", "e"],
                ["unfoldl", "s", ["func", ["x"], ["greater_equal", "x", "e"]], "id", "inc"]]])

        self.run(["define", "scope", ["macro", ["body"],
                ["qq", [["func", [], ["!", "body"]]]]]])

        self.run(["define", "when", ["macro", ["cnd", "thn"],
                ["qq", ["if", ["!", "cnd"], ["!", "thn"], None]]]])

        self.run(["define", "aif", ["macro", ["cnd", "thn", "els"],
                ["qq", ["scope", ["seq",
                    ["define", "it", ["!", "cnd"]],
                    ["if", "it", ["!", "thn"], ["!", "els"]]]]]]])

        self.run(["define", "and", ["macro", ["a", "b"],
                ["qq", ["aif", ["!", "a"], ["!", "b"], "it"]]]])
        self.run(["define", "or", ["macro", ["a", "b"],
                ["qq", ["aif", ["!", "a"], "it", ["!", "b"]]]]])

        self.run(["define", "while", ["macro", ["cnd", "body"], ["qq",
                ["scope", ["seq",
                    ["define", "__stdlib_while_loop", ["func", [],
                        ["when", ["!", "cnd"], ["seq", ["!", "body"], ["__stdlib_while_loop"]]]]],
                    ["__stdlib_while_loop"]]]]]])

        self.run(["define", "__stdlib_is_name_before", "is_name"])
        self.run(["define", "is_name", ["macro", ["e"], ["qq",
                ["__stdlib_is_name_before", ["q", ["!", "e"]]]]]])

        self.run(["define", "for", ["macro", ["e", "l", "body"], ["qq",
                ["scope", ["seq",
                    ["define", "__stdlib_for_index", 0],
                    ["define", ["!", "e"], None],
                    ["while", ["less", "__stdlib_for_index", ["len", ["!", "l"]]], ["seq",
                        ["assign", ["!", "e"], ["get_at", ["!", "l"], "__stdlib_for_index"]],
                        ["!", "body"],
                        ["assign", "__stdlib_for_index", ["inc", "__stdlib_for_index"]]]]]]]]])

        self.env = Environment(self.env)

if __name__ == "__main__":
    i = Interpreter()
    i.stdlib()

    i.run(["print", ["expand", [["macro", [], ["q", ["add", 5, 6]]]]]])
    i.run(["print", ["expand", [
        ["macro", ["a", "b"], ["qq", ["add", ["!", "a"], ["!", "b"]]]],
        ["add", 5, 6], 7]]])
    i.run(["print", [["macro", [], ["q", ["add", 5, 6]]]]])
