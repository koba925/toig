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
            case unexpected:
                assert False, f"Unexpected expression: {unexpected}"

class VM:
    def __init__(self):
        self._stack = []

    def execute(self, code):
        for inst in code:
            match inst:
                case ["const", val]:
                    self._stack.append(val)
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

