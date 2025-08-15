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
        self._expr(expr, False)
        self._code.append(["halt"])
        return self._code

    def _expr(self, expr, is_tail):
        match expr:
            case None | bool(_) |int(_):
                self._code.append(["const", expr])
            case ["func", params, body]:
                self._func(params, body)
            case str(name):
                self._code.append(["get", name])
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
            "add": lambda s: s.append(s.pop() + s.pop()),
            "sub": lambda s: s.append(s.pop() - s.pop()),
            "equal": lambda s: s.append(s.pop() == s.pop()),
            "not_equal": lambda s: s.append(s.pop() != s.pop()),

            "print": lambda s: [print(s.pop()), s.append(None)]
        }

        for name, func in builtins.items():
            self._env.define(name, func)

        self._env = Environment(self._env)

def run(vm, expr):
    print(f"\nSource:\n{expr}")
    code = Compiler().compile(expr)
    print("Code:")
    for i, inst in enumerate(code):
        print(f"{i:3}: {inst}")
    print("Output:")
    vm.load(code)
    return vm.execute()

def test_run(vm, expr, expected):
    result = run(vm, expr)
    print(f"Expected Result: {expected}")
    print(f"Actual Result  : {result}")
    assert expected == result

vm = VM()

test_run(vm, None, None)
test_run(vm, True, True)
test_run(vm, False, False)
test_run(vm, 5, 5)

test_run(vm, ["add", 5, 6], 11)
test_run(vm, ["sub", 11, 5], 6)
test_run(vm, ["equal", 5, 5], True)
test_run(vm, ["equal", 5, 6], False)
test_run(vm, ["not_equal", 5, 5], False)
test_run(vm, ["not_equal", 5, 6], True)

test_run(vm, ["add", 5, ["add", 6, 7]], 18)

test_run(vm, ["if", ["equal", 5, 5], 6, 7], 6)
test_run(vm, ["if", ["equal", 5, 6], 7, 8], 8)
test_run(vm, ["if", ["equal", 5, 6], 7, ["if", ["equal", 8, 8], 9, 10]], 9)

test_run(vm, ["define", "a", ["add", 5, 6]], 11)
test_run(vm, "a", 11)
test_run(vm, ["assign", "a", ["sub", "a", 5]], 6)
test_run(vm, "a", 6)

run(vm, ["print", 5])

run(vm, ["seq", ["print", 5], ["print", 6]])
test_run(vm, ["seq", ["define", "x", 5], ["define", "y", 6], ["add", "x", "y"]], 11)

run(vm, ["define", "myadd", ["func", ["a", "b"], ["add", "a", "b"]]])
test_run(vm, ["myadd", 5, 6], 11)

run(vm, ["define", "fib", ["func", ["n"],
    ["if", ["equal", "n", 0], 0,
    ["if", ["equal", "n", 1], 1,
    ["add", ["fib", ["sub", "n", 1]], ["fib", ["sub", "n", 2]]]]]]])
test_run(vm, ["fib", 10], 55)

run(vm, ["seq",
    ["define", "make_counter", ["func", [], ["seq",
                ["define", "c", 0],
                ["func", [], ["assign", "c", ["add", "c", 1]]]]]],
    ["define", "counter1", ["make_counter"]],
    ["define", "counter2", ["make_counter"]]
])
run(vm, ["seq",
    ["print", ["counter1"]],
    ["print", ["counter1"]],
    ["print", ["counter2"]],
    ["print", ["counter2"]],
    ["print", ["counter1"]],
    ["print", ["counter2"]]
])

run(vm, ["define", "loop_els", ["func", ["n"],
    ["if", ["equal", "n", 0], 0, ["loop_els", ["sub", "n", 1]]]
]])
test_run(vm, ["loop_els", 10000], 0)

run(vm, ["define", "loop_thn", ["func", ["n"],
    ["if", ["not_equal", "n", 0], ["loop_thn", ["sub", "n", 1]], 0]
]])
test_run(vm, ["loop_thn", 10000], 0)

run(vm, ["define", "loop_seq", ["func", ["n"],
    ["seq",
        ["add", 1, 1],
        ["if", ["equal", "n", 0], 0, ["loop_seq", ["sub", "n", 1]]]
    ]
]])
test_run(vm, ["loop_seq", 10000], 0)

run(vm, ["define", "loop_not_tail", ["func", ["n"],
    ["if", ["equal", "n", 0], 0, ["add", ["loop_not_tail", ["sub", "n", 1]], 1]]
]])
try:
    run(vm, ["loop_not_tail", 10000])
    assert False, "Should fail"
except AssertionError:
    print("AssertionError as expected")

run(vm, ["define", "even", ["func", ["n"],
    ["if", ["equal", "n", 0], True, ["odd", ["sub", "n", 1]]]
]])
run(vm, ["define", "odd", ["func", ["n"],
    ["if", ["equal", "n", 0], False, ["even", ["sub", "n", 1]]]
]])
test_run(vm, ["even", 10000], True)
test_run(vm, ["even", 10001], False)
test_run(vm, ["odd", 10000], False)
test_run(vm, ["odd", 10001], True)

run(vm, ["define", "fib_tail", ["func", ["n"], ["seq",
    ["define", "rec", ["func", ["k", "a", "b"],
        ["if", ["equal", "k", "n"],
            "a",
            ["rec", ["add", "k", 1], "b", ["add", "a", "b"]]]
    ]],
    ["rec", 0, 0, 1]
]]])

test_run(vm, ["fib_tail", 10], 55)
run(vm, ["print", ["fib_tail", 10000]])

test_run(vm, ["letcc", "skip-to", ["add", 5, 6]], 11)
test_run(vm, ["letcc", "skip-to", ["add", ["skip-to", 5], 6]], 5)
test_run(vm, ["add", 5, ["letcc", "skip-to", ["skip-to", 6]]], 11)
test_run(vm, ["letcc", "skip1", ["add", ["skip1", ["letcc", "skip2", ["add", ["skip2", 5], 6]]], 7]], 5)

run(vm, ["define", "inner", ["func", ["raise"], ["raise", 5]]])
run(vm, ["define", "outer", ["func", [],
        [ "letcc", "raise", ["add", ["inner", "raise"], 6]]]])
test_run(vm, ["outer"], 5)

run(vm, ["define", "add5", None])
test_run(vm, ["add", 5, ["letcc", "cc", ["seq", ["assign", "add5", "cc"], 6]]], 11)
test_run(vm, ["add5", 7], 12)
test_run(vm, ["add5", 8], 13)
