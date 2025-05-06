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

def extend(env, params, args):
    def new_env(params, args):
        if params == [] and args == []: return {}
        assert len(params) > 0, \
            f"Argument count doesn't match: `{params}, {args}` @ extend"
        match params[0]:
            case str(param):
                assert len(args) > 0, \
                    f"Argument count doesn't match: `{params}, {args}` @ extend"
                return {param: args[0], **new_env(params[1:], args[1:])}
            case ["*", rest]:
                assert len(params) == 1, \
                    f"Rest param must be last: `{params}` @ extend"
                return {rest: args}
            case unexpected:
                assert False, f"Unexpected param at extend: {unexpected}"

    return {"parent": env, "vals": new_env(params, args)}

# CPS operations

def foldl_cps(l, f, init, cont):
    cont(init) if l == [] else \
    f(init, l[0], lambda r: foldl_cps(l[1:], f, r, cont))

def map_cps(l, f, cont):
    foldl_cps(l,
        lambda acc, e, cont: f(e, lambda r: cont(acc + [r])),
        [], cont)

# evaluator

class Skip(Exception):
    def __init__(self, skip): self.skip = skip

def eval(expr, env, cont):
    match expr:
        case None | bool(_) | int(_): cont(expr)
        case str(name): cont(get(env, name))
        case ["q", elem]: cont(elem)
        case ["qq", elem]: eval_quasiquote(elem, env, cont)
        case ["func", params, body]:
            cont(["func", params, body, env])
        case ["macro", params, body]:
            cont(["macro", params, body, env])
        case ["define", name, expr]:
            eval(expr, env, lambda val: cont(define(env, name, val)))
        case ["assign", name, expr]:
            eval(expr, env, lambda val: cont(assign(env, name, val)))
        case ["do", *exprs]:
            foldl_cps(exprs, lambda _, expr, c: eval(expr, env, c), None, cont)
        case ["if", cnd_expr, thn_expr, els_expr]:
            eval(cnd_expr, env, lambda cnd:
                 eval(thn_expr, env, cont) if cnd else
                 eval(els_expr, env, cont))
        case ["letcc", name, body]:
            def skip(args): raise Skip(lambda: cont(args[0]))
            apply(["func", [name], body, env], [skip], cont)
        case ["expand", [op_expr, *args_expr]]:
            eval_expand(op_expr, args_expr, env, cont)
        case [op_expr, *args_expr]:
            eval_op(op_expr, args_expr, env, cont)
        case unexpected:
            assert False, f"Unexpected expression: {unexpected} @ eval"

def eval_quasiquote(expr, env, cont):
    def splice(quoted, elem_vals, cont):
        assert isinstance(elem_vals, list), \
            f"Cannot splice: {elem_vals} @ eval_quasiquote"
        cont(quoted + elem_vals)

    def unquote_splice(quoted, elem, cont):
        match elem:
            case ["!!", e]:
                eval(e, env, lambda e_val: splice(quoted, e_val, cont))
            case _:
                eval_quasiquote(elem, env,
                    lambda elem_val: cont(quoted + [elem_val]))

    match expr:
        case ["!", elem]: eval(elem, env, cont)
        case [*elems]: foldl_cps(elems, unquote_splice, [], cont)
        case _: cont(expr)

def eval_expand(op_expr, args_expr, env, cont):
    def _eval_expand(op):
        match op:
            case ["macro", params, body, macro_env]:
                expand(body, params, args_expr, macro_env, cont)
            case unexpected:
                assert False, f"Macro expected: {unexpected} @ eval_expand"

    eval(op_expr, env, _eval_expand)

def eval_op(op_expr, args_expr, env, cont):
    def _eval_op(op):
        match op:
            case ["macro", params, body, macro_env]:
                expand(body, params, args_expr, macro_env,
                    lambda expanded: eval(expanded, env, cont))
            case func:
                map_cps(args_expr,
                    lambda arg_expr, c: eval(arg_expr, env, c),
                    lambda args: apply(func, args, cont))

    eval(op_expr, env, _eval_op)

def expand(body, params, args, env, cont):
    env = extend(env, params, args)
    eval(body, env, cont)

def apply(func, args, cont):
    if callable(func):
        cont(func(args))
    else:
        _, params, body, env = func
        env = extend(env, params, args)
        eval(body, env, cont)

# runtime

import operator as op

def n_ary(n, f, args):
    assert len(args) == n, \
        f"Argument count doesn't match: `{args}` @ n_ary"
    return f(*args[0:n])

def is_arr(elem):
    return isinstance(elem, list)

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

def error(args):
    assert False, f"{' '.join(map(str, args))}"

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
    "error": lambda args: error(args)
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

    run(["define", "first", ["func", ["l"], ["getat", "l", 0]]])
    run(["define", "rest", ["func", ["l"], ["slice", "l", 1]]])
    run(["define", "last", ["func", ["l"], ["getat", "l", -1]]])
    run(["define", "append", ["func", ["l", "a"], ["+", "l", ["arr", "a"]]]])
    run(["define", "prepend", ["func", ["a", "l"], ["+", ["arr", "a"], "l"]]])

    run(["define", "foldl", ["func", ["l", "f", "init"],
            ["if", ["=", "l", ["arr"]],
                "init",
                ["foldl", ["rest", "l"], "f", ["f", "init", ["first", "l"]]]]]])
    run(["define", "unfoldl", ["func", ["x", "p", "h", "t"], ["do",
            ["define", "_unfoldl", ["func", ["x", "b"],
                ["if", ["p", "x"],
                    "b",
                    ["_unfoldl", ["t", "x"], ["+", "b", ["arr", ["h", "x"]]]]]]],
            ["_unfoldl", "x", ["arr"]]]]])

    run(["define", "map", ["func", ["l", "f"],
            ["foldl", "l", ["func", ["acc", "e"], ["append", "acc", ["f", "e"]]], ["arr"]]]])
    run(["define", "range", ["func", ["s", "e"],
            ["unfoldl", "s", ["func", ["x"], [">=", "x", "e"]], "id", "inc"]]])

    run(["define", "scope", ["macro", ["body"],
            ["qq", [["func", [], ["!", "body"]]]]]])

    run(["define", "when", ["macro", ["cnd", "thn"],
            ["qq", ["if", ["!", "cnd"], ["!", "thn"], None]]]])

    run(["define", "aif", ["macro", ["cnd", "thn", "els"],
            ["qq", ["scope", ["do",
                ["define", "it", ["!", "cnd"]],
                ["if", "it", ["!", "thn"], ["!", "els"]]]]]]])

    run(["define", "and", ["macro", ["a", "b"],
            ["qq", ["aif", ["!", "a"], ["!", "b"], "it"]]]])
    run(["define", "or", ["macro", ["a", "b"],
            ["qq", ["aif", ["!", "a"], "it", ["!", "b"]]]]])

    run(["define", "while", ["macro", ["cnd", "body"], ["qq",
            ["scope", ["do",
                ["define", "break", None],
                ["define", "continue", ["func", [],
                    ["when", ["!", "cnd"], ["do", ["!", "body"], ["continue"]]]]],
                ["letcc", "cc", ["do", ["assign", "break", "cc"], ["continue"]]]]]]]])

    run(["define", "awhile", ["macro", ["cnd", "body"], ["qq",
            ["scope", ["do",
                ["define", "break", None],
                ["define", "continue", ["func", [], ["do",
                    ["define", "it", ["!", "cnd"]],
                    ["when", "it", ["do", ["!", "body"], ["continue"]]]]]],
                ["letcc", "cc", ["do", ["assign", "break", "cc"], ["continue"]]]]]]]])

    run(["define", "gfunc", ["macro", ["params", "body"], ["qq",
            ["func", ["!", "params"], ["do",
                ["define", "yd", None],
                ["define", "nx", None],
                ["define", "yield", ["func", ["x"],
                    ["letcc", "cc", ["do",
                        ["assign", "nx", "cc"],
                        ["yd", "x"]]]]],
                ["define", "next", ["func", [],
                    ["letcc", "cc", ["do",
                        ["assign", "yd", "cc"],
                        ["nx", None]]]]],
                ["assign", "nx", ["func", ["_"], ["do",
                    ["!", "body"],
                    ["yield", None]]]],
                "next"]]]]])

    run(["define", "for", ["macro", ["e", "l", "body"], ["qq",
            ["scope", ["do",
                ["define", "__stdlib_for_index", 0],
                ["define", ["!", "e"], None],
                ["define", "break", None],
                ["define", "continue", ["func", [], ["do",
                    ["assign", "__stdlib_for_index", ["inc", "__stdlib_for_index"]],
                    ["go"]]]],
                ["define", "go", ["func", [],
                    ["when", ["<", "__stdlib_for_index", ["len", ["!", "l"]]],
                        ["do",
                            ["assign", ["!", "e"], ["getat", ["!", "l"], "__stdlib_for_index"]],
                            ["!", "body"],
                            ["continue"]]]]],
                ["letcc", "cc", ["do", ["assign", "break", "cc"], ["go"]]]]]]]])

    run(["define", "agen", ["gfunc", ["a"], ["for", "e", "a", ["yield", "e"]]]])

    run(["define", "gfor", ["macro", ["e", "gen", "body"], ["qq",
            ["scope", ["do",
                ["define", "__stdlib_gfor_gen", ["!", "gen"]],
                ["define", ["!", "e"], None],
                ["while", ["!=", ["assign", ["!", "e"], ["__stdlib_gfor_gen"]], None],
                    ["!", "body"]]]]]]])

    global top_env
    top_env = {"parent": top_env, "vals": {}}

result = None

def run(src):
    def save(val):
        global result; result = val

    computation = lambda: eval(src, top_env, save)
    while True:
        try:
            computation()
            return result
        except Skip as s:
            computation = s.skip

if __name__ == "__main__":
    init_env()
    stdlib()
    run(["print", ["q", "hello"], ["q", "world"]])
