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

def is_value(expr):
    match expr:
        case None | bool(_) | int(_): return True
        case ["func", _params, _body, _env]: return True
        case f if callable(f): return True
        case _: return False

def eval(expr, env, cont):
    if is_value(expr):
        if cont == ["$halt"]: return expr

        match cont:
            case ["$if", thn_expr, els_expr, next_cont]:
                if expr:
                    return eval(thn_expr, env, next_cont)
                else:
                    return eval(els_expr, env, next_cont)
            case ["$define", name, next_cont]:
                define(env, name, expr)
                return eval(expr, env, next_cont)
            case ["$call", args_expr, call_env, next_cont]:
                return eval(
                    args_expr[0],
                    call_env,
                    ["$args", expr, args_expr[1:], [], call_env, next_cont])
            case ["$args", func_val, args_expr, args_val, call_env, next_cont]:
                if args_expr == []:
                    return eval(
                        ["$apply", func_val, args_val + [expr]],
                        call_env,
                        next_cont)
                else:
                    return eval(
                        args_expr[0],
                        call_env,
                        ["$args", func_val, args_expr[1:], args_val + [expr], call_env, next_cont])
            case _:
                assert False, f"Invalid continuation: {cont}"
    else:
        match expr:
            case ["func", params, body]:
                return eval(["func", params, body, env], env, cont)
            case str(name):
                return eval(get(env, name), env, cont)
            case ["define", name, expr]:
                return eval(expr, env, ["$define", name, cont])
            case ["if", cnd_expr, thn_expr, els_expr]:
                return eval(cnd_expr, env, ["$if", thn_expr, els_expr, cont])
            case ["$apply", func_val, args_val]:
                match func_val:
                    case f if callable(f):
                        return eval(func_val(args_val), env, cont)
                    case ["func", params, body_expr, closure_env]:
                        closure_env = new_scope(closure_env)
                        for param, arg in zip(params, args_val):
                            define(closure_env, param, arg)
                        return eval(body_expr, closure_env, cont)
                    case _:
                        assert False, f"Invalid function: {expr}"
            case [func_expr, *args_expr]:
                return eval(func_expr, env, ["$call", args_expr, env, cont])
            case _:
                assert False, f"Invalid expression: {expr}"

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
    return eval(src, top_env, ["$halt"])

# tests

import sys
sys.setrecursionlimit(10000)

assert run(None) == None
assert run(5) == 5
assert run(True) == True
assert run(False) == False

assert run(["define", "a", 5]) == 5
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
