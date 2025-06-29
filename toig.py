# environment
def new_env(): return {"parent": None, "vals": {}}
def new_scope(env): return {"parent": env, "vals": {}}

def define(env, name, val):
    env["vals"][name] = val

def get(env, name):
    assert env is not None, f"name '{name}' is not defined"
    if name in env["vals"]:
        return env["vals"][name]
    else:
        return get(env["parent"], name)

# evaluator

def eval(expr, env, cont):
    match expr:
        case None | bool(_) | int(_): cont(expr)
        case ["func", params, body]: cont(["func", params, body, env])
        case str(name): cont(get(env, name))
        case ["define", name, expr]:
            eval(expr, env, lambda val: define(env, name, val))
            cont(None)
        case ["if", cnd_expr, thn_expr, els_expr]:
            eval(cnd_expr, env, lambda cnd:
                 eval(thn_expr, env, cont) if cnd else
                 eval(els_expr, env, cont))
        case [func_expr, *args_expr]:
            eval(func_expr, env, lambda func_val:
                map_cps(args_expr,
                    lambda arg_expr, c: eval(arg_expr, env, c),
                    lambda args_val: apply(func_val, args_val, cont)))

def foldl_cps(l, f, init, cont):
    cont(init) if l == [] else \
    f(init, l[0], lambda r: foldl_cps(l[1:], f, r, cont))

def map_cps(l, f, cont):
    foldl_cps(l,
        lambda acc, e, cont: f(e, lambda r: cont(acc + [r])),
        [], cont)

def apply(func_val, args_val, cont):
    match func_val:
        case f if callable(f): cont(func_val(args_val))
        case ["func", params, body_expr, env]:
            env = new_scope(env)
            for param, arg in zip(params, args_val):
                define(env, param, arg)
            eval(body_expr, env, cont)

# runtime

builtins = {
    "+": lambda args_val: args_val[0] + args_val[1],
    "-": lambda args_val: args_val[0] - args_val[1],
    "=": lambda args_val: args_val[0] == args_val[1],
}
top_env = new_env()
for name in builtins: define(top_env, name, builtins[name])
top_env = new_scope(top_env)

def run(src):
    def save(val): nonlocal result; result = val

    result = None
    eval(src, top_env, save)
    return result


# tests

assert run(None) == None
assert run(5) == 5
assert run(True) == True
assert run(False) == False

run(["define", "a", 5])
assert run("a") == 5

assert run(["if", True, 5, 6]) == 5
assert run(["if", False, 5, 6]) == 6

assert run(["+", 5, 6]) == 11
assert run(["-", 11, 5]) == 6
assert run(["=", 5, 5]) == True
assert run(["=", 5, 6]) == False

assert run([["func", ["n"], ["+", 5, "n"]], 6]) == 11

import sys
sys.setrecursionlimit(14000)

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

print("Success")