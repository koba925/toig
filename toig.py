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

class VariableNotFoundError(Exception):
    def __init__(self, name):
        self._name = name

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
            raise VariableNotFoundError(name)

    def get(self, name):
        if name in self._vals:
            return self._vals[name]
        elif self._parent is not None:
            return self._parent.get(name)
        else:
            raise VariableNotFoundError(name)

class Compiler:
    def __init__(self):
        self._code = []

    def compile(self, expr):
        self._expr(expr)
        self._code.append(["halt"])
        return self._code

    def _expr(self, expr):
        match expr:
            case None | bool(_) |int(_):
                self._code.append(["const", expr])
            case ["func", params, body]:
                self._func(params, body)
            case str(name):
                self._code.append(["get", name])
            case ["define", name, val]:
                self._expr(val)
                self._code.append(["def", name])
            case ["assign", name, val]:
                self._expr(val)
                self._code.append(["set", name])
            case ["seq", *exprs]:
                self._seq(exprs)
            case ["if", cnd, thn, els]:
                self._if(cnd, thn, els)
            case [op, *args]:
                self._op(op, args)
            case unexpected:
                assert False, f"Unexpected expression: {unexpected}"

    def _func(self, params, body):
        skip_jump = self._current_addr()
        self._code.append(["jump", None])
        func_addr = self._current_addr()
        self._expr(body)
        self._code.append(["ret"])
        self._set_operand(skip_jump, self._current_addr())
        self._code.append(["func", func_addr, params])

    def _seq(self, exprs):
        for expr in exprs:
            self._expr(expr)
            if expr is not exprs[-1]:
                self._code.append(["pop"])

    def _if(self, cnd, thn, els):
            self._expr(cnd)
            els_jump = self._current_addr()
            self._code.append(["jump_if_false", None])
            self._expr(thn)
            end_jump = self._current_addr()
            self._code.append(["jump", None])
            self._set_operand(els_jump, self._current_addr())
            self._expr(els)
            self._set_operand(end_jump, self._current_addr())

    def _op(self, op, args):
        for arg in args[-1::-1]:
            self._expr(arg)
        self._expr(op)
        self._code.append(["call"])

    def _set_operand(self, ip, operand):
        self._code[ip][1] = operand

    def _current_addr(self):
        return len(self._code)

class VM:
    def __init__(self):
        self._codes = []
        self._stack = []
        self._call_stack = []
        self._ncode = 0
        self._ip = 0
        self._env = Environment()
        self._load_builtins()

    def load(self, code):
        self._codes.append(code)

    def execute(self):
        self._stack = []
        self._call_stack = []
        self._ncode = len(self._codes) - 1
        self._ip = 0
        while (inst := self._codes[self._ncode][self._ip]) != ["halt"]:
            match inst:
                case ["const", val]:
                    self._stack.append(val)
                case ["func", addr, params]:
                    self._stack.append(["closure", [self._ncode, addr], params, self._env])
                case ["pop"]:
                    self._stack.pop()
                case ["def", name]:
                    self._env.define(name, self._stack[-1])
                case ["set", name]:
                    self._env.assign(name, self._stack[-1])
                case ["get", name]:
                    self._stack.append(self._env.get(name))
                case ["jump", addr]:
                    self._ip = addr
                    continue
                case ["jump_if_false", addr]:
                    if not self._stack.pop():
                        self._ip = addr
                        continue
                case ["call"]:
                    self._call()
                    continue
                case ["ret"]:
                    [self._ncode, self._ip], self._env = self._call_stack.pop()
                    continue
                case unexpected:
                    assert False, f"Unexpected instruction: {unexpected}"
            self._ip += 1
        assert len(self._stack) == 1, f"Unused stack left: {self._stack}"
        return self._stack[0]

    def _call(self):
        match self._stack.pop():
            case f if callable(f):
                f(self._stack)
                self._ip += 1
            case ["closure", [ncodes, addr], params, env]:
                args = [self._stack.pop() for _ in params]
                self._call_stack.append([[self._ncode, self._ip + 1], self._env])
                self._env = Environment(env)
                for param, val in zip(params, args):
                    self._env.define(param, val)
                self._ncode, self._ip = [ncodes, addr]
            case unexpected:
                assert False, f"Unexpected call: {unexpected}"

    def _load_builtins(self):
        builtins = {
            "add": lambda s: s.append(s.pop() + s.pop()),
            "sub": lambda s: s.append(s.pop() - s.pop()),
            "equal": lambda s: s.append(s.pop() == s.pop()),

            "print": lambda s: [print(s.pop()), s.append(None)]
        }

        for name, func in builtins.items():
            self._env.define(name, func)

        self._env = Environment(self._env)

class Interpreter:
    def __init__(self):
        self._vm = VM()

    def go(self, src):
        ast = Parser(src).parse()
        code = Compiler().compile(ast)
        self._vm.load(code)
        return self._vm.execute()

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
