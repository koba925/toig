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
            case str(name):
                self._code.append(["get", name])
            case ["define", name, val]:
                self._expr(val)
                self._code.append(["def", name])
            case ["assign", name, val]:
                self._expr(val)
                self._code.append(["set", name])
            case ["if", cnd, thn, els]:
                self._if(cnd, thn, els)
            case [op, *args]:
                self._op(op, args)
            case unexpected:
                assert False, f"Unexpected expression: {unexpected}"

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

    def _set_operand(self, ip, operand):
        self._code[ip][1] = operand

    def _current_addr(self):
        return len(self._code)

    def _op(self, op, args):
        for arg in args[-1::-1]:
            self._expr(arg)
        self._code.append(["op", op])

class VM:
    ops = {
        "add": lambda s: s.append(s.pop() + s.pop()),
        "sub": lambda s: s.append(s.pop() - s.pop()),
        "equal": lambda s: s.append(s.pop() == s.pop())
    }

    def __init__(self):
        self._stack = []
        self._ip = 0
        self._env = Environment()

    def execute(self, code):
        self._stack = []
        self._ip = 0
        while (inst := code[self._ip]) != ["halt"]:
            match inst:
                case ["const", val]:
                    self._stack.append(val)
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
                case ["op", op]:
                    VM.ops[op](self._stack)
                case unexpected:
                    assert False, f"Unexpected instruction: {unexpected}"
            self._ip += 1
        assert len(self._stack) == 1, "Unused stack left: {self.stack}"
        return self._stack[0]

def test_run(vm, expr, expected):
    print(f"Source:\n{expr}")
    code = Compiler().compile(expr)
    print("Code:")
    for i, inst in enumerate(code):
        print(f"{i:3}: {inst}")
    print(f"Expected Result: {expected}")
    result = vm.execute(code)
    print(f"Actual Result  : {result}\n")
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
