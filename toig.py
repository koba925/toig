# scanner

def is_name_first(c): return c.isalpha() or c == "_"
def is_name_rest(c): return c.isalnum() or c == "_"
def is_name(expr): return isinstance(expr, str) and is_name_first(expr[0])
def is_punctuation(c): return c in ":="

def scanner(src):
    def advance(): nonlocal pos; pos += 1
    def current_char(): return src[pos] if pos < len(src) else "$EOF"

    def append_char():
        nonlocal token
        token += current_char()
        advance()

    def word(is_rest):
        append_char()
        while is_rest(current_char()): append_char()

    def name():
        word(is_name_rest)
        match token:
            case "None": return None
            case "True": return True
            case "False": return False
            case _ : return token

    def next_token():
        while current_char().isspace(): advance()

        nonlocal token
        token = ""

        match current_char():
            case "$EOF": return "$EOF"
            case c if is_name_first(c):
                return name()
            case c if c.isnumeric():
                word(str.isnumeric)
                return int(token)
            case ":":
                append_char()
                if current_char() == "=": append_char()
            case "=" | ";":
                append_char()

        return token

    pos = 0; token = ""
    return next_token

# parser

def parse(src):
    def advance():
        nonlocal current_token
        prev_token = current_token
        current_token = next_token()
        return prev_token

    def parse_binary_right(ops, sub_elem):
        left = sub_elem()
        if (op := current_token) in ops:
            advance()
            return [ops[op], left, parse_binary_right(ops, sub_elem)]
        return left

    def parse_sequence():
        exprs = [parse_define_assign()]
        while current_token == ";":
            advance()
            exprs.append(parse_define_assign())
        return exprs[0] if len(exprs) == 1 else ["do"] + exprs

    def parse_define_assign():
        return parse_binary_right({
            ":=": "define",
            "=": "assign"
        }, parse_primary)

    def parse_primary():
        return advance()

    next_token = scanner(src)
    current_token = next_token()
    return parse_sequence()

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
    return lambda: (
        cont(init) if l == [] else
        f(init, l[0], lambda r: foldl_cps(l[1:], f, r, cont)))

def map_cps(l, f, cont):
    return lambda: foldl_cps(l,
        lambda acc, e, cont: f(e, lambda r: cont(acc + [r])),
        [], cont)

# evaluator

class Skip(Exception):
    def __init__(self, skip): self.skip = skip

def eval_expr(expr, env, cont):
    match expr:
        case None | bool(_) | int(_): return lambda: cont(expr)
        case str(name): return lambda: cont(get(env, name))
        case ["q", elem]: return lambda: cont(elem)
        case ["qq", elem]: return lambda: eval_quasiquote(elem, env, cont)
        case ["func", params, body]:
            return lambda: cont(["func", params, body, env])
        case ["macro", params, body]:
            return lambda: cont(["macro", params, body, env])
        case ["define", name, expr]:
            assert is_name(name), f"Invalid name: `{name}` @ eval_define"
            return lambda: eval_expr(expr, env,
                lambda val: cont(define(env, name, val)))
        case ["assign", name, expr]:
            return lambda: eval_expr(expr, env,
                lambda val: cont(assign(env, name, val)))
        case ["do", *exprs]:
            return lambda: foldl_cps(exprs,
                lambda _, expr, c: eval_expr(expr, env, c),
                None, cont)
        case ["if", cnd_expr, thn_expr, els_expr]:
            return lambda: eval_expr(cnd_expr, env, lambda cnd:
                eval_expr(thn_expr, env, cont) if cnd else
                eval_expr(els_expr, env, cont))
        case ["letcc", name, body]:
            def skip(args): raise Skip(lambda: cont(args[0]))
            return lambda: apply(["func", [name], body, env], [skip], cont)
        case ["expand", [op_expr, *args_expr]]:
            return lambda: eval_expand(op_expr, args_expr, env, cont)
        case [op_expr, *args_expr]:
            return lambda: eval_op(op_expr, args_expr, env, cont)
        case unexpected:
            assert False, f"Unexpected expression: {unexpected} @ eval"

def eval_quasiquote(expr, env, cont):
    def splice(quoted, elem_vals, cont):
        assert isinstance(elem_vals, list), \
            f"Cannot splice: {elem_vals} @ eval_quasiquote"
        return lambda: cont(quoted + elem_vals)

    def unquote_splice(quoted, elem, cont):
        match elem:
            case ["!!", e]:
                return lambda: eval_expr(e, env,
                    lambda e_val: splice(quoted, e_val, cont))
            case _:
                return lambda: eval_quasiquote(elem, env,
                    lambda elem_val: cont(quoted + [elem_val]))

    match expr:
        case ["!", elem]: return lambda: eval_expr(elem, env, cont)
        case [*elems]: return lambda: foldl_cps(elems, unquote_splice, [], cont)
        case _: return lambda: cont(expr)

def eval_expand(op_expr, args_expr, env, cont):
    def _eval_expand(op):
        match op:
            case ["macro", params, body, macro_env]:
                return lambda: expand(body, params, args_expr, macro_env, cont)
            case unexpected:
                assert False, f"Macro expected: {unexpected} @ eval_expand"

    return lambda: eval_expr(op_expr, env, _eval_expand)

def eval_op(op_expr, args_expr, env, cont):
    def _eval_op(op):
        match op:
            case ["macro", params, body, macro_env]:
                return lambda: expand(body, params, args_expr, macro_env,
                    lambda expanded: eval_expr(expanded, env, cont))
            case func:
                return lambda: map_cps(args_expr,
                    lambda arg_expr, c: eval_expr(arg_expr, env, c),
                    lambda args: apply(func, args, cont))

    return lambda: eval_expr(op_expr, env, _eval_op)

def expand(body, params, args, env, cont):
    env = extend(env, params, args)
    return lambda: eval_expr(body, env, cont)

def apply(func, args, cont):
    if callable(func):
        return lambda: cont(func(args))
    else:
        _, params, body, env = func
        env = extend(env, params, args)
        return lambda: eval_expr(body, env, cont)

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
    "add": lambda args: n_ary(2, op.add, args),
    "sub": lambda args: n_ary(2, op.sub, args),
    "mul": lambda args: n_ary(2, op.mul, args),
    "div": lambda args: n_ary(2, op.truediv, args),
    "equal": lambda args: n_ary(2, op.eq, args),
    "not_equal": lambda args: n_ary(2, op.ne, args),
    "less": lambda args: n_ary(2, op.lt, args),
    "greater": lambda args: n_ary(2, op.gt, args),
    "less_equal": lambda args: n_ary(2, op.le, args),
    "greater_equal": lambda args: n_ary(2, op.ge, args),
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
    eval(["define", "id", ["func", ["x"], "x"]])

    eval(["define", "inc", ["func", ["x"], ["add", "x", 1]]])
    eval(["define", "dec", ["func", ["x"], ["sub", "x", 1]]])

    eval(["define", "first", ["func", ["l"], ["getat", "l", 0]]])
    eval(["define", "rest", ["func", ["l"], ["slice", "l", 1]]])
    eval(["define", "last", ["func", ["l"], ["getat", "l", -1]]])
    eval(["define", "append", ["func", ["l", "a"], ["add", "l", ["arr", "a"]]]])
    eval(["define", "prepend", ["func", ["a", "l"], ["add", ["arr", "a"], "l"]]])

    eval(["define", "foldl", ["func", ["l", "f", "init"],
            ["if", ["equal", "l", ["arr"]],
                "init",
                ["foldl", ["rest", "l"], "f", ["f", "init", ["first", "l"]]]]]])
    eval(["define", "unfoldl", ["func", ["x", "p", "h", "t"], ["do",
            ["define", "_unfoldl", ["func", ["x", "b"],
                ["if", ["p", "x"],
                    "b",
                    ["_unfoldl", ["t", "x"], ["add", "b", ["arr", ["h", "x"]]]]]]],
            ["_unfoldl", "x", ["arr"]]]]])

    eval(["define", "map", ["func", ["l", "f"],
            ["foldl", "l", ["func", ["acc", "e"], ["append", "acc", ["f", "e"]]], ["arr"]]]])
    eval(["define", "range", ["func", ["s", "e"],
            ["unfoldl", "s", ["func", ["x"], ["greater_equal", "x", "e"]], "id", "inc"]]])

    eval(["define", "scope", ["macro", ["body"],
            ["qq", [["func", [], ["!", "body"]]]]]])

    eval(["define", "when", ["macro", ["cnd", "thn"],
            ["qq", ["if", ["!", "cnd"], ["!", "thn"], None]]]])

    eval(["define", "aif", ["macro", ["cnd", "thn", "els"],
            ["qq", ["scope", ["do",
                ["define", "it", ["!", "cnd"]],
                ["if", "it", ["!", "thn"], ["!", "els"]]]]]]])

    eval(["define", "and", ["macro", ["a", "b"],
            ["qq", ["aif", ["!", "a"], ["!", "b"], "it"]]]])
    eval(["define", "or", ["macro", ["a", "b"],
            ["qq", ["aif", ["!", "a"], "it", ["!", "b"]]]]])

    eval(["define", "while", ["macro", ["cnd", "body"], ["qq",
            ["scope", ["do",
                ["define", "break", None],
                ["define", "continue", ["func", [],
                    ["when", ["!", "cnd"], ["do", ["!", "body"], ["continue"]]]]],
                ["letcc", "cc", ["do", ["assign", "break", "cc"], ["continue"]]]]]]]])

    eval(["define", "awhile", ["macro", ["cnd", "body"], ["qq",
            ["scope", ["do",
                ["define", "break", None],
                ["define", "continue", ["func", [], ["do",
                    ["define", "it", ["!", "cnd"]],
                    ["when", "it", ["do", ["!", "body"], ["continue"]]]]]],
                ["letcc", "cc", ["do", ["assign", "break", "cc"], ["continue"]]]]]]]])

    eval(["define", "gfunc", ["macro", ["params", "body"], ["qq",
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

    eval(["define", "for", ["macro", ["e", "l", "body"], ["qq",
            ["scope", ["do",
                ["define", "__stdlib_for_index", 0],
                ["define", ["!", "e"], None],
                ["define", "break", None],
                ["define", "continue", ["func", [], ["do",
                    ["assign", "__stdlib_for_index", ["inc", "__stdlib_for_index"]],
                    ["go"]]]],
                ["define", "go", ["func", [],
                    ["when", ["less", "__stdlib_for_index", ["len", ["!", "l"]]],
                        ["do",
                            ["assign", ["!", "e"], ["getat", ["!", "l"], "__stdlib_for_index"]],
                            ["!", "body"],
                            ["continue"]]]]],
                ["letcc", "cc", ["do", ["assign", "break", "cc"], ["go"]]]]]]]])

    eval(["define", "agen", ["gfunc", ["a"], ["for", "e", "a", ["yield", "e"]]]])

    eval(["define", "gfor", ["macro", ["e", "gen", "body"], ["qq",
            ["scope", ["do",
                ["define", "__stdlib_gfor_gen", ["!", "gen"]],
                ["define", ["!", "e"], None],
                ["while", ["not_equal", ["assign", ["!", "e"], ["__stdlib_gfor_gen"]], None],
                    ["!", "body"]]]]]]])

    global top_env
    top_env = {"parent": top_env, "vals": {}}

result = None

def eval(expr):
    computation = lambda: eval_expr(expr, top_env, lambda result: result)
    while callable(computation):
        try:
            computation = computation()
        except Skip as s:
            computation = s.skip
    return computation

def run(src):
    return eval(parse(src))

if __name__ == "__main__":
    init_env()
    stdlib()
    print(run("  5  "))
