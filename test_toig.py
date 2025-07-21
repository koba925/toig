import unittest
from unittest.mock import patch
from io import StringIO

from toig import Interpreter

class TestToig(unittest.TestCase):
    def setUp(self):
        self.i = Interpreter()
        self.i.stdlib()

    def go(self, src):
        return self.i.run(src)

    def fails(self, src):
        try: self.i.run(src)
        except AssertionError: return True
        else: return False

    def expanded(self, src):
        return self.i.run(f"expand({src})")

    def printed(self, src):
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            val = self.i.run(src)
            return (val, mock_stdout.getvalue())

class TestCore(TestToig):
    def test_comment(self):
        self.assertEqual(self.go("5 # 6"), 5)
        self.assertEqual(self.go("""
            5 # 6
        """), 5)
        self.assertEqual(self.go("""
            # 5
            6
        """), 6)

    def test_primary(self):
        self.assertEqual(self.go("None"), None)
        self.assertEqual(self.go("5"), 5)
        self.assertEqual(self.go("True"), True)
        self.assertEqual(self.go("False"), False)

    def test_define(self):
        self.assertEqual(self.go("x := 5"), 5)
        self.assertEqual(self.go("x"), 5)
        self.assertEqual(self.go("y := z := 6"), 6)
        self.assertEqual(self.go("y"), 6)
        self.assertEqual(self.go("z"), 6)
        self.assertTrue(self.fails("6 := 5"), 5)

    def test_assign(self):
        self.assertEqual(self.go("x := y := 5"), 5)
        self.assertEqual(self.go("x = 6"), 6)
        self.assertEqual(self.go("x"), 6)
        self.assertEqual(self.go("x = y = 7"), 7)
        self.assertEqual(self.go("x"), 7)
        self.assertEqual(self.go("y"), 7)
        self.assertTrue(self.fails("z = 5"))
        self.assertTrue(self.fails("6 = 5"))

    def test_scope(self):
        self.assertEqual(
            self.printed("x := 5; scope x := 6; print(x) end; print(x)"),
            (None, "6\n5\n"))
        self.assertEqual(
            self.printed("x := 5; scope x = 6; print(x) end; print(x)"),
            (None, "6\n6\n"))
        self.assertTrue(self.fails("scope y := 5 end; print(y)"))

    def test_sequence(self):
        self.assertEqual(self.go("x := 5; y := 6; x + y"), 11)
        self.assertEqual(self.go("x"), 5)
        self.assertEqual(self.go("y"), 6)
        self.assertEqual(self.go("x = 6; y = 7; x * y"), 42)
        self.assertEqual(self.go("x"), 6)
        self.assertEqual(self.go("y"), 7)
        self.assertTrue(self.fails(";"))

    def test_or(self):
        self.assertTrue(self.go("5 == 5 or 5 == 5"))
        self.assertTrue(self.go("5 == 5 or 5 != 5"))
        self.assertTrue(self.go("5 != 5 or 5 == 5"))
        self.assertFalse(self.go("5 != 5 or 5 != 5"))

        self.assertEqual(self.go("5 or x"), 5)
        self.assertEqual(self.go("False or 5"), 5)

        self.assertTrue(self.go("False or False or True"))
        self.assertFalse(self.go("False or False or False"))

        self.assertEqual(self.go("x := True or False"), True)
        self.assertEqual(self.go("x"), True)

    def test_and(self):
        self.assertTrue(self.go("5 == 5 and 5 == 5"))
        self.assertFalse(self.go("5 == 5 and 5 != 5"))
        self.assertFalse(self.go("5 != 5 and 5 == 5"))
        self.assertFalse(self.go("5 != 5 and 5 != 5"))

        self.assertEqual(self.go("True and 5"), 5)
        self.assertEqual(self.go("0 and x"), 0)

        self.assertTrue(self.go("True or True and False"))
        self.assertFalse(self.go("(True or True) and False"))

    def test_not(self):
        self.assertFalse(self.go("not 5 == 5"))
        self.assertTrue(self.go("not 5 != 5"))

        self.assertFalse(self.go("not True and False"))
        self.assertTrue(self.go("not (True and False)"))

    def test_comparison(self):
        self.assertTrue(self.go("5 + 8 == 6 + 7"))
        self.assertFalse(self.go("5 + 6 == 6 + 7"))
        self.assertFalse(self.go("5 + 8 != 6 + 7"))
        self.assertTrue(self.go("5 + 6 != 6 + 7"))

        self.assertTrue(self.go("5 + 7 < 6 + 7"))
        self.assertFalse(self.go("5 + 8 < 6 + 7"))
        self.assertFalse(self.go("5 + 8 < 5 + 7"))
        self.assertFalse(self.go("5 + 7 > 6 + 7"))
        self.assertFalse(self.go("5 + 8 > 6 + 7"))
        self.assertTrue(self.go("5 + 8 > 5 + 7"))

        self.assertTrue(self.go("5 + 7 <= 6 + 7"))
        self.assertTrue(self.go("5 + 8 <= 6 + 7"))
        self.assertFalse(self.go("5 + 8 <= 5 + 7"))
        self.assertFalse(self.go("5 + 7 >= 6 + 7"))
        self.assertTrue(self.go("5 + 8 >= 6 + 7"))
        self.assertTrue(self.go("5 + 8 >= 5 + 7"))

        self.assertEqual(self.go("not 5 == 6"), True)
        self.assertEqual(self.go("(not 5) == 6"), False)

    def test_add_sub(self):
        self.assertEqual(self.go("5 + 6 + 7"), 18)
        self.assertEqual(self.go("18 - 6 - 7"), 5)
        self.assertEqual(self.go("x := 5 + 6"), 11)
        self.assertEqual(self.go("x"), 11)

    def test_mul_div_mod(self):
        self.assertEqual(self.go("5 * 6 * 7"), 210)
        self.assertEqual(self.go("210 / 6 / 7"), 5)
        self.assertEqual(self.go("216 / 6 % 7"), 1)
        self.assertEqual(self.go("5 + 6 * 7"), 47)
        self.assertEqual(self.go("5 * 6 + 7"), 37)

    def test_neg(self):
        self.assertEqual(self.go("-5"), -5)
        self.assertEqual(self.go("-5 * 6"), -30)
        self.assertEqual(self.go("5 * -6"), -30)

    def test_call(self):
        self.assertEqual(self.go("add(5; 6, 7; 8)"), 14)
        self.assertEqual(self.go("inc(5; 6)"), 7)
        self.assertEqual(self.go("and(True, False)"), False)

        self.assertTrue(self.fails("inc(5"))
        self.assertTrue(self.fails("inc(5 6)"))

    def test_print(self):
        self.assertEqual(self.printed("print(None)"), (None, "None\n"))
        self.assertEqual(self.printed("print(5)"), (None, "5\n"))
        self.assertEqual(self.printed("print(True)"), (None, "True\n"))
        self.assertEqual(self.printed("print(False)"), (None, "False\n"))
        self.assertEqual(self.printed("print()"), (None, "\n"))
        self.assertEqual(self.printed("print(5, 6)"), (None, "5 6\n"))

    def test_paren(self):
        self.assertEqual(self.go("(5; 6) * 7"), 42)
        self.assertEqual(self.go("5 * (6; 7)"), 35)
        self.assertEqual(self.go("(5) + 6"), 11)

        self.assertTrue(self.fails("(5"))

    def test_array_by_builtins(self):
        self.assertEqual(self.go("arr()"), [])
        self.assertEqual(self.go("arr(5; 6)"), [6])
        self.assertEqual(self.go("arr(5; 6, 7; 8)"), [6, 8])
        self.assertTrue(self.go("is_arr(arr())"))
        self.assertFalse(self.go("is_arr(1)"))
        self.assertEqual(self.go("len(arr(5, 6, 7))"), 3)
        self.assertEqual(self.go("get_at(arr(5, 6, 7), 1)"), 6)
        self.assertEqual(self.go("set_at(arr(5, 6, 7), 1, 8)"), 8)
        self.assertEqual(self.go("slice(arr(5, 6, 7), 1, 2, None)"), [6])

    def test_array_literal(self):
        self.assertEqual(self.go("[]"), [])
        self.assertEqual(self.go("[5; 6]"), [6])
        self.assertEqual(self.go("[5; 6, 7; 8]"), [6, 8])

    def test_is_arr(self):
        self.assertTrue(self.go("is_arr([])"))
        self.assertFalse(self.go("is_arr(1)"))

    def test_array_len(self):
        self.assertEqual(self.go("len([5, 6, 7])"), 3)

    def test_array_index_slice(self):
        self.go("a := [5, 6, 7, 8, 9]")
        self.assertTrue(self.fails("a[]"))
        self.assertEqual(self.go("a[1]"), 6)
        self.assertEqual(self.go("a[:]"), [5, 6, 7, 8, 9])
        self.assertTrue(self.fails("a[1,]"))
        self.assertEqual(self.go("a[1:]"), [6, 7, 8, 9])
        self.assertEqual(self.go("a[1:4]"), [6, 7, 8])
        self.assertEqual(self.go("a[:4]"), [5, 6, 7, 8])
        self.assertTrue(self.fails("a[1:2,]"))
        self.assertEqual(self.go("a[3:1:-1]"), [8, 7])
        self.assertEqual(self.go("a[:1:-1]"), [9, 8, 7])
        self.assertEqual(self.go("a[3::-1]"), [8, 7, 6, 5])
        self.assertEqual(self.go("a[1:4:]"), [6, 7, 8])
        self.assertEqual(self.go("a[::-1]"), [9, 8, 7, 6, 5])
        self.assertEqual(self.go("a[:3:]"), [5, 6, 7])
        self.assertEqual(self.go("a[1::]"), [6, 7, 8, 9])
        self.assertEqual(self.go("a[::]"), [5, 6, 7, 8, 9])
        self.assertTrue(self.fails("a[1:2:3,"))

        self.assertEqual(self.go("a[0;3:0;1:0;-1]"), [8, 7])

        self.assertEqual(self.go("[[5, 6, 7], [15, 16, 17], [25, 26, 27]][1]"), [15, 16, 17])
        self.assertEqual(self.go("[[5, 6, 7], [15, 16, 17], [25, 26, 27]][1][2]"), 17)
        self.assertEqual(self.go("[add, sub][0](5, 6)"), 11)
        self.assertEqual(self.go("func (a, b) do [a, b] end (5, 6)[1]"), 6)

    def test_array_set(self):
        self.go("a := [5, 6, 7, 8, 9]")
        self.assertEqual(self.go("a[0; 1] = True or False"), True)
        self.assertEqual(self.go("a"), [5, True, 7, 8, 9])
        self.assertEqual(self.go("a[3:] = [10, 11]"), [10, 11])
        self.assertEqual(self.go("a"), [5, True, 7, 10, 11])
        self.go("a[1:4] = [12, 13, 14]")
        self.assertEqual(self.go("a"), [5, 12, 13, 14, 11])
        self.go("a[:2] = [15, 16]")
        self.assertEqual(self.go("a"), [15, 16, 13, 14, 11])
        self.go("a[3:1:-1] = [17, 18]")
        self.assertEqual(self.go("a"), [15, 16, 18, 17, 11])

        self.go("a := [[5, 6, 7], [15, 16, 17], [25, 26, 27]]")
        self.assertEqual(self.go("a[1] = []"), [])
        self.assertEqual(self.go("a"), [[5, 6, 7], [], [25, 26, 27]])
        self.assertEqual(self.go("a[0][2] = 8"), 8)
        self.assertEqual(self.go("a"), [[5, 6, 8], [], [25, 26, 27]])

        self.assertTrue(self.fails("5 + 6 = 7"))

    def test_func(self):
        self.assertEqual(self.go("func (a, b) do a + b end (5, 6)"), 11)
        self.assertEqual(self.go("func (*args) do args end ()"), [])
        self.assertEqual(self.go("func (*args) do args end (5)"), [5])
        self.assertEqual(self.go("func (*args) do args end (5, 6)"), [5, 6])
        self.assertEqual(self.go("func (*(args)) do args end (5, 6)"), [5, 6])

        self.assertEqual(self.go("func (*args, a) do [args, a] end (5)"), [[], 5])
        self.assertEqual(self.go("func (*args, a) do [args, a] end (5, 6)"), [[5], 6])
        self.assertEqual(self.go("func (*args, a) do [args, a] end (5, 6, 7)"), [[5, 6], 7])
        self.assertEqual(self.go("func (*args, a, b) do [args, a, b] end (5, 6, 7)"), [[5], 6, 7])
        self.assertEqual(self.go("func (a, *args, b) do [a, args, b] end (5, 6, 7)"), [5, [6], 7])
        self.assertEqual(self.go("func (a, b, *args) do [a, b, args] end (5, 6, 7)"), [5, 6, [7]])

        self.assertTrue(self.fails("*a"))
        self.assertTrue(self.fails("func (a, b) a + b end"))
        self.assertTrue(self.fails("func (a, b) do a + b"))
        self.assertTrue(self.fails("func a, b) do a + b end (5, 6)"))
        self.assertTrue(self.fails("func (a, b do a + b end (5, 6)"))
        self.assertTrue(self.fails("func (a b) do a + b end (5, 6)"))
        self.assertTrue(self.fails("func (a, b + c) do a + b end (5, 6)"))
        self.assertTrue(self.fails("func (a, b) do a + b end (5) do 6"))
        self.assertTrue(self.fails("func (a, b) do a + b end (5) 6 end"))

        self.assertTrue(self.fails("func (*args, a) do [args, a] end ()"))

    def test_closure_adder(self):
        self.go("make_adder := func (n) do func (m) do n + m end end")
        self.assertEqual(self.go("make_adder(5)(6)"), 11)

    def test_closure_counter(self):
        self.go("""
            make_counter := func () do c := 0; func() do c = c + 1 end end;
            counter1 := make_counter();
            counter2 := make_counter()
        """)
        self.assertEqual(self.go("counter1()"), 1)
        self.assertEqual(self.go("counter1()"), 2)
        self.assertEqual(self.go("counter2()"), 1)
        self.assertEqual(self.go("counter2()"), 2)
        self.assertEqual(self.go("counter1()"), 3)
        self.assertEqual(self.go("counter2()"), 3)

    def test_q(self):
        self.assertEqual(self.go("q(5)"), 5)
        self.assertEqual(self.go("q(None)"), None)
        self.assertEqual(self.go("q(foo)"), "foo")
        self.assertEqual(self.go("q([5, 6])"), ["arr", 5, 6])
        self.assertEqual(self.go("q(add(5, 6))"), ["add", 5, 6])
        self.assertEqual(self.go("q(5 + 6)"), ["add", 5, 6])

    def test_qq(self):
        self.assertEqual(self.go("qq 5 end"), 5)
        self.assertEqual(self.go("qq None end"), None)
        self.assertEqual(self.go("qq foo end"), "foo")
        self.assertEqual(self.go("qq [5, 6] end"), ["arr", 5, 6])
        self.assertEqual(self.go("qq add(5, 6) end"), ["add", 5, 6])
        self.assertEqual(self.go("qq 5 + 6 end"), ["add", 5, 6])

        self.assertEqual(self.go("qq !(add(5, 6)) end"), 11)
        self.assertEqual(self.go("qq add(5, !(6 ; 7)) end"), ["add", 5, 7])
        self.assertEqual(self.go("qq !(5 + 6) end"), 11)
        self.assertEqual(self.go("qq 5 + !(6; 7) end"), ["add", 5, 7])
        self.assertEqual(self.go("qq add(!!([5, 6])) end"), ["add", 5, 6])
        self.assertEqual(self.go("qq add(5, !!([6])) end"), ["add", 5, 6])

        self.assertEqual(self.go("qq if a == 5 then 6; 7 else !(8; 9) end end"),
                         ["if", ["equal", "a", 5], ["scope", ["seq", 6, 7]], ["scope", 9]])

    def test_macro(self):
        self.assertEqual(self.expanded("macro () do q(abc) end ()"), "abc")

        self.assertEqual(
            self.expanded("macro (a) do qq !(a) * !(a) end end (5 + 6)"),
            ["mul", ["add", 5, 6], ["add", 5, 6]])

        self.go("build_exp := macro (op, *r) do qq !(op)(!!(r)) end end")
        self.assertEqual(self.expanded("build_exp(add)"), ["add"])
        self.assertEqual(self.expanded("build_exp(add, 5)"), ["add", 5])
        self.assertEqual(self.expanded("build_exp(add, 5, 6)"), ["add", 5, 6])

        self.assertEqual(self.go("macro (*a, b) do qq [q(!(a)), q(!(b))] end end (5)"), [[], 5])
        self.assertEqual(self.go("macro (*a, b) do qq [q(!(a)), q(!(b))] end end (5, 6)"), [[5], 6])
        self.assertEqual(self.go("macro (*a, b) do qq [q(!(a)), q(!(b))] end end (5, 6, 7)"), [[5, 6], 7])
        self.assertEqual(self.go("macro (a, *b, c) do qq [q(!(a)), q(!(b)), q(!(c))] end end (5, 6, 7)"), [5, [6], 7])

    def test_custom(self):
        self.assertTrue(self.fails("""
            foo := macro (a) do qq print(!(a)) end end;
            #rule [foo, foo, 5, EXPR, end]
            foo 6 end
        """))

    def test_if(self):
        self.assertEqual(self.go("if 5; True then 6; 7 end"), 7)
        self.assertEqual(self.go("if 5; False then 6; 7 end"), None)
        self.assertEqual(self.go("if 5; True then 6; 7 else 8; 9 end"), 7)
        self.assertEqual(self.go("if 5; False then 6; 7 else 8; 9 end"), 9)
        self.assertEqual(self.go("if 5; True then 6; 7 elif 8; True then 9; 10 else 11; 12 end"), 7)
        self.assertEqual(self.go("if 5; False then 6; 7 elif 8; True then 9; 10 else 11; 12 end"), 10)
        self.assertEqual(self.go("if 5; False then 6; 7 elif 8; False then 9; 10 else 11; 12 end"), 12)

        self.assertEqual(self.go("-if 5; True then 6; 7 end"), -7)

        self.assertTrue(self.fails("if True end"))
        self.assertTrue(self.fails("if True then"))
        self.assertTrue(self.fails("if True then 5 else"))

    def test_letcc(self):
        self.assertEqual(self.go("letcc cc do 5 + 6 end"), 11)
        self.assertEqual(self.go("letcc cc do cc(5) + 6 end"), 5)
        self.assertEqual(self.go("5 + letcc cc do cc(6) end"), 11)
        self.assertEqual(self.go("letcc cc1 do cc1(letcc cc2 do cc2(5) + 6 end) + 7 end"), 5)

        self.assertEqual(self.go("""
            inner := func (raise) do raise(5) end;
            outer := func () do letcc raise do inner(raise) + 6 end end;
            outer()
        """), 5)

        self.go("add5 := None")
        self.assertEqual(self.go("5 + letcc cc do add5 = cc; 6 end"), 11)
        self.assertEqual(self.go("add5(7)"), 12)
        self.assertEqual(self.go("add5(8)"), 13)

class TestStdlib(TestToig):

    def test_id(self):
        self.assertEqual(self.go("id(5 + 6)"), 11)

    def test_inc_dec(self):
        self.assertEqual(self.go("inc(5 + 6)"), 12)
        self.assertEqual(self.go("dec(5 + 6)"), 10)

    def test_first_rest_last(self):
        self.go("a := [5, 6, 7]")
        self.assertEqual(self.go("first(a)"), 5)
        self.assertEqual(self.go("rest(a)"), [6, 7])
        self.assertEqual(self.go("last(a)"), 7)

    def test_append_prepend(self):
        self.go("a := [5, 6, 7]")
        self.assertEqual(self.go("append(a, 8)"), [5, 6, 7, 8])
        self.assertEqual(self.go("prepend(8, a)"), [8, 5, 6, 7])

    def test_foldl(self):
        self.assertEqual(self.go("foldl([5, 6, 7], add, 0)"), 18)
        self.assertEqual(self.go("foldl([5, 6, 7], append, [])"), [5, 6, 7])

    def test_unfoldl(self):
        self.assertEqual(self.go(
            "unfoldl(5, func (n) do n == 0 end, func (n) do n * 2 end, func (n) do n - 1 end)"),
            [10, 8, 6, 4, 2])

    def test_map(self):
        self.assertEqual(self.go("map([5, 6, 7], inc)"), [6, 7, 8])

    def test_range(self):
        self.assertEqual(self.go("range(5, 5)"), [])
        self.assertEqual(self.go("range(5, 8)"), [5, 6, 7])

    def test_scope(self):
        self.assertEqual(self.printed("""
            a := 5;
            scope a := 6; print(a) end;
            print(a)
        """), (None, "6\n5\n"))

    def test_when(self):
        self.assertEqual(self.go("when 5 == 5 do 5 / 5 end"), 1)
        self.assertEqual(self.go("when 5 == 0 do 5 / 0 end"), None)

    def test_aif(self):
        self.assertEqual(self.go("aif 5 then it + 1 end"), 6)
        self.assertEqual(self.go("aif 0 then it + 1 end"), None)

        self.assertEqual(self.go("aif 5 then it + 1 else it + 1 end"), 6)
        self.assertEqual(self.go("aif 0 then it + 1 else it + 1 end"), 1)

        self.assertEqual(self.go("aif 0 then 5 elif 6 then it + 1 end"), 7)
        self.assertEqual(self.go("aif 0 then 5 elif 0 then it + 1 end"), None)

        self.assertEqual(self.go("aif 0 then 5 elif 6 then it + 1 else it + 1 end"), 7)
        self.assertEqual(self.go("aif 0 then 5 elif 0 then it + 1 else it + 1 end"), 1)

        self.assertEqual(self.go("aif 0 then 5 elif 0 then 6 elif 7 then it + 1 end"), 8)
        self.assertEqual(self.go("aif 0 then 5 elif 0 then 6 elif 0 then it + 1 end"), None)

    def test_while(self):
        self.assertEqual(self.go("""
            i := sum := 0;
            while i < 10 do
                sum = sum + i;
                i = i + 1;
                sum
            end
        """), 45)

        self.assertEqual(self.go("""
            r := c := [];
            while len(r) < 3 do
                c = [];
                while len(c) < 3 do
                    c = c + [0]
                end;
                r = r + [c]
            end
        """), [[0, 0, 0], [0, 0, 0], [0, 0, 0]])

    def test_while_break(self):
        self.assertEqual(self.go("""
            i := sum := 0;
            while True do
                if i >= 10 then break(sum) end;
                sum = sum + i;
                i = i + 1
            end
        """), 45)

        self.assertTrue(self.fails("break(5)"))

    def test_while_continue(self):
        self.assertEqual(self.go("""
            i := sum := 0;
            while i < 10 do
                if i == 5 then i = i + 1; continue() end;
                sum = sum + i;
                i = i + 1;
                sum
            end
        """), 40)

        self.assertTrue(self.fails("continue(None)"))

    def test_awhile(self):
        self.assertEqual(self.go("""
            a := [5, 6, 7, 8, 9, False];
            i := sum := 0;
            awhile a[i] do
                i = i + 1;
                sum = sum + it
            end
        """), 35)

        self.assertEqual(self.go("""
            a := [5, 6, 7, 8, 9, False];
            i := sum := 0;
            awhile a[i] do
                i = i + 1;
                if it == 8 then break(sum) end;
                sum = sum + it
            end
        """), 18)

        self.assertEqual(self.go("""
            a := [5, 6, 7, 8, 9, False];
            i := sum := 0;
            awhile a[i] do
                i = i + 1;
                if it == 8 then continue() end;
                sum = sum + it
            end
        """), 27)

    def test_is_name(self):
        self.assertTrue(self.go("is_name(a)"))
        self.assertFalse(self.go("is_name(5)"))
        self.assertFalse(self.go("is_name(5 + 6)"))

    def test_for(self):
        self.assertEqual(self.go("""
            sum := 0;
            for i in [5, 6, 7, 8, 9] do
                sum = sum + i
            end
        """), 35)

        self.assertEqual(self.go("""
            sum := 0;
            for i in [5, 6, 7, 8, 9] do
                if i == 8 then break(sum) end;
                sum = sum + i
            end
        """), 18)

        self.assertEqual(self.go("""
            sum := 0;
            for i in [5, 6, 7, 8, 9] do
                if i == 8 then continue() end;
                sum = sum + i
            end
        """), 27)

        self.assertTrue(self.fails("for 3 + 7 in [1, 2, 3] do print(i) end"))

    def test_letcc_generator(self):
        self.go("""
            g3 := gfunc (n) do
                yield(n); n = inc(n);
                yield(n); n = inc(n);
                yield(n)
            end;
            gsum := func (gen) do aif gen() then it + gsum(gen) else 0 end end
        """)
        self.assertEqual(self.go("gsum(g3(2))"), 9)
        self.assertEqual(self.go("gsum(g3(5))"), 18)

        self.go("""
            walk := gfunc (tree) do
                _walk := func (t) do
                    if is_arr(first(t)) then _walk(first(t)) else yield(first(t)) end;
                    if is_arr(last(t)) then _walk(last(t)) else yield(last(t)) end
                end;
                _walk(tree)
            end;
            gen := walk([[[5, 6], 7], [8, [9, 10]]])
        """)
        self.assertEqual(
            self.printed("awhile gen() do print(it) end"),
            (None, "5\n6\n7\n8\n9\n10\n"))

    def test_agen(self):
        self.go("gen := agen([5, 6, 7])")
        self.assertEqual(self.go("gen()"), 5)
        self.assertEqual(self.go("gen()"), 6)
        self.assertEqual(self.go("gen()"), 7)
        self.assertEqual(self.go("gen()"), None)

        self.go("gen0 := agen([])")
        self.assertEqual(self.go("gen0()"), None)

    def test_gfor(self):
        self.assertEqual(self.printed("""
            gfor n in agen([]) do print(n) end
        """), (None, ""))
        self.assertEqual(self.printed("""
            gfor n in agen([5, 6, 7, 8, 9]) do print(n) end
        """), (None, "5\n6\n7\n8\n9\n"))
        self.assertEqual(self.printed("""
            gfor n in agen([5, 6, 7, 8, 9]) do
                if n == 8 then break(None) end;
                print(n)
            end
        """), (None, "5\n6\n7\n"))
        self.assertEqual(self.printed("""
            gfor n in agen([5, 6, 7, 8, 9]) do
                if n == 8 then continue() end;
                print(n)
            end
        """), (None, "5\n6\n7\n9\n"))

class TestProblems(TestToig):
    def test_factorial(self):
        self.go("""
            factorial := func (n) do
                if n == 1 then 1 else n * factorial(n - 1) end
            end
        """)
        self.assertEqual(self.go("factorial(1)"), 1)
        self.assertEqual(self.go("factorial(10)"), 3628800)

    def test_fib(self):
        self.go("""
            fib := func (n) do
                if n == 0 then 0
                elif n == 1 then 1
                else fib(n - 1) + fib(n - 2) end
            end
        """)
        self.assertEqual(self.go("fib(0)"), 0)
        self.assertEqual(self.go("fib(1)"), 1)
        self.assertEqual(self.go("fib(2)"), 1)
        self.assertEqual(self.go("fib(3)"), 2)
        self.assertEqual(self.go("fib(10)"), 55)

    def test_macro_firstclass(self):
        self.assertEqual(self.go("func(op, a, b) do op(a, b) end (and, True, False)"), False)
        self.assertEqual(self.go("func(op, a, b) do op(a, b) end (or, True, False)"), True)

        self.assertEqual(self.go("func() do and end ()(True, False)"), False)
        self.assertEqual(self.go("func() do or end ()(True, False)"), True)

        self.assertEqual(self.go("map([and, or], func(op) do op(True, False) end)"), [False, True])

    def test_sieve(self):
        self.assertEqual(self.go("""
            n := 30;
            sieve := [False] * 2 + [True] * (n - 2);
            j := None;
            for i in range(2, n) do
                when sieve[i] do
                    j = i * i;
                    while j < n do
                        sieve[j] = False;
                        j = j + i
                    end
                end
            end;
            primes := [];
            for i in range(0, n) do
                when sieve[i] do
                     primes = append(primes, i)
                end
            end
        """), [2, 3, 5, 7, 11, 13, 17, 19, 23, 29])

    def test_let(self):
        self.go("""
            _let := macro(bindings, body) do
                defines := func (bindings) do
                    map(bindings[1:], func (b) do
                        qq !(b[1]) := !(b[2]) end
                    end)
                end;
                qq scope
                    !!(defines(bindings)); !(body)
                end end
            end
        """)

        self.assertEqual(self.go("""
            #rule [let, _let, EXPR, do, EXPR, end]
            let [[a, 5], [b, 6]] do a + b end
        """), 11)

        self.assertEqual(self.go("""
            #rule [let2, _let, vars, EXPR, do, EXPR, end]
            let2 vars [[a, 5], [b, 6]] do a + b end
        """), 11)

        self.go("""
            _let3 := macro(*bindings, body) do
                defines := func (bindings) do
                    map(bindings, func (b) do
                        qq !(b[1]) := !(b[2]) end
                    end)
                end;
                qq scope
                    !!(defines(bindings)); !(body)
                end end
            end

            #rule [let3, _let3, *[var, EXPR], do, EXPR, end]
        """)

        self.assertEqual(self.go("let3 do 5 end"), 5)
        self.assertEqual(self.go("""
            let3
                var [a, 5]
                var [b, 6]
            do
                a + b
            end
        """), 11)

    def test_cond(self):
        self.go("""
            cond := macro(*clauses) do
                _cond := func (clauses) do
                    if clauses == [] then None else
                        clause := first(clauses);
                        cnd := clause[1];
                        thn := clause[2];
                        qq
                            if !(cnd) then !(thn) else !(_cond(rest(clauses))) end
                        end
                    end
                end;
                _cond(clauses)
            end
        """)
        self.go("""
            fib := func (n) do
                cond(
                    [n == 0, 0],
                    [n == 1, 1],
                    [True, fib(n - 1) + fib(n - 2)])
            end
        """)
        self.assertEqual(self.go("fib(0)"), 0)
        self.assertEqual(self.go("fib(1)"), 1)
        self.assertEqual(self.go("fib(2)"), 1)
        self.assertEqual(self.go("fib(3)"), 2)
        self.assertEqual(self.go("fib(10)"), 55)

    def test_my_if(self):
        self.go("""
            _my_if := macro(cnd, thn, *rest) do
                if len(rest) == 0 then
                    qq if !(cnd) then !(thn) else None end end
                elif len(rest) == 1 then
                    qq if !(cnd) then !(thn) else !(rest[0]) end end
                else qq
                    if !(cnd) then !(thn) else _my_if(!!(rest)) end
                end end
            end

            #rule [my_if, _my_if, EXPR, then, EXPR, *[elif, EXPR, then, EXPR], ?[else, EXPR], end]
        """)

        self.go("print(expand(_my_if(True, 5 + 6)))")
        self.go("print(expand(my_if True then 5 + 6 end))")

        self.go("print(expand(_my_if(True, 5 + 6, 7 + 8)))")
        self.go("print(expand(my_if True then 5 + 6 else 7 + 8 end))")

        self.go("print(expand(_my_if(False, 5 + 6, True, 7 + 8)))")
        self.go("print(expand(my_if False then 5 + 6 elif True then 7 + 8 end))")

        self.go("print(expand(_my_if(False, 5 + 6, True, 7 + 8, 9 + 10)))")
        self.go("print(expand(my_if False then 5 + 6 elif True then 7 + 8 else 9 + 10 end))")

        self.go("print(expand(_my_if(False, 5 + 6, False, 7 + 8, True, 9 + 10)))")
        self.go("print(expand(my_if False then 5 + 6 elif False then 7 + 8 elif True then 9 + 10 end))")

        self.go("print(expand(_my_if(False, 5 + 6, False, 7 + 8, True, 9 + 10, 11 + 12)))")
        self.go("print(expand(my_if False then 5 + 6 elif False then 7 + 8 elif True then 9 + 10 else 11 + 12 end))")

        self.assertEqual(self.go("_my_if(True, 5)"), 5)
        self.assertEqual(self.go("_my_if(False, 5)"), None)
        self.assertEqual(self.go("my_if True then 5 end"), 5)
        self.assertEqual(self.go("my_if False then 5 end"), None)

        self.assertEqual(self.go("_my_if(True, 5, 6)"), 5)
        self.assertEqual(self.go("_my_if(False, 5, 6)"), 6)
        self.assertEqual(self.go("my_if True then 5 else 6 end"), 5)
        self.assertEqual(self.go("my_if False then 5 else 6 end"), 6)

        self.assertEqual(self.go("_my_if(False, 5, True, 6)"), 6)
        self.assertEqual(self.go("_my_if(False, 5, False, 6)"), None)
        self.assertEqual(self.go("my_if False then 5 elif True then 6 end"), 6)
        self.assertEqual(self.go("my_if False then 5 elif False then 6 end"), None)

        self.assertEqual(self.go("_my_if(False, 5, True, 6, 7)"), 6)
        self.assertEqual(self.go("_my_if(False, 5, False, 6, 7)"), 7)
        self.assertEqual(self.go("my_if False then 5 elif True then 6 else 7 end"), 6)
        self.assertEqual(self.go("my_if False then 5 elif False then 6 else 7 end"), 7)

        self.assertEqual(self.go("_my_if(False, 5, False, 6, True, 7)"), 7)
        self.assertEqual(self.go("_my_if(False, 5, False, 6, False, 7)"), None)
        self.assertEqual(self.go("my_if False then 5 elif False then 6 elif True then 7 end"), 7)
        self.assertEqual(self.go("my_if False then 5 elif False then 6 elif False then 7 end"), None)

        self.assertEqual(self.go("_my_if(False, 5, False, 6, True, 7, 8)"), 7)
        self.assertEqual(self.go("_my_if(False, 5, False, 6, False, 7, 8)"), 8)
        self.assertEqual(self.go("my_if False then 5 elif False then 6 elif True then 7 else 8 end"), 7)
        self.assertEqual(self.go("my_if False then 5 elif False then 6 elif False then 7 else 8 end"), 8)

    def test_letcc_return(self):
        self.go("""
        early_return := func (n) do letcc return do
            if n == 1 then return(5) else 6 end;
            7
        end end
        """)
        self.assertEqual(self.go("early_return(1)"), 5)
        self.assertEqual(self.go("early_return(2)"), 7)

        self.go("""
            _runc := macro (params, body) do qq
                func (!!(rest(params))) do letcc return do !(body) end end
            end end;

            #rule [runc, _runc, PARAMS, do, EXPR, end]

            early_return_runc := runc (n) do if n == 1 then return(5) else 6 end; 7 end;
            early_return_runc2 := runc (n) do if early_return_runc(n) == 5 then return(6) else 7 end; 8 end
        """)
        self.assertEqual(self.go("early_return_runc(1)"), 5)
        self.assertEqual(self.go("early_return_runc(2)"), 7)
        self.assertEqual(self.go("early_return_runc2(1)"), 6)
        self.assertEqual(self.go("early_return_runc2(2)"), 8)

    def test_letcc_escape(self):
        self.go("""
            riskyfunc := func (n, escape) do
                if n == 1 then escape(5) else 6 end; 7
            end;
            middlefunc := func (n, escape) do
                riskyfunc(n, escape); 8
            end;
            parentfunc := func (n) do
                letcc escape do middlefunc(n, escape) end
            end
        """)
        self.assertEqual(self.go("parentfunc(1)"), 5)
        self.assertEqual(self.go("parentfunc(2)"), 8)

    def test_letcc_except(self):
        self.go("""
            raise := None;
            riskyfunc := func (n) do
                if n == 1 then raise(5) end; print(6)
            end;
            middlefunc := func (n) do
                riskyfunc(n); print(7)
            end;
            parentfunc := func (n) do
                letcc escape do
                    raise = func (e) do escape(print(e)) end;
                    middlefunc(n);
                    print(8)
                end;
                print(9)
            end
        """)
        self.assertEqual(self.printed("parentfunc(1) "), (None, "5\n9\n"))
        self.assertEqual(self.printed("parentfunc(2) "), (None, "6\n7\n8\n9\n"))

    def test_letcc_try(self):
        self.go("""
            raise := func (e) do error(q(raised_outside_of_try), e) end;
            _try := macro (try_expr, exc_var, exc_expr) do qq scope
                prev_raise := raise;
                letcc escape do
                    raise = func (!(exc_var)) do escape(!(exc_expr)) end;
                    !(try_expr)
                end;
                raise = prev_raise
            end end end;

            #rule [try, _try, EXPR, catch, EXPR, do, EXPR, end]

            riskyfunc := func (n) do
                if n == 1 then raise(5) end; print(6)
            end;
            middlefunc := func (n) do
                riskyfunc(n); print(7)
            end;
            parentfunc := func (n) do
                try
                    middlefunc(n); print(8)
                catch e do
                     print(e)
                end;
                print(9)
            end
        """)
        self.assertEqual(self.printed("parentfunc(1) "), (None, "5\n9\n"))
        self.assertEqual(self.printed("parentfunc(2) "), (None, "6\n7\n8\n9\n"))

        self.go("""
            nested := func (n) do
                try
                    if n == 1 then raise(5) end;
                    print(6);
                    try
                        if n == 2 then raise(7) end;
                        print(8)
                    catch e do
                        print(q(exception_inner_try), e)
                    end;
                    if n == 3 then raise(9) end;
                    print(10)
                catch e do
                    print(q(exception_outer_try), e)
                end;
                print(11)
            end
        """)
        self.assertEqual(self.printed("nested(1)"),  (None, "exception_outer_try 5\n11\n"))
        self.assertEqual(self.printed("nested(2)"),  (None, "6\nexception_inner_try 7\n10\n11\n"))
        self.assertEqual(self.printed("nested(3)"),  (None, "6\n8\nexception_outer_try 9\n11\n"))
        self.assertEqual(self.printed("nested(4)"),  (None, "6\n8\n10\n11\n"))

        self.assertTrue(self.fails("raise(5)"))

    def test_letcc_concurrent(self):
        self.go("""
            tasks := [];
            add_task := func (t) do tasks = append(tasks, t) end;
            start := func () do
                while tasks != [] do
                    next_task := first(tasks);
                    tasks = rest(tasks);
                    if next_task() then add_task(next_task) end
                end
            end;

            three_times := gfunc (n) do
                print(n); yield(True);
                print(n); yield(True);
                print(n)
            end;

            add_task(three_times(5));
            add_task(three_times(6));
            add_task(three_times(7))
        """)
        self.assertEqual(self.printed("start()"), (None, "5\n6\n7\n5\n6\n7\n5\n6\n7\n"))

    def test_replace_AST_element(self):
        self.go("""
            force_minus := macro(expr) do
                expr[0] = q(sub); expr
            end
        """)
        self.assertEqual(self.go("force_minus(5 + 6)"), -1)

if __name__ == "__main__":
    unittest.main()
