from test_commons import Testable

class TestTailCallOptimizationBase(Testable):
    def test_tco_if(self):
        self.assertEqual(self.go("""
            loop_els := func (n) do if n == 0 then 0 else loop_els(n - 1) end end;
            loop_els(10000)
        """), 0)
        self.assertEqual(self.go("""
            loop_thn := func (n) do if n != 0 then loop_thn(n - 1) else 0 end end;
            loop_thn(10000)
        """), 0)

    def test_tco_seq(self):
        self.assertEqual(self.go("""
            loop_seq := func (n) do
                1 + 1;
                if n == 0 then 0 else loop_seq(n - 1) end
            end;
            loop_seq(10000)
        """), 0)
        # self.assertTrue(self.fails("""
        #     loop_not_tail := func (n) do
        #         if n == 0 then 0 else loop_not_tail(n - 1) + 1 end
        #     end;
        #     loop_not_tail(10000)
        # """))

    def test_tco_mutual_recursion(self):
        self.go("""
            even := func (n) do
                if n == 0 then True else odd(n - 1) end
            end;
            odd := func (n) do
                if n == 0 then False else even(n - 1) end
            end
        """)
        self.assertEqual(self.go("even(10000)"), True)
        self.assertEqual(self.go("odd(10000)"), False)
        self.assertEqual(self.go("even(10001)"), False)
        self.assertEqual(self.go("odd(10001)"), True)

    def test_tco_fib_tail(self):
        self.go("""
            fib_tail := func (n) do
                rec := func (k, a, b) do
                    if k == n then a else rec(k + 1, b, a + b) end
                end;
                rec(0, 0, 1)
            end
        """)
        self.assertEqual(self.go("fib_tail(10)"), 55)
        self.go("fib_tail(10000)")
