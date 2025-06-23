
# custom rules

def init_rule():
    global custom_rule
    custom_rule = {}

def add_rule(name, rule):
    global custom_rule
    custom_rule[name] = rule

def print_rule():
    print(custom_rule)

# scanner

def is_name_first(c): return c.isalpha() or c == "_"
def is_name_rest(c): return c.isalnum() or c == "_"
def is_name(expr): return isinstance(expr, str) and is_name_first(expr[0])

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
            case "#": return comment()
            case c if is_name_first(c):
                return name()
            case c if c.isnumeric():
                word(str.isnumeric)
                return int(token)
            case c if c in "!":
                append_char()
                if current_char() == "=" or current_char() == "!":
                    append_char()
            case c if c in "=<>:":
                append_char()
                if current_char() == "=": append_char()
            case c if c in "+-*/%?()[],;":
                append_char()

        return token

    def comment():
        advance()
        line = []
        while current_char() not in("\n", "$EOF"):
            line += current_char()
            advance()
        line = "".join(line)
        if line.startswith("rule "):
            rule = parse(line[5:])
            add_rule(rule[1], rule[2:])
        return next_token()

    pos = 0; token = ""
    return next_token

# parser

def parse(src):

    # helpers

    def advance():
        nonlocal current_token
        prev_token = current_token
        current_token = next_token()
        return prev_token

    def consume(expected):
        assert isinstance(current_token, str) and current_token in expected, \
            f"Expected `{expected}`, found `{current_token}` @ consume"
        return advance()

    def binary_left(ops, sub_elem):
        left = sub_elem()
        while (op := current_token) in ops:
            advance()
            left = [ops[op], left, sub_elem()]
        return left

    def binary_right(ops, sub_elem):
        left = sub_elem()
        if (op := current_token) in ops:
            advance()
            return [ops[op], left, binary_right(ops, sub_elem)]
        return left

    def unary(ops, sub_elem):
        if (op := current_token) not in ops:
            return sub_elem()
        advance()
        return [ops[op], unary(ops, sub_elem)]

    def comma_separated_exprs(closing_token):
        cse = []
        if current_token != closing_token:
            cse.append(expression())
            while current_token == ",":
                advance()
                cse.append(expression())
        consume(closing_token)
        return cse

    # grammar

    def expression():
        return sequence()

    def sequence():
        exprs = [define_assign()]
        while current_token == ";":
            advance()
            exprs.append(define_assign())
        return exprs[0] if len(exprs) == 1 else ["seq"] + exprs

    def define_assign():
        return binary_right({
            ":=": "define", "=": "assign"
        }, or_)

    def or_():
        return binary_left({"or": "or"}, and_)

    def and_():
        return binary_left({"and": "and"}, not_)

    def not_():
        return unary({"not": "not"}, comparison)

    def comparison():
        return binary_left({
            "==": "equal", "!=": "not_equal",
            "<": "less", ">": "greater",
            "<=": "less_equal", ">=": "greater_equal"
        }, add_sub)

    def add_sub():
        return binary_left({
            "+": "add", "-": "sub"
        }, mul_div_mod)

    def mul_div_mod():
        return binary_left({
            "*": "mul", "/": "div", "%": "mod"
        }, unary_ops)

    def unary_ops():
        return unary({"-": "neg", "*": "*", "?": "?"}, call_index)

    def call_index():
        target = primary()
        while current_token in ("(", "["):
            match current_token:
                case "(":
                    advance()
                    target = [target] + comma_separated_exprs(")")
                case "[":
                    advance()
                    target = index_slice(target)
        return target

    def index_slice(target):
        start = end = step = None

        if current_token == "]":
            assert False, f"Invalid index/slice: `{current_token}` @ index_slice"
        if current_token != ":":
            start = expression()
        if current_token == "]":
            advance()
            return ["getat", target, start]

        if current_token != ":":
            assert False, f"Invalid index/slice: `{current_token}` @ index_slice"
        advance()

        if current_token == "]":
            advance()
            return ["slice", target, start, end, step]
        if current_token != ":":
            end = expression()
        if current_token == "]":
            advance()
            return ["slice", target, start, end, step]

        if current_token != ":":
            assert False, f"Invalid index/slice: `{current_token}` @ index_slice"
        advance()
        if current_token == "]":
            advance()
            return ["slice", target, start, end, step]
        if current_token != ":":
            step = expression()
        if current_token == "]":
            advance()
            return ["slice", target, start, end, step]

        assert False, f"Invalid index/slice: `{current_token}` @ index_slice"

    def primary():
        match current_token:
            case "(":
                advance(); expr = expression(); consume(")")
                return expr
            case "[":
                advance(); elems = comma_separated_exprs("]")
                return ["arr"] + elems
            case "func":
                advance(); return func_()
            case "macro":
                advance(); return macro()
            case "if":
                advance(); return if_()
            case "letcc":
                advance(); return letcc()
            case op if op in custom_rule:
                advance(); return custom(custom_rule[op])
        return advance()

    def if_():
        cnd = expression()
        consume("then")
        thn = expression()
        if current_token == "elif":
            advance()
            return ["if", cnd, ["scope", thn], if_()]
        if current_token == "else":
            advance()
            els = expression()
            consume("end")
            return ["if", cnd, ["scope", thn], ["scope", els]]
        consume("end")
        return ["if", cnd, ["scope", thn], None]

    def letcc():
        name = advance()
        assert is_name(name), f"Invalid name: `{name}` @ letcc"
        consume("do")
        body = expression()
        consume("end")
        return ["letcc", name, ["scope", body]]

    def func_():
        consume("(")
        params = comma_separated_exprs(")")
        consume("do")
        body = expression()
        consume("end")
        return ["func", params, body]

    def macro():
        consume("(")
        params = comma_separated_exprs(")")
        consume("do")
        body = expression()
        consume("end")
        return ["macro", params, body]

    def custom(rule):
        def _custom(r):
            if r == []: return []
            match r[0]:
                case "EXPR":
                    return  [expression()] + _custom(r[1:])
                case "NAME":
                    name = expression()
                    assert is_name(name), f"Invalid name: `{name}` @ custom({rule[0]})"
                    return [name] + _custom(r[1:])
                case "PARAMS":
                    consume("(")
                    return  [["arr"] + comma_separated_exprs(")")] + _custom(r[1:])
                case keyword if is_name(keyword):
                    consume(keyword); return  _custom(r[1:])
                case ["*", subrule]:
                    ast = []
                    while current_token == subrule[1]:
                        advance()
                        ast += _custom(subrule[2:])
                    return ast + _custom(r[1:])
                case ["?", subrule]:
                    ast = []
                    if current_token == subrule[1]:
                        advance()
                        ast += _custom(subrule[2:])
                    return ast + _custom(r[1:])
                case unexpected:
                    assert False, f"Illegal rule: `{unexpected}` @ custom({rule[0]})"

        ast = [rule[0]] + _custom(rule[1:])
        return ast

    next_token = scanner(src)
    current_token = next_token()
    expr = expression()
    assert current_token == "$EOF", \
        f"Unexpected token at end: `{current_token}` @ parse"
    return expr

# environment

def new_env(): return {"parent": None, "vals": {}}
def new_scope(env): return {"parent": env, "vals": {}}

top_env = new_env()

def define(env, name, val):
    # assert name not in env["vals"], \
    #     f"Variable already defined: `{name}` @ define"
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

def print_env(env={}):
    if env == {}: env = top_env
    if env is None: return
    print(env["vals"])
    print_env(env["parent"])

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
    # print("eval_expr:", expr)
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
        case ["assign", left, expr]:
            return lambda: eval_assign(left, expr, env, cont)
        case ["scope", expr]:
            return lambda: eval_expr(expr, new_scope(env), cont)
        case ["seq", *exprs]:
            return lambda: foldl_cps(exprs,
                lambda _, expr, c: eval_expr(expr, env, c),
                None, cont)
        case ["if", cnd_expr, thn_expr, els_expr]:
            return lambda: eval_expr(cnd_expr, env, lambda cnd:
                eval_expr(thn_expr, env, cont) if cnd else
                eval_expr(els_expr, env, cont))
        case ["letcc", name, body]:
            def skip(args): raise Skip(lambda: cont(args[0] if len(args) > 0 else None))
            return lambda: apply(["func", [name], body, env], [skip], cont)
        case ["expand", [op_expr, *args_expr]]:
            return lambda: eval_expand(op_expr, args_expr, env, cont)
        case [op_expr, *args_expr]:
            return lambda: eval_op(op_expr, args_expr, env, cont)
        case unexpected:
            assert False, f"Unexpected expression: {unexpected} @ eval"

def eval_assign(left, expr, env, cont):
    def _eval_assign(val):
        match left:
            case str(name):
                return cont(assign(env, name, val))
            case ["getat", arr, idx]:
                return eval_expr(arr, env,
                    lambda arr_val: eval_expr(idx, env,
                        lambda idx_val: cont(setat([arr_val, idx_val, val]))))
            case ["slice", arr, start, end, step]:
                return eval_expr(arr, env,
                    lambda arr_val: eval_expr(start, env,
                        lambda start_val: eval_expr(end, env,
                            lambda end_val: eval_expr(step, env,
                                lambda step_val: cont(set_slice(
                                    [arr_val, start_val, end_val, step_val, val]))))))
        assert False, f"Invalid assign target: {left} @ eval_assign"

    return lambda: eval_expr(expr, env, _eval_assign)

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
    env = new_scope(env); extend(env, params, args)
    return lambda: eval_expr(body, env, cont)

def apply(func, args, cont):
    if callable(func):
        return lambda: cont(func(args))
    else:
        _, params, body, env = func
        env = new_scope(env); extend(env, params, args)
        return lambda: eval_expr(body, env, cont)

def extend(env, params, args):
    if params == [] and args == []: return {}
    assert len(params) > 0, \
        f"Argument count doesn't match: `{params}, {args}` @ extend"
    match params[0]:
        case str(param):
            assert len(args) > 0, \
                f"Argument count doesn't match: `{params}, {args}` @ extend"
            define(env, param, args[0])
            extend(env, params[1:], args[1:])
        case ["*", rest]:
            rest_len = len(args) - len(params) + 1
            assert rest_len >= 0, \
                f"Argument count doesn't match: `{params}, {args}` @ extend"
            define(env, rest, args[:rest_len])
            extend(env, params[1:], args[rest_len:])
        case unexpected:
            assert False, f"Unexpected param at extend: {unexpected}"

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
    return args[2]

def slice_(args):
    match args:
        case [arr]: return arr[:]
        case [arr, start]: return arr[start:]
        case [arr, start, end]: return arr[start:end]
        case [arr, start, end, step]: return arr[slice(start, end, step)]
        case _: assert False, f"Invalid slice: args=`{args}` @ slice"

def set_slice(args):
    arr, start, end, step, val = args
    arr[start:end:step] = val
    return val

def error(args):
    assert False, f"{' '.join(map(str, args))}"

builtins = {
    "add": lambda args: n_ary(2, op.add, args),
    "sub": lambda args: n_ary(2, op.sub, args),
    "mul": lambda args: n_ary(2, op.mul, args),
    "div": lambda args: n_ary(2, op.floordiv, args),
    "mod": lambda args: n_ary(2, op.mod, args),
    "neg": lambda args: n_ary(1, op.neg, args),
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
    "slice": slice_,
    "set_slice": set_slice,

    "is_name": lambda args: n_ary(1, is_name, args),

    "print": lambda args: print(*args),
    "error": lambda args: error(args)
}

def init_env():
    global top_env
    top_env = new_env()
    for name, func in builtins.items(): define(top_env, name, func)
    top_env = new_scope(top_env)

def stdlib():
    run("None #rule [scope, scope, EXPR, end]")
    run("None #rule [qq, qq, EXPR, end]")

    run("id := func (x) do x end")

    run("inc := func (n) do n + 1 end")
    run("dec := func (n) do n - 1 end")

    run("first := func (l) do l[0] end")
    run("rest := func (l) do l[1:] end")
    run("last := func (l) do l[-1] end")
    run("append := func (l, a) do l + [a] end")
    run("prepend := func (a, l) do [a] + l end")

    run("""
        foldl := func (l, f, init) do
            if l == [] then init else
                foldl(rest(l), f, f(init, first(l)))
            end
        end
    """)
    run("""
        unfoldl := func (x, p, h, t) do
            _unfoldl := func (x, b) do
                if p(x) then b else _unfoldl(t(x), b + [h(x)]) end
            end;
            _unfoldl(x, [])
        end
    """)

    run("map := func (l, f) do foldl(l, func(acc, e) do append(acc, f(e)) end, []) end")
    run("range := func (s, e) do unfoldl(s, func (x) do x >= e end, id, inc) end")

    run("""
        __stdlib_when := macro (cnd, thn) do qq
            if !(cnd) then !(thn) end
        end end

        #rule [when, __stdlib_when, EXPR, do, EXPR, end]
    """)

    run("""
        _aif := macro (cnd, thn, *rest) do
            if len(rest) == 0 then qq scope
                it := !(cnd); if it then !(thn) else None end
            end end elif len(rest) == 1 then qq scope
                it := !(cnd); if it then !(thn) else !(rest[0]) end
            end end else qq scope
                it := !(cnd); if it then !(thn) else _aif(!!(rest)) end
            end end end
        end

        #rule [aif, _aif, EXPR, then, EXPR, *[elif, EXPR, then, EXPR], ?[else, EXPR], end]
        """)

    run("and := macro (a, b) do qq aif !(a) then !(b) else it end end end")
    run("or := macro (a, b) do qq aif !(a) then it else !(b) end end end")

    run("""
        __stdlib_while := macro (cnd, body) do qq scope
            break := continue := val := None;
            loop := func() do
                letcc cc do continue = cc end;
                if !(cnd) then val = !(body); loop() else val end
            end;
            letcc cc do break = cc; loop() end
        end end end

        #rule [while, __stdlib_while, EXPR, do, EXPR, end]
    """)

    run("""
        __stdlib_awhile := macro (cnd, body) do qq scope
            break := continue := val := None;
            loop := func() do
                letcc cc do continue = cc end;
                it := !(cnd);
                if it then val = !(body); loop() else val end
            end;
            letcc cc do break = cc; loop() end
        end end end

        #rule [awhile, __stdlib_awhile, EXPR, do, EXPR, end]
    """)

    run("""
        __stdlib_is_name_before := is_name;
        is_name := macro (e) do qq __stdlib_is_name_before(q(!(e))) end end
    """)

    run("""
        __stdlib_for := macro (e, l, body) do qq scope
            __stdlib_for_index := -1;
            __stdlib_for_l := !(l);
            break := continue := __stdlib_for_val := !(e) := None;
            loop := func () do
                letcc __stdlib_for_cc do continue = __stdlib_for_cc end;
                __stdlib_for_index = __stdlib_for_index + 1;
                if __stdlib_for_index < len(__stdlib_for_l) then
                    !(e) = __stdlib_for_l[__stdlib_for_index];
                    __stdlib_for_val = !(body);
                    loop()
                else __stdlib_for_val end
            end;
            letcc __stdlib_for_cc do break = __stdlib_for_cc; loop() end
        end end end

        #rule [for, __stdlib_for, NAME, in, EXPR, do, EXPR, end]
    """)

    run("""
        __stdlib_gfunc := macro (params, body) do qq
            func (!!(params[1:])) do
                yd := nx := None;
                yield := func (x) do letcc cc do nx = cc; yd(x) end end;
                next := func () do letcc cc do yd = cc; nx(None) end end;
                nx := func (_) do !(body); yield(None) end;
                next
            end
        end end

        #rule [gfunc, __stdlib_gfunc, PARAMS, do, EXPR, end]
    """)

    run("agen := gfunc (a) do for e in a do yield(e) end end")

    run("""
        __stdlib_gfor := macro(e, gen, body) do qq scope
            __stdlib_gfor_gen := !(gen);
            !(e) := None;
            while (!(e) = __stdlib_gfor_gen()) != None do !(body) end
        end end end

        #rule [gfor, __stdlib_gfor, NAME, in, EXPR, do, EXPR, end]
    """)

    global top_env
    top_env = new_scope(top_env)

result = None

def eval(expr):
    # print("eval: ", expr)
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
    init_rule()
    stdlib()

    code = "if 5 then 6 end"
    print(parse(code))
    # run(f"print(expand({code}))")
    print(run(code))
