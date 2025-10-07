import pytest

from test_commons import BaseTest
from ici import Interpreter as ICI
from stm import Interpreter as STM

@pytest.mark.parametrize(
    "set_interpreter",
    [ICI, STM], ids=["ici", "stm"],
    indirect=True)
class TestCore(BaseTest):
    def test_comment(self):
        assert self.go("5 # 6") == 5
        assert self.go("\n5 # 6\n") == 5
        assert self.go("# 5\n6") == 6

    def test_primary(self):
        assert self.go("None") is None
        assert self.go("5") == 5
        assert self.go("True") is True
        assert self.go("False") is False

    def test_define(self):
        assert self.go("x := 5") == 5
        assert self.go("x") == 5
        assert self.go("y := z := 6") == 6
        assert self.go("y") == 6
        assert self.go("z") == 6
        with pytest.raises(AssertionError):
            self.go("6 := 5")

    def test_assign(self):
        assert self.go("x := y := 5") == 5
        assert self.go("x = 6") == 6
        assert self.go("x") == 6
        assert self.go("x = y = 7") == 7
        assert self.go("x") == 7
        assert self.go("y") == 7
        with pytest.raises(AssertionError):
            self.go("z = 5")
        with pytest.raises(AssertionError):
            self.go("6 = 5")

    def test_scope(self, capsys):
        self.go("x := 5; scope x := 6; print(x) end; print(x)")
        assert capsys.readouterr().out == "6\n5\n"

        self.go("x := 5; scope x = 6; print(x) end; print(x)")
        assert capsys.readouterr().out == "6\n6\n"

        with pytest.raises(AssertionError):
            self.go("scope y := 5 end; print(y)")

    def test_sequence(self):
        assert self.go("x := 5; y := 6; x + y") == 11
        assert self.go("x") == 5
        assert self.go("y") == 6
        assert self.go("x = 6; y = 7; x * y") == 42
        assert self.go("x") == 6
        assert self.go("y") == 7
        with pytest.raises(AssertionError):
            self.go(";")

    def test_or(self):
        assert self.go("5 == 5 or 5 == 5") is True
        assert self.go("5 == 5 or 5 != 5") is True
        assert self.go("5 != 5 or 5 == 5") is True
        assert self.go("5 != 5 or 5 != 5") is False

        assert self.go("5 or x") == 5
        assert self.go("False or 5") == 5

        assert self.go("False or False or True") is True
        assert self.go("False or False or False") is False

        assert self.go("x := True or False") is True
        assert self.go("x") is True

    def test_and(self):
        assert self.go("5 == 5 and 5 == 5") is True
        assert self.go("5 == 5 and 5 != 5") is False
        assert self.go("5 != 5 and 5 == 5") is False
        assert self.go("5 != 5 and 5 != 5") is False

        assert self.go("True and 5") == 5
        assert self.go("0 and x") == 0

        assert self.go("True or True and False") is True
        assert self.go("(True or True) and False") is False

    def test_not(self):
        assert self.go("not 5 == 5") is False
        assert self.go("not 5 != 5") is True

        assert self.go("not True and False") is False
        assert self.go("not (True and False)") is True

        assert self.go("not not True") is True

    def test_comparison(self):
        assert self.go("5 + 8 == 6 + 7") is True
        assert self.go("5 + 6 == 6 + 7") is False
        assert self.go("5 + 8 != 6 + 7") is False
        assert self.go("5 + 6 != 6 + 7") is True

        assert self.go("5 + 7 < 6 + 7") is True
        assert self.go("5 + 8 < 6 + 7") is False
        assert self.go("5 + 8 < 5 + 7") is False
        assert self.go("5 + 7 > 6 + 7") is False
        assert self.go("5 + 8 > 6 + 7") is False
        assert self.go("5 + 8 > 5 + 7") is True

        assert self.go("5 + 7 <= 6 + 7") is True
        assert self.go("5 + 8 <= 6 + 7") is True
        assert self.go("5 + 8 <= 5 + 7") is False
        assert self.go("5 + 7 >= 6 + 7") is False
        assert self.go("5 + 8 >= 6 + 7") is True
        assert self.go("5 + 8 >= 5 + 7") is True

        assert self.go("5 == 5 == True") is True

        assert self.go("not 5 == 6") is True
        assert self.go("(not 5) == 6") is False

    def test_add_sub(self):
        assert self.go("5 + 6 + 7") == 18
        assert self.go("18 - 6 - 7") == 5
        assert self.go("x := 5 + 6") == 11
        assert self.go("x") == 11

    def test_mul_div_mod(self):
        assert self.go("5 * 6 * 7") == 210
        assert self.go("210 / 6 / 7") == 5
        assert self.go("216 / 6 % 7") == 1
        assert self.go("5 + 6 * 7") == 47
        assert self.go("5 * 6 + 7") == 37

    def test_neg(self):
        assert self.go("-5") == -5
        assert self.go("-5 * 6") == -30
        assert self.go("5 * -6") == -30

    def test_call(self):
        assert self.go("add(5; 6, 7; 8)") == 14
        assert self.go("inc(5; 6)") == 7
        assert self.go("and(True, False)") is False
        with pytest.raises(AssertionError):
            self.go("inc(5")
        with pytest.raises(AssertionError):
            self.go("inc(5 6)")

    def test_print(self, capsys):
        self.go("print(None)")
        assert capsys.readouterr().out == "None\n"
        self.go("print(5)")
        assert capsys.readouterr().out == "5\n"
        self.go("print(True)")
        assert capsys.readouterr().out == "True\n"
        self.go("print(False)")
        assert capsys.readouterr().out == "False\n"
        self.go("print()")
        assert capsys.readouterr().out == "\n"
        self.go("print(5, 6)")
        assert capsys.readouterr().out == "5 6\n"

    def test_paren(self):
        assert self.go("(5; 6) * 7") == 42
        assert self.go("5 * (6; 7)") == 35
        assert self.go("(5) + 6") == 11
        with pytest.raises(AssertionError):
            self.go("(5")

    def test_array_by_builtins(self):
        assert self.go("array()") == []
        assert self.go("array(5; 6)") == [6]
        assert self.go("array(5; 6, 7; 8)") == [6, 8]
        assert self.go("is_array(array())")
        assert not self.go("is_array(1)")
        assert self.go("len(array(5, 6, 7))") == 3
        assert self.go("get_at(array(5, 6, 7), 1)") == 6
        assert self.go("set_at(array(5, 6, 7), 1, 8)") == 8
        assert self.go("slice(array(5, 6, 7), 1, 2, None)") == [6]

    def test_array_literal(self):
        assert self.go("[]") == []
        assert self.go("[5; 6]") == [6]
        assert self.go("[5; 6, 7; 8]") == [6, 8]

    def test_is_array(self):
        assert self.go("is_array([])")
        assert not self.go("is_array(1)")

    def test_array_len(self):
        assert self.go("len([5, 6, 7])") == 3

    def test_array_index_slice(self):
        self.go("a := [5, 6, 7, 8, 9]")
        with pytest.raises(AssertionError):
            self.go("a[]")
        assert self.go("a[1]") == 6
        assert self.go("a[:]") == [5, 6, 7, 8, 9]
        with pytest.raises(AssertionError):
            self.go("a[1,]")
        assert self.go("a[1:]") == [6, 7, 8, 9]
        assert self.go("a[1:4]") == [6, 7, 8]
        assert self.go("a[:4]") == [5, 6, 7, 8]
        with pytest.raises(AssertionError):
            self.go("a[1:2,]")
        assert self.go("a[3:1:-1]") == [8, 7]
        assert self.go("a[:1:-1]") == [9, 8, 7]
        assert self.go("a[3::-1]") == [8, 7, 6, 5]
        assert self.go("a[1:4:]") == [6, 7, 8]
        assert self.go("a[::-1]") == [9, 8, 7, 6, 5]
        assert self.go("a[:3:]") == [5, 6, 7]
        assert self.go("a[1::]") == [6, 7, 8, 9]
        assert self.go("a[::]") == [5, 6, 7, 8, 9]
        with pytest.raises(AssertionError):
            self.go("a[1:2:3,")

        assert self.go("a[0;3:0;1:0;-1]") == [8, 7]

        assert self.go("[[5, 6, 7], [15, 16, 17], [25, 26, 27]][1]") == [15, 16, 17]
        assert self.go("[[5, 6, 7], [15, 16, 17], [25, 26, 27]][1][2]") == 17
        assert self.go("[add, sub][0](5, 6)") == 11
        assert self.go("func (a, b) do [a, b] end (5, 6)[1]") == 6

    def test_array_set(self):
        self.go("a := [5, 6, 7, 8, 9]")
        assert self.go("a[0; 1] = True or False") is True
        assert self.go("a") == [5, True, 7, 8, 9]
        assert self.go("a[3:] = [10, 11]") == [10, 11]
        assert self.go("a") == [5, True, 7, 10, 11]
        self.go("a[1:4] = [12, 13, 14]")
        assert self.go("a") == [5, 12, 13, 14, 11]
        self.go("a[:2] = [15, 16]")
        assert self.go("a") == [15, 16, 13, 14, 11]
        self.go("a[3:1:-1] = [17, 18]")
        assert self.go("a") == [15, 16, 18, 17, 11]

        self.go("a := [[5, 6, 7], [15, 16, 17], [25, 26, 27]]")
        assert self.go("a[1] = []") == []
        assert self.go("a") == [[5, 6, 7], [], [25, 26, 27]]
        assert self.go("a[0][2] = 8") == 8
        assert self.go("a") == [[5, 6, 8], [], [25, 26, 27]]

        with pytest.raises(AssertionError):
            self.go("5 + 6 = 7")

    def test_raw_string(self):
        assert self.go(""" ')' """) == ')'
        assert self.go(""" 'not' """) == 'not'

    def test_string(self, capsys):
        assert self.go(""" "hello, world" """) == "hello, world"

        assert self.go(""" "hello, " + "world" """) == "hello, world"
        assert self.go(""" "hello" * 3""") == "hellohellohello"

        assert self.go(""" "hello" == "hello" """) == True
        assert self.go(""" "Hello" > "hello" """) == False
        assert self.go(""" "Hello" < "hello" """) == True

        assert self.go(""" "hello"[1]""") == "e"
        assert self.go(""" "hello"[1:4:2]""") == "el"

        self.go("""print("hello, world")""")
        assert capsys.readouterr().out == "hello, world\n"

        with pytest.raises(AssertionError):
            self.go("""print("hello, world)""")


    def test_string_escape(self, capsys):
        assert self.go(r""" "\n" """) == "\n"
        assert self.go(r""" "\\" """) == "\\"
        assert self.go(r""" "\'" """) == "'"
        assert self.go(r""" "\a" """) == "a"
        assert self.go(r"""if 1 != "\'" then 1 else 2 end""") == 1

    def test_type(self):
        assert self.go(r"""is_bool(None)""") == False
        assert self.go(r"""is_int(None)""") == False
        assert self.go(r"""is_str(None)""") == False
        assert self.go(r"""is_bool(5)""") == False
        assert self.go(r"""is_int(5)""") == True
        assert self.go(r"""is_str(5)""") == False
        assert self.go(r"""is_bool(True)""") == True
        assert self.go(r"""is_int(True)""") == False
        assert self.go(r"""is_str(True)""") == False
        assert self.go(r"""is_bool("hello")""") == False
        assert self.go(r"""is_int("hello")""") == False
        assert self.go(r"""is_str("hello")""") == True

    def test_func(self):
        assert self.go("func (a, b) do a + b end (5, 6)") == 11
        assert self.go("func (*args) do args end ()") == []
        assert self.go("func (*args) do args end (5)") == [5]
        assert self.go("func (*args) do args end (5, 6)") == [5, 6]
        assert self.go("func (*(args)) do args end (5, 6)") == [5, 6]

        assert self.go("func (*args, a) do [args, a] end (5)") == [[], 5]
        assert self.go("func (*args, a) do [args, a] end (5, 6)") == [[5], 6]
        assert self.go("func (*args, a) do [args, a] end (5, 6, 7)") == [[5, 6], 7]
        assert self.go("func (*args, a, b) do [args, a, b] end (5, 6, 7)") == [[5], 6, 7]
        assert self.go("func (a, *args, b) do [a, args, b] end (5, 6, 7)") == [5, [6], 7]
        assert self.go("func (a, b, *args) do [a, b, args] end (5, 6, 7)") == [5, 6, [7]]

        with pytest.raises(AssertionError):
            self.go("*a")
        with pytest.raises(AssertionError):
            self.go("func (a, b) a + b end")
        with pytest.raises(AssertionError):
            self.go("func (a, b) do a + b")
        with pytest.raises(AssertionError):
            self.go("func a, b) do a + b end (5, 6)")
        with pytest.raises(AssertionError):
            self.go("func (a, b do a + b end (5, 6)")
        with pytest.raises(AssertionError):
            self.go("func (a b) do a + b end (5, 6)")
        with pytest.raises(AssertionError):
            self.go("func (a, b + c) do a + b end (5, 6)")
        with pytest.raises(AssertionError):
            self.go("func (a, b) do a + b end (5) do 6")
        with pytest.raises(AssertionError):
            self.go("func (a, b) do a + b end (5) 6 end")

        with pytest.raises(AssertionError):
            self.go("func (*args, a) do [args, a] end ()")

    def test_closure_adder(self):
        self.go("make_adder := func (n) do func (m) do n + m end end")
        assert self.go("make_adder(5)(6)") == 11

    def test_closure_counter(self):
        self.go("""
            make_counter := func () do c := 0; func() do c = c + 1 end end;
            counter1 := make_counter();
            counter2 := make_counter()
        """)
        assert self.go("counter1()") == 1
        assert self.go("counter1()") == 2
        assert self.go("counter2()") == 1
        assert self.go("counter2()") == 2
        assert self.go("counter1()") == 3
        assert self.go("counter2()") == 3

    def test_quote(self):
        assert self.go("quote(5)") == 5
        assert self.go("quote(None)") is None
        assert self.go("quote(foo)") == "foo"
        assert self.go("quote([5, 6])") == ["array", 5, 6]
        assert self.go("quote(add(5, 6))") == ["add", 5, 6]
        assert self.go("quote(5 + 6)") == ["add", 5, 6]

    def test_quasiquote(self):
        assert self.go("quasiquote 5 end") == 5
        assert self.go("quasiquote None end") is None
        assert self.go("quasiquote foo end") == "foo"
        assert self.go("quasiquote [5, 6] end") == ["array", 5, 6]
        assert self.go("quasiquote add(5, 6) end") == ["add", 5, 6]
        assert self.go("quasiquote 5 + 6 end") == ["add", 5, 6]

        assert self.go("quasiquote unquote(add(5, 6)) end") == 11
        assert self.go("quasiquote add(5, unquote(6 ; 7)) end") == ["add", 5, 7]
        assert self.go("quasiquote unquote(5 + 6) end") == 11
        assert self.go("quasiquote 5 + unquote(6; 7) end") == ["add", 5, 7]
        assert self.go("quasiquote add(unquote_splicing([5, 6])) end") == ["add", 5, 6]
        assert self.go("quasiquote add(5, unquote_splicing([6])) end") == ["add", 5, 6]
        assert self.go("quasiquote unquote(when False do 5 end) end") is None
        assert self.go("quasiquote if a == 5 then 6; 7 else unquote(8; 9) end end") == ["if", ["equal", "a", 5], ["seq", 6, 7], 9]

    def test_defmacro(self):
        self.go("defmacro foo () do quote(abc) end")
        assert self.expanded("foo()") == "abc"

        self.go("""
            defmacro sq (a) do quasiquote unquote(a) * unquote(a) end end
        """)
        assert self.expanded("sq(5 + 6)") == ["mul", ["add", 5, 6], ["add", 5, 6]]

        self.go("""
            defmacro build_exp (op, *r) do quasiquote
                unquote(op)(unquote_splicing(r))
            end end
        """)
        assert self.expanded("build_exp(add)") == ["add"]
        assert self.expanded("build_exp(add, 5)") == ["add", 5]
        assert self.expanded("build_exp(add, 5, 6)") == ["add", 5, 6]

        self.go("""
            defmacro rest2 (*a, b) do quasiquote
                [quote(unquote(a)), quote(unquote(b))]
            end end
        """)
        assert self.go("rest2(5)") == [[], 5]
        assert self.go("rest2(5, 6)") == [[5], 6]
        assert self.go("rest2(5, 6, 7)") == [[5, 6], 7]

        self.go("""
            defmacro rest3 (a, *b, c) do quasiquote
                [quote(unquote(a)), quote(unquote(b)), quote(unquote(c))]
            end end
        """)
        assert self.go("rest3(5, 6, 7)") == [5, [6], 7]

    def test_step_execution(self):
        self.go("""
            myadd := func (a, b) do a + b end;
            defmacro foo (a) do myadd([quote(array)], [a]) end;
            foo(5)
        """)

    def test_custom(self):
        with pytest.raises(AssertionError):
            self.go("""
                defmacro foo (a) do quasiquote print(unquote(a)) end end;
                #rule [foo, foo, 5, EXPR, end]
                foo 6 end
            """)

    def test_if(self):
        assert self.go("if 5; True then 6; 7 end") == 7
        assert self.go("if 5; False then 6; 7 end") is None
        assert self.go("if 5; True then 6; 7 else 8; 9 end") == 7
        assert self.go("if 5; False then 6; 7 else 8; 9 end") == 9
        assert self.go("if 5; True then 6; 7 elif 8; True then 9; 10 else 11; 12 end") == 7
        assert self.go("if 5; False then 6; 7 elif 8; True then 9; 10 else 11; 12 end") == 10
        assert self.go("if 5; False then 6; 7 elif 8; False then 9; 10 else 11; 12 end") == 12

        assert self.go("-if 5; True then 6; 7 end") == -7

        with pytest.raises(AssertionError):
            self.go("if True end")
        with pytest.raises(AssertionError):
            self.go("if True then")
        with pytest.raises(AssertionError):
            self.go("if True then 5 else")

    def test_letcc(self):
        assert self.go("letcc cc do 5 + 6 end") == 11
        assert self.go("letcc cc do cc(5) + 6 end") == 5
        assert self.go("5 + letcc cc do cc(6) end") == 11
        assert self.go("letcc cc1 do cc1(letcc cc2 do cc2(5) + 6 end) + 7 end") == 5

        assert self.go("""
            inner := func (raise) do raise(5) end;
            outer := func () do letcc raise do inner(raise) + 6 end end;
            outer()
        """) == 5

        self.go("add5 := None")
        assert self.go("5 + letcc cc do add5 = cc; 6 end") == 11
        assert self.go("add5(7)") == 12
        assert self.go("add5(8)") == 13