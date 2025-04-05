# environment

def define(env, name, val):
    assert name not in env["vals"], \
        f"Variable already defined: `{name}` @ define"
    env["vals"][name] = val
    return val

def assign(env, name, val):
    assert env is not None, f"Undefined variable: `{name}` @ assign."
    if name in env["vals"]:
        env["vals"][name] = val
        return val
    else:
        return assign(env["parent"], name, val)

def get(env, name):
    assert env is not None, f"Undefined variable: `{name}` @ get"
    if name in env["vals"]:
        return env["vals"][name]
    else:
        return get(env["parent"], name)

# evaluator

from functools import reduce

def eval(expr, env):
    match expr:
        case None | bool(_) | int(_): return expr
        case str(name): return get(env, name)
        case ["q", elem]: return elem
        case ["qq", elem]: return eval_quasiquote(elem, env)
        case ["func", params, body]:
            return ["func", params, body, env]
        case ["macro", params, body]:
            return ["macro", params, body, env]
        case ["define", name, val]:
            return define(env, name, eval(val, env))
        case ["assign", name, val]:
            return assign(env, name, eval(val, env))
        case ["do", *exprs]:
            return reduce(lambda _, e: eval(e, env), exprs, None)
        case ["if", cnd, thn, els]:
            return eval(thn, env) if eval(cnd, env) else eval(els, env)
        case ["expand", [op, *args]]:
            return eval_expand(op, args, env)
        case [op, *args]:
            return eval_op(op, args, env)
        case unexpected:
            assert False, f"Unexpected expression: {unexpected} @ eval"

def is_arr(elem): return isinstance(elem, list)

def eval_quasiquote(elem, env):
    if not is_arr(elem): return elem
    quoted = []
    for e in elem:
        match e:
            case ["!", e]: quoted.append(eval(e, env))
            case _: quoted.append(eval_quasiquote(e, env))
    return quoted

def eval_expand(op, args, env):
    match eval(op, env):
        case ["macro", params, body, macro_env]:
            return expand(body, params, args, macro_env)
        case unexpected:
            assert False, f"Macro expected: {unexpected} @ eval"

def eval_op(op, args, env):
    match eval(op, env):
        case ["macro", params, body, macro_env]:
            return eval(expand(body, params, args, macro_env), env)
        case f_val:
            return apply(f_val, [eval(arg, env) for arg in args])

def expand(body, params, args, env):
    assert len(params) == len(args), \
        f"Argument count doesn't match: `{args}` @ expand"
    env = {"parent": env, "vals": dict(zip(params, args))}
    return eval(body, env)

def apply(f_val, args_val):
    if callable(f_val): return f_val(args_val)
    _, params, body, env = f_val
    assert len(params) == len(args_val), \
        f"Argument count doesn't match: `{args_val}` @ apply"
    env = {"parent": env, "vals": dict(zip(params, args_val))}
    return eval(body, env)

# runtime

import operator as op

def n_ary(n, f, args):
    assert len(args) == n, \
        f"Argument count doesn't match: `{args}` @ n_ary"
    return f(*args[0:n])

def setat(args):
    assert len(args) == 3, \
        f"Argument count doesn't match: `{args}` @ setat"
    args[0][args[1]] = args[2]
    return args[0]

def slice(args):
    match args:
        case [arr]: return arr[:]
        case [arr, start]: return arr[start:]
        case [arr, start, end]: return arr[start:end]
        case _: assert False, f"Invalid slice: args=`{args}` @ slice"

builtins = {
    "+": lambda args: n_ary(2, op.add, args),
    "-": lambda args: n_ary(2, op.sub, args),
    "*": lambda args: n_ary(2, op.mul, args),
    "/": lambda args: n_ary(2, op.truediv, args),
    "=": lambda args: n_ary(2, op.eq, args),
    "!=": lambda args: n_ary(2, op.ne, args),
    "<": lambda args: n_ary(2, op.lt, args),
    ">": lambda args: n_ary(2, op.gt, args),
    "<=": lambda args: n_ary(2, op.le, args),
    ">=": lambda args: n_ary(2, op.ge, args),
    "not": lambda args: n_ary(1, op.not_, args),

    "arr": lambda args: args,
    "is_arr": lambda args: n_ary(1, is_arr, args),
    "len": lambda args: n_ary(1, len, args),
    "getat": lambda args: n_ary(2, lambda arr, ind: arr[ind], args),
    "setat": setat,
    "slice": slice,

    "print": lambda args: print(*args),
}

top_env = None

def init_env():
    global top_env
    top_env = {"parent": top_env, "vals": builtins.copy()}
    top_env = {"parent": top_env, "vals": {}}

def stdlib():
    run(["define", "id", ["func", ["x"], "x"]])

    run(["define", "inc", ["func", ["x"], ["+", "x", 1]]])
    run(["define", "dec", ["func", ["x"], ["-", "x", 1]]])

    run(["define", "unfoldl", ["func", ["x", "p", "h", "t"], ["do",
            ["define", "_unfoldl", ["func", ["x", "b"],
                ["if", ["p", "x"],
                    "b",
                    ["_unfoldl", ["t", "x"], ["+", "b", ["arr", ["h", "x"]]]]]]],
            ["_unfoldl", "x", ["arr"]]]]])

    run(["define", "range", ["func", ["s", "e"],
            ["unfoldl", "s", ["func", ["x"], [">=", "x", "e"]], "id", "inc"]]])

    run(["define", "append", ["func", ["l", "a"], ["+", "l", ["arr", "a"]]]])
    run(["define", "prepend", ["func", ["a", "l"], ["+", ["arr", "a"], "l"]]])

    run(["define", "scope", ["macro", ["body"],
            ["qq", [["func", [], ["!", "body"]]]]]])

    run(["define", "when", ["macro", ["cnd", "thn"],
            ["qq", ["if", ["!", "cnd"], ["!", "thn"], None]]]])
    run(["define", "and", ["macro", ["a", "b"],
            ["qq", ["if", ["!", "a"], ["!", "b"], False]]]])
    run(["define", "or", ["macro", ["a", "b"],
            ["qq", ["if", ["!", "a"], True, ["!", "b"]]]]])

    run(["define", "while", ["macro", ["cnd", "body"], ["qq",
            ["scope", ["do",
                ["define", "loop", ["func", [],
                    ["when", ["!", "cnd"], ["do", ["!", "body"], ["loop"]]]]],
                ["loop"]]]]]])

    run(["define", "for", ["macro", ["e", "l", "body"], ["qq",
            ["scope", ["do",
                ["define", "__index", 0],
                ["define", ["!", "e"], None],
                ["while", ["<", "__index", ["len", ["!", "l"]]], ["do",
                    ["assign", ["!", "e"], ["getat", ["!", "l"], "__index"]],
                    ["!", "body"],
                    ["assign", "__index", ["inc", "__index"]]]]]]]]])

    global top_env
    top_env = {"parent": top_env, "vals": {}}

def run(src):
    return eval(src, top_env)

if __name__ == "__main__":
    init_env()
    stdlib()
    run(["print", ["q", "hello"], ["q", "world"]])
