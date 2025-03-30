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
        case ["func", params, body]: return ["func", params, body, env]
        case ["define", name, val]:
            return define(env, name, eval(val, env))
        case ["assign", name, val]:
            return assign(env, name, eval(val, env))
        case ["do", *exprs]:
            return reduce(lambda _, e: eval(e, env), exprs, None)
        case ["if", cnd, thn, els]:
            return eval(thn, env) if eval(cnd, env) else eval(els, env)
        case [func, *args]:
            return apply(eval(func, env), [eval(arg, env) for arg in args])
        case unexpected:
            assert False, f"Unexpected expression: {unexpected} @ eval"

def apply(f_val, args_val):
    if callable(f_val): return f_val(args_val)
    _, params, body, env = f_val
    assert len(params) == len(args_val), \
        f"Argument count doesn't match: `{args_val}` @ apply"
    env = {"parent": env, "vals": dict(zip(params, args_val))}
    return eval(body, env)

# runtime

import operator as op

def binary_op(f, args):
    assert len(args) == 2, \
        f"Argument count doesn't match: `{args}` @ binary_op"
    return f(args[0], args[1])

builtins = {
    "+": lambda args_val: binary_op(op.add, args_val),
    "-": lambda args_val: binary_op(op.sub, args_val),
    "=": lambda args_val: binary_op(op.eq, args_val),
    "print": lambda args_val: print(*args_val),
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
