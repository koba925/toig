class Compiler:
    def __init__(self):
        self._code = []

    def compile(self, expr):
        self._expr(expr)
        return self._code

    def _expr(self, expr):
        match expr:
            case None | bool(_) |int(_):
                self._code.append(["const", expr])
            case [op, *args]:
                self._op(op, args)
            case unexpected:
                assert False, f"Unexpected expression: {unexpected}"

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

    def execute(self, code):
        for inst in code:
            match inst:
                case ["const", val]:
                    self._stack.append(val)
                case ["op", op]:
                    VM.ops[op](self._stack)
                case unexpected:
                    assert False, f"Unexpected instruction: {unexpected}"
        assert len(self._stack) == 1, "Unused stack left: {self.stack}"
        return self._stack[0]

def test_run(expr):
    vm = VM()
    print(f"Source:\n{expr}")
    code = Compiler().compile(expr)
    print("Code:")
    for i, inst in enumerate(code):
        print(f"{i:3}: {inst}")
    print(f"Result:\n{vm.execute(code)}\n")

test_run(None)
test_run(True)
test_run(False)
test_run(5)

test_run(["add", 5, 6])
test_run(["sub", 11, 5])
test_run(["equal", 5, 5])
test_run(["equal", 5, 6])

test_run(["add", 5, ["add", 6, 7]])
