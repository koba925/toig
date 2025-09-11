from commons import ValueType, is_name
from environment import Environment

from dataclasses import dataclass

@dataclass
class Expr:
    elems: ValueType

class Evaluator:
    def __init__(self, expr, env, cont):
        self._expr: Expr | ValueType = Expr(expr)
        self._env = env
        self._cont = cont

    def eval(self):
        while True:
            if isinstance(self._expr, Expr):
                self._eval_expr()
            elif self._cont == ["$halt"]:
                return self._expr
            else:
                self._apply_val()

    def _eval_expr(self):
        assert isinstance(self._expr, Expr)
        match self._expr.elems:
            case bool(_) | int(_) | None:
                self._expr = self._expr.elems
            case f if callable(f):
                self._expr = f
            case ["func", params, body]:
                self._expr = ["closure", params, body, self._env]
            case ["macro", params, body]:
                self._expr = ["mclosure", params, body, self._env]
            case str(name):
                self._expr = self._env.get(name)
            case ["quote", expr]:
                self._expr = expr
            case ["quasiquote", expr]:
                self._expr, self._cont = expr, ["$quasiquote", self._cont]
            case ["define", name, val_expr]:
                assert is_name(name), f"Invalid name: `{name}`"
                self._expr, self._cont = Expr(val_expr), \
                    ["$define", name, self._cont]
            case ["defmacro", name, params, body]:
                self._expr = Expr(["define", name, ["macro", params, body]])
            case ["assign", left, val_expr]:
                self._eval_assign(left, val_expr)
            case ["seq", *exprs]:
                self._expr, self._cont = None, \
                    ["$seq", exprs, self._cont]
            case ["if", cnd_expr, thn_expr, els_expr]:
                self._expr, self._cont = Expr(cnd_expr), \
                    ["$if", thn_expr, els_expr, self._cont]
            case ["letcc", name, body]:
                self._env.define(name, ["cont", self._env, self._cont])
                self._expr = Expr(body)
            case ["expand", [op_expr, *args_expr]]:
                self._expr, self._cont = Expr(op_expr), \
                    ["$expand", args_expr, self._env, self._cont]
            case ["$apply", op_val, args_val]:
                self._apply_op(op_val, args_val)
            case [op_expr, *args_expr]:
                self._expr, self._cont = Expr(op_expr), \
                    ["$call", args_expr, self._env, self._cont]
            case _:
                assert False, f"Invalid expression: {self._expr}"

    def _eval_assign(self, left, val_expr):
        match left:
            case name if is_name(name):
                self._expr, self._cont = Expr(val_expr), \
                    ["$assign", name, self._cont]
            case ["get_at", arr, idx]:
                self._expr = Expr(["set_at", arr, idx, val_expr])
            case ["slice", arr, start, end, step]:
                self._expr = Expr(["set_slice", arr, start, end, step, val_expr])
            case _:
                assert False, f"Invalid assign target: {left} @ eval_assign"

    def _apply_op(self, op_val, args_val):
        match op_val:
            case f if callable(f):
                self._expr = op_val(args_val)
            case ["closure", params, body_expr, closure_env]:
                closure_env = self.extend(closure_env, params, args_val)
                if not isinstance(self._cont, list) or \
                        self._cont[0] != "$restore_env":
                    self._cont = ["$restore_env", self._env, self._cont]
                self._expr, self._env = Expr(body_expr), closure_env
            case ["mclosure", params, body_expr, mclosure_env]:
                mclosure_env = self.extend(mclosure_env, params, args_val)
                self._expr, self._env, self._cont = Expr(body_expr), mclosure_env, \
                    ["$meval", self._env, self._cont]
            case ["cont", env, cont]:
                val = args_val[0] if args_val else None
                self._expr, self._env, self._cont = val, env, cont
            case _:
                assert False, f"Invalid function: {self._expr}"

    def _apply_val(self):
        assert not isinstance(self._expr, Expr), \
            f"Invalid value: {self._expr}"
        match self._cont:
            case ["$quasiquote", next_cont]:
                self._apply_quasiquote(next_cont)
            case ["$qq_elems", splicing, elems, elems_done, next_cont]:
                elems_done = self._qq_add_element(elems_done,splicing)
                self._apply_qq_elems(elems, elems_done, next_cont)
            case ["$define", name, next_cont]:
                self._apply_define(name, next_cont)
            case ["$assign", name, next_cont]:
                self._apply_assign(name, next_cont)
            case ["$seq", exprs, next_cont]:
                self._apply_seq(exprs, next_cont)
            case ["$if", thn_expr, els_expr, next_cont]:
                self._apply_if(thn_expr, els_expr, next_cont)
            case ["$call", args_expr, call_env, next_cont]:
                self._apply_call(args_expr, call_env, next_cont)
            case ["$args", op_expr, args_expr, args_val, call_env, next_cont]:
                self._apply_args(op_expr, args_expr, args_val, call_env, next_cont)
            case ["$expand", args_expr, call_env, next_cont]:
                self._apply_expand(args_expr, call_env, next_cont)
            case ["$meval", call_env, next_cont]:
                self._expr, self._env, self._cont = (
                    Expr(self._expr), call_env, next_cont
                )
            case ["$restore_env", env, next_cont]:
                self._env, self._cont = env, next_cont
            case _:
                assert False, f"Invalid continuation: {self._cont}"

    def _apply_quasiquote(self, next_cont):
        match self._expr:
            case ["unquote", expr]:
                self._expr = Expr(expr)
                self._cont = next_cont
            case [*elems]:
                self._apply_qq_elems(elems, [], next_cont)
            case _:
                self._cont = next_cont

    def _qq_add_element(self, elems_done, splicing):
        if splicing:
            assert isinstance(self._expr , list), f"Cannot splice: {self._expr}"
            return elems_done + self._expr
        else:
            return elems_done + [self._expr]

    def _apply_qq_elems(self, elems, elems_done, next_cont):
        match elems:
            case []:
                self._expr, self._cont  = elems_done, next_cont
            case [["unquote_splicing", elem], *rest]:
                self._expr = Expr(elem)
                self._cont = ["$qq_elems", True, rest, elems_done, next_cont]
            case [first, *rest]:
                self._expr = first
                self._cont = ["$quasiquote", ["$qq_elems", False, rest, elems_done, next_cont]]
            case _:
                assert False, f"Invalid quasiquote elements: {elems}"

    def _apply_define(self, name, next_cont):
        self._env.define(name, self._expr)
        self._cont = next_cont

    def _apply_assign(self, name, next_cont):
        self._env.assign(name, self._expr)
        self._cont = next_cont

    def _apply_seq(self, exprs, next_cont):
        match exprs:
            case []:
                self._cont = next_cont
            case [expr]:
                self._expr, self._cont = Expr(expr), next_cont
            case [expr, *rest]:
                self._expr, self._cont = Expr(expr), ["$seq", rest, next_cont]

    def _apply_if(self, thn_expr, els_expr, next_cont):
        if self._expr:
            self._expr, self._cont = Expr(thn_expr), next_cont
        else:
            self._expr, self._cont = Expr(els_expr), next_cont

    def _apply_call(self, args_expr, call_env, next_cont):
        match self._expr:
            case ["mclosure", _params, _body_expr, _mclosure_env]:
                self._expr, self._env, self._cont = (
                    Expr(["$apply", self._expr, args_expr]), call_env, next_cont
                )
            case op_val:
                self._apply_arg(op_val, args_expr, [], call_env, next_cont)

    def _apply_args(self, op_val, args_expr, args_val, call_env, next_cont):
        args_val = args_val + [self._expr]
        self._apply_arg(op_val, args_expr, args_val, call_env, next_cont)

    def _apply_arg(self, op_val, args_expr, args_val, call_env, next_cont):
        if args_expr == []:
            self._expr, self._env, self._cont = (
                Expr(["$apply", op_val, args_val]), call_env, next_cont
            )
        else:
            self._expr, self._env, self._cont = (
                Expr(args_expr[0]),
                call_env,
                ["$args", op_val, args_expr[1:], args_val, call_env, next_cont]
            )

    def _apply_expand(self, args_expr, call_env, next_cont):
        match self._expr:
            case ["mclosure", params, body_expr, mclosure_env]:
                mclosure_env = self.extend(mclosure_env, params, args_expr)
                if not isinstance(self._cont, list) or \
                        self._cont[0] != "$restore_env":
                    self._cont = ["$restore_env", call_env, next_cont]
                self._expr, self._env = (
                    Expr(body_expr), mclosure_env
                )
            case unexpected:
                assert False, f"Cannot expand: {unexpected}"

    def extend(self, env, params, args):
        def _extend(params, args):
            if params == [] and args == []: return {}
            assert len(params) > 0, \
                f"Argument count doesn't match: `{params}, {args}` @ extend"
            match params[0]:
                case str(param):
                    assert len(args) > 0, \
                        f"Argument count doesn't match: `{params}, {args}` @ extend"
                    env.define(param, args[0])
                    _extend(params[1:], args[1:])
                case ["*", rest]:
                    rest_len = len(args) - len(params) + 1
                    assert rest_len >= 0, \
                        f"Argument count doesn't match: `{params}, {args}` @ extend"
                    env.define(rest, args[:rest_len])
                    _extend(params[1:], args[rest_len:])
                case unexpected:
                    assert False, f"Unexpected param at extend: {unexpected}"

        env = Environment(env)
        _extend(params, args)
        return env
