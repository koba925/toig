class StdLib:
    def __init__(self, interpreter):
        self._interpreter = interpreter

    def _go(self, src):
        self._interpreter.go(src)

    def load(self):
        self._go("__stdlib__ := None")

        self._go("None #rule [quasiquote, quasiquote, EXPR, end]")

        self._go("""
            defmacro scope with (body) do quasiquote
                func () do unquote(body) end ()
            end end

            #rule [scope, scope, EXPR, end]
        """)

        self._go("id := func (x) do x end")

        self._go("inc := func (n) do n + 1 end")
        self._go("dec := func (n) do n - 1 end")

        self._go("first := func (l) do l[0] end")
        self._go("rest := func (l) do l[1:] end")
        self._go("last := func (l) do l[-1] end")
        self._go("push := func (l, a) do l + [a] end")
        self._go("pop := func (l) do l[:-1] end")

        self._go("""
            foldl := func (l, f, init) do
                if l == [] then init else
                    foldl(rest(l), f, f(init, first(l)))
                end
            end
        """)
        self._go("""
            unfoldl := func (x, p, h, t) do
                _unfoldl := func (x, b) do
                    if p(x) then b else _unfoldl(t(x), b + [h(x)]) end
                end;
                _unfoldl(x, [])
            end
        """)

        self._go("""
            map := func (l, f) do
                foldl(l, func(acc, e) do push(acc, f(e)) end, [])
            end
        """)
        self._go("""
            range := func (s, e) do
                unfoldl(s, func (x) do x >= e end, id, inc)
            end
        """)

        self._go("""
            defmacro __stdlib_when with (cnd, thn) do quasiquote
                if unquote(cnd) then unquote(thn) end
            end end

            #rule [when, __stdlib_when, EXPR, do, EXPR, end]
        """)

        self._go("""
            defmacro _aif with  (cnd, thn, *rest) do
                if len(rest) == 0 then quasiquote scope
                    it := unquote(cnd); if it then unquote(thn) else None end
                end end elif len(rest) == 1 then quasiquote scope
                    it := unquote(cnd); if it then unquote(thn) else unquote(rest[0]) end
                end end else quasiquote scope
                    it := unquote(cnd); if it then unquote(thn) else _aif(unquote_splicing(rest)) end
                end end end
            end

            #rule [aif, _aif, EXPR, then, EXPR, *[elif, EXPR, then, EXPR], ?[else, EXPR], end]
        """)

        self._go("defmacro and with (a, b) do quasiquote aif unquote(a) then unquote(b) else it end end end")
        self._go("defmacro or with (a, b) do quasiquote aif unquote(a) then it else unquote(b) end end end")

        self._go("""
            zip := func (l1, l2) do
                unfoldl(
                    [l1, l2],
                    func (s) do first(s) == [] or last(s) == [] end,
                    func (s) do [first(first(s)), first(last(s))] end,
                    func (s) do [rest(first(s)), rest(last(s))] end
                )
            end
        """)

        self._go("""
            defmacro __stdlib_while with (cnd, body) do quasiquote scope
                continue := val := None;
                letcc break do
                    loop := func() do
                        letcc cc do continue = cc end;
                        if unquote(cnd) then val = unquote(body); loop() else val end
                    end;
                    loop()
                end
            end end end

            #rule [while, __stdlib_while, EXPR, do, EXPR, end]
        """)

        self._go("""
            defmacro __stdlib_awhile with (cnd, body) do quasiquote scope
                continue := val := None;
                letcc break do
                    loop := func() do
                        letcc cc do continue = cc end;
                        it := unquote(cnd);
                        if it then val = unquote(body); loop() else val end
                    end;
                    loop()
                end
            end end end

            #rule [awhile, __stdlib_awhile, EXPR, do, EXPR, end]
        """)

        self._go("""
            __stdlib_is_name_before := is_name;
            defmacro is_name with (e) do quasiquote __stdlib_is_name_before(quote(unquote(e))) end end
        """)

        self._go("""
            defmacro __stdlib_for with (e, l, body) do quasiquote scope
                __stdlib_for_index := -1;
                __stdlib_for_l := unquote(l);
                continue := __stdlib_for_val := unquote(e) := None;
                letcc break do
                    loop := func () do
                        letcc cc do continue = cc end;
                        __stdlib_for_index = __stdlib_for_index + 1;
                        if __stdlib_for_index < len(__stdlib_for_l) then
                            unquote(e) = __stdlib_for_l[__stdlib_for_index];
                            __stdlib_for_val = unquote(body);
                            loop()
                        else __stdlib_for_val end
                    end;
                    loop()
                end
            end end end

            #rule [for, __stdlib_for, NAME, in, EXPR, do, EXPR, end]
        """)

        self._go("""
            defmacro _runc with (params, body) do quasiquote
                func (unquote_splicing(rest(params))) do
                    letcc return do unquote(body) end
                end
            end end

            #rule [runc, _runc, PARAMS, do, EXPR, end]
        """)

        self._go("""
            defmacro __stdlib_gfunc with (params, body) do quasiquote
                func (unquote_splicing(params[1:])) do
                    yd := nx := None;
                    yield := func (x) do letcc cc do nx = cc; yd(x) end end;
                    next := func () do letcc cc do yd = cc; nx(None) end end;
                    nx := func (_) do unquote(body); yield(None) end;
                    next
                end
            end end

            #rule [gfunc, __stdlib_gfunc, PARAMS, do, EXPR, end]
        """)

        self._go("agen := gfunc (a) do for e in a do yield(e) end end")

        self._go("""
            defmacro __stdlib_gfor with (e, gen, body) do quasiquote scope
                __stdlib_gfor_gen := unquote(gen);
                unquote(e) := None;
                while (unquote(e) = __stdlib_gfor_gen()) != None do unquote(body) end
            end end end

            #rule [gfor, __stdlib_gfor, NAME, in, EXPR, do, EXPR, end]
        """)
