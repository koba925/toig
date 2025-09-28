import pytest

from test_commons import BaseTest
from ici import Interpreter as ICI
from stm import Interpreter as STM

@pytest.mark.parametrize(
    "set_interpreter",
    [ICI, STM], ids=["ici", "stm"],
    indirect=True)
class TestStdlib(BaseTest):
    def test_id(self):
        assert self.go("id(5 + 6)") == 11

    def test_inc_dec(self):
        assert self.go("inc(5 + 6)") == 12
        assert self.go("dec(5 + 6)") == 10

    def test_first_rest_last(self):
        self.go("a := [5, 6, 7]")
        assert self.go("first(a)") == 5
        assert self.go("rest(a)") == [6, 7]
        assert self.go("last(a)") == 7

    def test_push_pop(self):
        self.go("a := [5, 6, 7]")
        assert self.go("push(a, 8)") == [5, 6, 7, 8]
        assert self.go("pop(a)") == [5, 6]

    def test_foldl(self):
        assert self.go("foldl([5, 6, 7], add, 0)") == 18
        assert self.go("foldl([5, 6, 7], push, [])") == [5, 6, 7]

    def test_unfoldl(self):
        assert self.go(
            "unfoldl(5, func (n) do n == 0 end, func (n) do n * 2 end, func (n) do n - 1 end)") == [10, 8, 6, 4, 2]

    def test_map(self):
        assert self.go("map([5, 6, 7], inc)") == [6, 7, 8]

    def test_range(self):
        assert self.go("range(5, 5)") == []
        assert self.go("range(5, 8)") == [5, 6, 7]

    def test_scope(self, capsys):
        val = self.go("""
            a := 5;
            scope a := 6; print(a) end;
            print(a)
        """)
        assert val is None
        assert capsys.readouterr().out == "6\n5\n"

    def test_when(self):
        assert self.go("when 5 == 5 do 5 / 5 end") == 1
        assert self.go("when 5 == 0 do 5 / 0 end") is None

    def test_aif(self):
        assert self.go("aif 5 then it + 1 end") == 6
        assert self.go("aif 0 then it + 1 end") is None

        assert self.go("aif 5 then it + 1 else it + 1 end") == 6
        assert self.go("aif 0 then it + 1 else it + 1 end") == 1

        assert self.go("aif 0 then 5 elif 6 then it + 1 end") == 7
        assert self.go("aif 0 then 5 elif 0 then it + 1 end") is None

        assert self.go("aif 0 then 5 elif 6 then it + 1 else it + 1 end") == 7
        assert self.go("aif 0 then 5 elif 0 then it + 1 else it + 1 end") == 1

        assert self.go("aif 0 then 5 elif 0 then 6 elif 7 then it + 1 end") == 8
        assert self.go("aif 0 then 5 elif 0 then 6 elif 0 then it + 1 end") is None

    def test_zip(self):
        assert self.go("zip([], [])") == []
        assert self.go("zip([5], [15])") == [[5, 15]]
        assert self.go("zip([5, 6], [15, 16])") == [[5, 15], [6, 16]]
        assert self.go("zip([5, 6], [15])") == [[5, 15]]
        assert self.go("zip([5], [15, 16])") == [[5, 15]]

    def test_while(self):
        assert self.go("""
            i := sum := 0;
            while i < 10 do
                sum = sum + i;
                i = i + 1;
                sum
            end
        """) == 45

        assert self.go("""
            r := c := [];
            while len(r) < 3 do
                c = [];
                while len(c) < 3 do
                    c = c + [0]
                end;
                r = r + [c]
            end
        """) == [[0, 0, 0], [0, 0, 0], [0, 0, 0]]

    def test_while_break(self):
        assert self.go("""
            i := sum := 0;
            while True do
                if i >= 10 then break(sum) end;
                sum = sum + i;
                i = i + 1
            end
        """) == 45

        with pytest.raises(AssertionError):
            self.go("break(5)")

    def test_while_continue(self):
        assert self.go("""
            i := sum := 0;
            while i < 10 do
                if i == 5 then i = i + 1; continue() end;
                sum = sum + i;
                i = i + 1;
                sum
            end
        """) == 40

        with pytest.raises(AssertionError):
            self.go("continue(None)")

    def test_awhile(self):
        assert self.go("""
            a := [5, 6, 7, 8, 9, False];
            i := sum := 0;
            awhile a[i] do
                i = i + 1;
                sum = sum + it
            end
        """) == 35

        assert self.go("""
            a := [5, 6, 7, 8, 9, False];
            i := sum := 0;
            awhile a[i] do
                i = i + 1;
                if it == 8 then break(sum) end;
                sum = sum + it
            end
        """) == 18

        assert self.go("""
            a := [5, 6, 7, 8, 9, False];
            i := sum := 0;
            awhile a[i] do
                i = i + 1;
                if it == 8 then continue() end;
                sum = sum + it
            end
        """) == 27

    def test_is_name(self):
        assert self.go(r"""is_name(a)""") == True
        assert self.go(r"""is_name(None)""") == False
        assert self.go(r"""is_name(True)""") == False
        assert self.go(r"""is_name(5)""") == False
        assert self.go(r"""is_name("hello")""") == False
        assert self.go(r"""is_name(5 + 6)""") == False

    def test_for(self):
        assert self.go("""
            sum := 0;
            for i in [5, 6, 7, 8, 9] do
                sum = sum + i
            end
        """) == 35

        assert self.go("""
            sum := 0;
            for i in [5, 6, 7, 8, 9] do
                if i == 8 then break(sum) end;
                sum = sum + i
            end
        """) == 18

        assert self.go("""
            sum := 0;
            for i in [5, 6, 7, 8, 9] do
                if i == 8 then continue() end;
                sum = sum + i
            end
        """) == 27

        with pytest.raises(AssertionError):
            self.go("for 3 + 7 in [1, 2, 3] do print(i) end")

    def test_runc(self):
        self.go("""
            early_return_runc := runc (n) do
                if n == 1 then return(5) else 6 end; 7
            end;
            early_return_runc2 := runc (n) do
                if early_return_runc(n) == 5 then return(6) else 7 end; 8
            end
        """)
        assert self.go("early_return_runc(1)") == 5
        assert self.go("early_return_runc(2)") == 7
        assert self.go("early_return_runc2(1)") == 6
        assert self.go("early_return_runc2(2)") == 8

    def test_letcc_generator(self, capsys):
        self.go("""
            g3 := gfunc (n) do
                yield(n); n = inc(n);
                yield(n); n = inc(n);
                yield(n)
            end;
            gsum := func (gen) do aif gen() then it + gsum(gen) else 0 end end
        """)
        assert self.go("gsum(g3(2))") == 9
        assert self.go("gsum(g3(5))") == 18

        self.go("""
            walk := gfunc (tree) do
                _walk := func (t) do
                    if is_array(first(t)) then _walk(first(t)) else yield(first(t)) end;
                    if is_array(last(t)) then _walk(last(t)) else yield(last(t)) end
                end;
                _walk(tree)
            end;
            gen := walk([[[5, 6], 7], [8, [9, 10]]])
        """)
        val = self.go("awhile gen() do print(it) end")
        assert val is None
        assert capsys.readouterr().out == "5\n6\n7\n8\n9\n10\n"

    def test_agen(self):
        self.go("gen := agen([5, 6, 7])")
        assert self.go("gen()") == 5
        assert self.go("gen()") == 6
        assert self.go("gen()") == 7
        assert self.go("gen()") is None

        self.go("gen0 := agen([])")
        assert self.go("gen0()") is None

    def test_gfor(self, capsys):
        val = self.go("gfor n in agen([]) do print(n) end")
        assert val is None
        assert capsys.readouterr().out == ""

        val = self.go("gfor n in agen([5, 6, 7, 8, 9]) do print(n) end")
        assert val is None
        assert capsys.readouterr().out == "5\n6\n7\n8\n9\n"

        val = self.go("""
            gfor n in agen([5, 6, 7, 8, 9]) do
                if n == 8 then break(None) end;
                print(n)
            end
        """)
        assert val is None
        assert capsys.readouterr().out == "5\n6\n7\n"

        val = self.go("""
            gfor n in agen([5, 6, 7, 8, 9]) do
                if n == 8 then continue() end;
                print(n)
            end
        """)
        assert val is None
        assert capsys.readouterr().out == "5\n6\n7\n9\n"
