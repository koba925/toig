# Scanner

def is_name_first(c): return c.isalpha() or c == "_"
def is_name_rest(c): return c.isalnum() or c == "_"

import dataclasses

@dataclasses.dataclass(frozen=True)
class Name:
    name: str

    def __repr__(self):
        return f"Name({self.name})"

@dataclasses.dataclass(frozen=True)
class Token:
    val: None | bool | int | str | list | Name
    text: str
    line: int

    def with_val(self, val):
        return dataclasses.replace(self, val=val)

    def __repr__(self):
        return f"Token({self.val!r}, {self.text!r}, {self.line})"

from typing import NoReturn

def report_error(msg, text, line) -> NoReturn:
    if text == "$EOF":
        raise AssertionError(msg + f" at end")
    else:
        raise AssertionError(msg + f": `{text}` at line {line}")

class Scanner():
    def __init__(self, src):
        self._src = src
        self._pos = 0
        self._line = 1
        self._text = ""

    def __repr__(self):
        return f"Scanner(_pos={self._pos}, _line={self._line}, _text='{self._text}')"

    def next_token(self):
        while self._current_char().isspace(): self._advance()

        self._text = ""

        match self._current_char():
            case "$EOF":
                return Token("$EOF", "$EOF", self._line)
            case c if is_name_first(c):
                return self._name()
            case c if c.isnumeric():
                self._word(str.isnumeric)
                return self._token(int(self._text))
            case c if c == "'":
                self._advance()
                while (c := self._current_char()) != "'":
                    if c == "$EOF":
                        report_error("Unterminated string", self._text, self._line)
                    self._append_char()
                self._advance()
                return self._token(self._text)
            case c if c in "!":
                self._append_char()
                if self._current_char() == "!":
                    self._append_char()
                return self._token(self._text)
            case c if c in "=:":
                self._append_char()
                if self._current_char() == "=": self._append_char()
                return self._token(Name(self._text))
            case c if c in "+-(),;":
                self._append_char()
                return self._token(Name(self._text))
            case c:
                report_error("Unexpected character", c, self._line)

    def _name(self):
        self._word(is_name_rest)
        match self._text:
            case "None": return self._token(None)
            case "True": return self._token(True)
            case "False": return self._token(False)
            case text : return self._token(Name(text))

    def _word(self, is_rest):
        self._append_char()
        while is_rest(self._current_char()):
            self._append_char()

    def _append_char(self):
        self._text += self._current_char()
        self._advance()

    def _current_char(self):
        if self._pos < len(self._src):
            return self._src[self._pos]
        else:
            return "$EOF"

    def _advance(self):
        if self._current_char() == "\n":
            self._line += 1
        self._pos += 1

    def _token(self, val):
        return Token(val, self._text, self._line)

# Parser

class Parser:
    def __init__(self, src):
        self._src = src
        self._scanner = Scanner(src)
        self._current_token = self._scanner.next_token()

    def __repr__(self):
        return f"Parser(_current_token={self._current_token})"

    def parse(self):
        expr = self._expression()
        if self._current_token.val != "$EOF":
            self._report_error("Unexpected token at end")
        return expr

    # Grammar

    def _expression(self):
        return self._sequence()

    def _sequence(self):
        expr = self._define_assign()
        if self._current_token.val != Name(";"):
            return expr
        else:
            op = self._current_token.with_val(Name("seq"))
            seq = [op, expr]
            while self._current_token.val == Name(";"):
                self._advance()
                seq.append(self._define_assign())
            return seq

    def _define_assign(self):
        return self._binary_right({
            ":=": "define", "=": "assign"
        }, self._comparison)

    def _comparison(self):
        return self._binary_left({
            "==": "equal",
        }, self._add_sub)

    def _add_sub(self):
        return self._binary_left({
            "+": "add", "-": "sub"
        }, self._call)

    def _call(self):
        target = self._primary()
        while self._current_token.val == Name("("):
            self._advance()
            target = [target] + self._comma_separated_exprs(")")
        return target

    def _primary(self):
        match self._current_token.val:
            case Name("("):
                self._advance()
                expr = self._expression()
                self._consume(")")
                return expr
            case Name("func") | Name("macro"):
                return self._func_macro()
            case Name("if"):
                return self._if()
        return self._advance()

    def _if(self):
        op = self._advance().with_val(Name("if"))
        cnd = self._expression()
        self._consume("then")
        thn = self._expression()
        if self._current_token.val == Name("elif"):
            return [op, cnd, thn, self._if()]
        if self._current_token.val == Name("else"):
            self._advance()
            els = self._expression()
            self._consume("end")
            return [op, cnd, thn, els]
        self._consume("end")
        return [op, cnd, thn, Token(None, "None", op.line)]

    def _func_macro(self):
        op = self._advance()
        self._consume("(")
        params = self._comma_separated_exprs(")")
        self._consume("do")
        body = self._expression()
        self._consume("end")
        return [op, params, body]

    # Helpers

    def _binary_left(self, ops, sub_elem):
        left = sub_elem()
        while (op := self._current_token).text in ops:
            self._advance()
            left = [op.with_val(Name(ops[op.text])), left, sub_elem()]
        return left

    def _binary_right(self, ops, sub_elem):
        left = sub_elem()
        if (op := self._current_token).text in ops:
            self._advance()
            return [op.with_val(Name(ops[op.text])),
                left, self._binary_right(ops, sub_elem)]
        return left

    def _comma_separated_exprs(self, closing_token):
        cse = []
        if self._current_token.val != Name(closing_token):
            cse.append(self._expression())
            while self._current_token.val == Name(","):
                self._advance()
                cse.append(self._expression())
        self._consume(closing_token)
        return cse

    def _consume(self, expected):
        if not isinstance(self._current_token.val, Name) or \
                self._current_token.val.name not in expected:
            self._report_error(f"`{expected}` expected")
        return self._advance()

    def _advance(self):
        prev_token = self._current_token
        self._current_token = self._scanner.next_token()
        return prev_token

    def _report_error(self, msg):
        report_error(msg, self._current_token.text, self._current_token.line)

# Evaluator

class VariableNotFoundError(Exception): pass

class Environment:
    def __init__(self, parent=None):
        self._parent = parent
        self._vals = {}

    def define(self, name, val):
        self._vals[name] = val
        return val

    def assign(self, name, val):
        if name in self._vals:
            self._vals[name] = val
            return val
        elif self._parent is not None:
            return self._parent.assign(name, val)
        else:
            raise VariableNotFoundError()

    def get(self, name):
        if name in self._vals:
            return self._vals[name]
        elif self._parent is not None:
            return self._parent.get(name)
        else:
            raise VariableNotFoundError()

class Evaluator:
    def eval(self, expr, env):
        match expr:
            case Token(Name(name)):
                try:
                    return env.get(name)
                except VariableNotFoundError:
                    self._report_error(f"Variable not found", expr)
            case Token(val=v):
                return v
            case [Token(val=Name("q")), elem]:
                return elem
            case [Token(val=Name("qq")), elem]:
                return self._eval_quasiquote(elem, env)
            case [Token(val=Name("func")), params, body]:
                return ["func", params, body, env]
            case [Token(val=Name("macro")), params, body]:
                return ["macro", params, body, env]
            case [Token(val=Name("define")), name, val]:
                return env.define(name.val.name, self.eval(val, env))
            case [Token(val=Name("assign")), name, val]:
                try:
                    return env.assign(name.val.name, self.eval(val, env))
                except VariableNotFoundError:
                    self._report_error(f"Variable not found", name)
            case [Token(val=Name("seq")), *exprs]:
                return self._eval_seq(exprs, env)
            case [Token(val=Name("if")), cnd, thn, els]:
                return self._eval_if(cnd, thn, els, env)
            case [Token(val=Name("expand")), [op, *args]]:
                return self._eval_expand(op, args, env)
            case [op, *args]:
                return self._eval_op(op, args, env)
            case unexpected:
                self._report_error("Unexpected expression", expr)

    def _eval_quasiquote(self, expr, env):
        def qqelems(elems):
            quoted = []
            for elem in elems:
                match elem:
                    case [Token(val="!!") as op, e]:
                        vals = self.eval(e, env)
                        if not isinstance(vals, list):
                            self._report_error("Cannot splice", op)
                        quoted += vals
                    case _: quoted.append(self._eval_quasiquote(elem, env))
            return quoted

        match expr:
            case [Token(val="!"), elem]: return self.eval(elem, env)
            case [*elems]: return qqelems(elems)
            case _: return expr

    def _eval_seq(self, exprs, env):
        val = None
        for expr in exprs:
            val = self.eval(expr, env)
        return val

    def _eval_if(self, cnd, thn, els, env):
        if self.eval(cnd, env):
            return self.eval(thn, env)
        else:
            return self.eval(els, env)

    def _eval_expand(self, op, args, env):
        match self.eval(op, env):
            case ["macro", params, body, menv]:
                return self._expand(body, params, args, menv)
            case unexpected:
                self._report_error("Macro expected", op)

    def _eval_op(self, op, args, env):
        match self.eval(op, env):
            case ["macro", params, body, menv]:
                return self.eval(self._expand(body, params, args, menv), env)
            case f_val:
                try:
                    return self._apply(
                        f_val,
                        [self.eval(arg, env) for arg in args])
                except TypeError:
                    self._report_error("Type error", op)

    def _expand(self, body, params, args, menv):
        new_menv = self._extend(menv, params, args)
        return self.eval(body, new_menv)

    def _apply(self, f_val, args_val):
        if callable(f_val):
            return f_val(*args_val)

        _, params, body, env = f_val
        new_env = self._extend(env, params, args_val)
        return self.eval(body, new_env)

    def _extend(self, env, params, args_val):
        new_env = Environment(env)
        for param, arg in zip(params, args_val):
            new_env.define(param.val.name, arg)
        return new_env

    def _report_error(self, msg, expr):
        def first_token(expr):
            match expr:
                case Token():
                    return expr
                case [first, *_rest]:
                    return first_token(first)
                case _:
                    return Token("Unknown", "Unknown", 0)

        token = first_token(expr)
        report_error(msg, token.text, token.line)

class Interpreter:
    def __init__(self):
        self._env = Environment()
        self.init_builtins()

    def init_builtins(self):
        _builtins = {
            "add": lambda a, b: a + b,
            "sub": lambda a, b: a - b,
            "equal": lambda a, b: a == b,

            "print": print
        }

        for name, func in _builtins.items():
            self._env.define(name, func)

        self._env = Environment(self._env)

    def parse(self, src):
        return Parser(src).parse()

    def go(self, src):
        return Evaluator().eval(Parser(src).parse(), self._env)

if __name__ == "__main__":
    i = Interpreter()

    print(i.go("'hello, world'"))
    i.go("print('hello, world')")
    i.go("print('hello, ' + 'world')")

    i.go("""
        myif := macro(cnd, thn, els) do qq(if !(cnd) then !(thn) else !(els) end) end;
        print(expand(myif(5 == 5, 6, 7)));
        print(myif(5 == 5, 6, a));
        print(myif(5 == 6, a, 8))
    """)

    i.go("""
        fib := func (n) do
            if n == 0 then 0
            elif n == 1 then 1
            else fib(n - 1) + fib(n - 2) end
        end;

        print(fib(10))
    """)

    i.go("""
        make_counter := func () do
            c := 0;
            func() do c = c + 1 end
        end;

        counter1 := make_counter();
        counter2 := make_counter();

        print(counter1());
        print(counter1());
        print(counter2());
        print(counter2());
        print(counter1());
        print(counter2())
    """)
