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
    def setup_env(self):
        self.go("""
            define := runc (env, name, val) do
                for p in env do
                    if p[0] == name then p[1] = val; return(val) end
                end;
                append(env, [name, val]);
                return(val)
            end
        """)

        self.go("""
            get := runc (env, name) do
                for p in env do
                    if p[0] == name then return(p[1]) end
                end;
                error('Not found:', name)
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
                elif expr[0] == 'define' then
                    define(env, expr[1], _eval(expr[2], env))
                elif expr[0] == 'if' then
                    if _eval(expr[1], env) then
                        _eval(expr[2], env)
                    else
                        _eval(expr[3], env)
                    end
                else
                    error('Unexpected expression: ', expr)
                end
            end
        """)

        self.go("""
            global_env := [];
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
