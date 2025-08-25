class VariableNotFoundError(Exception):
    def __init__(self, name):
        self._name = name

class Environment:
    def __init__(self, parent=None):
        self._parent = parent
        self._vals = {}

    def __repr__(self):
        def keys():
            if "__builtins__" in self._vals:
                return "__builtins__"
            else:
                return ", ".join([str(k) for k  in self._vals.keys()])

        if self._parent is None:
            return f"[{keys()}]"
        else:
            return f"[{keys()}] < {self._parent}"

    def __contains__(self, name):
        try:
            self.get(name)
            return True
        except VariableNotFoundError:
            return False

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

class Expander:
    def __init__(self, vm):
        self._vm = vm

        self._menv = Environment()
        self._menv.define("when", lambda cnd, body: ["if", cnd, body, None])
        self._menv.define("when2", lambda cnd, body: ["when", cnd, body])

    def __repr__(self):
        return f"Expander({self._menv})"

    def expand(self, expr):
        return self._expr(expr)

    def _expr(self, expr):
        match expr:
            case None | bool(_) |int(_):
                return expr
            case ["array", *elems]:
                return ["array"] + [self._expr(elem) for elem in elems]
            case ["func", params, body]:
                return ["func", params, self._expr(body)]
            case str(name):
                return expr
            case ["quote", elem]:
                return ["quote", elem]
            case ["quasiquote", elem]:
                return self._quasiquote(elem)
            case ["defmacro", name, params, body]:
                self._menv.define(name, ["macro", params, self._expr(body)])
                return None
            case ["define", name, val]:
                return ["define", name, self._expr(val)]
            case ["assign", name, val]:
                return ["assign", name, self._expr(val)]
            case ["seq", *exprs]:
                return ["seq"] + [self._expr(expr) for expr in exprs]
            case ["if", cnd, thn, els]:
                return ["if", self._expr(cnd), self._expr(thn), self._expr(els)]
            case ["letcc", name, body]:
                return ["letcc", name, self._expr(body)]
            case [op, *args] :
                if isinstance(op, str) and op in self._menv:
                    macro = self._menv.get(op)
                    return self._expr(self._macro(macro, args))
                else:
                    return [op] + [self._expr(arg) for arg in args]
            case unexpected:
                assert False, f"Unexpected expression: {unexpected}"

    def _quasiquote(self, expr):
        def _quote_elements(elems):
            arr = ["array"]
            for elem in elems:
                match elem:
                    case ["unquote_splicing", e]:
                        expanded = self._expr(e)
                        assert isinstance(expanded, list) and len(expanded) > 0, \
                            f"Cannot splice: {expanded}"
                        arr += expanded[1:]
                    case _:
                        arr += [self._quasiquote(elem)]
            return arr

        match expr:
            case ["unquote", elem]: return elem
            case [*elems]: return _quote_elements(elems)
            case elem: return ["quote", elem]

    def _macro(self, macro, args):
        match macro:
            case m if callable(m):
                return self._expr(m(*args))
            case ["macro", params, body]:
                self._vm._env = Environment(self._vm.env())
                for param, arg in zip(params, args):
                    self._vm._env.define(param, arg)
                code = Compiler().compile(body)
                self._vm.load(code)
                expanded = self._vm.execute()
                return expanded

class Compiler:
    def __init__(self):
        self._code = []

    def __repr__(self):
        return f"Compiler({self._code})"

    def compile(self, expr):
        self._expr(expr, False)
        self._code.append(["halt"])
        return self._code

    def _expr(self, expr, is_tail):
        match expr:
            case None | bool(_) |int(_):
                self._code.append(["const", expr])
            case ["array", *elems]:
                self._array(elems)
            case ["func", params, body]:
                self._func(params, body)
            case str(name):
                self._code.append(["get", name])
            case ["quote", elem]:
                self._code.append(["const", elem])
            case ["define", name, val]:
                self._expr(val, False)
                self._code.append(["def", name])
            case ["assign", name, val]:
                self._expr(val, False)
                self._code.append(["set", name])
            case ["seq", *exprs]:
                self._seq(exprs, is_tail)
            case ["if", cnd, thn, els]:
                self._if(cnd, thn, els, is_tail)
            case ["letcc", name, body]:
                self._letcc(name, body, is_tail)
            case [op, *args]:
                self._op(op, args, is_tail)
            case unexpected:
                assert False, f"Unexpected expression: {unexpected}"

    def _array(self, elems):
        for elem in elems: self._expr(elem, False)
        self._code.append(["array", len(elems)])

    def _func(self, params, body):
        skip_jump = self._current_addr()
        self._code.append(["jump", None])
        func_addr = self._current_addr()
        self._expr(body, True)
        self._code.append(["ret"])
        self._set_operand(skip_jump, self._current_addr())
        self._code.append(["func", func_addr, params])

    def _seq(self, exprs, is_tail):
        if len(exprs) == 0: return
        for expr in exprs[:-1]:
            self._expr(expr, False)
            self._code.append(["pop"])
        self._expr(exprs[-1], is_tail)

    def _if(self, cnd, thn, els, is_tail):
        self._expr(cnd, False)
        els_jump = self._current_addr()
        self._code.append(["jump_if_false", None])
        self._expr(thn, is_tail)
        end_jump = self._current_addr()
        self._code.append(["jump", None])
        self._set_operand(els_jump, self._current_addr())
        self._expr(els, is_tail)
        self._set_operand(end_jump, self._current_addr())

    def _letcc(self, name, body, is_tail):
        cont_jump = self._current_addr()
        self._code.append(["cc", None])
        self._func([name], body)
        if is_tail:
            self._code.append(["call_tail"])
        else:
            self._code.append(["call"])
        self._set_operand(cont_jump, self._current_addr())

    def _op(self, op, args, is_tail):
        for arg in args[-1::-1]:
            self._expr(arg, False)
        self._expr(op, False)
        if is_tail:
            self._code.append(["call_tail"])
        else:
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

    def __repr__(self):
        return f"VM({self._ncode}:{self._ip}, {self._env})"

    def env(self):
        return self._env

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
                case ["array", size]:
                    arr = [self._stack.pop() for _ in range(size)]
                    self._stack.append(list(reversed(arr)))
                case ["func", addr, params]:
                    self._stack.append(["closure", [self._ncode, addr], params, self._env])
                case ["cc", addr]:
                    self._stack.append(["cont",
                        [self._ncode, addr], self._env, self._stack[:], self._call_stack[:]])
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
                    self._call(False)
                    continue
                case ["call_tail"]:
                    self._call(True)
                    continue
                case ["ret"]:
                    [self._ncode, self._ip], self._env = self._call_stack.pop()
                    continue
                case unexpected:
                    assert False, f"Unexpected instruction: {unexpected}"
            self._ip += 1
        assert len(self._stack) == 1, f"Unused stack left: {self._stack}"
        return self._stack[0]

    def _call(self, is_tail):
        match self._stack.pop():
            case f if callable(f):
                f(self._stack)
                self._ip += 1
            case ["closure", [ncodes, addr], params, env]:
                args = [self._stack.pop() for _ in params]
                if not is_tail:
                    self._call_stack.append([[self._ncode, self._ip + 1], self._env])
                    if len(self._call_stack) > 1000:
                        assert False, "Call stack overflow"
                self._env = Environment(env)
                for param, val in zip(params, args):
                    self._env.define(param, val)
                self._ncode, self._ip = [ncodes, addr]
            case ["cont", [ncodes, addr], env, stack, call_stack]:
                val = self._stack.pop()
                self._ncode, self._ip = [ncodes, addr]
                self._env = env
                self._stack = stack[:]
                self._stack.append(val)
                self._call_stack = call_stack[:]
            case unexpected:
                assert False, f"Unexpected call: {unexpected}"

    def _load_builtins(self):
        builtins = {
            "__builtins__": None,
            "add": lambda s: s.append(s.pop() + s.pop()),
            "sub": lambda s: s.append(s.pop() - s.pop()),
            "equal": lambda s: s.append(s.pop() == s.pop()),
            "not_equal": lambda s: s.append(s.pop() != s.pop()),

            "print": lambda s: s.append(print(s.pop()))
        }

        for name, func in builtins.items():
            self._env.define(name, func)

        self._env = Environment(self._env)

class Interpreter:
    def __init__(self):
        self._vm = VM()

    def __repr__(self) -> str:
        return f"Interpreter({self._vm})"

    def go(self, expr):
        expanded = Expander(self._vm).expand(expr)
        code = Compiler().compile(expanded)
        self._vm.load(code)
        return self._vm.execute()

    def go_verbose(self, expr):
        print(f"\nSource:\n{expr}")
        expanded = Expander(self._vm).expand(expr)
        print(f"Expanded:\n{expanded}")
        code = Compiler().compile(expanded)
        print("Code:")
        for i, inst in enumerate(code):
            print(f"{i:3}: {inst}")
        print("Output:")
        self._vm.load(code)
        return self._vm.execute()

    def go_test(self, expr, expected):
        result = self.go_verbose(expr)
        print(f"Expected Result: {expected}")
        print(f"Actual Result  : {result}")
        assert expected == result

i = Interpreter()

i.go_test(None, None)
i.go_test(True, True)
i.go_test(False, False)
i.go_test(5, 5)

i.go_test(["add", 5, 6], 11)
i.go_test(["sub", 11, 5], 6)
i.go_test(["equal", 5, 5], True)
i.go_test(["equal", 5, 6], False)
i.go_test(["not_equal", 5, 5], False)
i.go_test(["not_equal", 5, 6], True)

i.go_test(["add", 5, ["add", 6, 7]], 18)

i.go_test(["if", ["equal", 5, 5], 6, 7], 6)
i.go_test(["if", ["equal", 5, 6], 7, 8], 8)
i.go_test(["if", ["equal", 5, 6], 7, ["if", ["equal", 8, 8], 9, 10]], 9)

i.go_test(["define", "a", ["add", 5, 6]], 11)
i.go_test("a", 11)
i.go_test(["assign", "a", ["sub", "a", 5]], 6)
i.go_test("a", 6)

i.go_verbose(["print", 5])

i.go_verbose(["seq", ["print", 5], ["print", 6]])
i.go_test(["seq", ["define", "x", 5], ["define", "y", 6], ["add", "x", "y"]], 11)

i.go_verbose(["define", "myadd", ["func", ["a", "b"], ["add", "a", "b"]]])
i.go_test(["myadd", 5, 6], 11)

i.go_verbose(["define", "fib", ["func", ["n"],
    ["if", ["equal", "n", 0], 0,
    ["if", ["equal", "n", 1], 1,
    ["add", ["fib", ["sub", "n", 1]], ["fib", ["sub", "n", 2]]]]]]])
i.go_test(["fib", 10], 55)

i.go_verbose(["seq",
    ["define", "make_counter", ["func", [], ["seq",
                ["define", "c", 0],
                ["func", [], ["assign", "c", ["add", "c", 1]]]]]],
    ["define", "counter1", ["make_counter"]],
    ["define", "counter2", ["make_counter"]]
])
i.go_verbose(["seq",
    ["print", ["counter1"]],
    ["print", ["counter1"]],
    ["print", ["counter2"]],
    ["print", ["counter2"]],
    ["print", ["counter1"]],
    ["print", ["counter2"]]
])

# tail call optimization test

i.go_verbose(["define", "loop_els", ["func", ["n"],
    ["if", ["equal", "n", 0], 0, ["loop_els", ["sub", "n", 1]]]
]])
i.go_test(["loop_els", 10000], 0)

i.go_verbose(["define", "loop_thn", ["func", ["n"],
    ["if", ["not_equal", "n", 0], ["loop_thn", ["sub", "n", 1]], 0]
]])
i.go_test(["loop_thn", 10000], 0)

i.go_verbose(["define", "loop_seq", ["func", ["n"],
    ["seq",
        ["add", 1, 1],
        ["if", ["equal", "n", 0], 0, ["loop_seq", ["sub", "n", 1]]]
    ]
]])
i.go_test(["loop_seq", 10000], 0)

i.go_verbose(["define", "loop_not_tail", ["func", ["n"],
    ["if", ["equal", "n", 0], 0, ["add", ["loop_not_tail", ["sub", "n", 1]], 1]]
]])
try:
    i.go_verbose(["loop_not_tail", 10000])
    assert False, "Should fail"
except AssertionError:
    print("AssertionError as expected")
i = Interpreter() # エラーが起きたのでInterpreterを初期化する

i.go_verbose(["define", "even", ["func", ["n"],
    ["if", ["equal", "n", 0], True, ["odd", ["sub", "n", 1]]]
]])
i.go_verbose(["define", "odd", ["func", ["n"],
    ["if", ["equal", "n", 0], False, ["even", ["sub", "n", 1]]]
]])
i.go_test(["even", 10000], True)
i.go_test(["even", 10001], False)
i.go_test(["odd", 10000], False)
i.go_test(["odd", 10001], True)

i.go_verbose(["define", "fib_tail", ["func", ["n"], ["seq",
    ["define", "rec", ["func", ["k", "a", "b"],
        ["if", ["equal", "k", "n"],
            "a",
            ["rec", ["add", "k", 1], "b", ["add", "a", "b"]]]
    ]],
    ["rec", 0, 0, 1]
]]])

i.go_test(["fib_tail", 10], 55)
i.go_verbose(["print", ["fib_tail", 10000]])

# letcc test

i.go_test(["letcc", "skip-to", ["add", 5, 6]], 11)
i.go_test(["letcc", "skip-to", ["add", ["skip-to", 5], 6]], 5)
i.go_test(["add", 5, ["letcc", "skip-to", ["skip-to", 6]]], 11)
i.go_test(["letcc", "skip1", ["add", ["skip1", ["letcc", "skip2", ["add", ["skip2", 5], 6]]], 7]], 5)

i.go_verbose(["define", "inner", ["func", ["raise"], ["raise", 5]]])
i.go_verbose(["define", "outer", ["func", [],
        [ "letcc", "raise", ["add", ["inner", "raise"], 6]]]])
i.go_test(["outer"], 5)

i.go_verbose(["define", "add5", None])
i.go_test(["add", 5, ["letcc", "cc", ["seq", ["assign", "add5", "cc"], 6]]], 11)
i.go_test(["add5", 7], 12)
i.go_test(["add5", 8], 13)

# array test

i.go_test(["array"], [])
i.go_test(["array", 5], [5])
i.go_test(["array", ["add", 5, 6], ["add", 7, 8]], [11, 15])

# quote test

i.go_test(["quote", 5], 5)
i.go_test(["quote", ["add", 5, 6]], ["add", 5, 6])

i.go_test(["quasiquote", 5], 5)
i.go_test(["quasiquote", ["add", 5, 6]], ["add", 5, 6])
i.go_test(["quasiquote", ["add", ["unquote", ["add", 5, 6]], 7]], ["add", 11, 7])
i.go_test(["quasiquote", ["add", ["unquote_splicing", ["array", 5, 6]]]], ["add", 5, 6])

# macro test

i.go_test(["when", ["equal", 5, 5], 6], 6)
i.go_test(["when", ["equal", 5, 6], "notdefinedvar"], None)
i.go_test(["add", 7, ["when", ["equal", 5, 5], 6]], 13)
i.go_test(["when2", ["equal", 5, 5], 6], 6)
i.go_test(["when2", ["equal", 5, 6], "notdefinedvar"], None)

i.go_test(["seq",
    ["defmacro", "foo", [], ["array", ["quote", "add"], 5, 6]],
    ["foo"]
], 11)

i.go_test(["seq",
    ["defmacro", "foo", ["a", "b"], ["quasiquote",
            ["add", ["unquote", "a"], ["unquote", "b"]]]],
    ["foo", ["sub", 8, 5], ["sub", 7, 6]]
], 4)

i.go_test(["seq",
    ["defmacro", "foo", [], ["quasiquote",
            ["add", ["unquote_splicing", ["array", 5, 6]]]]],
    ["foo"]
], 11)

i.go_test(["seq",
    ["defmacro", "foo", ["a", "b"], ["quasiquote",
            ["add", ["unquote_splicing", ["quasiquote",
                [["unquote", "a"], ["unquote", "b"]]]]]]],
    ["foo", ["sub", 8, 5], ["sub", 7, 6]]
], 4)

i.go_verbose(["define", "my_add", ["func", ["a", "b"], ["add", "a", "b"]]])
i.go_test(["seq",
    ["defmacro", "bar", ["a", "b"], ["my_add", "a", "b"]],
    ["bar", ["sub"], [7, 6]]
], 1)

