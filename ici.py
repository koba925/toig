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

    def execute(self, code):
        while (inst := code[self._ip]) != ["halt"]:
            match inst:
                case ["const", val]:
                    self._stack.append(val)
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

def test_run(expr, expected):
    vm = VM()
    print(f"Source:\n{expr}")
    code = Compiler().compile(expr)
    print("Code:")
    for i, inst in enumerate(code):
        print(f"{i:3}: {inst}")
    print(f"Expected Result: {expected}")
    result = vm.execute(code)
    print(f"Actual Result  : {result}\n")
    assert expected == result

test_run(None, None)
test_run(True, True)
test_run(False, False)
test_run(5, 5)

test_run(["add", 5, 6], 11)
test_run(["sub", 11, 5], 6)
test_run(["equal", 5, 5], True)
test_run(["equal", 5, 6], False)

test_run(["add", 5, ["add", 6, 7]], 18)

test_run(["if", ["equal", 5, 5], 6, 7], 6)
test_run(["if", ["equal", 5, 6], 7, 8], 8)
test_run(["if", ["equal", 5, 6], 7, ["if", ["equal", 8, 8], 9, 10]], 9)

