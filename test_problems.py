import unittest
from test_toig import TestToig

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
                        quasiquote unquote(b[1]) := unquote(b[2]) end
                    end)
                end;
                quasiquote scope
                    unquote_splicing(defines(bindings)); unquote(body)
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

    def test_let3(self):
        self.go("""
            _let3 := macro(*bindings, body) do
                defines := func (bindings) do
                    map(bindings, func (b) do
                        quasiquote unquote(b[1]) := unquote(b[2]) end
                    end)
                end;
                quasiquote scope
                    unquote_splicing(defines(bindings)); unquote(body)
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

    def test_let4(self):
        self.go("""
            _let4 := macro(*bindings, body) do
                i := 0; defines := array();
                while i < len(bindings) do
                    defines = defines + array(
                        quasiquote unquote(bindings[i]) := unquote(bindings[i + 1]) end
                    );
                    i = i + 2
                end;
                quasiquote scope
                    unquote_splicing(defines); unquote(body)
                end end
            end

            #rule [let4, _let4, *[var, NAME, is, EXPR], do, EXPR, end]
        """)

        self.assertEqual(self.go("let4 do 5 end"), 5)
        self.assertEqual(self.go("""
            let4
                var a is 5
                var b is 6
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
                        quasiquote
                            if unquote(cnd) then unquote(thn) else unquote(_cond(rest(clauses))) end
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


    def test_cond2(self):
        self.go("""
            _cond := macro(*clauses) do
                __cond := func (clauses) do
                    if clauses == [] then None else
                        cnd := first(clauses); clauses := rest(clauses);
                        thn := first(clauses); clauses := rest(clauses);
                        quasiquote
                            if unquote(cnd) then unquote(thn) else unquote(__cond(clauses)) end
                        end
                    end
                end;
                __cond(clauses)
            end

            #rule [cond, _cond, *[case, EXPR, then, EXPR], end]
        """)
        self.go("""
            fib := func (n) do
                cond
                    case n == 0 then
                        0
                    case n == 1 then
                        1
                    case True then
                        fib(n - 1) + fib(n - 2)
                end
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
                    quasiquote if unquote(cnd) then unquote(thn) else None end end
                elif len(rest) == 1 then
                    quasiquote if unquote(cnd) then unquote(thn) else unquote(rest[0]) end end
                else quasiquote
                    if unquote(cnd) then unquote(thn) else _my_if(unquote_splicing(rest)) end
                end end
            end

            #rule [my_if, _my_if, EXPR, then, EXPR, *[elif, EXPR, then, EXPR], ?[else, EXPR], end]
        """)

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
            _runc := macro (params, body) do quasiquote
                func (unquote_splicing(rest(params))) do letcc return do unquote(body) end end
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
            raise := func (e) do error(quote(raised_outside_of_try), e) end;
            _try := macro (try_expr, exc_var, exc_expr) do quasiquote scope
                prev_raise := raise;
                letcc escape do
                    raise = func (unquote(exc_var)) do escape(unquote(exc_expr)) end;
                    unquote(try_expr)
                end;
                raise = prev_raise
            end end end;

            #rule [try, _try, EXPR, catch, NAME, do, EXPR, end]

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
                        print(quote(exception_inner_try), e)
                    end;
                    if n == 3 then raise(9) end;
                    print(10)
                catch e do
                    print(quote(exception_outer_try), e)
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
                expr[0] = quote(sub); expr
            end
        """)
        self.assertEqual(self.go("force_minus(5 + 6)"), -1)

if __name__ == "__main__":
    unittest.main()
