from commons import CustomRules, is_name, is_name_first, is_name_rest

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
            rule = Parser(line[5:], CustomRules()).parse()
            assert isinstance(rule, list) and len(rule) >= 2, \
                f"Invalid rule: {rule} @ comment"
            self._custom_rules[rule[1]] = rule[2:]
        return self.next_token()

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
        return expr

    def parse_step(self):
        yield self._defmacro()
        while self._current_token == ";":
            self._advance()
            yield self._defmacro()
        assert self._current_token == "$EOF", \
            f"Unexpected token at end: `{self._current_token}` @ parse"

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
        exprs = [self._defmacro()]
        while self._current_token == ";":
            self._advance()
            exprs.append(self._defmacro())
        return exprs[0] if len(exprs) == 1 else ["seq"] + exprs

    def _defmacro(self):
        if self._current_token != "defmacro":
            return self._define_assign()
        self._advance()
        name = self._advance()
        self._consume("(")
        params = self._comma_separated_exprs(")")
        self._consume("do")
        body = self._expression()
        self._consume("end")
        return ["defmacro", name, params, body]

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
                self._advance()
                expr = self._expression()
                self._consume(")")
                return expr
            case "[":
                self._advance()
                elems = self._comma_separated_exprs("]")
                return ["array"] + elems
            case "func":
                self._advance(); return self._func()
            case "macro":
                self._advance(); return self._macro()
            case "if":
                self._advance(); return self._if()
            case "letcc":
                self._advance(); return self._letcc()
            case op if op in self._custom_rules:
                self._advance()
                return self._custom(self._custom_rules[op])
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
                    return  [["array"] + self._comma_separated_exprs(")")] + _custom(r[1:])
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
