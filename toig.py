# Scanner

class CustomRules(dict): pass

def is_name_first(c): return c.isalpha() or c == "_"
def is_name_rest(c): return c.isalnum() or c == "_"
def is_name(expr): return isinstance(expr, str) and is_name_first(expr[0])

class Scanner():
    def __init__(self, src, custom_rules):
        self._src = src
        self._custom_rules = custom_rules
        self._pos = 0
        self._token = ""

    def next_token(self):
        while self._current_char().isspace(): self._advance()

        self._token = ""

        match self._current_char():
            case "$EOF": return "$EOF"
            case "#": return self._comment()
            case c if is_name_first(c):
                return self._name()
            case c if c.isnumeric():
                self._word(str.isnumeric)
                return int(self._token)
            case c if c in "!":
                self._append_char()
                if self._current_char() == "=" or self._current_char() == "!":
                    self._append_char()
            case c if c in "=<>:":
                self._append_char()
                if self._current_char() == "=": self._append_char()
            case c if c in "+-*/%?()[],;":
                self._append_char()

        return self._token

    def _advance(self): self._pos += 1

    def _current_char(self):
        if self._pos < len(self._src):
            return self._src[self._pos]
        else:
            return "$EOF"

    def _append_char(self):
        self._token += self._current_char()
        self._advance()

    def _word(self, is_rest):
        self._append_char()
        while is_rest(self._current_char()):
            self._append_char()

    def _name(self):
        self._word(is_name_rest)
        match self._token:
            case "None": return None
            case "True": return True
            case "False": return False
            case _ : return self._token

    def _comment(self):
        self._advance()
        line = []
        while self._current_char() not in("\n", "$EOF"):
            line += self._current_char()
            self._advance()
        line = "".join(line)
        if line.startswith("rule "):
            rule = Parser(line[5:], CustomRules()).parse().elems
            assert isinstance(rule, list) and len(rule) >= 2, \
                f"Invalid rule: {rule} @ comment"
            self._custom_rules[rule[1]] = rule[2:]
        return self.next_token()

# Parser

class Parser:
    def __init__(self, src, custom_rules):
        self._src = src
        self._custom_rules = custom_rules
        self._scanner = Scanner(src, custom_rules)
        self._current_token = self._scanner.next_token()

    def parse(self):
        expr = self._expression()
        assert self._current_token == "$EOF", \
            f"Unexpected token at end: `{self._current_token}` @ parse"
        return Expr(expr)

    # Helpers

    def _advance(self):
        prev_token = self._current_token
        self._current_token = self._scanner.next_token()
        return prev_token

    def _consume(self, expected):
        assert isinstance(self._current_token, str) and \
            self._current_token in expected, \
            f"Expected `{expected}`, found `{self._current_token}` @ consume"
        return self._advance()

    def _binary_left(self, ops, sub_elem):
        left = sub_elem()
        while (op := self._current_token) in ops:
            self._advance()
            left = [ops[op], left, sub_elem()]
        return left

    def _binary_right(self, ops, sub_elem):
        left = sub_elem()
        if (op := self._current_token) in ops:
            self._advance()
            return [ops[op], left, self._binary_right(ops, sub_elem)]
        return left

    def _unary(self, ops, sub_elem):
        if (op := self._current_token) not in ops:
            return sub_elem()
        self._advance()
        return [ops[op], self._unary(ops, sub_elem)]

    def _comma_separated_exprs(self, closing_token):
        cse = []
        if self._current_token != closing_token:
            cse.append(self._expression())
            while self._current_token == ",":
                self._advance()
                cse.append(self._expression())
        self._consume(closing_token)
        return cse

    # Grammar

    def _expression(self):
        return self._sequence()

    def _sequence(self):
        exprs = [self._define_assign()]
        while self._current_token == ";":
            self._advance()
            exprs.append(self._define_assign())
        return exprs[0] if len(exprs) == 1 else ["seq"] + exprs

    def _define_assign(self):
        return self._binary_right({
            ":=": "define", "=": "assign"
        }, self._or)

    def _or(self):
        return self._binary_left({"or": "or"}, self._and)

    def _and(self):
        return self._binary_left({"and": "and"}, self._not)

    def _not(self):
        return self._unary({"not": "not"}, self._comparison)

    def _comparison(self):
        return self._binary_left({
            "==": "equal", "!=": "not_equal",
            "<": "less", ">": "greater",
            "<=": "less_equal", ">=": "greater_equal"
        }, self._add_sub)

    def _add_sub(self):
        return self._binary_left({
            "+": "add", "-": "sub"
        }, self._mul_div_mod)

    def _mul_div_mod(self):
        return self._binary_left({
            "*": "mul", "/": "div", "%": "mod"
        }, self._unary_ops)

    def _unary_ops(self):
        return self._unary({"-": "neg", "*": "*", "?": "?"}, self._call_index)

    def _call_index(self):
        target = self._primary()
        while self._current_token in ("(", "["):
            match self._current_token:
                case "(":
                    self._advance()
                    target = [target] + self._comma_separated_exprs(")")
                case "[":
                    self._advance()
                    target = self._index_slice(target)
        return target

    def _index_slice(self, target):
        start = end = step = None

        if self._current_token == "]":
            assert False, f"Invalid index/slice: `{self._current_token}` @ index_slice"
        if self._current_token != ":":
            start = self._expression()
        if self._current_token == "]":
            self._advance()
            return ["get_at", target, start]

        if self._current_token != ":":
            assert False, f"Invalid index/slice: `{self._current_token}` @ index_slice"
        self._advance()

        if self._current_token == "]":
            self._advance()
            return ["slice", target, start, end, step]
        if self._current_token != ":":
            end = self._expression()
        if self._current_token == "]":
            self._advance()
            return ["slice", target, start, end, step]

        if self._current_token != ":":
            assert False, f"Invalid index/slice: `{self._current_token}` @ index_slice"
        self._advance()
        if self._current_token == "]":
            self._advance()
            return ["slice", target, start, end, step]
        if self._current_token != ":":
            step = self._expression()
        if self._current_token == "]":
            self._advance()
            return ["slice", target, start, end, step]

        assert False, f"Invalid index/slice: `{self._current_token}` @ index_slice"

    def _primary(self):
        match self._current_token:
            case "(":
                self._advance();
                expr = self._expression();
                self._consume(")")
                return expr
            case "[":
                self._advance();
                elems = self._comma_separated_exprs("]")
                return ["arr"] + elems
            case "func":
                self._advance(); return self._func()
            case "macro":
                self._advance(); return self._macro()
            case "if":
                self._advance(); return self._if()
            case "letcc":
                self._advance(); return self._letcc()
            case op if op in self._custom_rules:
                self._advance();
                return self._custom(self._custom_rules[op])
        return self._advance()

    def _if(self):
        cnd = self._expression()
        self._consume("then")
        thn = self._expression()
        if self._current_token == "elif":
            self._advance()
            return ["if", cnd, ["scope", thn], self._if()]
        if self._current_token == "else":
            self._advance()
            els = self._expression()
            self._consume("end")
            return ["if", cnd, ["scope", thn], ["scope", els]]
        self._consume("end")
        return ["if", cnd, ["scope", thn], None]

    def _letcc(self):
        name = self._advance()
        assert is_name(name), f"Invalid name: `{name}` @ letcc"
        self._consume("do")
        body = self._expression()
        self._consume("end")
        return ["letcc", name, ["scope", body]]

    def _func(self):
        self._consume("(")
        params = self._comma_separated_exprs(")")
        self._consume("do")
        body = self._expression()
        self._consume("end")
        return ["func", params, body]

    def _macro(self):
        self._consume("(")
        params = self._comma_separated_exprs(")")
        self._consume("do")
        body = self._expression()
        self._consume("end")
        return ["macro", params, body]

    def _custom(self, rule):
        def _custom(r):
            if r == []: return []
            match r[0]:
                case "EXPR":
                    return  [self._expression()] + _custom(r[1:])
                case "NAME":
                    name = self._expression()
                    assert is_name(name), f"Invalid name: `{name}` @ custom({rule[0]})"
                    return [name] + _custom(r[1:])
                case "PARAMS":
                    self._consume("(")
                    return  [["arr"] + self._comma_separated_exprs(")")] + _custom(r[1:])
                case keyword if is_name(keyword):
                    self._consume(keyword); return _custom(r[1:])
                case ["*", subrule]:
                    ast = []
                    while self._current_token == subrule[1]:
                        self._advance()
                        ast += _custom(subrule[2:])
                    return ast + _custom(r[1:])
                case ["?", subrule]:
                    ast = []
                    if self._current_token == subrule[1]:
                        self._advance()
                        ast += _custom(subrule[2:])
                    return ast + _custom(r[1:])
                case unexpected:
                    assert False, f"Illegal rule: `{unexpected}` @ custom({rule[0]})"

        return [rule[0]] + _custom(rule[1:])

# Environment

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

# Evaluator

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
                if not isinstance(self._cont, list) or \
                        self._cont[0] != "$restore_env":
                    self._cont = ["$restore_env", self._env, self._cont]
                self._expr, self._env = (
                    Expr(expr), Environment(self._env)
                )
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
                if not isinstance(self._cont, list) or \
                        self._cont[0] != "$restore_env":
                    self._cont = ["$restore_env", self._env, self._cont]
                self._expr, self._env = Expr(body_expr), closure_env
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
            case ["$meval", call_env, next_cont]:
                self._expr, self._env, self._cont = (
                    Expr(self._expr), call_env, next_cont
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
                if not isinstance(self._cont, list) or \
                        self._cont[0] != "$restore_env":
                    self._cont = ["$restore_env", call_env, next_cont]
                self._expr, self._env = (
                    Expr(body_expr), mclosure_env
                )
            case unexpected:
                assert False, f"Cannot expand: {unexpected}"

# Runtime

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

class BuiltIns:
    def __init__(self, env):
        self._env = env

    def load(self):
        _builtins = {
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

        for name, func in _builtins.items():
            self._env.define(name, func)


class StdLib:
    def __init__(self, interpreter):
        self._interpreter = interpreter

    def _run(self, src):
        self._interpreter.run(src)

    def load(self):
        self._run("__stdlib__ := None")

        self._run("None #rule [scope, scope, EXPR, end]")
        self._run("None #rule [qq, qq, EXPR, end]")

        self._run("id := func (x) do x end")

        self._run("inc := func (n) do n + 1 end")
        self._run("dec := func (n) do n - 1 end")

        self._run("first := func (l) do l[0] end")
        self._run("rest := func (l) do l[1:] end")
        self._run("last := func (l) do l[-1] end")
        self._run("append := func (l, a) do l + [a] end")
        self._run("prepend := func (a, l) do [a] + l end")

        self._run("""
            foldl := func (l, f, init) do
                if l == [] then init else
                    foldl(rest(l), f, f(init, first(l)))
                end
            end
        """)
        self._run("""
            unfoldl := func (x, p, h, t) do
                _unfoldl := func (x, b) do
                    if p(x) then b else _unfoldl(t(x), b + [h(x)]) end
                end;
                _unfoldl(x, [])
            end
        """)

        self._run("map := func (l, f) do foldl(l, func(acc, e) do append(acc, f(e)) end, []) end")
        self._run("range := func (s, e) do unfoldl(s, func (x) do x >= e end, id, inc) end")

        self._run("""
            __stdlib_when := macro (cnd, thn) do qq
                if !(cnd) then !(thn) end
            end end

            #rule [when, __stdlib_when, EXPR, do, EXPR, end]
        """)

        self._run("""
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

        self._run("and := macro (a, b) do qq aif !(a) then !(b) else it end end end")
        self._run("or := macro (a, b) do qq aif !(a) then it else !(b) end end end")

        self._run("""
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

        self._run("""
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

        self._run("""
            __stdlib_is_name_before := is_name;
            is_name := macro (e) do qq __stdlib_is_name_before(q(!(e))) end end
        """)

        self._run("""
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

        self._run("""
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

        self._run("agen := gfunc (a) do for e in a do yield(e) end end")

        self._run("""
            __stdlib_gfor := macro(e, gen, body) do qq scope
                __stdlib_gfor_gen := !(gen);
                !(e) := None;
                while (!(e) = __stdlib_gfor_gen()) != None do !(body) end
            end end end

            #rule [gfor, __stdlib_gfor, NAME, in, EXPR, do, EXPR, end]
        """)

# Interpreter

class Interpreter:
    def __init__(self):
        self._env = Environment()
        BuiltIns(self._env).load()
        self._env = Environment(self._env)
        self._custom_rule = CustomRules()
        StdLib(self).load()
        self._env = Environment(self._env)

    def parse(self, src):
        return Parser(src, self._custom_rule).parse()

    def run(self, src):
        return Evaluator(self.parse(src), self._env, ["$halt"]).eval()

if __name__ == "__main__":
    i = Interpreter()

    src = """
        loop := func () do loop() end;
        loop()
    """
    src = """
        loop := func (n) do if n > 0 then loop(n - 1) end end;
        loop(3)
    """
    src = """
        wh := macro (cnd, body) do qq
            loop := func() do
                if !(cnd) then !(body); loop() end
            end;
            loop()
        end end;
        n := 3;
        wh(n > 0, n = n - 1)
    """

    src = """
        when 1 > 0 do when 1 > 0 do when 1 > 0 do None end end end
    """

    print(i.parse(src))
    # i.run(f"print(expand({code}))")
    print(i.run(src))
