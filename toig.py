
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
            rule = parse(line[5:]).elems
            assert isinstance(rule, list) and len(rule) >= 2, \
                f"Invalid rule: {rule} @ comment"
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
            return ["get_at", target, start]

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
    return Expr(expr)

class Environment:
    def __init__(self, parent=None):
        self._parent = parent
        self._vals = {}

    def __repr__(self):
        if "__builtins__" in self._vals:
            this_env = "builtins"
        elif "__stdlib__" in self._vals:
            this_env = "stdlib"
        else:
            this_env = self._vals
        return f"{this_env} > {self._parent}"

    def define(self, name, val):
        self._vals[name] = val

    def assign(self, name, val):
        if name in self._vals:
            self._vals[name] = val
        elif self._parent is not None:
            self._parent.assign(name, val)
        else:
            assert False, f"name '{name}' is not defined"

    def get(self, name):
        if name in self._vals:
            return self._vals[name]
        elif self._parent is not None:
            return self._parent.get(name)
        else:
            assert False, f"name '{name}' is not defined"

    def extend(self, params, args):
        def _extend(params, args):
            if params == [] and args == []: return {}
            assert len(params) > 0, \
                f"Argument count doesn't match: `{params}, {args}` @ extend"
            match params[0]:
                case str(param):
                    assert len(args) > 0, \
                        f"Argument count doesn't match: `{params}, {args}` @ extend"
                    env.define(param, args[0])
                    _extend(params[1:], args[1:])
                case ["*", rest]:
                    rest_len = len(args) - len(params) + 1
                    assert rest_len >= 0, \
                        f"Argument count doesn't match: `{params}, {args}` @ extend"
                    env.define(rest, args[:rest_len])
                    _extend(params[1:], args[rest_len:])
                case unexpected:
                    assert False, f"Unexpected param at extend: {unexpected}"

        env = Environment(self)
        _extend(params, args)
        return env

from typing import Callable
from dataclasses import dataclass

ValueType = None | bool | int | Callable | list

@dataclass
class Expr:
    elems: ValueType

class Evaluator:
    def __init__(self, expr, env, cont):
        self._expr: Expr | ValueType = expr
        self._env = env
        self._cont = cont

    def eval(self):
        while True:
            if isinstance(self._expr, Expr):
                self._eval_expr()
            elif self._cont == ["$halt"]:
                return self._expr
            else:
                self._apply_val()

    def _eval_expr(self):
        assert isinstance(self._expr, Expr)
        match self._expr.elems:
            case bool(_) | int(_) | None:
                self._expr = self._expr.elems
            case f if callable(f):
                self._expr = f
            case ["func", params, body]:
                self._expr = ["closure", params, body, self._env]
            case ["macro", params, body]:
                self._expr = ["mclosure", params, body, self._env]
            case str(name):
                self._expr = self._env.get(name)
            case ["q", expr]:
                self._expr = expr
            case ["qq", expr]:
                self._expr, self._cont = expr, ["$qq", self._cont]
            case ["define", name, val_expr]:
                assert is_name(name), f"Invalid name: `{name}`"
                self._expr, self._cont = Expr(val_expr), \
                    ["$define", name, self._cont]
            case ["assign", left, val_expr]:
                self._eval_assign(left, val_expr)
            case ["scope", expr]:
                self._expr, self._env, self._cont = (
                    Expr(expr), Environment(self._env),
                    ["$restore_env", self._env, self._cont])
            case ["seq", *exprs]:
                self._expr, self._cont = None, \
                    ["$seq", exprs, self._cont]
            case ["if", cnd_expr, thn_expr, els_expr]:
                self._expr, self._cont = Expr(cnd_expr), \
                    ["$if", thn_expr, els_expr, self._cont]
            case ["letcc", name, body]:
                self._env.define(name, ["cont", self._env, self._cont])
                self._expr = Expr(body)
            case ["expand", [op_expr, *args_expr]]:
                self._expr, self._cont = Expr(op_expr), \
                    ["$expand", args_expr, self._env, self._cont]
            case ["$apply", op_val, args_val]:
                self._apply_op(op_val, args_val)
            case [op_expr, *args_expr]:
                self._expr, self._cont = Expr(op_expr), \
                    ["$call", args_expr, self._env, self._cont]
            case _:
                assert False, f"Invalid expression: {self._expr}"

    def _eval_assign(self, left, val_expr):
        match left:
            case name if is_name(name):
                self._expr, self._cont = Expr(val_expr), \
                    ["$assign", name, self._cont]
            case ["get_at", arr, idx]:
                self._expr = Expr(["set_at", arr, idx, val_expr])
            case ["slice", arr, start, end, step]:
                self._expr = Expr(["set_slice", arr, start, end, step, val_expr])
            case _:
                assert False, f"Invalid assign target: {left} @ eval_assign"

    def _apply_op(self, op_val, args_val):
        match op_val:
            case f if callable(f):
                self._expr = op_val(args_val)
            case ["closure", params, body_expr, closure_env]:
                closure_env = closure_env.extend(params, args_val)
                self._expr, self._env, self._cont = Expr(body_expr), closure_env, \
                    ["$restore_env", self._env, self._cont]
            case ["mclosure", params, body_expr, mclosure_env]:
                mclosure_env = mclosure_env.extend(params, args_val)
                self._expr, self._env, self._cont = Expr(body_expr), mclosure_env, \
                    ["$meval", self._env, self._cont]
            case ["cont", env, cont]:
                val = args_val[0] if args_val else None
                self._expr, self._env, self._cont = val, env, cont
            case _:
                assert False, f"Invalid function: {self._expr}"

    def _apply_val(self):
        assert not isinstance(self._expr, Expr), \
            f"Invalid value: {self._expr}"
        match self._cont:
            case ["$qq", next_cont]:
                self._apply_quasiquote(next_cont)
            case ["$qq_elems", splicing, elems, elems_done, next_cont]:
                elems_done = self._qq_add_element(elems_done,splicing)
                self._apply_qq_elems(elems, elems_done, next_cont)
            case ["$define", name, next_cont]:
                self._apply_define(name, next_cont)
            case ["$assign", name, next_cont]:
                self._apply_assign(name, next_cont)
            case ["$seq", exprs, next_cont]:
                self._apply_seq(exprs, next_cont)
            case ["$if", thn_expr, els_expr, next_cont]:
                self._apply_if(thn_expr, els_expr, next_cont)
            case ["$call", args_expr, call_env, next_cont]:
                self._apply_call(args_expr, call_env, next_cont)
            case ["$args", op_expr, args_expr, args_val, call_env, next_cont]:
                self._apply_args(op_expr, args_expr, args_val, call_env, next_cont)
            case ["$expand", args_expr, call_env, next_cont]:
                self._apply_expand(args_expr, call_env, next_cont)
            case ["$meval", mclosure_env, next_cont]:
                self._expr, self._env, self._cont = (
                    Expr(self._expr), mclosure_env, next_cont
                )
            case ["$restore_env", env, next_cont]:
                self._env, self._cont = env, next_cont
            case _:
                assert False, f"Invalid continuation: {self._cont}"

    def _apply_quasiquote(self, next_cont):
        match self._expr:
            case ["!", expr]:
                self._expr = Expr(expr)
                self._cont = next_cont
            case [*elems]:
                self._apply_qq_elems(elems, [], next_cont)
            case _:
                self._cont = next_cont

    def _qq_add_element(self, elems_done, splicing):
        if splicing:
            assert isinstance(self._expr , list), f"Cannot splice: {self._expr}"
            return elems_done + self._expr
        else:
            return elems_done + [self._expr]

    def _apply_qq_elems(self, elems, elems_done, next_cont):
        match elems:
            case []:
                self._expr, self._cont  = elems_done, next_cont
            case [["!!", elem], *rest]:
                self._expr = Expr(elem)
                self._cont = ["$qq_elems", True, rest, elems_done, next_cont]
            case [first, *rest]:
                self._expr = first
                self._cont = ["$qq", ["$qq_elems", False, rest, elems_done, next_cont]]
            case _:
                assert False, f"Invalid quasiquote elements: {elems}"

    def _apply_define(self, name, next_cont):
        self._env.define(name, self._expr)
        self._cont = next_cont

    def _apply_assign(self, name, next_cont):
        self._env.assign(name, self._expr)
        self._cont = next_cont

    def _apply_seq(self, exprs, next_cont):
        if exprs == []:
            self._cont = next_cont
        else:
            self._expr, self._cont = Expr(exprs[0]), \
                ["$seq", exprs[1:], next_cont]

    def _apply_if(self, thn_expr, els_expr, next_cont):
        if self._expr:
            self._expr, self._cont = Expr(thn_expr), next_cont
        else:
            self._expr, self._cont = Expr(els_expr), next_cont

    def _apply_call(self, args_expr, call_env, next_cont):
        match self._expr:
            case ["mclosure", _params, _body_expr, _mclosure_env]:
                self._expr, self._env, self._cont = (
                    Expr(["$apply", self._expr, args_expr]), call_env, next_cont
                )
            case op_val:
                self._apply_arg(op_val, args_expr, [], call_env, next_cont)

    def _apply_args(self, op_val, args_expr, args_val, call_env, next_cont):
        args_val = args_val + [self._expr]
        self._apply_arg(op_val, args_expr, args_val, call_env, next_cont)

    def _apply_arg(self, op_val, args_expr, args_val, call_env, next_cont):
        if args_expr == []:
            self._expr, self._env, self._cont = (
                Expr(["$apply", op_val, args_val]), call_env, next_cont
            )
        else:
            self._expr, self._env, self._cont = (
                Expr(args_expr[0]),
                call_env,
                ["$args", op_val, args_expr[1:], args_val, call_env, next_cont]
            )

    def _apply_expand(self, args_expr, call_env, next_cont):
        match self._expr:
            case ["mclosure", params, body_expr, mclosure_env]:
                mclosure_env = mclosure_env.extend(params, args_expr)
                self._expr, self._env, self._cont = (
                    Expr(body_expr), mclosure_env,
                    ["$restore_env", call_env, next_cont]
                )
            case unexpected:
                assert False, f"Cannot expand: {unexpected}"

def set_at(args):
    args[0][args[1]] = args[2]
    return args[2]

def slice_(args):
    arr, start, end, step = args
    return arr[slice(start, end, step)]

def set_slice(args):
    arr, start, end, step, val = args
    arr[start:end:step] = val
    return val

def error(args):
    assert False, f"{' '.join(map(str, args))}"

class Interpreter:

    builtins = {
        "__builtins__": None,
        "add": lambda args: args[0] + args[1],
        "sub": lambda args: args[0] - args[1],
        "mul": lambda args: args[0] * args[1],
        "div": lambda args: args[0] // args[1],
        "mod": lambda args: args[0] % args[1],
        "neg": lambda args: -args[0],
        "equal": lambda args: args[0] == args[1],
        "not_equal": lambda args: args[0] != args[1],
        "less": lambda args: args[0] < args[1],
        "greater": lambda args: args[0] > args[1],
        "less_equal": lambda args: args[0] <= args[1],
        "greater_equal": lambda args: args[0] >= args[1],
        "not": lambda args: not args[0],

        "arr": lambda args: args,
        "is_arr": lambda args: isinstance(args[0], list),
        "len": lambda args: len(args[0]),
        "get_at": lambda args: args[0][args[1]],
        "set_at": set_at,
        "slice": slice_,
        "set_slice": set_slice,

        "is_name": lambda args: isinstance(args[0], str),

        "print": lambda args: print(*args),
        "error": lambda args: error(args)
    }

    def __init__(self):
        self.env = Environment()
        for name, func in Interpreter.builtins.items():
            self.env.define(name, func)
        self.env = Environment(self.env)
        init_rule()

    def stdlib(self):
        self.run("__stdlib__ := None")

        self.run("None #rule [scope, scope, EXPR, end]")
        self.run("None #rule [qq, qq, EXPR, end]")

        self.run("id := func (x) do x end")

        self.run("inc := func (n) do n + 1 end")
        self.run("dec := func (n) do n - 1 end")

        self.run("first := func (l) do l[0] end")
        self.run("rest := func (l) do l[1:] end")
        self.run("last := func (l) do l[-1] end")
        self.run("append := func (l, a) do l + [a] end")
        self.run("prepend := func (a, l) do [a] + l end")

        self.run("""
            foldl := func (l, f, init) do
                if l == [] then init else
                    foldl(rest(l), f, f(init, first(l)))
                end
            end
        """)
        self.run("""
            unfoldl := func (x, p, h, t) do
                _unfoldl := func (x, b) do
                    if p(x) then b else _unfoldl(t(x), b + [h(x)]) end
                end;
                _unfoldl(x, [])
            end
        """)

        self.run("map := func (l, f) do foldl(l, func(acc, e) do append(acc, f(e)) end, []) end")
        self.run("range := func (s, e) do unfoldl(s, func (x) do x >= e end, id, inc) end")

        self.run("""
            __stdlib_when := macro (cnd, thn) do qq
                if !(cnd) then !(thn) end
            end end

            #rule [when, __stdlib_when, EXPR, do, EXPR, end]
        """)

        self.run("""
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

        self.run("and := macro (a, b) do qq aif !(a) then !(b) else it end end end")
        self.run("or := macro (a, b) do qq aif !(a) then it else !(b) end end end")

        self.run("""
            __stdlib_while := macro (cnd, body) do qq scope
                continue := val := None;
                letcc break do
                    loop := func() do
                        letcc cc do continue = cc end;
                        if !(cnd) then val = !(body); loop() else val end
                    end;
                    loop()
                end
            end end end

            #rule [while, __stdlib_while, EXPR, do, EXPR, end]
        """)

        self.run("""
            __stdlib_awhile := macro (cnd, body) do qq scope
                continue := val := None;
                letcc break do
                    loop := func() do
                        letcc cc do continue = cc end;
                        it := !(cnd);
                        if it then val = !(body); loop() else val end
                    end;
                    loop()
                end
            end end end

            #rule [awhile, __stdlib_awhile, EXPR, do, EXPR, end]
        """)

        self.run("""
            __stdlib_is_name_before := is_name;
            is_name := macro (e) do qq __stdlib_is_name_before(q(!(e))) end end
        """)

        self.run("""
            __stdlib_for := macro (e, l, body) do qq scope
                __stdlib_for_index := -1;
                __stdlib_for_l := !(l);
                continue := __stdlib_for_val := !(e) := None;
                letcc break do
                    loop := func () do
                        letcc cc do continue = cc end;
                        __stdlib_for_index = __stdlib_for_index + 1;
                        if __stdlib_for_index < len(__stdlib_for_l) then
                            !(e) = __stdlib_for_l[__stdlib_for_index];
                            __stdlib_for_val = !(body);
                            loop()
                        else __stdlib_for_val end
                    end;
                    loop()
                end
            end end end

            #rule [for, __stdlib_for, NAME, in, EXPR, do, EXPR, end]
        """)

        self.run("""
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

        self.run("agen := gfunc (a) do for e in a do yield(e) end end")

        self.run("""
            __stdlib_gfor := macro(e, gen, body) do qq scope
                __stdlib_gfor_gen := !(gen);
                !(e) := None;
                while (!(e) = __stdlib_gfor_gen()) != None do !(body) end
            end end end

            #rule [gfor, __stdlib_gfor, NAME, in, EXPR, do, EXPR, end]
        """)

        self.env = Environment(self.env)

    def run(self, src):
        return Evaluator(parse(src), self.env, ["$halt"]).eval()

if __name__ == "__main__":
    i = Interpreter()
    i.stdlib()

    code = """
        5
    """
    print(parse(code))
    # i.run(f"print(expand({code}))")
    print(i.run(code))
