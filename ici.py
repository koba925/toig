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

