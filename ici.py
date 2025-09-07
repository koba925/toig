from toig_environment import Environment
from ici_evaluator import Expander, Compiler, VM

# Builtins

def _get_at(_, s):
    arr = s.pop(); index = s.pop(); s.append(arr[index])

def _set_at(_, s):
    arr = s.pop(); index = s.pop(); val = s.pop()
    arr[index] = val
    s.append(val)

def _slice(_, s):
    arr = s.pop(); start = s.pop(); end = s.pop(); step = s.pop()
    s.append(arr[slice(start, end, step)])

def _set_slice(_, s):
    arr = s.pop(); start = s.pop(); end = s.pop(); step = s.pop(); val = s.pop()
    arr[start:end:step] = val
    s.append(val)

def _error(n, s):
    assert False, f"{' '.join(map(str, [s.pop() for _ in range(n)]))}"

_builtins = {
    "__builtins__": None,
    "add": lambda _, s: s.append(s.pop() + s.pop()),
    "sub": lambda _, s: s.append(s.pop() - s.pop()),
    "mul": lambda _, s: s.append(s.pop() * s.pop()),
    "div": lambda _, s: s.append(s.pop() // s.pop()),
    "mod": lambda _, s: s.append(s.pop() % s.pop()),
    "neg": lambda _, s: s.append(-s.pop()),

    "equal": lambda _, s: s.append(s.pop() == s.pop()),
    "not_equal": lambda _, s: s.append(s.pop() != s.pop()),
    "less": lambda _, s: s.append(s.pop() < s.pop()),
    "greater": lambda _, s: s.append(s.pop() > s.pop()),
    "less_equal": lambda _, s: s.append(s.pop() <= s.pop()),
    "greater_equal": lambda _, s: s.append(s.pop() >= s.pop()),
    "not": lambda _, s: s.append(not s.pop()),

    "array": lambda n, s: s.append([s.pop() for _ in range(n)]),
    "is_array": lambda _, s: s.append(isinstance(s.pop(), list)),
    "len": lambda _, s: s.append(len(s.pop())),
    "get_at": _get_at,
    "set_at": _set_at,
    "slice": _slice,
    "set_slice": _set_slice,

    "is_name": lambda _, s: s.append(isinstance(s.pop(), str)),

    "print": lambda n, s: s.append(print(*[s.pop() for _ in range(n)])),
    "error": _error
}

class Builtins:
    @staticmethod
    def load(env):
        for name, func in _builtins.items():
            env.define(name, func)

class Interpreter:
    def __init__(self):
        self._env = Environment()
        self._vm = VM(self._env)
        Builtins.load(self._env)
        self._vm.new_scope()

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

# temporal test

# exit()

# basic test

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
i.go_test(["define", "a", ["array", 5, 6, 7]], [5, 6, 7])
i.go_test(["assign", ["get_at","a", 1], 8], 8)
i.go_test("a", [5, 8, 7])
i.go_test(["assign", ["slice","a", 1, 3, None], ["array", 2, 3, 4]], [2, 3, 4])
i.go_test("a", [5, 2, 3, 4])

# quote test

i.go_test(["quote", 5], 5)
i.go_test(["quote", ["add", 5, 6]], ["add", 5, 6])

i.go_test(["quasiquote", 5], 5)
i.go_test(["quasiquote", ["add", 5, 6]], ["add", 5, 6])
i.go_test(["quasiquote", ["add", ["unquote", ["add", 5, 6]], 7]], ["add", 11, 7])
i.go_test(["quasiquote", ["add", ["unquote_splicing", ["array", 5, 6]]]], ["add", 5, 6])

i.go_verbose(["define", "my_array", ["func", [], ["array", 5, 6]]])
i.go_test(["quasiquote", ["add", ["unquote_splicing", ["my_array"]]]], ["add", 5, 6])

# macro test

i.go_verbose(["defmacro", "when", ["cnd", "body"], ["quasiquote",
    ["if", ["unquote", "cnd"], ["unquote", "body"], None]
]])
i.go_verbose(["defmacro", "when2", ["cnd", "body"], ["quasiquote",
    ["when", ["unquote", "cnd"], ["unquote", "body"]]
]])

i.go_test(["when", ["equal", 5, 5], 6], 6)
i.go_test(["when", ["equal", 5, 6], "notdefinedvar"], None)
i.go_test(["add", 7, ["when", ["equal", 5, 5], 6]], 13)
i.go_test(["when2", ["equal", 5, 5], 6], 6)
i.go_test(["when2", ["equal", 5, 6], "notdefinedvar"], None)

i.go_verbose(["defmacro", "foo", [], ["array", ["quote", "add"], 5, 6]])
i.go_test(["foo"], 11)

i.go_verbose(["defmacro", "foo", ["a", "b"], ["quasiquote",
    ["add", ["unquote", "a"], ["unquote", "b"]]
]])
i.go_test(["foo", ["sub", 8, 5], ["sub", 7, 6]], 4)

i.go_verbose(["defmacro", "foo", [], ["quasiquote",
    ["add", ["unquote_splicing", ["array", 5, 6]]]
]])
i.go_test(["foo"], 11)

i.go_verbose(["defmacro", "foo", ["a", "b"], ["quasiquote",
    ["add", ["unquote_splicing", ["quasiquote",
        [["unquote", "a"], ["unquote", "b"]]
    ]]]
]])
i.go_test(["foo", ["sub", 8, 5], ["sub", 7, 6]], 4)

i.go_verbose(["define", "my_add", ["func", ["a", "b"], ["add", "a", "b"]]])
i.go_verbose(["defmacro", "bar", ["a", "b"], ["my_add", "a", "b"]])
i.go_test(["bar", ["sub"], [7, 6]], 1)

# macro test (let)

i.go_verbose(["define", "first", ["func", ["l"], ["get_at", "l", 0]]])
i.go_verbose(["define", "rest", ["func", ["l"], ["slice", "l", 1, None, None]]])
i.go_verbose(["define", "last", ["func", ["l"], ["get_at", "l", -1]]])

i.go_verbose(["define", "append", ["func", ["l", "a"], ["add", "l", ["array", "a"]]]])

i.go_verbose(["define", "foldl", ["func", ["l", "f", "init"],
    ["if", ["equal", "l", ["array"]],
        "init",
        ["foldl", ["rest", "l"], "f", ["f", "init", ["first", "l"]]]]]])

i.go_verbose(["define", "map", ["func", ["l", "f"],
    ["foldl", "l", ["func", ["acc", "e"], ["append", "acc", ["f", "e"]]], ["array"]]]])

i.go_verbose(["defmacro", "scope", ["body"],
    ["quasiquote", [["func", [], ["unquote", "body"]]]]])

i.go_verbose(["defmacro", "let", ["bindings", "body"], ["seq",
    ["define", "defines", ["func", ["bindings"],
        ["map", "bindings", ["func", ["b"], ["quasiquote",
            ["define",
                ["unquote", ["first", "b"]],
                ["unquote", ["last", "b"]]]]]]]],
    ["quasiquote", ["scope", ["seq",
        ["unquote_splicing", ["defines", "bindings"]],
        ["unquote","body"]]]]]])

i.go_test(["let", [["a", 5], ["b", 6]], ["add", "a", "b"]], 11)

# variable lenghth parameters test

i.go_test([["func", [["*", "rest"]], "rest"]], [])
i.go_test([["func", ["a", ["*", "rest"]], ["array", "a", "rest"]], 5], [5, []])
i.go_test([["func", ["a", ["*", "rest"]], ["array", "a", "rest"]], 5, 6], [5, [6]])
i.go_test([["func", ["a", ["*", "rest"]], ["array", "a", "rest"]], 5, 6, 7], [5, [6, 7]])

i.go_test([["func", [["*", "args"], "a"], ["array", "args", "a"]], 5], [[], 5])
i.go_test([["func", [["*", "args"], "a"], ["array", "args", "a"]], 5, 6], [[5], 6])
i.go_test([["func", [["*", "args"], "a"], ["array", "args", "a"]], 5, 6, 7], [[5, 6], 7])
i.go_test([["func", [["*", "args"], "a", "b"], ["array", "args", "a", "b"]], 5, 6, 7], [[5], 6, 7])
i.go_test([["func", ["a", ["*", "args"], "b"], ["array", "a", "args", "b"]], 5, 6, 7], [5, [6], 7])
i.go_test([["func", ["a", "b", ["*", "args"]], ["array", "a", "b", "args"]], 5, 6, 7], [5, 6, [7]])

i.go(["defmacro", "rest_param", ["a", ["*", "rest"]], ["quasiquote",
    ["array", ["quote", ["unquote", "a"]], ["quote", ["unquote", "rest"]]]
]])
i.go_test(["rest_param", ["add", 5, 1]],
          [["add", 5, 1], []])
i.go_test(["rest_param", ["add", 5, 1], ["add", 6, 1], ["add", 7, 1]],
          [["add", 5, 1], [["add", 6, 1], ["add", 7, 1]]])
