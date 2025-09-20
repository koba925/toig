import pytest

from test_commons import BaseTest
from ici import Interpreter as ICI
from stm import Interpreter as STM

@pytest.mark.parametrize(
    "set_interpreter",
    [ICI, STM], ids=["ici", "stm"],
    indirect=True)
class TestEval(BaseTest):
    @pytest.fixture(autouse=True)
    def setup_eval(self):
        self.go("""
            define := runc (env, name, val) do
                for p in env[1] do
                    if p[0] == name then p[1] = val; return(val) end
                end;
                append(env[1], [name, val]);
                return(val)
            end
        """)

        self.go("""
            get := runc (env, name) do
                for p in env[1] do
                    if p[0] == name then return(p[1]) end
                end;
                if env[0] != None then
                    get(env[0], name)
                else
                    error('Not found:', name)
                end
            end
        """)

        self.go("""
            _eval := func (expr, env) do
                # print('eval', expr);
                if expr == None then
                    None
                elif is_bool(expr) or is_int(expr) then
                    expr
                elif is_str(expr) then
                    get(env, expr)
                elif expr[0] == 'func' then
                    ['closure', expr[1], expr[2], env]
                elif expr[0] == 'define' then
                    define(env, expr[1], _eval(expr[2], env))
                elif expr[0] == 'if' then
                    if _eval(expr[1], env) then
                        _eval(expr[2], env)
                    else
                        _eval(expr[3], env)
                    end
                else
                    op_val := _eval(expr[0], env);
                    args_val := map(expr[1:], func (arg) do _eval(arg, env) end);
                    apply(op_val, args_val)
                end
            end
        """)

        self.go("""
            apply := func (op_val, args_val) do
                if op_val[0] == 'primitive' then
                    op_val[1](args_val)
                else
                    env := [op_val[3], []];
                    for name_val in zip(op_val[1], args_val) do
                        define(env, name_val[0], name_val[1])
                    end;
                    _eval(op_val[2], env)
                end
            end
        """)

        self.go("""
            global_env := [None, [
                ['add', ['primitive', func (args) do args[0] + args[1] end]],
                ['sub', ['primitive', func (args) do args[0] - args[1] end]],
                ['equal', ['primitive', func (args) do args[0] == args[1] end]]
            ]];
            eval := func (expr) do _eval(expr, global_env) end
        """)

    def test_primary(self):
        assert self.go("eval(None)") == None
        assert self.go("eval(True)") == True
        assert self.go("eval(False)") == False
        assert self.go("eval(5)") == 5

    def test_if(self):
        assert self.go("eval(['if', True, 5, 6])") == 5
        assert self.go("eval(['if', False, 5, 6])") == 6
        assert self.go("eval(['if', ['if', True, True, True], 5, 6])") == 5
        assert self.go("eval(['if', True, ['if', True, 5, 6], 6])") == 5
        assert self.go("eval(['if', False, 5, ['if', False, 5, 6]])") == 6

        with pytest.raises(AssertionError):
            self.go("eval(['unexpected case'])")

    def test_define(self):
        assert self.go("eval(['define', 'a', 5])") == 5
        assert self.go("eval('a')") == 5
        assert self.go("eval(['define', 'b', 6])") == 6
        assert self.go("eval('b')") == 6
        assert self.go("eval(['define', 'b', 7])") == 7
        assert self.go("eval('b')") == 7

        with pytest.raises(AssertionError):
            self.go("eval('c')")

    def test_primitives(self):
        assert self.go("eval(['add', 5, 6])") == 11
        assert self.go("eval(['sub', 11, 6])") == 5
        assert self.go("eval(['equal', 5, 5])") == True
        assert self.go("eval(['equal', 5, 6])") == False

    def test_function(self):
        assert self.go("eval([['func', ['n'], ['add', 'n', 5]], 6])") == 11

    def test_fib(self):
        self.go("""eval(
            ['define', 'fib', ['func', ['n'],
                ['if', ['equal', 'n', 0], 0,
                ['if', ['equal', 'n', 1], 1,
                ['add', ['fib', ['sub', 'n', 1]], ['fib', ['sub', 'n', 2]]]]]]]
        )""")
        assert self.go("eval(['fib', 0])") == 0
        assert self.go("eval(['fib', 1])") == 1
        assert self.go("eval(['fib', 2])") == 1
        assert self.go("eval(['fib', 3])") == 2
        assert self.go("eval(['fib', 6])") == 8

    def test_adder(self):
        self.go("""eval(
            ['define', 'make_adder', ['func', ['n'],
                ['func', ['m'], ['add', 'n', 'm']]
            ]]
        )""")
        assert self.go("eval([['make_adder', 5], 6])") == 11


