import pytest

from commons import ToigStr
from test_commons import BaseTest
from ici import Interpreter as ICI
from stm import Interpreter as STM
from toig_on_toig import setup_toig

@pytest.fixture(scope="session", params=[ICI, STM], ids=["ici", "stm"])
# @pytest.fixture(scope="session", params=[ICI], ids=["ici"])
# @pytest.fixture(scope="session", params=[STM], ids=["stm"])
def shared_interpreter(request):
    ParentToigClass = request.param
    child_toig = setup_toig(ParentToigClass)
    yield child_toig

@pytest.fixture(scope="class", autouse=True)
def use_interpreter(request, shared_interpreter):
    request.cls.i = shared_interpreter

@pytest.fixture(autouse=True)
def reset_interpreter(shared_interpreter):
    shared_interpreter.go("reset_interpreter()")

class TestToTBase:

    def go(self, src):
        return self.i.go(src)

class TestUtilities(TestToTBase):

    def test_is_space(self):
        assert self.go(r""" is_space(" ") """) == True
        assert self.go(r""" is_space("\n") """) == True
        assert self.go(r""" is_space("a") """) == False

    def test_is_digit(self):
        assert self.go(r""" is_digit("0") """) == True
        assert self.go(r""" is_digit("1") """) == True
        assert self.go(r""" is_digit("9") """) == True
        assert self.go(r""" is_digit(" ") """) == False
        assert self.go(r""" is_digit("A") """) == False

    def test_is_alphabet(self):
        assert self.go(r""" is_alphabet("a") """) == True
        assert self.go(r""" is_alphabet("z") """) == True
        assert self.go(r""" is_alphabet("A") """) == True
        assert self.go(r""" is_alphabet("Z") """) == True
        assert self.go(r""" is_alphabet("_") """) == False
        assert self.go(r""" is_alphabet("0") """) == False
        assert self.go(r""" is_alphabet(" ") """) == False

    def test_is_name_first(self):
        assert self.go(r""" is_name_first("a") """) == True
        assert self.go(r""" is_name_first("z") """) == True
        assert self.go(r""" is_name_first("A") """) == True
        assert self.go(r""" is_name_first("Z") """) == True
        assert self.go(r""" is_name_first("_") """) == True
        assert self.go(r""" is_name_first("0") """) == False
        assert self.go(r""" is_name_first("#") """) == False
        assert self.go(r""" is_name_first(" ") """) == False

    def test_is_name_rest(self):
        assert self.go(r""" is_name_rest("a") """) == True
        assert self.go(r""" is_name_rest("z") """) == True
        assert self.go(r""" is_name_rest("A") """) == True
        assert self.go(r""" is_name_rest("Z") """) == True
        assert self.go(r""" is_name_rest("_") """) == True
        assert self.go(r""" is_name_rest("0") """) == True
        assert self.go(r""" is_name_rest("#") """) == False
        assert self.go(r""" is_name_rest(" ") """) == False

    def test_contains(self):
        assert self.go(r""" contains("a", []) """) == False
        assert self.go(r""" contains("a", [1, None, "b", False, []]) """) == False
        assert self.go(r""" contains("a", [1, None, "b", False, "a"]) """) == True

class TestScanner(TestToTBase):
    def test_whitespace(self):
        assert self.go(r""" scan('', [None, []]) """) == [ToigStr("$EOF")]
        assert self.go(r""" scan(' 5 ', [None, []]) """) == [5, ToigStr("$EOF")]
        assert self.go(r""" scan("\n5\n", [None, []]) """) == [5, ToigStr("$EOF")]

    def test_comment(self):
        assert self.go(r""" scan("\n# comment\n5", [None, []]) """) == [5, ToigStr("$EOF")]
        assert self.go(r""" scan("5 # comment", [None, []]) """) == [5, ToigStr("$EOF")]


    def test_primary(self):
        assert self.go(r""" scan('None', [None, []]) """) == [None, ToigStr("$EOF")]
        assert self.go(r""" scan('True False', [None, []]) """) == [True, False, ToigStr("$EOF")]
        assert self.go(r""" scan('5 56', [None, []]) """) == [5, 56, ToigStr("$EOF")]

    def test_raw_string(self):
        assert self.go(r""" scan("''", [None, []]) """) == [[ToigStr("$STR"), ToigStr("")], ToigStr("$EOF")]
        assert self.go(r""" scan("'abc'", [None, []]) """) == [[ToigStr("$STR"), ToigStr("abc")], ToigStr("$EOF")]
        assert self.go(r""" scan("'\\'", [None, []]) """) == [[ToigStr("$STR"), ToigStr("\\")], ToigStr("$EOF")]

    def test_string(self):
        assert self.go(r""" scan('""', [None, []]) """) == [[ToigStr("$STR"), ToigStr("")], ToigStr("$EOF")]
        assert self.go(r""" scan('"abc"', [None, []]) """) == [[ToigStr("$STR"), ToigStr("abc")], ToigStr("$EOF")]
        assert self.go(r""" scan('"\\\n\""', [None, []]) """) == [[ToigStr("$STR"), ToigStr("\\\n\"")], ToigStr("$EOF")]

    def test_rule(self):
        self.go(r""" rules := new_env() """)
        self.go(r""" scan("#rule [foo, _foo, EXPR, end]", rules) """)
        assert self.go(r""" rules """) == [None, [[ToigStr('foo'), [ToigStr('_foo'), ToigStr('EXPR'), ToigStr('end')]]]]

class TestInterpreter(TestToTBase):
    def tot_go(self, tot_src):
        return self.go(f"go({tot_src})")

    def tot_go_verbose(self, tot_src):
        return self.go(f"go_verbose({tot_src})")

    def test_comment(self):
        assert self.tot_go(r""" "# comment\n5" """) == 5
        assert self.tot_go(r""" "5 # comment" """) == 5

    def test_primary(self):
        assert self.tot_go(r""" 'None' """) == None
        assert self.tot_go(r""" 'True' """) == True
        assert self.tot_go(r""" 'False' """) == False
        assert self.tot_go(r""" '5' """) == 5

    def test_raw_string(self):
        assert self.tot_go(r""" "''" """) == ""
        assert self.tot_go(r""" "'abc'" """) == "abc"
        assert self.tot_go(r""" "'\\'" """) == "\\"

        with pytest.raises(AssertionError):
            assert self.tot_go(r""" "'abc" """)

    def test_string(self):
        assert self.tot_go(r""" '""' """) == ""
        assert self.tot_go(r""" '"abc"' """) == "abc"
        assert self.tot_go(r""" '"\\\n\""' """) == "\\\n\""

        with pytest.raises(AssertionError):
            assert self.tot_go(r""" '"abc' """)
        with pytest.raises(AssertionError):
            assert self.tot_go(r""" '"abc\"' """)

    def test_if(self):
        assert self.tot_go(r""" '__if 1; True then 2; 5 else 3; 6 end' """) == 5
        assert self.tot_go(r""" '__if 1; False then 2; 5 else 3; 6 end' """) == 6

        with pytest.raises(AssertionError):
            self.tot_go(r""" '__if True end' """)
        with pytest.raises(AssertionError):
            self.tot_go(r""" '__if True then 5' """)
        with pytest.raises(AssertionError):
            self.tot_go(r""" '__if True then 5 else 6' """)

    def test_sequence(self):
        assert self.tot_go(r""" '5; 6' """) == 6

    def test_define(self, capsys):
        assert self.tot_go(r""" 'a := not True' """) == False
        assert self.tot_go(r""" 'a' """) == False
        assert self.tot_go(r""" 'a := b := 6' """) == 6
        assert self.tot_go(r""" 'a' """) == 6
        assert self.tot_go(r""" 'b' """) == 6

    def test_assign(self):
        self.tot_go(r""" 'a := b := not True' """)
        assert self.tot_go(r""" 'a = 6' """) == 6
        assert self.tot_go(r""" 'a' """) == 6
        assert self.tot_go(r""" 'a = b = 7' """) == 7
        assert self.tot_go(r""" 'a' """) == 7
        assert self.tot_go(r""" 'b' """) == 7

    def test_not(self):
        assert self.tot_go(r""" 'not 5 == 5' """) == False
        assert self.tot_go(r""" 'not 5 == 6' """) == True
        assert self.tot_go(r""" 'not not 5 == 5' """) == True

    def test_comparison(self):
        assert self.tot_go(r""" '5 + 8 == 6 + 7' """) == True
        assert self.tot_go(r""" '5 + 6 == 6 + 7' """) == False
        assert self.tot_go(r""" '5 + 8 != 6 + 7' """) == False
        assert self.tot_go(r""" '5 + 6 != 6 + 7' """) == True

        assert self.tot_go(r""" '5 + 7 < 6 + 7' """) == True
        assert self.tot_go(r""" '5 + 8 < 6 + 7' """) == False
        assert self.tot_go(r""" '5 + 8 < 5 + 7' """) == False
        assert self.tot_go(r""" '5 + 7 > 6 + 7' """) == False
        assert self.tot_go(r""" '5 + 8 > 6 + 7' """) == False
        assert self.tot_go(r""" '5 + 8 > 5 + 7' """) == True
        assert self.tot_go(r""" '5 + 7 <= 6 + 7' """) == True
        assert self.tot_go(r""" '5 + 8 <= 6 + 7' """) == True
        assert self.tot_go(r""" '5 + 8 <= 5 + 7' """) == False
        assert self.tot_go(r""" '5 + 7 >= 6 + 7' """) == False
        assert self.tot_go(r""" '5 + 8 >= 6 + 7' """) == True
        assert self.tot_go(r""" '5 + 8 >= 5 + 7' """) == True

        assert self.tot_go(r""" '5 == 5 == True' """) == True

    def test_add_sub(self):
        assert self.tot_go(r""" '5 + 6 + 7' """) == 18
        assert self.tot_go(r""" '18 - 7 - 6' """) == 5

    def test_mul_div_mod(self):
        assert self.tot_go(r""" '5 * 6 * 7' """) == 210
        assert self.tot_go(r""" '210 / 6 / 7' """) == 5
        assert self.tot_go(r""" '216 / 6 % 7' """) == 1
        assert self.tot_go(r""" '5 + 6 * 7' """) == 47
        assert self.tot_go(r""" '5 * 6 + 7' """) == 37

    def test_neg(self):
        assert self.tot_go(r""" '-5' """) == -5
        assert self.tot_go(r""" '-5 * 6' """) == -30
        assert self.tot_go(r""" '5 * -6' """) == -30

        assert self.tot_go(r""" '--5' """) == 5

    def test_paren(self):
        assert self.tot_go(r""" '(5; 6) * 7' """) == 42
        assert self.tot_go(r""" '5 * (6; 7)' """) == 35
        assert self.tot_go(r""" '(5) + 6' """) == 11

        with pytest.raises(AssertionError):
            self.tot_go(r""" '(5' """)
        with pytest.raises(AssertionError):
            self.tot_go(r""" '5)' """)

    def test_call_builtins(self):
        self.tot_go(r""" 'clock_ms()' """)
        assert self.tot_go(r""" 'neg(5; 6)' """) == -6
        assert self.tot_go(r""" 'add(5; 6, 7; 8)' """) == 14

        with pytest.raises(AssertionError):
            self.tot_go(r""" 'inc(5' """)
        with pytest.raises(AssertionError):
            self.tot_go(r""" 'inc(5 6)' """)

    def test_func(self):
        assert self.tot_go(r""" 'func () do 5 end ()' """) == 5
        assert self.tot_go(r""" 'func (a) do a + 1 end (5)' """) == 6
        assert self.tot_go(r""" 'func (a, b) do a + b end (5, 6)' """) == 11
        assert self.tot_go(r""" 'func (*args) do args end ()' """) == []
        assert self.tot_go(r""" 'func (*args) do args end (5)' """) == [5]
        assert self.tot_go(r""" 'func (*args) do args end (5, 6)' """) == [5, 6]
        assert self.tot_go(r""" 'func (*(args)) do args end (5, 6)' """) == [5, 6]

        assert self.tot_go(r""" 'func (*args, a) do [args, a] end (5)' """) == [[], 5]
        assert self.tot_go(r""" 'func (*args, a) do [args, a] end (5, 6)' """) == [[5], 6]
        assert self.tot_go(r""" 'func (*args, a) do [args, a] end (5, 6, 7)' """) == [[5, 6], 7]
        assert self.tot_go(r""" 'func (*args, a, b) do [args, a, b] end (5, 6, 7)' """) == [[5], 6, 7]
        assert self.tot_go(r""" 'func (a, *args, b) do [a, args, b] end (5, 6, 7)' """) == [5, [6], 7]
        assert self.tot_go(r""" 'func (a, b, *args) do [a, b, args] end (5, 6, 7)' """) == [5, 6, [7]]

        with pytest.raises(AssertionError):
            self.tot_go(r""" 'func (a, b) a + b end' """)
        with pytest.raises(AssertionError):
            self.tot_go(r""" 'func (a, b) do a + b' """)
        with pytest.raises(AssertionError):
            self.tot_go(r""" 'func a, b) do a + b end (5, 6)' """)
        with pytest.raises(AssertionError):
            self.tot_go(r""" 'func (a, b do a + b end (5, 6)' """)
        with pytest.raises(AssertionError):
            self.tot_go(r""" 'func (a b) do a + b end (5, 6)' """)
        with pytest.raises(AssertionError):
            self.tot_go(r""" 'func (a, b + c) do a + b end (5, 6)' """)
        with pytest.raises(AssertionError):
            self.tot_go(r""" 'func (a, b) do a + b end (5) do 6' """)
        with pytest.raises(AssertionError):
            self.tot_go(r""" 'func (a, b) do a + b end (5) 6 end' """)

        with pytest.raises(AssertionError):
            self.tot_go(r""" '*a' """)
        with pytest.raises(AssertionError):
            self.tot_go(r""" 'func (*args, a) do [args, a] end ()' """)

    def test_closure_adder(self):
        self.tot_go(r""" 'make_adder := func (n) do func (m) do n + m end end' """)
        assert self.tot_go(r""" 'make_adder(5)(6)' """) == 11

    def test_closure_counter(self):
        self.tot_go(r""" '
            make_counter := func () do c := 0; func() do c = c + 1 end end;
            counter1 := make_counter();
            counter2 := make_counter()
        ' """)
        assert self.tot_go(r""" 'counter1()' """) == 1
        assert self.tot_go(r""" 'counter1()' """) == 2
        assert self.tot_go(r""" 'counter2()' """) == 1
        assert self.tot_go(r""" 'counter2()' """) == 2
        assert self.tot_go(r""" 'counter1()' """) == 3
        assert self.tot_go(r""" 'counter2()' """) == 3

    def test_fib(self):
        self.tot_go_verbose(r""" '
            fib := func (n) do
                if n == 0 then 0
                else if n == 1 then 1
                else fib(n - 1) + fib(n - 2) end end
            end
        ' """)
        assert self.tot_go(r""" 'fib(0)' """) == 0
        assert self.tot_go(r""" 'fib(1)' """) == 1
        assert self.tot_go(r""" 'fib(2)' """) == 1
        assert self.tot_go(r""" 'fib(3)' """) == 2
        assert self.tot_go(r""" 'fib(4)' """) == 3
        # assert self.tot_go(r""" 'fib(10)' """) == 55
        # self.tot_go(r""" 'fib(100)' """)

    # def test_tco(self):
    #     self.tot_go(r""" '
    #         loop := func (n) do if n > 0 then loop(n - 1) else 0 end end;
    #         loop(1000)
    #     ' """)

    # def test_not_tail(self):
    #     self.tot_go(r""" '
    #         loop := func (n) do if n > 0 then 2 + loop(n - 1) else 0 end end;
    #         loop(5);
    #         loop(500)
    #     ' """)

    def test_tco_fib_tail(self):
        self.tot_go(r""" '
            fib_tail := func (n) do
                rec := func (k, a, b) do
                    if k == n then a else rec(k + 1, b, a + b) end
                end;
                rec(0, 0, 1)
            end
        ' """)
        assert self.tot_go(r""" 'fib_tail(10)' """) == 55
        # self.tot_go(r""" 'fib_tail(10000)' """)

    def test_array_by_builtin(self):
        assert self.tot_go(r""" 'array()' """) == []
        assert self.tot_go(r""" 'array(5; 6)' """) == [6]
        assert self.tot_go(r""" 'array(5; 6, 7; 8)' """) == [6, 8]

    def test_array(self):
        assert self.tot_go(r""" '[]' """) == []
        assert self.tot_go(r""" '[5; 6]' """) == [6]
        assert self.tot_go(r""" '[5; 6, 7; 8]' """) == [6, 8]

        assert self.tot_go(r""" 'is_array([])' """) == True
        assert self.tot_go(r""" 'is_array(1)' """) == False

        assert self.tot_go(r""" 'len([5, 6, 7])' """) == 3

        assert self.tot_go(r""" 'get_at([5, 6, 7], 1)' """) == 6
        assert self.tot_go(r""" 'a := [5, 6, 7]; set_at(a, 1, 8); a' """) == [5, 8, 7]
        assert self.tot_go(r""" 'a := [5, 6, 7]; a[1] = 8; a' """) == [5, 8, 7]
        assert self.tot_go(r""" 'slice(array(5, 6, 7), 1, 2, None)' """) == [6]

        assert self.tot_go(r""" 'first([5, 6, 7])' """) == 5
        assert self.tot_go(r""" 'rest([5, 6, 7])' """) == [6, 7]
        assert self.tot_go(r""" 'last([5, 6, 7])' """) == 7

    def test_array_index(self):
        self.tot_go(r""" 'a := [5, 6, 7]' """)
        assert self.tot_go_verbose(r""" 'a[1]' """) == 6
        assert self.tot_go_verbose(r""" 'a[-1]' """) == 7

        assert self.tot_go(r""" '[[5, 6, 7], [15, 16, 17], [25, 26, 27]][1]' """) == [15, 16, 17]
        assert self.tot_go(r""" '[[5, 6, 7], [15, 16, 17], [25, 26, 27]][1][2]' """) == 17
        assert self.tot_go(r""" '[add, sub][0](5, 6)' """) == 11
        assert self.tot_go(r""" 'func (a, b) do [a, b] end (5, 6)[1]' """) == 6

    def test_array_append(self):
        assert self.tot_go(r""" 'a := [5, 6]; append(a, 7); a' """) == [5, 6, 7]

    def test_quote(self):
        assert self.tot_go(r""" 'q(5)' """) == 5
        assert self.tot_go(r""" 'q(None)' """) is None
        assert self.tot_go(r""" 'q(foo)' """) == "foo"
        assert self.tot_go(r""" 'q([5, 6])' """) == [ToigStr("array"), 5, 6]
        assert self.tot_go(r""" 'q(add(5, 6))' """) == [ToigStr("add"), 5, 6]
        assert self.tot_go(r""" 'q(5 + 6)' """) == [ToigStr("add"), 5, 6]

    def test_array_index_slice(self):
        self.tot_go(r""" 'a := [5, 6, 7, 8, 9]' """)
        with pytest.raises(AssertionError):
            self.tot_go(r""" 'a[]' """)
        assert self.tot_go(r""" 'a[1]' """) == 6
        assert self.tot_go(r""" 'a[:]' """) == [5, 6, 7, 8, 9]
        with pytest.raises(AssertionError):
            self.tot_go(r""" 'a[1,]' """)
        assert self.tot_go(r""" 'a[1:]' """) == [6, 7, 8, 9]
        assert self.tot_go(r""" 'a[1:4]' """) == [6, 7, 8]
        assert self.tot_go(r""" 'a[:4]' """) == [5, 6, 7, 8]
        with pytest.raises(AssertionError):
            self.tot_go(r""" 'a[1:2,]' """)
        assert self.tot_go(r""" 'a[3:1:-1]' """) == [8, 7]
        assert self.tot_go(r""" 'a[:1:-1]' """) == [9, 8, 7]
        assert self.tot_go(r""" 'a[3::-1]' """) == [8, 7, 6, 5]
        assert self.tot_go(r""" 'a[1:4:]' """) == [6, 7, 8]
        assert self.tot_go(r""" 'a[::-1]' """) == [9, 8, 7, 6, 5]
        assert self.tot_go(r""" 'a[:3:]' """) == [5, 6, 7]
        assert self.tot_go(r""" 'a[1::]' """) == [6, 7, 8, 9]
        assert self.tot_go(r""" 'a[::]' """) == [5, 6, 7, 8, 9]
        with pytest.raises(AssertionError):
            self.tot_go(r""" 'a[1:2:3,' """)

        assert self.tot_go(r""" 'a[0;3:0;1:0;-1]' """) == [8, 7]

        assert self.tot_go(r""" '[[5, 6, 7], [15, 16, 17], [25, 26, 27]][1]' """) == [15, 16, 17]
        assert self.tot_go(r""" '[[5, 6, 7], [15, 16, 17], [25, 26, 27]][1][2]' """) == 17
        assert self.tot_go(r""" '[add, sub][0](5, 6)' """) == 11
        assert self.tot_go(r""" 'func (a, b) do [a, b] end (5, 6)[1]' """) == 6

    def test_macro(self):
        self.tot_go(r""" 'sq := macro (a) do [q(mul), a, a] end' """)
        assert self.tot_go(r""" 'expand(sq(5 + 6))' """) == [
            ToigStr("mul"), [ToigStr("add"), 5, 6], [ToigStr("add"), 5, 6]
        ]
        assert self.tot_go(r""" 'sq(5 + 6)' """) == 121

        self.tot_go(r""" '
            when := macro (cnd, thn, els) do
                expr := q(if c then t else e end);
                expr[1] = cnd;
                expr[2] = thn;
                expr[3] = els;
                expr
            end
        ' """)
        assert self.tot_go(r""" 'expand(when(5 == 6, 7, 8))' """) == [
            ToigStr("_if"), [ToigStr("equal"), 5, 6], 7, 8
        ]
        assert self.tot_go(r""" 'when(5 == 6, 7, 8)' """) == 8

        self.tot_go(r""" 'arg_array := macro (*args) do [q(array)] + args end' """)
        assert self.tot_go(r""" 'expand(arg_array(5 + 6, 7))' """) == [
            ToigStr("array"), [ToigStr("add"), 5, 6], 7
        ]
        assert self.tot_go(r""" 'arg_array(5 + 6, 7)' """) == [11, 7]

    def test_custom_expr(self):
        self.tot_go(r""" '
            _custom := macro (a) do [q(mul), a, a] end
            #rule [custom, _custom, EXPR, end]
        ' """)
        assert self.tot_go(r""" '
            expand(custom 5 + 6 end)
        ' """) == [
            ToigStr("mul"), [ToigStr("add"), 5, 6], [ToigStr("add"), 5, 6]
        ]
        assert self.tot_go(r""" 'custom 5 + 6 end' """) == 121

    def test_custom_params(self):
        self.tot_go(r""" '
            _custom := macro (a) do [q(mul), a[0], a[1]] end
            #rule [custom, _custom, PARAMS, end]
        ' """)
        assert self.tot_go_verbose(r""" '
            expand(custom(5 + 6, 7) end)
        ' """) == [
            ToigStr("mul"), [ToigStr("add"), 5, 6], 7
        ]
        assert self.tot_go_verbose(r""" 'custom (5 + 6, 7) end' """) == 77

    def test_custom_many(self):
        self.tot_go(r""" '
            _custom := macro (*args) do [q(array)] + args end
            #rule [custom, _custom, EXPR, *[many, EXPR], end]
        ' """)

        assert self.tot_go(r""" 'expand(custom 5 + 6 end)' """) == [
            ToigStr("array"), [ToigStr("add"), 5, 6]
        ]
        assert self.tot_go(r""" 'custom 5 + 6 end' """) == [11]

        assert self.tot_go(r""" 'expand(custom 5 + 6 many 7 end)' """) == [
            ToigStr("array"), [ToigStr("add"), 5, 6], 7
        ]
        assert self.tot_go(r""" 'custom 5 + 6 many 7 end' """) == [11, 7]

        assert self.tot_go(r""" 'expand(custom 5 + 6 many 7 many 8 end)' """) == [
            ToigStr("array"), [ToigStr("add"), 5, 6], 7, 8
        ]
        assert self.tot_go(r""" 'custom 5 + 6 many 7 many 8 end' """) == [11, 7, 8]

    def test_custom_optional(self):
        self.tot_go(r""" '
            _custom := macro (*args) do [q(array)] + args end
            #rule [custom, _custom, EXPR, ?[optional, EXPR], end]
        ' """)

        assert self.tot_go_verbose(r""" 'expand(custom 5 + 6 end)' """) == [
            ToigStr("array"), [ToigStr("add"), 5, 6]
        ]
        assert self.tot_go(r""" 'custom 5 + 6 end' """) == [11]

        assert self.tot_go(r""" 'expand(custom 5 + 6 optional 7 end)' """) == [
            ToigStr("array"), [ToigStr("add"), 5, 6], 7
        ]
        assert self.tot_go(r""" 'custom 5 + 6 optional 7 end' """) == [11, 7]

        with pytest.raises(AssertionError):
            self.tot_go(r""" 'expand(custom 5 + 6 optional 7 optional 8 end)' """)

    def test_quasiquote(self):
        assert self.tot_go(r""" 'qq 5 end' """) == 5
        assert self.tot_go(r""" 'qq None end' """) is None
        assert self.tot_go(r""" 'qq foo end' """) == "foo"
        assert self.tot_go(r""" 'qq [5, 6] end' """) == [ToigStr("array"), 5, 6]
        assert self.tot_go(r""" 'qq add(5, 6) end' """) == [ToigStr("add"), 5, 6]
        assert self.tot_go(r""" 'qq 5 + 6 end' """) == [ToigStr("add"), 5, 6]

        assert self.tot_go(r""" 'qq unquote(add(5, 6)) end' """) == 11
        assert self.tot_go(r""" 'qq add(5, unquote(6; 7)) end' """) == [ToigStr("add"), 5, 7]
        assert self.tot_go(r""" 'qq unquote(5 + 6) end' """) == 11
        assert self.tot_go(r""" 'qq 5 + unquote(6; 7) end' """) == [ToigStr("add"), 5, 7]
        assert self.tot_go(r""" 'qq add(unquote_splicing([5, 6])) end' """) == [ToigStr("add"), 5, 6]
        assert self.tot_go(r""" 'qq add(5, unquote_splicing([6])) end' """) == [ToigStr("add"), 5, 6]
        assert self.tot_go(r""" '
            qq if a == 5 then 6; 7 else unquote(8; 9) end end
        ' """) == [ToigStr("_if"), [ToigStr("equal"), ToigStr("a"), 5], [ToigStr("seq"), 6, 7], 9]

        # assert self.tot_go(r""" 'qq unquote(when(False, 5)) end' """) is None

    def test_unquote_operator(self):
        assert self.tot_go(r""" 'qq !(add(5, 6)) end' """) == 11
        assert self.tot_go(r""" 'qq add(5, !(6; 7)) end' """) == [ToigStr("add"), 5, 7]
        assert self.tot_go(r""" 'qq !(5 + 6) end' """) == 11
        assert self.tot_go(r""" 'qq ![5, 6; 7] end' """) == [5, 7]
        assert self.tot_go(r""" 'a := 5; qq !a + 6 end' """) == [ToigStr("add"), 5, 6]
        assert self.tot_go(r""" 'qq 5 + !(6; 7) end' """) == [ToigStr("add"), 5, 7]
        assert self.tot_go(r""" 'qq add(!![5, 6]) end' """) == [ToigStr("add"), 5, 6]
        assert self.tot_go(r""" 'qq add(5, !![6]) end' """) == [ToigStr("add"), 5, 6]
        assert self.tot_go(r""" '
            qq if a == 5 then 6; 7 else !(8; 9) end end
        ' """) == [ToigStr("_if"), [ToigStr("equal"), ToigStr("a"), 5], [ToigStr("seq"), 6, 7], 9]

    def test_defmacro(self):
        assert self.tot_go_verbose(r""" '
            expand(defmacro myadd with (a, b) do
                qq !a + !b end
            end)
        ' """) == [ToigStr('define'), ToigStr('myadd'),
            [ToigStr('macro'), [ToigStr('a'), ToigStr('b')], [ToigStr('_qq'),
                [ToigStr('add'),
                    [ToigStr('unquote'), ToigStr('a')],
                    [ToigStr('unquote'), ToigStr('b')]
                ]
            ]
        ]]
        self.tot_go_verbose(r""" '
            defmacro myadd with (a, b) do
                qq !a + !b end
            end
        ' """)
        assert self.tot_go_verbose(r""" 'myadd(5, 6)' """) == 11

    def test_scope(self):
        assert self.tot_go_verbose(""" 'expand(
            scope x := 6; y = x end
        )' """) == [[ToigStr("func"), [], [ToigStr("seq"),
            [ToigStr("define"), ToigStr("x"), 6],
            [ToigStr("assign"), ToigStr("y"), ToigStr("x")]
        ]]]
        assert self.tot_go_verbose(""" '
            x := 5; y := 6; scope x := 6; y = x end; [x, y]
        ' """) == [5, 6]
        assert self.tot_go(""" '
            x := 5; y := 6; scope x = 6; y = x end; [x, y]
        ' """) == [6, 6]

    def test_elif(self):
        assert self.tot_go(""" 'if 5; True then 6; 7 end' """) == 7
        assert self.tot_go(""" 'if 5; False then 6; 7 end' """) is None
        assert self.tot_go(""" 'if 5; True then 6; 7 else 8; 9 end' """) == 7
        assert self.tot_go(""" 'if 5; False then 6; 7 else 8; 9 end' """) == 9
        assert self.tot_go(""" 'if 5; True then 6; 7 elif 8; True then 9; 10 else 11; 12 end' """) == 7
        assert self.tot_go(""" 'if 5; False then 6; 7 elif 8; True then 9; 10 else 11; 12 end' """) == 10
        assert self.tot_go(""" 'if 5; False then 6; 7 elif 8; False then 9; 10 else 11; 12 end' """) == 12


    def test_aif(self):
        assert self.tot_go(""" 'aif 5 then it + 1 end' """) == 6
        assert self.tot_go(""" 'aif 0 then it + 1 end' """) is None
        assert self.tot_go(""" 'aif 5 then it + 1 else it + 1 end' """) == 6
        assert self.tot_go(""" 'aif 0 then it + 1 else it + 1 end' """) == 1
        assert self.tot_go(""" 'aif 0 then 5 elif 6 then it + 1 end' """) == 7
        assert self.tot_go(""" 'aif 0 then 5 elif 0 then it + 1 end' """) is None
        assert self.tot_go(""" 'aif 0 then 5 elif 6 then it + 1 else it + 1 end' """) == 7
        assert self.tot_go(""" 'aif 0 then 5 elif 0 then it + 1 else it + 1 end' """) == 1
        assert self.tot_go(""" 'aif 0 then 5 elif 0 then 6 elif 7 then it + 1 end' """) == 8
        assert self.tot_go(""" 'aif 0 then 5 elif 0 then 6 elif 0 then it + 1 end' """) is None

    def test_or(self):
        assert self.tot_go(""" '5 == 5 or 5 == 5' """) is True
        assert self.tot_go(""" '5 == 5 or 5 != 5' """) is True
        assert self.tot_go(""" '5 != 5 or 5 == 5' """) is True
        assert self.tot_go(""" '5 != 5 or 5 != 5' """) is False
        assert self.tot_go(""" '5 or x' """) == 5
        assert self.tot_go(""" 'False or 5' """) == 5
        assert self.tot_go(""" 'False or False or True' """) is True
        assert self.tot_go(""" 'False or False or False' """) is False
        assert self.tot_go(""" 'x := True or False' """) is True
        assert self.tot_go(""" 'x' """) is True

    def test_and(self):
        assert self.tot_go(""" '5 == 5 and 5 == 5' """) is True
        assert self.tot_go(""" '5 == 5 and 5 != 5' """) is False
        assert self.tot_go(""" '5 != 5 and 5 == 5' """) is False
        assert self.tot_go(""" '5 != 5 and 5 != 5' """) is False
        assert self.tot_go(""" 'True and 5' """) == 5
        assert self.tot_go(""" '0 and x' """) == 0
        assert self.tot_go(""" 'True or True and False' """) is True
        assert self.tot_go(""" '(True or True) and False' """) is False

    def test_letcc(self):
        assert self.tot_go(""" 'letcc cc do 5 + 6 end' """) == 11
        assert self.tot_go(""" 'letcc cc do cc() end' """) == None
        assert self.tot_go(""" 'letcc cc do cc(5) + 6 end' """) == 5
        assert self.tot_go(""" '5 + letcc cc do cc(6) end' """) == 11
        assert self.tot_go(""" 'letcc cc1 do cc1(letcc cc2 do cc2(5) + 6 end) + 7 end' """) == 5

        assert self.tot_go(r""" '
            inner := func (raise) do raise(5) end;
            outer := func () do letcc raise do inner(raise) + 6 end end;
            outer()
        ' """) == 5

        self.tot_go(""" 'add5 := None' """)
        assert self.tot_go(""" '5 + letcc cc do add5 = cc; 6 end' """) == 11
        assert self.tot_go(""" 'add5(7)' """) == 12
        assert self.tot_go(""" 'add5(8)' """) == 13

    # def test_while(self):
    #     assert self.tot_go(r""" '
    #         i := sum := 0;
    #         while i < 10 do
    #             sum = sum + i;
    #             i = i + 1;
    #             sum
    #         end
    #     ' """) == 45

    #     assert self.tot_go(r""" '
    #         r := c := [];
    #         while len(r) < 3 do
    #             c = [];
    #             while len(c) < 3 do
    #                 c = c + [0]
    #             end;
    #             r = r + [c]
    #         end
    #     ' """) == [[0, 0, 0], [0, 0, 0], [0, 0, 0]]

    # def test_while_break(self):
    #     assert self.tot_go(r""" '
    #         i := sum := 0;
    #         while True do
    #             if i >= 10 then break(sum) end;
    #             sum = sum + i;
    #             i = i + 1
    #         end
    #     ' """) == 45

    #     with pytest.raises(AssertionError):
    #         self.tot_go(r""" ' break(5)' """)

    # def test_while_continue(self):

    #     assert self.tot_go_verbose(r""" '
    #         print("loop1");
    #         loop := None;
    #         letcc cc do loop = cc end;
    #         print("loop2");
    #         loop(5);
    #         print("loop3")
    #     ' """) == 40

        # assert self.tot_go_verbose(r""" '
        #     defmacro __wh with (cnd, body) do qq scope
        #         continue := None;
        #         loop := func() do
        #             print("while1");
        #             letcc cc do continue = cc end;
        #             print("while2");
        #             continue(5);
        #             print("while3")
        #         end;
        #         loop()
        #     end end end;

        #     #rule [wh, __wh, EXPR, do, EXPR, end]
        #     wh True do continue(5) end
        # ' """) == 40

        # assert self.tot_go_verbose(r""" '
        #     i := sum := 0;
        #     while i < 10 do
        #         if i == 5 then i = i + 1; continue() end;
        #         sum = sum + i;
        #         i = i + 1;
        #         sum
        #     end
        # ' """) == 40

        # with pytest.raises(AssertionError):
        #     self.tot_go(r""" 'continue(None)' """)

class TestEvaluator(TestToTBase):
    def eot_go(self, eot_src):
        return self.go(f""" eval({eot_src}) """)

    def test_primary(self):
        assert self.eot_go(r""" None """) == None
        assert self.eot_go(r""" True """) == True
        assert self.eot_go(r""" False """) == False
        assert self.eot_go(r""" 5 """) == 5

    def test_if(self):
        assert self.eot_go(r""" ["if", True, 5, 6] """) == 5
        assert self.eot_go(r""" ["if", False, 5, 6] """) == 6
        assert self.eot_go(r""" ["if", ["if", True, True, True], 5, 6] """) == 5
        assert self.eot_go(r""" ["if", True, ["if", True, 5, 6], 6] """) == 5
        assert self.eot_go(r""" ["if", False, 5, ["if", False, 5, 6]] """) == 6

        with pytest.raises(AssertionError):
            self.eot_go(r""" ["unexpected case"] """)

    def test_define(self):
        assert self.eot_go(r""" ["define", "a", 5] """) == 5
        assert self.eot_go(r""" "a" """) == 5
        assert self.eot_go(r""" ["define", "b", 6] """) == 6
        assert self.eot_go(r""" "b" """) == 6
        assert self.eot_go(r""" ["define", "b", 7] """) == 7
        assert self.eot_go(r""" "b" """) == 7

        with pytest.raises(AssertionError):
            self.eot_go(r""" "c" """)

    def test_primitives(self):
        assert self.eot_go(r""" ["add", 5, 6] """) == 11
        assert self.eot_go(r""" ["sub", 11, 6] """) == 5
        assert self.eot_go(r""" ["equal", 5, 5] """) == True
        assert self.eot_go(r""" ["equal", 5, 6] """) == False

    def test_function(self):
        assert self.eot_go(r""" [["func", ["n"], ["add", "n", 5]], 6] """) == 11

    def test_fib(self):
        self.eot_go(r"""
            ["define", "fib", ["func", ["n"],
                ["if", ["equal", "n", 0], 0,
                ["if", ["equal", "n", 1], 1,
                ["add", ["fib", ["sub", "n", 1]], ["fib", ["sub", "n", 2]]]]]]]
         """)
        assert self.eot_go(r""" ["fib", 0] """) == 0
        assert self.eot_go(r""" ["fib", 1] """) == 1
        assert self.eot_go(r""" ["fib", 2] """) == 1
        assert self.eot_go(r""" ["fib", 3] """) == 2
        assert self.eot_go(r""" ["fib", 6] """) == 8

    def test_adder(self):
        self.eot_go(r"""
            ["define", "make_adder", ["func", ["n"],
                ["func", ["m"], ["add", "n", "m"]]
            ]]
         """)
        assert self.eot_go(r""" [["make_adder", 5], 6] """) == 11

    def test_counter(self):
        self.eot_go(r""" ["seq",
            ["define", "make_counter", ["func", [], ["seq",
                ["define", "c", 0],
                ["func", [], ["assign", "c", ["add", "c", 1]]]
            ]]],
            ["define", "counter1", ["make_counter"]],
            ["define", "counter2", ["make_counter"]]
        ] """)

        assert self.eot_go(r""" ["counter1"] """) == 1
        assert self.eot_go(r""" ["counter1"] """) == 2
        assert self.eot_go(r""" ["counter2"] """) == 1
        assert self.eot_go(r""" ["counter2"] """) == 2
        assert self.eot_go(r""" ["counter1"] """) == 3
        assert self.eot_go(r""" ["counter2"] """) == 3
