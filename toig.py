# environment

def define(env, name, val):
    env["vals"][name] = val

def get(env, name):
    return env["vals"][name] if name in env["vals"] else get(env["parent"], name)

def extend(env, params, args):
    return {"parent": env, "vals": dict(zip(params, args))}

# evaluator

def cps(expr):
    return lambda cont: cont(expr)

def cpscall2(cps1, cps2, body):
    return cps1(lambda val1: cps2(lambda val2: body(val1, val2)))

def if_cps(cnd_cps, thn_cps, els_cps):
    return cnd_cps(lambda cnd: thn_cps() if cnd else els_cps())

import operator as op

def unop_cps(op, a_cps):
    return lambda cont: a_cps(lambda a: cont(op(a)))

def callable_cps(a_cps):
    return unop_cps(callable, a_cps)

def binop_cps(op, a_cps, b_cps):
    return lambda cont: a_cps(lambda a: b_cps(lambda b: cont(op(a, b))))

def equal_cps(a_cps, b_cps):
    return binop_cps(op.eq, a_cps, b_cps)

def add_cps(a_cps, b_cps):
    return binop_cps(op.add, a_cps, b_cps)

def sub_cps(a_cps, b_cps):
    return binop_cps(op.sub, a_cps, b_cps)

def array_cps(*es_cps):
    return (cps([]) if es_cps == () else
            es_cps[0](lambda r: add_cps(
                cps([r]),
                array_cps(*es_cps[1:]))))

def first_cps(l_cps):
    return lambda cont: l_cps(lambda l: cont(l[0]))

def rest_cps(l_cps):
    return lambda cont: l_cps(lambda l: cont(l[1:]))

def foldl_cps(l_cps, f_cps, init_cps):
    return if_cps(
        equal_cps(l_cps, cps([])),
        lambda: init_cps,
        lambda: foldl_cps(rest_cps(l_cps), f_cps,
            f_cps(init_cps, first_cps(l_cps))))

def map_cps(l_cps, f):
    return foldl_cps(l_cps,
        lambda acc_cps, e_cps: add_cps(acc_cps, array_cps(f(e_cps))),
        cps([]))

def eval_cps(expr_cps, env_cps):
    def _eval(expr, env, cont):
        match expr:
            case None | bool(_) | int(_): return cont(expr)
            case str(name): return cont(get(env, name))
            case ["func", params, body]: return cont(["func", params, body, env])
            case ["define", name, val]:
                eval_cps(cps(val), cps(env))(lambda v: define(env, name, v))
                return cont(None)
            case ["if", cnd, thn, els]:
                return if_cps(eval_cps(cps(cnd), cps(env)),
                    lambda: eval_cps(cps(thn), cps(env)),
                    lambda: eval_cps(cps(els), cps(env)))(cont)
            case [func, *args]:
                f_val_cps = eval_cps(cps(func), cps(env))
                args_val_cps = map_cps(cps(args), lambda arg_cps: eval_cps(arg_cps, cps(env)))
                return apply_cps(f_val_cps, args_val_cps)(cont)

    return lambda cont: cpscall2(expr_cps, env_cps,
                lambda expr, env: _eval(expr, env, cont))

def apply_cps(f_val_cps, args_val_cps):
    def _apply_cps(f_val, cont):
        match f_val:
            case f if callable(f):
                return args_val_cps(lambda args_val: cont(f(args_val)))
            case ["func", params, body, env]:
                new_env = args_val_cps(lambda args: extend(env, params, args))
                return eval_cps(cps(body), cps(new_env))(cont)

    return lambda cont: f_val_cps(lambda f_val: _apply_cps(f_val, cont))

# runtime

def identity(x): return x

builtins = {
    "+": lambda args: args[0] + args[1],
    "-": lambda args: args[0] - args[1],
    "=": lambda args: args[0] == args[1],
}

top_env = {"parent": None, "vals": builtins}

def run(src):
    return eval_cps(cps(src), cps(top_env))(identity)

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

assert run([["func", ["n"], "n"], 5]) == 5
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