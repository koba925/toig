# environment

def new_env(): return {"parent": None, "vals": {}}
def new_scope(env): return {"parent": env, "vals": {}}

def define(env, name, val):
    env["vals"][name] = val

def get(env, name):
    return env["vals"][name] if name in env["vals"] else get(env["parent"], name)

# evaluator

def eval(expr, env):
    match expr:
        case None | bool(_) | int(_): return expr
        case str(name): return get(env, name)
        case ["func", params, body]: return ["func", params, body, env]
        case ["define", name, val]:
            return define(env, name, eval(val, env))
        case ["if", cnd, thn, els]:
            return eval(thn, env) if eval(cnd, env) else eval(els, env)
        case [func, *args]:
            return apply(eval(func, env), [eval(arg, env) for arg in args])

def apply(f_val, args_val):
    if callable(f_val): return f_val(args_val)
    _, params, body, env = f_val
    env = new_scope(env)
    for param, arg in zip(params, args_val): define(env, param, arg)
    return eval(body, env)

# runtime

builtins = {
    "+": lambda args: args[0] + args[1],
    "-": lambda args: args[0] - args[1],
    "=": lambda args: args[0] == args[1],
}

top_env = new_env()
for name in builtins: define(top_env, name, builtins[name])
top_env = new_scope(top_env)

def run(src):
    return eval(src, top_env)

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