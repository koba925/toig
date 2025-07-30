# Scanner

def is_name_first(c): return c.isalpha() or c == "_"
def is_name_rest(c): return c.isalnum() or c == "_"

class Scanner():
    def __init__(self, src):
        self._src = src
        self._pos = 0
        self._token = ""

    def next_token(self):
        while self._current_char().isspace(): self._advance()

        self._token = ""

        match self._current_char():
            case "$EOF": return "$EOF"
            case c if is_name_first(c):
                return self._name()
            case c if c.isnumeric():
                self._word(str.isnumeric)
                return int(self._token)
            case c if c in "=:":
                self._append_char()
                if self._current_char() == "=": self._append_char()
            case c if c in "+-(),;":
                self._append_char()

        return self._token

    def _name(self):
        self._word(is_name_rest)
        match self._token:
            case "None": return None
            case "True": return True
            case "False": return False
            case _ : return self._token

    def _word(self, is_rest):
        self._append_char()
        while is_rest(self._current_char()):
            self._append_char()

    def _append_char(self):
        self._token += self._current_char()
        self._advance()

    def _current_char(self):
        if self._pos < len(self._src):
            return self._src[self._pos]
        else:
            return "$EOF"

    def _advance(self): self._pos += 1


# Parser

class Parser:
    def __init__(self, src):
        self._src = src
        self._scanner = Scanner(src)
        self._current_token = self._scanner.next_token()

    def parse(self):
        expr = self._expression()
        assert self._current_token == "$EOF", \
            f"Unexpected token at end: `{self._current_token}` @ parse"
        return expr

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
        while self._current_token == "(":
            self._advance()
            target = [target] + self._comma_separated_exprs(")")
        return target

    def _primary(self):
        match self._current_token:
            case "(":
                self._advance()
                expr = self._expression()
                self._consume(")")
                return expr
            case "func":
                self._advance(); return self._func()
            case "if":
                self._advance(); return self._if()
        return self._advance()

    def _if(self):
        cnd = self._expression()
        self._consume("then")
        thn = self._expression()
        if self._current_token == "elif":
            self._advance()
            return ["if", cnd, thn, self._if()]
        if self._current_token == "else":
            self._advance()
            els = self._expression()
            self._consume("end")
            return ["if", cnd, thn, els]
        self._consume("end")
        return ["if", cnd, thn, None]

    def _func(self):
        self._consume("(")
        params = self._comma_separated_exprs(")")
        self._consume("do")
        body = self._expression()
        self._consume("end")
        return ["func", params, body]

    # Helpers

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

    def _comma_separated_exprs(self, closing_token):
        cse = []
        if self._current_token != closing_token:
            cse.append(self._expression())
            while self._current_token == ",":
                self._advance()
                cse.append(self._expression())
        self._consume(closing_token)
        return cse

    def _consume(self, expected):
        assert isinstance(self._current_token, str) and \
            self._current_token in expected, \
            f"Expected `{expected}`, found `{self._current_token}` @ consume"
        return self._advance()

    def _advance(self):
        prev_token = self._current_token
        self._current_token = self._scanner.next_token()
        return prev_token

# Evaluator

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
            assert False, f"Undefined variable: `{name}` @ assign."

    def get(self, name):
        if name in self._vals:
            return self._vals[name]
        elif self._parent is not None:
            return self._parent.get(name)
        else:
            assert False, f"Undefined variable: `{name}` @ get"

class Evaluator:
    def eval(self, expr, env):
        match expr:
            case None | bool(_) | int(_):
                return expr
            case str(name):
                return env.get(name)
            case ["func", params, body]:
                return ["func", params, body, env]
            case ["define", name, val]:
                return env.define(name, self.eval(val, env))
            case ["assign", name, val]:
                return env.assign(name, self.eval(val, env))
            case ["seq", *exprs]:
                return self._eval_seq(exprs, env)
            case ["if", cnd, thn, els]:
                return self._eval_if(cnd, thn, els, env)
            case [func, *args]:
                return self._apply(
                    self.eval(func, env),
                    [self.eval(arg, env) for arg in args])
            case unexpected:
                assert False, f"Unexpected expression: {unexpected} @ eval"

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

    def _apply(self, f_val, args_val):
        if callable(f_val):
            return f_val(*args_val)

        _, params, body, env = f_val
        new_env = Environment(env)
        for param, arg in zip(params, args_val):
            new_env.define(param, arg)
        return self.eval(body, new_env)

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

    def go(self, src):
        return Evaluator().eval(Parser(src).parse(), self._env)

if __name__ == "__main__":
    i = Interpreter()

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
