import unittest
from unittest.mock import patch
from io import StringIO

from toig import init_env, init_rule, stdlib, run

def fails(expr):
    try: run(expr)
    except AssertionError: return True
    else: return False

def expanded(expr):
    return run(f"expand({expr})")

def printed(expr):
    with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
        val = run(expr)
        return (val, mock_stdout.getvalue())

class TestToig(unittest.TestCase):
    def setUp(self):
        init_env()
        init_rule()
        stdlib()

class TestCore(TestToig):
    def test_comment(self):
        self.assertEqual(run("5 # 6"), 5)
        self.assertEqual(run("""
            5 # 6
        """), 5)
        self.assertEqual(run("""
            # 5
            6
        """), 6)

    def test_primary(self):
        self.assertEqual(run("None"), None)
        self.assertEqual(run("5"), 5)
        self.assertEqual(run("True"), True)
        self.assertEqual(run("False"), False)

    def test_define(self):
        self.assertEqual(run("x := 5"), 5)
        self.assertEqual(run("x"), 5)
        self.assertEqual(run("y := z := 6"), 6)
        self.assertEqual(run("y"), 6)
        self.assertEqual(run("z"), 6)
        self.assertTrue(fails("6 := 5"), 5)

    def test_assign(self):
        self.assertEqual(run("x := y := 5"), 5)
        self.assertEqual(run("x = 6"), 6)
        self.assertEqual(run("x"), 6)
        self.assertEqual(run("x = y = 7"), 7)
        self.assertEqual(run("x"), 7)
        self.assertEqual(run("y"), 7)
        self.assertTrue(fails("z = 5"))
        self.assertTrue(fails("6 = 5"))

    def test_sequence(self):
        self.assertEqual(run("x := 5; y := 6; x + y"), 11)
        self.assertEqual(run("x"), 5)
        self.assertEqual(run("y"), 6)
        self.assertEqual(run("x = 6; y = 7; x * y"), 42)
        self.assertEqual(run("x"), 6)
        self.assertEqual(run("y"), 7)
        self.assertTrue(fails(";"))

    def test_or(self):
        self.assertTrue(run("5 == 5 or 5 == 5"))
        self.assertTrue(run("5 == 5 or 5 != 5"))
        self.assertTrue(run("5 != 5 or 5 == 5"))
        self.assertFalse(run("5 != 5 or 5 != 5"))

        self.assertEqual(run("5 or x"), 5)
        self.assertEqual(run("False or 5"), 5)

        self.assertTrue(run("False or False or True"))
        self.assertFalse(run("False or False or False"))

        self.assertEqual(run("x := True or False"), True)
        self.assertEqual(run("x"), True)

    def test_and(self):
        self.assertTrue(run("5 == 5 and 5 == 5"))
        self.assertFalse(run("5 == 5 and 5 != 5"))
        self.assertFalse(run("5 != 5 and 5 == 5"))
        self.assertFalse(run("5 != 5 and 5 != 5"))

        self.assertEqual(run("True and 5"), 5)
        self.assertEqual(run("0 and x"), 0)

        self.assertTrue(run("True or True and False"))
        self.assertFalse(run("(True or True) and False"))

    def test_not(self):
        self.assertFalse(run("not 5 == 5"))
        self.assertTrue(run("not 5 != 5"))

        self.assertFalse(run("not True and False"))
        self.assertTrue(run("not (True and False)"))

    def test_comparison(self):
        self.assertTrue(run("5 + 8 == 6 + 7"))
        self.assertFalse(run("5 + 6 == 6 + 7"))
        self.assertFalse(run("5 + 8 != 6 + 7"))
        self.assertTrue(run("5 + 6 != 6 + 7"))

        self.assertTrue(run("5 + 7 < 6 + 7"))
        self.assertFalse(run("5 + 8 < 6 + 7"))
        self.assertFalse(run("5 + 8 < 5 + 7"))
        self.assertFalse(run("5 + 7 > 6 + 7"))
        self.assertFalse(run("5 + 8 > 6 + 7"))
        self.assertTrue(run("5 + 8 > 5 + 7"))

        self.assertTrue(run("5 + 7 <= 6 + 7"))
        self.assertTrue(run("5 + 8 <= 6 + 7"))
        self.assertFalse(run("5 + 8 <= 5 + 7"))
        self.assertFalse(run("5 + 7 >= 6 + 7"))
        self.assertTrue(run("5 + 8 >= 6 + 7"))
        self.assertTrue(run("5 + 8 >= 5 + 7"))

        self.assertEqual(run("not 5 == 6"), True)
        self.assertEqual(run("(not 5) == 6"), False)

    def test_add_sub(self):
        self.assertEqual(run("5 + 6 + 7"), 18)
        self.assertEqual(run("18 - 6 - 7"), 5)
        self.assertEqual(run("x := 5 + 6"), 11)
        self.assertEqual(run("x"), 11)

    def test_mul_div_mod(self):
        self.assertEqual(run("5 * 6 * 7"), 210)
        self.assertEqual(run("210 / 6 / 7"), 5)
        self.assertEqual(run("216 / 6 % 7"), 1)
        self.assertEqual(run("5 + 6 * 7"), 47)
        self.assertEqual(run("5 * 6 + 7"), 37)

    def test_neg(self):
        self.assertEqual(run("-5"), -5)
        self.assertEqual(run("-5 * 6"), -30)
        self.assertEqual(run("5 * -6"), -30)

    def test_call(self):
        self.assertEqual(run("add(5; 6, 7; 8)"), 14)
        self.assertEqual(run("inc(5; 6)"), 7)
        self.assertEqual(run("and(True, False)"), False)

        self.assertTrue(fails("inc(5"))
        self.assertTrue(fails("inc(5 6)"))

    def test_print(self):
        self.assertEqual(printed("print(None)"), (None, "None\n"))
        self.assertEqual(printed("print(5)"), (None, "5\n"))
        self.assertEqual(printed("print(True)"), (None, "True\n"))
        self.assertEqual(printed("print(False)"), (None, "False\n"))
        self.assertEqual(printed("print()"), (None, "\n"))
        self.assertEqual(printed("print(5, 6)"), (None, "5 6\n"))

    def test_paren(self):
        self.assertEqual(run("(5; 6) * 7"), 42)
        self.assertEqual(run("5 * (6; 7)"), 35)
        self.assertEqual(run("(5) + 6"), 11)

        self.assertTrue(fails("(5"))

    def test_array_by_builtins(self):
        self.assertEqual(run("arr()"), [])
        self.assertEqual(run("arr(5; 6)"), [6])
        self.assertEqual(run("arr(5; 6, 7; 8)"), [6, 8])
        self.assertTrue(run("is_arr(arr())"))
        self.assertFalse(run("is_arr(1)"))
        self.assertEqual(run("len(arr(5, 6, 7))"), 3)
        self.assertEqual(run("getat(arr(5, 6, 7), 1)"), 6)
        self.assertEqual(run("setat(arr(5, 6, 7), 1, 8)"), 8)
        self.assertEqual(run("slice(arr(5, 6, 7), 1, 2)"), [6])

    def test_array_literal(self):
        self.assertEqual(run("[]"), [])
        self.assertEqual(run("[5; 6]"), [6])
        self.assertEqual(run("[5; 6, 7; 8]"), [6, 8])

    def test_is_arr(self):
        self.assertTrue(run("is_arr([])"))
        self.assertFalse(run("is_arr(1)"))

    def test_array_len(self):
        self.assertEqual(run("len([5, 6, 7])"), 3)

    def test_array_index_slice(self):
        run("a := [5, 6, 7, 8, 9]")
        self.assertTrue(fails("a[]"))
        self.assertEqual(run("a[1]"), 6)
        self.assertEqual(run("a[:]"), [5, 6, 7, 8, 9])
        self.assertTrue(fails("a[1,]"))
        self.assertEqual(run("a[1:]"), [6, 7, 8, 9])
        self.assertEqual(run("a[1:4]"), [6, 7, 8])
        self.assertEqual(run("a[:4]"), [5, 6, 7, 8])
        self.assertTrue(fails("a[1:2,]"))
        self.assertEqual(run("a[3:1:-1]"), [8, 7])
        self.assertEqual(run("a[:1:-1]"), [9, 8, 7])
        self.assertEqual(run("a[3::-1]"), [8, 7, 6, 5])
        self.assertEqual(run("a[1:4:]"), [6, 7, 8])
        self.assertEqual(run("a[::-1]"), [9, 8, 7, 6, 5])
        self.assertEqual(run("a[:3:]"), [5, 6, 7])
        self.assertEqual(run("a[1::]"), [6, 7, 8, 9])
        self.assertEqual(run("a[::]"), [5, 6, 7, 8, 9])
        self.assertTrue(fails("a[1:2:3,"))

        self.assertEqual(run("a[0;3:0;1:0;-1]"), [8, 7])

        self.assertEqual(run("[[5, 6, 7], [15, 16, 17], [25, 26, 27]][1]"), [15, 16, 17])
        self.assertEqual(run("[[5, 6, 7], [15, 16, 17], [25, 26, 27]][1][2]"), 17)
        self.assertEqual(run("[add, sub][0](5, 6)"), 11)
        self.assertEqual(run("func (a, b) do [a, b] end (5, 6)[1]"), 6)

    def test_array_set(self):
        run("a := [5, 6, 7, 8, 9]")
        self.assertEqual(run("a[0; 1] = True or False"), True)
        self.assertEqual(run("a"), [5, True, 7, 8, 9])
        self.assertEqual(run("a[3:] = [10, 11]"), [10, 11])
        self.assertEqual(run("a"), [5, True, 7, 10, 11])
        run("a[1:4] = [12, 13, 14]")
        self.assertEqual(run("a"), [5, 12, 13, 14, 11])
        run("a[:2] = [15, 16]")
        self.assertEqual(run("a"), [15, 16, 13, 14, 11])
        run("a[3:1:-1] = [17, 18]")
        self.assertEqual(run("a"), [15, 16, 18, 17, 11])

        run("a := [[5, 6, 7], [15, 16, 17], [25, 26, 27]]")
        self.assertEqual(run("a[1] = []"), [])
        self.assertEqual(run("a"), [[5, 6, 7], [], [25, 26, 27]])
        self.assertEqual(run("a[0][2] = 8"), 8)
        self.assertEqual(run("a"), [[5, 6, 8], [], [25, 26, 27]])

        self.assertTrue(fails("5 + 6 = 7"))

    def test_func(self):
        self.assertEqual(run("func (a, b) do a + b end (5, 6)"), 11)
        self.assertEqual(run("func (*args) do args end ()"), [])
        self.assertEqual(run("func (*args) do args end (5)"), [5])
        self.assertEqual(run("func (*args) do args end (5, 6)"), [5, 6])
        self.assertEqual(run("func (*(args)) do args end (5, 6)"), [5, 6])

        self.assertEqual(run("func (*args, a) do [args, a] end (5)"), [[], 5])
        self.assertEqual(run("func (*args, a) do [args, a] end (5, 6)"), [[5], 6])
        self.assertEqual(run("func (*args, a) do [args, a] end (5, 6, 7)"), [[5, 6], 7])
        self.assertEqual(run("func (*args, a, b) do [args, a, b] end (5, 6, 7)"), [[5], 6, 7])
        self.assertEqual(run("func (a, *args, b) do [a, args, b] end (5, 6, 7)"), [5, [6], 7])
        self.assertEqual(run("func (a, b, *args) do [a, b, args] end (5, 6, 7)"), [5, 6, [7]])

        self.assertTrue(fails("*a"))
        self.assertTrue(fails("func (a, b) a + b end"))
        self.assertTrue(fails("func (a, b) do a + b"))
        self.assertTrue(fails("func a, b) do a + b end (5, 6)"))
        self.assertTrue(fails("func (a, b do a + b end (5, 6)"))
        self.assertTrue(fails("func (a b) do a + b end (5, 6)"))
        self.assertTrue(fails("func (a, b + c) do a + b end (5, 6)"))
        self.assertTrue(fails("func (a, b) do a + b end (5) do 6"))
        self.assertTrue(fails("func (a, b) do a + b end (5) 6 end"))

        self.assertTrue(fails("func (*args, a) do [args, a] end ()"))

    def test_closure_adder(self):
        run("make_adder := func (n) do func (m) do n + m end end")
        self.assertEqual(run("make_adder(5)(6)"), 11)

    def test_closure_counter(self):
        run("""
            make_counter := func () do c := 0; func() do c = c + 1 end end;
            counter1 := make_counter();
            counter2 := make_counter()
        """)
        self.assertEqual(run("counter1()"), 1)
        self.assertEqual(run("counter1()"), 2)
        self.assertEqual(run("counter2()"), 1)
        self.assertEqual(run("counter2()"), 2)
        self.assertEqual(run("counter1()"), 3)
        self.assertEqual(run("counter2()"), 3)

    def test_q(self):
        self.assertEqual(run("q(5)"), 5)
        self.assertEqual(run("q(None)"), None)
        self.assertEqual(run("q(foo)"), "foo")
        self.assertEqual(run("q([5, 6])"), ["arr", 5, 6])
        self.assertEqual(run("q(add(5, 6))"), ["add", 5, 6])
        self.assertEqual(run("q(5 + 6)"), ["add", 5, 6])

    def test_qq(self):
        self.assertEqual(run("qq 5 end"), 5)
        self.assertEqual(run("qq None end"), None)
        self.assertEqual(run("qq foo end"), "foo")
        self.assertEqual(run("qq [5, 6] end"), ["arr", 5, 6])
        self.assertEqual(run("qq add(5, 6) end"), ["add", 5, 6])
        self.assertEqual(run("qq 5 + 6 end"), ["add", 5, 6])

        self.assertEqual(run("qq !(add(5, 6)) end"), 11)
        self.assertEqual(run("qq add(5, !(6 ; 7)) end"), ["add", 5, 7])
        self.assertEqual(run("qq !(5 + 6) end"), 11)
        self.assertEqual(run("qq 5 + !(6; 7) end"), ["add", 5, 7])
        self.assertEqual(run("qq add(!!([5, 6])) end"), ["add", 5, 6])
        self.assertEqual(run("qq add(5, !!([6])) end"), ["add", 5, 6])

        self.assertEqual(run("qq if a == 5 then 6; 7 else !(8; 9) end end"),
                         ["if", ["equal", "a", 5], ["scope", ["do", 6, 7]], ["scope", 9]])

    def test_macro(self):
        self.assertEqual(expanded("macro () do q(abc) end ()"), "abc")

        self.assertEqual(
            expanded("macro (a) do qq !(a) * !(a) end end (5 + 6)"),
            ["mul", ["add", 5, 6], ["add", 5, 6]])

        run("build_exp := macro (op, *r) do qq !(op)(!!(r)) end end")
        self.assertEqual(expanded("build_exp(add)"), ["add"])
        self.assertEqual(expanded("build_exp(add, 5)"), ["add", 5])
        self.assertEqual(expanded("build_exp(add, 5, 6)"), ["add", 5, 6])

        self.assertEqual(run("macro (*a, b) do qq [q(!(a)), q(!(b))] end end (5)"), [[], 5])
        self.assertEqual(run("macro (*a, b) do qq [q(!(a)), q(!(b))] end end (5, 6)"), [[5], 6])
        self.assertEqual(run("macro (*a, b) do qq [q(!(a)), q(!(b))] end end (5, 6, 7)"), [[5, 6], 7])
        self.assertEqual(run("macro (a, *b, c) do qq [q(!(a)), q(!(b)), q(!(c))] end end (5, 6, 7)"), [5, [6], 7])

    def test_if(self):
        self.assertEqual(run("if 5; True then 6; 7 end"), 7)
        self.assertEqual(run("if 5; False then 6; 7 end"), None)
        self.assertEqual(run("if 5; True then 6; 7 else 8; 9 end"), 7)
        self.assertEqual(run("if 5; False then 6; 7 else 8; 9 end"), 9)
        self.assertEqual(run("if 5; True then 6; 7 elif 8; True then 9; 10 else 11; 12 end"), 7)
        self.assertEqual(run("if 5; False then 6; 7 elif 8; True then 9; 10 else 11; 12 end"), 10)
        self.assertEqual(run("if 5; False then 6; 7 elif 8; False then 9; 10 else 11; 12 end"), 12)

        self.assertEqual(run("-if 5; True then 6; 7 end"), -7)

        self.assertTrue(fails("if True end"))
        self.assertTrue(fails("if True then"))
        self.assertTrue(fails("if True then 5 else"))

    def test_letcc(self):
        self.assertEqual(run("letcc cc do 5 + 6 end"), 11)
        self.assertEqual(run("letcc cc do cc(5) + 6 end"), 5)
        self.assertEqual(run("5 + letcc cc do cc(6) end"), 11)
        self.assertEqual(run("letcc cc1 do cc1(letcc cc2 do cc2(5) + 6 end) + 7 end"), 5)

        self.assertEqual(run("""
            inner := func (raise) do raise(5) end;
            outer := func () do letcc raise do inner(raise) + 6 end end;
            outer()
        """), 5)

        run("add5 := None")
        self.assertEqual(run("5 + letcc cc do add5 = cc; 6 end"), 11)
        self.assertEqual(run("add5(7)"), 12)
        self.assertEqual(run("add5(8)"), 13)

class TestStdlib(TestToig):

    def test_id(self):
        self.assertEqual(run("id(5 + 6)"), 11)

    def test_inc_dec(self):
        self.assertEqual(run("inc(5 + 6)"), 12)
        self.assertEqual(run("dec(5 + 6)"), 10)

    def test_first_rest_last(self):
        run("a := [5, 6, 7]")
        self.assertEqual(run("first(a)"), 5)
        self.assertEqual(run("rest(a)"), [6, 7])
        self.assertEqual(run("last(a)"), 7)

    def test_append_prepend(self):
        run("a := [5, 6, 7]")
        self.assertEqual(run("append(a, 8)"), [5, 6, 7, 8])
        self.assertEqual(run("prepend(8, a)"), [8, 5, 6, 7])

    def test_foldl(self):
        self.assertEqual(run("foldl([5, 6, 7], add, 0)"), 18)
        self.assertEqual(run("foldl([5, 6, 7], append, [])"), [5, 6, 7])

    def test_unfoldl(self):
        self.assertEqual(run(
            "unfoldl(5, func (n) do n == 0 end, func (n) do n * 2 end, func (n) do n - 1 end)"),
            [10, 8, 6, 4, 2])

    def test_map(self):
        self.assertEqual(run("map([5, 6, 7], inc)"), [6, 7, 8])

    def test_range(self):
        self.assertEqual(run("range(5, 5)"), [])
        self.assertEqual(run("range(5, 8)"), [5, 6, 7])

    def test_scope(self):
        self.assertEqual(printed("""
            a := 5;
            scope a := 6; print(a) end;
            print(a)
        """), (None, "6\n5\n"))

    def test_when(self):
        self.assertEqual(run("when 5 == 5 do 5 / 5 end"), 1)
        self.assertEqual(run("when 5 == 0 do 5 / 0 end"), None)

    def test_aif(self):
        self.assertEqual(run("aif(inc(5), inc(it), 8)"), 7)
        self.assertEqual(run("aif(dec(1), 5, inc(it))"), 1)

    def test_while(self):
        self.assertEqual(run("""
            i := sum := 0;
            while i < 10 do
                sum = sum + i;
                i = i + 1;
                sum
            end
        """), 45)

        self.assertEqual(run("""
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
        self.assertEqual(run("""
            i := sum := 0;
            while True do
                if i >= 10 then break(sum) end;
                sum = sum + i;
                i = i + 1
            end
        """), 45)

        self.assertTrue(fails("break(5)"))

    def test_while_continue(self):
        self.assertEqual(run("""
            i := sum := 0;
            while i < 10 do
                if i == 5 then i = i + 1; continue() end;
                sum = sum + i;
                i = i + 1;
                sum
            end
        """), 40)

        self.assertTrue(fails("continue(None)"))

    def test_awhile(self):
        self.assertEqual(run("""
            a := [5, 6, 7, 8, 9, False];
            i := sum := 0;
            awhile a[i] do
                i = i + 1;
                sum = sum + it
            end
        """), 35)

        self.assertEqual(run("""
            a := [5, 6, 7, 8, 9, False];
            i := sum := 0;
            awhile a[i] do
                i = i + 1;
                if it == 8 then break(sum) end;
                sum = sum + it
            end
        """), 18)

        self.assertEqual(run("""
            a := [5, 6, 7, 8, 9, False];
            i := sum := 0;
            awhile a[i] do
                i = i + 1;
                if it == 8 then continue() end;
                sum = sum + it
            end
        """), 27)

    def test_is_name(self):
        self.assertTrue(run("is_name(a)"))
        self.assertFalse(run("is_name(5)"))
        self.assertFalse(run("is_name(5 + 6)"))

    def test_for(self):
        self.assertEqual(run("""
            sum := 0;
            for i in [5, 6, 7, 8, 9] do
                sum = sum + i
            end
        """), 35)

        self.assertEqual(run("""
            sum := 0;
            for i in [5, 6, 7, 8, 9] do
                if i == 8 then break(sum) end;
                sum = sum + i
            end
        """), 18)

        self.assertEqual(run("""
            sum := 0;
            for i in [5, 6, 7, 8, 9] do
                if i == 8 then continue() end;
                sum = sum + i
            end
        """), 27)

        self.assertTrue(fails("for 3 + 7 in [1, 2, 3] do print(i) end"))

    def test_letcc_generator(self):
        run("""
            g3 := gfunc (n) do
                yield(n); n = inc(n);
                yield(n); n = inc(n);
                yield(n)
            end;
            gsum := func (gen) do aif(gen(), it + gsum(gen), 0) end
        """)
        self.assertEqual(run("gsum(g3(2))"), 9)
        self.assertEqual(run("gsum(g3(5))"), 18)

        run("""
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
            printed("awhile gen() do print(it) end"),
            (None, "5\n6\n7\n8\n9\n10\n"))

    def test_agen(self):
        run("gen := agen([5, 6, 7])")
        self.assertEqual(run("gen()"), 5)
        self.assertEqual(run("gen()"), 6)
        self.assertEqual(run("gen()"), 7)
        self.assertEqual(run("gen()"), None)

        run("gen0 := agen([])")
        self.assertEqual(run("gen0()"), None)

    def test_gfor(self):
        self.assertEqual(printed("""
            gfor n in agen([]) do print(n) end
        """), (None, ""))
        self.assertEqual(printed("""
            gfor n in agen([5, 6, 7, 8, 9]) do print(n) end
        """), (None, "5\n6\n7\n8\n9\n"))
        self.assertEqual(printed("""
            gfor n in agen([5, 6, 7, 8, 9]) do
                if n == 8 then break(None) end;
                print(n)
            end
        """), (None, "5\n6\n7\n"))
        self.assertEqual(printed("""
            gfor n in agen([5, 6, 7, 8, 9]) do
                if n == 8 then continue() end;
                print(n)
            end
        """), (None, "5\n6\n7\n9\n"))

class TestProblems(TestToig):
    def test_factorial(self):
        run("""
            factorial := func (n) do
                if n == 1 then 1 else n * factorial(n - 1) end
            end
        """)
        self.assertEqual(run("factorial(1)"), 1)
        self.assertEqual(run("factorial(10)"), 3628800)

    def test_fib(self):
        run("""
            fib := func (n) do
                if n == 0 then 0
                elif n == 1 then 1
                else fib(n - 1) + fib(n - 2) end
            end
        """)
        self.assertEqual(run("fib(0)"), 0)
        self.assertEqual(run("fib(1)"), 1)
        self.assertEqual(run("fib(2)"), 1)
        self.assertEqual(run("fib(3)"), 2)
        self.assertEqual(run("fib(10)"), 55)

    def test_macro_firstclass(self):
        self.assertEqual(run("func(op, a, b) do op(a, b) end (and, True, False)"), False)
        self.assertEqual(run("func(op, a, b) do op(a, b) end (or, True, False)"), True)

        self.assertEqual(run("func() do and end ()(True, False)"), False)
        self.assertEqual(run("func() do or end ()(True, False)"), True)

        self.assertEqual(run("map([and, or], func(op) do op(True, False) end)"), [False, True])

    def test_sieve(self):
        self.assertEqual(run("""
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
        run("""
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

        self.assertEqual(run("""
            #rule [let, _let, EXPR, do, EXPR, end]

            let [
                [a, 5],
                [b, 6]
            ] do a + b end
        """), 11)

        self.assertEqual(run("""
            #rule [let2, _let, vars, EXPR, do, EXPR, end]

            let2 vars [
                [a, 5],
                [b, 6]
            ] do a + b end
        """), 11)

    def test_cond(self):
        run("""
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
        run("""
            fib := func (n) do
                cond(
                    [n == 0, 0],
                    [n == 1, 1],
                    [True, fib(n - 1) + fib(n - 2)])
            end
        """)
        self.assertEqual(run("fib(0)"), 0)
        self.assertEqual(run("fib(1)"), 1)
        self.assertEqual(run("fib(2)"), 1)
        self.assertEqual(run("fib(3)"), 2)
        self.assertEqual(run("fib(10)"), 55)

    def test_letcc_return(self):
        run("""
        early_return := func (n) do letcc return do
            if n == 1 then return(5) else 6 end;
            7
        end end
        """)
        self.assertEqual(run("early_return(1)"), 5)
        self.assertEqual(run("early_return(2)"), 7)

        run("""
            _runc := macro (params, body) do qq
                func (!!(rest(params))) do letcc return do !(body) end end
            end end;

            #rule [runc, _runc, PARAMS, do, EXPR, end]

            early_return_runc := runc (n) do if n == 1 then return(5) else 6 end; 7 end;
            early_return_runc2 := runc (n) do if early_return_runc(n) == 5 then return(6) else 7 end; 8 end
        """)
        self.assertEqual(run("early_return_runc(1)"), 5)
        self.assertEqual(run("early_return_runc(2)"), 7)
        self.assertEqual(run("early_return_runc2(1)"), 6)
        self.assertEqual(run("early_return_runc2(2)"), 8)

    def test_letcc_escape(self):
        run("""
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
        self.assertEqual(run("parentfunc(1)"), 5)
        self.assertEqual(run("parentfunc(2)"), 8)

    def test_letcc_except(self):
        run("""
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
        self.assertEqual(printed("parentfunc(1) "), (None, "5\n9\n"))
        self.assertEqual(printed("parentfunc(2) "), (None, "6\n7\n8\n9\n"))

    def test_letcc_try(self):
        run("""
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
        self.assertEqual(printed("parentfunc(1) "), (None, "5\n9\n"))
        self.assertEqual(printed("parentfunc(2) "), (None, "6\n7\n8\n9\n"))

        run("""
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
        self.assertEqual(printed("nested(1)"),  (None, "exception_outer_try 5\n11\n"))
        self.assertEqual(printed("nested(2)"),  (None, "6\nexception_inner_try 7\n10\n11\n"))
        self.assertEqual(printed("nested(3)"),  (None, "6\n8\nexception_outer_try 9\n11\n"))
        self.assertEqual(printed("nested(4)"),  (None, "6\n8\n10\n11\n"))

        self.assertTrue(fails("raise(5)"))

    def test_letcc_concurrent(self):
        run("""
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
        self.assertEqual(printed("start()"), (None, "5\n6\n7\n5\n6\n7\n5\n6\n7\n"))

    def test_replace_AST_element(self):
        run("""
            force_minus := macro(expr) do
                expr[0] = q(sub); expr
            end
        """)
        self.assertEqual(run("force_minus(5 + 6)"), -1)

if __name__ == "__main__":
    unittest.main()
