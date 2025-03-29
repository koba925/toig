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
top_env = {"parent": None, "vals": builtins}

def run(src):
    return eval(src, top_env)

# tests

def fails(expr):
    try: run(expr)
    except AssertionError: return True
    else: return False

import sys
from io import StringIO

def printed(expr):
    stdout_bak = sys.stdout
    sys.stdout = captured = StringIO()
    try: val = run(expr)
    finally: sys.stdout = stdout_bak
    return val, captured.getvalue()

assert run(None) == None
assert run(5) == 5
assert run(True) == True
assert run(False) == False

assert run(["define", "a", 5]) == 5
assert run("a") == 5
assert fails(["define", "a", 6])
assert fails(["b"])
assert printed([["func", [], ["do",
                    ["print", ["define", "a", 6]],
                    ["print", "a"]]]]) == (None, "6\n6\n")
assert run("a") == 5

assert run(["assign", "a", 6]) == 6
assert run("a") == 6
assert fails(["assign", "b", 6])
assert run([["func", [], ["assign", "a", 7]]]) == 7
assert printed([["func", [], ["do",
                    ["print", ["assign", "a", 7]],
                    ["print", "a"]]]]) == (None, "7\n7\n")
assert run("a") == 7

assert run(["do"]) == None
assert run(["do", 5]) == 5
assert run(["do", 5, 6]) == 6
assert printed(["do", ["print", 5]]) == (None, "5\n")
assert printed(["do", ["print", 5], ["print", 6]]) == (None, "5\n6\n")

assert run(["if", True, 5, 6]) == 5
assert run(["if", False, 5, 6]) == 6
assert fails(["if", True, 5])

assert run(["+", 5, 6]) == 11
assert run(["-", 11, 5]) == 6
assert run(["=", 5, 5]) == True
assert run(["=", 5, 6]) == False
assert fails(["+", 5])
assert fails(["+", 5, 6, 7])

assert run([["func", ["n"], ["+", 5, "n"]], 6]) == 11
assert fails([["func", ["n"], ["+", 5, "n"]]])
assert fails([["func", ["n"], ["+", 5, "n"]], 6, 7])

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

run(["define", "make_counter", ["func", [], ["do",
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
