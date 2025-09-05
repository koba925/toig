import unittest
from test_toig import TestToig

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


if __name__ == "__main__":
    unittest.main()
