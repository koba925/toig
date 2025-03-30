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
        case ["q", expr]: return expr
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
    if len(args) == 1:
        return args[0][:]
    elif len(args) == 2:
        return args[0][args[1]:]
    elif len(args) == 3:
        return args[0][args[1]:args[2]]
    assert False, f"Invalid slice: args=`{args}` @ slice"

builtins = {
    "+": lambda args: n_ary(2, op.add, args),
    "-": lambda args: n_ary(2, op.sub, args),
    "*": lambda args: n_ary(2, op.mul, args),
    "/": lambda args: n_ary(2, op.truediv, args),
    "=": lambda args: n_ary(2, op.eq, args),
    "not": lambda args: n_ary(1, op.not_, args),

    "arr": lambda args: args,
    "is_arr": lambda args: n_ary(1, lambda arr: isinstance(arr, list), args),
    "len": lambda args: n_ary(1, lambda arr: len(arr), args),
    "getat": lambda args: n_ary(2, lambda arr, ind: arr[ind], args),
    "setat": setat,
    "slice": slice,

    "print": lambda args: print(*args),
}

top_env = None

def init_env():
    global top_env
    top_env = {
        "parent": {"parent": None, "vals": builtins.copy()},
        "vals": {}
    }

def run(src):
    return eval(src, top_env)

if __name__ == "__main__":
    init_env()
    run(["print", ["q", "hello"], ["q", "world"]])
