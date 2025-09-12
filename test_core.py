from test_commons import Testable

class TestCoreBase(Testable):
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
        self.assertEqual(self.go("array()"), [])
        self.assertEqual(self.go("array(5; 6)"), [6])
        self.assertEqual(self.go("array(5; 6, 7; 8)"), [6, 8])
        self.assertTrue(self.go("is_array(array())"))
        self.assertFalse(self.go("is_array(1)"))
        self.assertEqual(self.go("len(array(5, 6, 7))"), 3)
        self.assertEqual(self.go("get_at(array(5, 6, 7), 1)"), 6)
        self.assertEqual(self.go("set_at(array(5, 6, 7), 1, 8)"), 8)
        self.assertEqual(self.go("slice(array(5, 6, 7), 1, 2, None)"), [6])

    def test_array_literal(self):
        self.assertEqual(self.go("[]"), [])
        self.assertEqual(self.go("[5; 6]"), [6])
        self.assertEqual(self.go("[5; 6, 7; 8]"), [6, 8])

    def test_is_array(self):
        self.assertTrue(self.go("is_array([])"))
        self.assertFalse(self.go("is_array(1)"))

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

    def test_quote(self):
        self.assertEqual(self.go("quote(5)"), 5)
        self.assertEqual(self.go("quote(None)"), None)
        self.assertEqual(self.go("quote(foo)"), "foo")
        self.assertEqual(self.go("quote([5, 6])"), ["array", 5, 6])
        self.assertEqual(self.go("quote(add(5, 6))"), ["add", 5, 6])
        self.assertEqual(self.go("quote(5 + 6)"), ["add", 5, 6])

    def test_quasiquote(self):
        self.assertEqual(self.go("quasiquote 5 end"), 5)
        self.assertEqual(self.go("quasiquote None end"), None)
        self.assertEqual(self.go("quasiquote foo end"), "foo")
        self.assertEqual(self.go("quasiquote [5, 6] end"), ["array", 5, 6])
        self.assertEqual(self.go("quasiquote add(5, 6) end"), ["add", 5, 6])
        self.assertEqual(self.go("quasiquote 5 + 6 end"), ["add", 5, 6])

        self.assertEqual(self.go("quasiquote unquote(add(5, 6)) end"), 11)
        self.assertEqual(self.go("quasiquote add(5, unquote(6 ; 7)) end"), ["add", 5, 7])
        self.assertEqual(self.go("quasiquote unquote(5 + 6) end"), 11)
        self.assertEqual(self.go("quasiquote 5 + unquote(6; 7) end"), ["add", 5, 7])
        self.assertEqual(self.go("quasiquote add(unquote_splicing([5, 6])) end"), ["add", 5, 6])
        self.assertEqual(self.go("quasiquote add(5, unquote_splicing([6])) end"), ["add", 5, 6])

        self.assertEqual(
            self.go("quasiquote unquote(when False do 5 end) end"),
            None)

        self.assertEqual(self.go("quasiquote if a == 5 then 6; 7 else unquote(8; 9) end end"),
                         ["if", ["equal", "a", 5], ["seq", 6, 7], 9])

    def test_defmacro(self):
        self.go("defmacro foo () do quote(abc) end")
        self.assertEqual(self.expanded("foo()"), "abc")

        self.go("""
            defmacro sq (a) do quasiquote unquote(a) * unquote(a) end end
        """)
        self.assertEqual(
            self.expanded("sq(5 + 6)"),
            ["mul", ["add", 5, 6], ["add", 5, 6]])

        self.go("defmacro build_exp (op, *r) do quasiquote unquote(op)(unquote_splicing(r)) end end")
        self.assertEqual(self.expanded("build_exp(add)"), ["add"])
        self.assertEqual(self.expanded("build_exp(add, 5)"), ["add", 5])
        self.assertEqual(self.expanded("build_exp(add, 5, 6)"), ["add", 5, 6])

        self.go("defmacro rest2 (*a, b) do quasiquote [quote(unquote(a)), quote(unquote(b))] end end")
        self.assertEqual(self.go("rest2(5)"), [[], 5])
        self.assertEqual(self.go("rest2(5, 6)"), [[5], 6])
        self.assertEqual(self.go("rest2(5, 6, 7)"), [[5, 6], 7])

        self.go("defmacro rest3 (a, *b, c) do quasiquote [quote(unquote(a)), quote(unquote(b)), quote(unquote(c))] end end")
        self.assertEqual(self.go("rest3(5, 6, 7)"), [5, [6], 7])

    def test_step_execution(self):
        self.go("""
            myadd := func (a, b) do a + b end;
            defmacro foo (a) do myadd([quote(array)], [a]) end;
            foo(5)
        """)


    def test_custom(self):
        self.assertTrue(self.fails("""
            defmacro foo (a) do quasiquote print(unquote(a)) end end;
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
