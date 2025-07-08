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

import operator as op

def is_name(expr):
    return isinstance(expr, str)

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

        # "arr": lambda args: args,
        # "is_arr": lambda args: isinstance(args[0], list),
        # "len": lambda args: len(args),
        # "getat": lambda args: args[0][args[1]],
        # "setat": setat,
        # "slice": slice_,
        # "set_slice": set_slice,

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
        return Evaluator(src, self.env, ["$halt"]).eval()

if __name__ == "__main__":
    i = Interpreter()

    print(i.run(5))
