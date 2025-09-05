from ici_environment import Environment

class Expander:
    def __init__(self, vm):
        self._vm = vm

    def __repr__(self):
        return f"Expander({self._vm})"

    def expand(self, expr):
        return self._expr(expr)

    def _expr(self, expr):
        match expr:
            case None | bool(_) |int(_):
                return expr
            case ["array", *elems]:
                return ["array"] + [self._expr(elem) for elem in elems]
            case ["func", params, body]:
                return ["func", params, self._expr(body)]
            case str(name):
                return expr
            case ["quote", elem]:
                return ["quote", elem]
            case ["quasiquote", elem]:
                return self._quasiquote(elem)
            case ["defmacro", name, params, body]:
                return self._defmacro(name, params, self._expr(body))
            case ["define", name, val]:
                return ["define", name, self._expr(val)]
            case ["assign", name, val]:
                return ["assign", name, self._expr(val)]
            case ["seq", *exprs]:
                return ["seq"] + [self._expr(expr) for expr in exprs]
            case ["if", cnd, thn, els]:
                return ["if", self._expr(cnd), self._expr(thn), self._expr(els)]
            case ["letcc", name, body]:
                return ["letcc", name, self._expr(body)]
            case [op, *args] :
                if isinstance(op, str) and op in self._vm.menv():
                    macro = self._vm.menv().get(op)
                    return self._expr(self._macro(macro, args))
                else:
                    return [op] + [self._expr(arg) for arg in args]
            case unexpected:
                assert False, f"Unexpected expression: {unexpected}"

    def _defmacro(self, name, params, body):
        code = Compiler().compile(body)
        ncode = self._vm.load(code)
        self._vm.menv().define(name, ["macro", ncode, params])
        return None

    def _quasiquote(self, expr):
        def _quote_elements(elems):
            arr = ["array"]
            for elem in elems:
                match elem:
                    case ["unquote_splicing", e]:
                        arr = ["add", arr, self._expr(e)]
                    case _:
                        arr = ["add", arr, ["array", self._quasiquote(elem)]]
            return arr

        match expr:
            case ["unquote", elem]: return elem
            case [*elems]: return _quote_elements(elems)
            case elem: return ["quote", elem]

    def _macro(self, macro, args):
        match macro:
            case ["macro", ncode, params]:
                self._vm.new_scope()
                self._vm.extend(params, args)
                expanded = self._vm.execute(ncode)
                self._vm.drop_scope()
                return expanded
            case unexpected:
                assert False, f"Unexpected macro: {unexpected}"

class Compiler:
    def __init__(self):
        self._code = []

    def __repr__(self):
        return f"Compiler({self._code})"

    def compile(self, expr):
        self._expr(expr, False)
        self._code.append(["halt"])
        return self._code

    def _expr(self, expr, is_tail):
        match expr:
            case None | bool(_) |int(_):
                self._code.append(["const", expr])
            case ["array", *elems]:
                self._array(elems)
            case ["func", params, body]:
                self._func(params, body)
            case str(name):
                self._code.append(["get", name])
            case ["quote", elem]:
                self._code.append(["const", elem])
            case ["define", name, val]:
                self._expr(val, False)
                self._code.append(["def", name])
            case ["assign", name, val]:
                self._expr(val, False)
                self._code.append(["set", name])
            case ["seq", *exprs]:
                self._seq(exprs, is_tail)
            case ["if", cnd, thn, els]:
                self._if(cnd, thn, els, is_tail)
            case ["letcc", name, body]:
                self._letcc(name, body, is_tail)
            case [op, *args]:
                self._op(op, args, is_tail)
            case unexpected:
                assert False, f"Unexpected expression: {unexpected}"

    def _array(self, elems):
        for elem in elems: self._expr(elem, False)
        self._code.append(["array", len(elems)])

    def _func(self, params, body):
        skip_jump = self._current_addr()
        self._code.append(["jump", None])
        func_addr = self._current_addr()
        self._expr(body, True)
        self._code.append(["ret"])
        self._set_operand(skip_jump, self._current_addr())
        self._code.append(["func", func_addr, params])

    def _seq(self, exprs, is_tail):
        if len(exprs) == 0: return
        for expr in exprs[:-1]:
            self._expr(expr, False)
            self._code.append(["pop"])
        self._expr(exprs[-1], is_tail)

    def _if(self, cnd, thn, els, is_tail):
        self._expr(cnd, False)
        els_jump = self._current_addr()
        self._code.append(["jump_if_false", None])
        self._expr(thn, is_tail)
        end_jump = self._current_addr()
        self._code.append(["jump", None])
        self._set_operand(els_jump, self._current_addr())
        self._expr(els, is_tail)
        self._set_operand(end_jump, self._current_addr())

    def _letcc(self, name, body, is_tail):
        cont_jump = self._current_addr()
        self._code.append(["cc", None])
        self._func([name], body)
        if is_tail:
            self._code.append(["call_tail", 1])
        else:
            self._code.append(["call", 1])
        self._set_operand(cont_jump, self._current_addr())

    def _op(self, op, args, is_tail):
        for arg in args[-1::-1]:
            self._expr(arg, False)
        self._expr(op, False)
        if is_tail:
            self._code.append(["call_tail", len(args)])
        else:
            self._code.append(["call", len(args)])

    def _set_operand(self, ip, operand):
        self._code[ip][1] = operand

    def _current_addr(self):
        return len(self._code)

class VM:
    def __init__(self, env):
        self._codes = []
        self._stack = []
        self._call_stack = []
        self._ncode = 0
        self._ip = 0
        self._env = env
        self._menv = Environment()

    def __repr__(self):
        return f"VM({self._ncode}:{self._ip}, {self._env}, {self._menv})"

    def menv(self):
        return self._menv

    def load(self, code):
        self._codes.append(code)
        return len(self._codes) - 1

    def execute(self, ncode=None):
        self._stack = []
        self._call_stack = []
        self._ncode = len(self._codes) - 1 if ncode is None else ncode
        self._ip = 0
        while (inst := self._codes[self._ncode][self._ip]) != ["halt"]:
            match inst:
                case ["const", val]:
                    self._stack.append(val)
                case ["array", size]:
                    arr = [self._stack.pop() for _ in range(size)]
                    self._stack.append(list(reversed(arr)))
                case ["func", addr, params]:
                    self._stack.append(["closure", [self._ncode, addr], params, self._env])
                case ["cc", addr]:
                    self._stack.append(["cont",
                        [self._ncode, addr], self._env, self._stack[:], self._call_stack[:]])
                case ["pop"]:
                    self._stack.pop()
                case ["def", name]:
                    self._env.define(name, self._stack[-1])
                case ["set", name]:
                    self._env.assign(name, self._stack[-1])
                case ["get", name]:
                    self._stack.append(self._env.get(name))
                case ["jump", addr]:
                    self._ip = addr
                    continue
                case ["jump_if_false", addr]:
                    if not self._stack.pop():
                        self._ip = addr
                        continue
                case ["call", nargs]:
                    self._call(nargs, False)
                    continue
                case ["call_tail", nargs]:
                    self._call(nargs, True)
                    continue
                case ["ret"]:
                    [self._ncode, self._ip], self._env = self._call_stack.pop()
                    continue
                case unexpected:
                    assert False, f"Unexpected instruction: {unexpected}"
            self._ip += 1
        assert len(self._stack) == 1, f"Unused stack left: {self._stack}"
        return self._stack[0]

    def _call(self, nargs, is_tail):
        match self._stack.pop():
            case f if callable(f):
                f(nargs, self._stack)
                self._ip += 1
            case ["closure", [ncodes, addr], params, env]:
                args = [self._stack.pop() for _ in range(nargs)]
                if not is_tail:
                    self._call_stack.append([[self._ncode, self._ip + 1], self._env])
                    if len(self._call_stack) > 1000:
                        assert False, "Call stack overflow"
                self._env = Environment(env)
                self.extend(params, args)
                self._ncode, self._ip = [ncodes, addr]
            case ["cont", [ncodes, addr], env, stack, call_stack]:
                val = self._stack.pop()
                self._ncode, self._ip = [ncodes, addr]
                self._env = env
                self._stack = stack[:]
                self._stack.append(val)
                self._call_stack = call_stack[:]
            case unexpected:
                assert False, f"Unexpected call: {unexpected}"

    def new_scope(self):
        self._env = Environment(self._env)

    def drop_scope(self):
        assert isinstance(self._env, Environment)
        assert self._env._parent is not None
        self._env = self._env._parent

    def extend(self, params, args):
        if params == [] and args == []: return
        assert len(params) > 0, \
            f"Argument count doesn't match: `{params}, {args}`"
        match params[0]:
            case str(param):
                assert len(args) > 0, \
                    f"Argument count doesn't match: `{params}, {args}`"
                self._env.define(param, args[0])
                self.extend(params[1:], args[1:])
            case ["*", rest]:
                rest_len = len(args) - len(params) + 1
                assert rest_len >= 0, \
                    f"Argument count doesn't match: `{params}, {args}`"
                self._env.define(rest, args[:rest_len])
                self.extend(params[1:], args[rest_len:])
            case unexpected:
                assert False, f"Unexpected param: {unexpected}"
