# environment

def define(env, name, val):
    env["vals"][name] = val

def get(env, name):
    return env["vals"][name] if name in env["vals"] else get(env["parent"], name)

# evaluator

class Skip(Exception):
    def __init__(self, skip): self.skip = skip

def eval(expr, env, cont):
    match expr:
        case None | bool(_) | int(_): return lambda: cont(expr)
        case ["func", params, body]: return lambda: cont(["func", params, body, env])
        case str(name): return lambda: cont(get(env, name))
        case ["define", name, expr]:
            return lambda: eval(expr, env, lambda val: lambda: [
                define(env, name, val),
                cont(None)][1])
        case ["if", cnd_expr, thn_expr, els_expr]:
            return lambda: eval(cnd_expr, env, lambda cnd: lambda: (
                eval(thn_expr, env, cont) if cnd else
                eval(els_expr, env, cont)))
        case ["letcc", name, body]:
            def skip(args): raise Skip(lambda: cont(args[0]))
            return lambda: apply(["func", [name], body, env], [skip], cont)
        case [func_expr, *args_expr]:
            return lambda: eval(func_expr, env, lambda func_val:
                lambda: map_cps(args_expr,
                    lambda arg_expr, c: lambda: eval(arg_expr, env, c),
                    lambda args_val: lambda: apply(func_val, args_val, cont)))

def foldl_cps(l, f, init, cont):
    return lambda: cont(init) if l == [] else \
        f(init, l[0], lambda r: lambda: foldl_cps(l[1:], f, r, cont))

def map_cps(l, f, cont):
    return lambda: foldl_cps(l,
        lambda acc, e, cont: lambda: f(e, lambda r: cont(acc + [r])),
        [], cont)

def apply(func_val, args_val, cont):
    match func_val:
        case f if callable(f): return lambda: cont(func_val(args_val))
        case ["func", params, body_expr, env]:
            env = {"parent": env, "vals": dict(zip(params, args_val))}
            return lambda: eval(body_expr, env, cont)

# runtime

builtins = {
    "+": lambda args_val: args_val[0] + args_val[1],
    "-": lambda args_val: args_val[0] - args_val[1],
    "=": lambda args_val: args_val[0] == args_val[1],
}
top_env = {"parent": None, "vals": builtins}

def run(src):
    computation = lambda: eval(src, top_env, lambda result: result)
    while callable(computation):
        try:
            computation = computation()
        except Skip as s:
            computation = s.skip
    return computation

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

assert run(["letcc", "skip-to", ["+", 5, 6]]) == 11
assert run(["letcc", "skip-to", ["+", ["skip-to", 5], 6]]) == 5
assert run(["+", 5, ["letcc", "skip-to", ["skip-to", 6]]]) == 11
assert run(["letcc", "skip1", ["+", ["skip1", ["letcc", "skip2", ["+", ["skip2", 5], 6]]], 7]]) == 5

run(["define", "inner", ["func", ["raise"], ["raise", 5]]])
run(["define", "outer", ["func", [],
        [ "letcc", "raise", ["+", ["inner", "raise"], 6]]]])
assert run(["outer"]) == 5

print("Success")