from toig_parser import CustomRules, Parser
from toig_evaluator import Environment, Evaluator

# Builtin Functions

def _set_at(args):
    args[0][args[1]] = args[2]
    return args[2]

def _slice(args):
    arr, start, end, step = args
    return arr[slice(start, end, step)]

def _set_slice(args):
    arr, start, end, step, val = args
    arr[start:end:step] = val
    return val

def _error(args):
    assert False, f"{' '.join(map(str, args))}"

_builtins = {
    "__builtins__": None,
    "add": lambda args: args[0] + args[1],
    "sub": lambda args: args[0] - args[1],
    "mul": lambda args: args[0] * args[1],
    "div": lambda args: args[0] // args[1],
    "mod": lambda args: args[0] % args[1],
    "neg": lambda args: -args[0],
    "equal": lambda args: args[0] == args[1],
    "not_equal": lambda args: args[0] != args[1],
    "less": lambda args: args[0] < args[1],
    "greater": lambda args: args[0] > args[1],
    "less_equal": lambda args: args[0] <= args[1],
    "greater_equal": lambda args: args[0] >= args[1],
    "not": lambda args: not args[0],

    "array": lambda args: args,
    "is_arr": lambda args: isinstance(args[0], list),
    "len": lambda args: len(args[0]),
    "get_at": lambda args: args[0][args[1]],
    "set_at": _set_at,
    "slice": _slice,
    "set_slice": _set_slice,

    "is_name": lambda args: isinstance(args[0], str),

    "print": lambda args: print(*args),
    "error": lambda args: _error(args)
}

class BuiltIns:
    @staticmethod
    def load(env):
        for name, func in _builtins.items():
            env.define(name, func)

# Standard Library

class StdLib:
    def __init__(self, interpreter):
        self._interpreter = interpreter

    def _run(self, src):
        self._interpreter.run(src)

    def load(self):
        self._run("__stdlib__ := None")

        self._run("None #rule [scope, scope, EXPR, end]")
        self._run("None #rule [quasiquote, quasiquote, EXPR, end]")

        self._run("id := func (x) do x end")

        self._run("inc := func (n) do n + 1 end")
        self._run("dec := func (n) do n - 1 end")

        self._run("first := func (l) do l[0] end")
        self._run("rest := func (l) do l[1:] end")
        self._run("last := func (l) do l[-1] end")
        self._run("append := func (l, a) do l + [a] end")
        self._run("prepend := func (a, l) do [a] + l end")

        self._run("""
            foldl := func (l, f, init) do
                if l == [] then init else
                    foldl(rest(l), f, f(init, first(l)))
                end
            end
        """)
        self._run("""
            unfoldl := func (x, p, h, t) do
                _unfoldl := func (x, b) do
                    if p(x) then b else _unfoldl(t(x), b + [h(x)]) end
                end;
                _unfoldl(x, [])
            end
        """)

        self._run("map := func (l, f) do foldl(l, func(acc, e) do append(acc, f(e)) end, []) end")
        self._run("range := func (s, e) do unfoldl(s, func (x) do x >= e end, id, inc) end")

        self._run("""
            __stdlib_when := macro (cnd, thn) do quasiquote
                if unquote(cnd) then unquote(thn) end
            end end

            #rule [when, __stdlib_when, EXPR, do, EXPR, end]
        """)

        self._run("""
            _aif := macro (cnd, thn, *rest) do
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

        self._run("and := macro (a, b) do quasiquote aif unquote(a) then unquote(b) else it end end end")
        self._run("or := macro (a, b) do quasiquote aif unquote(a) then it else unquote(b) end end end")

        self._run("""
            __stdlib_while := macro (cnd, body) do quasiquote scope
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

        self._run("""
            __stdlib_awhile := macro (cnd, body) do quasiquote scope
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

        self._run("""
            __stdlib_is_name_before := is_name;
            is_name := macro (e) do quasiquote __stdlib_is_name_before(quote(unquote(e))) end end
        """)

        self._run("""
            __stdlib_for := macro (e, l, body) do quasiquote scope
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

        self._run("""
            __stdlib_gfunc := macro (params, body) do quasiquote
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

        self._run("agen := gfunc (a) do for e in a do yield(e) end end")

        self._run("""
            __stdlib_gfor := macro(e, gen, body) do quasiquote scope
                __stdlib_gfor_gen := unquote(gen);
                unquote(e) := None;
                while (unquote(e) = __stdlib_gfor_gen()) != None do unquote(body) end
            end end end

            #rule [gfor, __stdlib_gfor, NAME, in, EXPR, do, EXPR, end]
        """)

# Interpreter

class Interpreter:
    def __init__(self):
        self._env = Environment()
        BuiltIns.load(self._env)
        self._env = Environment(self._env)
        self._custom_rule = CustomRules()
        StdLib(self).load()
        self._env = Environment(self._env)

    def parse(self, src):
        return Parser(src, self._custom_rule).parse()

    def run(self, src):
        return Evaluator(self.parse(src), self._env, ["$halt"]).eval()

if __name__ == "__main__":
    i = Interpreter()

    src = """
        a
    """

    print(i.parse(src))
    print(i.run(src))
