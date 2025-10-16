import pytest

from commons import ToigStr
from toig_on_toig import BaseToigOnToigTest
from ici import Interpreter as ICI
from stm import Interpreter as STM

@pytest.mark.parametrize(
    "set_interpreter",
    [ICI, STM], ids=["ici", "stm"],
    indirect=True)
class TestUtilities(BaseToigOnToigTest):
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

@pytest.mark.parametrize(
    "set_interpreter",
    [ICI, STM], ids=["ici", "stm"],
    indirect=True)
class TestScanner(BaseToigOnToigTest):
    def test_whitespace(self):
        assert self.go(r""" scan('') """) == [ToigStr("$EOF")]
        assert self.go(r""" scan(' 5 ') """) == [5, ToigStr("$EOF")]
        assert self.go(r""" scan("\n5\n") """) == [5, ToigStr("$EOF")]

    def test_primary(self):
        assert self.go(r""" scan('None') """) == [None, ToigStr("$EOF")]
        assert self.go(r""" scan('True False') """) == [True, False, ToigStr("$EOF")]
        assert self.go(r""" scan('5 56') """) == [5, 56, ToigStr("$EOF")]

    def test_raw_string(self):
        assert self.go(r""" scan("''") """) == [[ToigStr("$STR"), ToigStr("")], ToigStr("$EOF")]
        assert self.go(r""" scan("'abc'") """) == [[ToigStr("$STR"), ToigStr("abc")], ToigStr("$EOF")]
        assert self.go(r""" scan("'\\'") """) == [[ToigStr("$STR"), ToigStr("\\")], ToigStr("$EOF")]

    def test_string(self):
        assert self.go(r""" scan('""') """) == [[ToigStr("$STR"), ToigStr("")], ToigStr("$EOF")]
        assert self.go(r""" scan('"abc"') """) == [[ToigStr("$STR"), ToigStr("abc")], ToigStr("$EOF")]
        assert self.go(r""" scan('"\\\n\""') """) == [[ToigStr("$STR"), ToigStr("\\\n\"")], ToigStr("$EOF")]

@pytest.mark.parametrize(
    "set_interpreter",
    [ICI, STM], ids=["ici", "stm"],
    indirect=True)
class TestInterpreter(BaseToigOnToigTest):
    def tot_go(self, tot_src):
        return self.go(f"go({tot_src})")

    def tot_go_verbose(self, tot_src):
        return self.go(f"go_verbose({tot_src})")

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
        assert self.tot_go(r""" 'if 1; True then 2; 5 else 3; 6 end' """) == 5
        assert self.tot_go(r""" 'if 1; False then 2; 5 else 3; 6 end' """) == 6

        with pytest.raises(AssertionError):
            self.tot_go(r""" 'if True end' """)
        with pytest.raises(AssertionError):
            self.tot_go(r""" 'if True then 5' """)
        with pytest.raises(AssertionError):
            self.tot_go(r""" 'if True then 5 else 6' """)

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
        # assert self.tot_go(r""" 'func (*args) do args end ()' """) == []
        # assert self.tot_go(r""" 'func (*args) do args end (5)' """) == [5]
        # assert self.tot_go(r""" 'func (*args) do args end (5, 6)' """) == [5, 6]
        # assert self.tot_go(r""" 'func (*(args)) do args end (5, 6)' """) == [5, 6]

        # assert self.tot_go(r""" 'func (*args, a) do [args, a] end (5)' """) == [[], 5]
        # assert self.tot_go(r""" 'func (*args, a) do [args, a] end (5, 6)' """) == [[5], 6]
        # assert self.tot_go(r""" 'func (*args, a) do [args, a] end (5, 6, 7)' """) == [[5, 6], 7]
        # assert self.tot_go(r""" 'func (*args, a, b) do [args, a, b] end (5, 6, 7)' """) == [[5], 6, 7]
        # assert self.tot_go(r""" 'func (a, *args, b) do [a, args, b] end (5, 6, 7)' """) == [5, [6], 7]
        # assert self.tot_go(r""" 'func (a, b, *args) do [a, b, args] end (5, 6, 7)' """) == [5, 6, [7]]

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

        # with pytest.raises(AssertionError):
        #     self.tot_go(r""" '*a' """)
        # with pytest.raises(AssertionError):
        #     self.tot_go(r""" 'func (*args, a) do [args, a] end ()' """)

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
        self.tot_go(r""" '
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

@pytest.mark.parametrize(
    "set_interpreter",
    [ICI, STM], ids=["ici", "stm"],
    indirect=True)
class TestEvaluator(BaseToigOnToigTest):
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
