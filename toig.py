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
                eval_args(args_expr, env,
                    lambda args_val: apply(func_val, args_val, cont)))

def eval_args(args_expr, env, cont):
    def _eval_args(exprs, acc):
        if exprs == []:
            cont(acc)
        else:
            eval(exprs[0], env, lambda val:
                _eval_args(exprs[1:], acc + [val]))
    _eval_args(args_expr, [])

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
    "print": lambda args_val: print(*args_val),
}
top_env = new_env()
for name in builtins: define(top_env, name, builtins[name])
top_env = new_scope(top_env)

def run(src):
    eval(src, top_env, lambda val: print(val))

# tests

print("\nprimaries")
run(None)
run(5)
run(True)
run(False)

print("\nvariable")
run(["define", "a", 5])
run("a")

print("\nif")
run(["if", True, 5, 6])
run(["if", False, 5, 6])

print("\nbuilt-ins")
run(["+", 5, 6])
run(["-", 11, 5])
run(["=", 5, 5])
run(["=", 5, 6])

print("\nfunc")
run([["func", ["n"], ["+", 5, "n"]], 6])

import sys
sys.setrecursionlimit(14000)

print("\nfib")
run(["define", "fib", ["func", ["n"],
        ["if", ["=", "n", 0], 0,
        ["if", ["=", "n", 1], 1,
        ["+", ["fib", ["-", "n", 1]], ["fib", ["-", "n", 2]]]]]]])
run(["fib", 0])
run(["fib", 1])
run(["fib", 2])
run(["fib", 3])
run(["fib", 10])

print("\nclosure")
run(["define", "make_adder", ["func", ["n"], ["func", ["m"], ["+", "n", "m"]]]])
run([["make_adder", 5], 6])

print("\nSuccess")