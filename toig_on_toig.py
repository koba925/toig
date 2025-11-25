import pytest

from test_commons import BaseTest

class BaseToigOnToigTest(BaseTest):
    @pytest.fixture(autouse=True)
    def setup_eval(self):

        # Utilities

        self.go(r"""
            is_space := func (c) do c == ' ' or c == "\n" end;
            is_digit := func (c) do '0' <= c and c <= '9' end;
            is_alphabet := func (c) do
                ('A' <= c and c <= 'Z') or ('a' <= c and c <= 'z')
            end
        """)

        self.go(r"""
            is_name_first := func (c) do is_alphabet(c) or c == '_' end;
            is_name_rest := func (c) do
                is_name_first(c) or is_digit(c)
            end
        """)

        self.go(r"""
            contains := runc (a, l) do
                for e in l do
                    if a == e then return(True) end
                end;
                False
            end
        """)

        # Scanner

        self.go(r"""
            scan := func (src, rules) do
                pos := 0;
                token := '';

                advance := func () do pos = pos + 1 end;

                current_char := func () do
                    if pos < len(src) then src[pos] else '$EOF' end
                end;

                append_char := func () do
                    token = token + current_char();
                    advance()
                end;

                word := func (is_rest) do
                    append_char();
                    while is_rest(current_char()) do append_char() end
                end;

                name := func () do
                    word(is_name_rest);
                    if token == 'None' then None
                    elif token == 'True' then True
                    elif token == 'False' then False
                    else token end
                end;

                raw_string := func () do
                    advance();
                    while (c := current_char()) != "'" do
                        if c == '$EOF' then
                            error('Unexpected end of string:', c)
                        end;
                        append_char()
                    end;
                    advance();
                    ['$STR', token]
                end;

                string := func () do
                    advance();
                    while (c := current_char()) != '"' do
                        if c == '$EOF' then
                            error('Unexpected end of string:', c)
                        end;
                        if c == '\' then
                            advance();
                            c := current_char();
                            if c == '$EOF' then
                                error('Unexpected end of string:', c)
                            end;
                            if c == 'n' then token = token + "\n"
                            else token = token + c end;
                            advance()
                        else
                            append_char()
                        end
                    end;
                    advance();
                    ['$STR', token]
                end;

                comment := func () do
                    advance();

                    line := "";
                    while not contains(current_char(), ["\n", '$EOF']) do
                        line = line + current_char();
                        advance()
                    end;
                    if line[0:5] == 'rule ' then
                        rule := parse(scan(line[5:], new_env()), new_env());
                        define(rules, rule[1], rule[2:])
                    end;
                    get_token()
                end;

                get_token := func () do
                    token = '';

                    while is_space(current_char()) do advance() end;

                    c := current_char();
                    if c == '$EOF' then '$EOF'
                    elif c == '#' then
                        comment()
                    elif is_name_first(c) then
                        name()
                    elif is_digit(c) then
                        word(is_digit);
                        to_int(token)
                    elif c == "'" then
                        raw_string()
                    elif c == '"' then
                        string()
                    elif c == '!' then
                        append_char();
                        if contains(current_char(), '!=') then append_char() end;
                        token
                    elif contains(c, '=<>!:') then
                        append_char();
                        if current_char() == '=' then append_char() end;
                        token
                    elif contains(c, '+-*/%?()[],;') then
                        append_char(); token
                    else
                        error('Invalid char:', c)
                    end
                end;

                tokens := [];
                while True do
                    token := get_token();
                    append(tokens, token);
                    if token == '$EOF' then break() end
                end;
                tokens
            end
        """)

        # Parser

        self.go(r"""
            parse := func (tokens, rules) do
                pos := 0;

                current_token := func () do tokens[pos] end;

                advance := func() do
                    pos = pos + 1;
                    tokens[pos - 1]
                end;

                match := func (expected) do
                    contains(current_token(), expected)
                end;

                consume := func (expected) do
                    if not match(expected) then
                        error('Expected:', expected, ', found:', current_token())
                    end;
                    advance()
                end;

                comma_separated_exprs := func (closing_token) do
                    cse := [];
                    if not match([closing_token]) then
                        append(cse, expression());
                        while match([',']) do
                            advance();
                            append(cse, expression())
                        end
                    end;
                    consume([closing_token]);
                    cse
                end;

                func_macro := func () do
                    op := advance();
                    consume(['(']);
                    params := comma_separated_exprs(')');
                    consume(['do']);
                    body := expression();
                    consume(['end']);
                    [op, params, body]
                end;

                if_ := func () do
                    advance();
                    cond_expr := expression();
                    consume(['then']);
                    then_expr := expression();
                    consume(['else']);
                    else_expr := expression();
                    consume(['end']);
                    ['if', cond_expr, then_expr, else_expr]
                end;

                custom := func (rule) do
                    _custom := func (r) do
                        if r == [] then []
                        elif r[0] == 'EXPR' then
                            [expression()] + [_custom(r[1:])][0]
                        elif r[0] == 'PARAMS' then
                            consume(['(']);
                            [comma_separated_exprs(")")] + _custom(r[1:])
                        elif is_str(r[0]) then
                            consume([r[0]]);
                            _custom(r[1:])
                        elif r[0][0] == '*' then
                            subrule := r[0][1]; elems := [];
                            while current_token() == subrule[1] do
                                advance();
                                elems = elems + _custom(subrule[2:])
                            end;
                            elems + _custom(r[1:])
                        elif r[0][0] == '?' then
                            subrule := r[0][1]; elems := [];
                            if current_token() == subrule[1] then
                                advance();
                                elems = elems + _custom(subrule[2:])
                            end;
                            elems + _custom(r[1:])
                        else
                            error('Illegal rule:', r)
                        end
                    end;

                    [rule[0]] + _custom(rule[1:])
                end;

                primary := func () do
                    c := current_token();
                    if c == None or is_bool(c) or is_int(c) then
                        advance()
                    elif is_array(c) and c[0] == '$STR' then
                        advance()
                    elif c == '(' then
                        advance(); expr := expression(); consume([')']);
                        expr
                    elif c == '[' then
                        advance();
                        ['array'] + comma_separated_exprs(']')
                    elif contains(c, ['func', 'macro']) then
                        func_macro()
                    elif c == '__if' then
                        if_()
                    elif has_name(rules, c) then
                        advance();
                        custom(get(rules, c))
                    else
                        advance()
                    end
                end;

                index_slice := runc (target) do
                    start := end := step := None;

                    if current_token() == "]" then
                        error("Invalid index/slice:", current_token())
                    end;
                    if current_token() != ":" then
                        start = expression()
                    end;
                    if current_token() == "]" then
                        advance();
                        return(["get_at", target, start])
                    end;

                    if current_token() != ":" then
                        error("Invalid index/slice:", current_token())
                    end;
                    advance();

                    if current_token() == "]" then
                        advance();
                        return(["slice", target, start, end, step])
                    end;
                    if current_token() != ":" then
                        end = expression()
                    end;
                    if current_token() == "]" then
                        advance();
                        return(["slice", target, start, end, step])
                    end;

                    if current_token() != ":" then
                        error("Invalid index/slice:", current_token())
                    end;
                    advance();
                    if current_token() == "]" then
                        advance();
                        return(["slice", target, start, end, step])
                    end;
                    if current_token() != ":" then
                        step = expression()
                    end;
                    if current_token() == "]" then
                        advance();
                        return(["slice", target, start, end, step])
                    end;

                    error("Invalid index/slice:", current_token())
                end;

                call_index := func () do
                    target := primary();
                    if match(['(', '[']) then
                        while match(['(', '[']) do
                            if advance() == '(' then
                                target = [target] + comma_separated_exprs(')')
                            else
                                target = index_slice(target)
                            end
                        end
                    end;
                    target
                end;

                unary_ops := func () do
                    c := current_token();
                    if c == '-' then
                        advance(); ['neg', unary_ops()]
                    elif c == '*' then
                        advance(); ['*', unary_ops()]
                    elif c == '?' then
                        advance(); ['?', unary_ops()]
                    elif c == '!' then
                        advance(); ['unquote', unary_ops()]
                    elif c == '!!' then
                        advance(); ['unquote_splicing', unary_ops()]
                    else
                        call_index()
                    end
                end;

                mul_div := runc () do
                    left := unary_ops();
                    while True do
                        op := current_token();
                        if op == '*' then
                            advance(); left = ['mul', left, unary_ops()]
                        elif op == '/' then
                            advance(); left = ['div', left, unary_ops()]
                        elif op == '%' then
                            advance(); left = ['mod', left, unary_ops()]
                        else
                            return(left)
                        end
                    end
                end;

                add_sub := runc () do
                    left := mul_div();
                    while True do
                        op := current_token();
                        if op == '+' then
                            advance(); left = ['add', left, mul_div()]
                        elif op == '-' then
                            advance(); left = ['sub', left, mul_div()]
                        else
                            return(left)
                        end
                    end
                end;

                comparison := runc () do
                    left := add_sub();
                    while True do
                        op := current_token();
                        if op == '==' then
                            advance(); left = ['equal', left, add_sub()]
                        elif op == '!=' then
                            advance(); left = ['not_equal', left, add_sub()]
                        elif op == '<' then
                            advance(); left = ['less', left, add_sub()]
                        elif op == '>' then
                            advance(); left = ['greater', left, add_sub()]
                        elif op == '<=' then
                            advance(); left = ['less_equal', left, add_sub()]
                        elif op == '>=' then
                            advance(); left = ['greater_equal', left, add_sub()]
                        else
                            return(left)
                        end
                    end
                end;

                not_ := func () do
                    c := current_token();
                    if c == 'not' then
                        advance(); ['not', not_()]
                    else
                        comparison()
                    end
                end;

                and_ := runc () do
                    left := not_();
                    while True do
                        op := current_token();
                        if op == 'and' then
                            advance(); left = ['and', left, not_()]
                        else
                            return(left)
                        end
                    end
                end;

                or_ := runc () do
                    left := and_();
                    while True do
                        op := current_token();
                        if op == 'or' then
                            advance(); left = ['or', left, and_()]
                        else
                            return(left)
                        end
                    end
                end;

                define_assign := func () do
                    left := or_();
                    op := current_token();
                    if op == ':=' then
                        advance(); ['define', left, define_assign()]
                    elif op == '=' then
                        advance(); ['assign', left, define_assign()]
                    else
                        left
                    end
                end;

                sequence := func () do
                    exprs := [define_assign()];
                    while current_token() == ';' do
                        advance();
                        append(exprs, define_assign())
                    end;
                    if len(exprs) == 1 then exprs[0] else ['seq'] + exprs end
                end;

                expression := func () do
                    sequence()
                end;

                expr := expression();
                if current_token() != '$EOF' then
                    error('Unexpected token at end:', current_token())
                end;
                expr
            end
        """)

        # Evaluator

        self.go(r"""
            new_env := func() do [None, []][:] end;
            enter_scope := func (env) do [env, []] end
        """)

        self.go(r"""
            define := runc (env, name, val) do
                for p in env[1] do
                    if p[0] == name then p[1] = val; return(val) end
                end;
                append(env[1], [name, val]);
                val
            end
        """)

        self.go(r"""
            assign := runc (env, name, val) do
                for p in env[1] do
                    if p[0] == name then p[1] = val; return(val) end
                end;
                if env[0] != None then
                    assign(env[0], name, val)
                else
                    error('Variable not found:', name)
                end
            end
        """)

        self.go(r"""
            get := runc (env, name) do
                for p in env[1] do
                    if p[0] == name then return(p[1]) end
                end;
                if env[0] != None then
                    get(env[0], name)
                else
                    error('Variable not found:', name)
                end
            end
        """)

        self.go(r"""
             has_name := runc (env, name) do
                for p in env[1] do
                    if p[0] == name then return(True) end
                end;
                if env[0] != None then
                    has_name(env[0], name)
                else
                    False
                end
            end
        """)

        self.go(r"""
            _eval := func (expr, env) do
                print("_eval", expr);
                if expr == None then
                    None
                elif is_bool(expr) or is_int(expr) then
                    expr
                elif is_str(expr) then
                    get(env, expr)
                elif expr[0] == '$STR' then
                    expr[1]
                elif expr[0] == 'func' then
                    ['closure', expr[1], expr[2], env]
                elif expr[0] == 'macro' then
                    ['mclosure', expr[1], expr[2], env]
                elif expr[0] == 'q' then
                    expr[1]
                elif expr[0] == '_qq' then
                    eval_quasiquote(expr[1], env)
                elif expr[0] == 'define' then
                    define(env, expr[1], _eval(expr[2], env))
                elif expr[0] == 'assign' then
                    eval_assign(expr, env)
                elif expr[0] == 'seq' then
                    eval_seq(expr, env)
                elif expr[0] == 'if' then
                    eval_if(expr, env)
                elif expr[0] == 'expand' then
                    eval_expand(expr[1][0], expr[1][1:], env)
                else
                    eval_op(expr[0], expr[1:], env)
                end
            end
        """)

        self.go(r"""
            eval_quasiquote := func (expr, env) do
                quote_elements := func (elems) do
                    quoted := [];
                    for elem in elems do
                        if is_array(elem) and len(elem) > 0 and elem[0] == "unquote_splicing" then
                            quoted = quoted + _eval(elem[1], env)
                        else
                            append(quoted, eval_quasiquote(elem, env))
                        end
                    end;
                    quoted
                end;

                if is_array(expr) and len(expr) > 0 then
                    if expr[0] == "unquote" then
                        _eval(expr[1], env)
                    else
                        quote_elements(expr)
                    end
                else
                    expr
                end
            end
        """)

        self.go(r"""
            eval_assign := func (expr, env) do
                if is_str(expr[1]) then
                    assign(env, expr[1], _eval(expr[2], env))
                elif expr[1][0] == 'get_at' then
                    eval_op("set_at", expr[1][1:] + [expr[2]], env)
                end
            end
        """)

        self.go(r"""
            eval_if := func (expr, env) do
                if _eval(expr[1], env) then
                    _eval(expr[2], env)
                else
                    _eval(expr[3], env)
                end
            end
        """)

        self.go(r"""
            eval_seq := func (expr, env) do
                val := None;
                for e in expr[1:] do
                    val = _eval(e, env)
                end;
                val
            end
        """)

        self.go(r"""
            eval_expand := func (op_expr, args_expr, env) do
                op_val := _eval(op_expr, env);
                params := op_val[1]; body := op_val[2]; menv := op_val[3];
                expand(body, params, args_expr, menv)
            end
        """)

        self.go(r"""
            eval_op := runc (op_expr, args_expr, env) do
                op_val := _eval(op_expr, env);
                kind := op_val[0];
                if kind == 'mclosure' then
                    params := op_val[1]; body := op_val[2]; menv := op_val[3];
                    return(_eval(expand(body, params, args_expr, menv), env))
                end;

                args_val := map(args_expr, func (arg) do _eval(arg, env) end);
                if kind == 'primitive' then
                    op_val[1](args_val)
                else
                    params := op_val[1]; body := op_val[2]; cenv := op_val[3];
                    _eval(body, extend(cenv, params, args_val))
                end
            end
        """)

        self.go(r"""
            apply_macro := func (op_val, args_expr, env) do
                params := op_val[1]; body := op_val[2]; menv := op_val[3];
                _eval(expand(body, params, args_expr, menv), env)
            end
        """)

        self.go(r"""
            expand := func (body, params, args, menv) do
                new_menv := extend(menv, params, args);
                _eval(body, new_menv)
            end
        """)

        self.go(r"""
            extend := func (env, params, args) do
                _extend := runc(params, args) do
                    if params == [] and args == [] then
                        return(env)
                    elif params == [] then
                        error('Too many arguments:', args)
                    end;

                    param := params[0];
                    if is_str(param) then
                        if args == [] then
                            error('Too many parameters:', params)
                        end;
                        define(env, param, args[0]);
                        _extend(rest(params), args[1:])
                    elif param[0] == '*' then
                        rest_len := len(args) - len(params) + 1;
                        define(env, param[1], args[:rest_len]);
                        _extend(params[1:], args[rest_len:])
                    else
                        error('Unexpected param:', param)
                    end
                end;

                env := enter_scope(env);
                _extend(params, args)
            end
        """)

        self.go(r"""
            global_env := [None, [
                ['id', ['primitive', func (args) do id(args[0]) end]],
                ['inc', ['primitive', func (args) do inc(args[0]) end]],
                ['dec', ['primitive', func (args) do dec(args[0]) end]],

                ['add', ['primitive', func (args) do args[0] + args[1] end]],
                ['sub', ['primitive', func (args) do args[0] - args[1] end]],
                ['mul', ['primitive', func (args) do args[0] * args[1] end]],
                ['div', ['primitive', func (args) do args[0] / args[1] end]],
                ['mod', ['primitive', func (args) do args[0] % args[1] end]],
                ['neg', ['primitive', func (args) do -args[0] end]],

                ['equal', ['primitive', func (args) do args[0] == args[1] end]],
                ['not_equal', ['primitive', func (args) do args[0] != args[1] end]],
                ['less', ['primitive', func (args) do args[0] < args[1] end]],
                ['greater', ['primitive', func (args) do args[0] > args[1] end]],
                ['less_equal', ['primitive', func (args) do args[0] <= args[1] end]],
                ['greater_equal', ['primitive', func (args) do args[0] >= args[1] end]],
                ['not', ['primitive', func (args) do not args[0] end]],

                ['array', ['primitive', func (args) do args end]],
                ['is_array', ['primitive', func (args) do is_array(args[0]) end]],
                ['len', ['primitive', func (args) do len(args[0]) end]],
                ['get_at', ['primitive', func (args) do get_at(args[0], args[1]) end]],
                ['set_at', ['primitive', func (args) do set_at(args[0], args[1], args[2]) end]],
                ['slice', ['primitive', func (args) do slice(args[0], args[1], args[2], args[3]) end]],
                ['first', ['primitive', func (args) do first(args[0]) end]],
                ['rest', ['primitive', func (args) do rest(args[0]) end]],
                ['last', ['primitive', func (args) do last(args[0]) end]],
                ['append', ['primitive', func (args) do append(args[0], args[1]) end]],

                ['map', ['primitive', func (args) do map(args[0], args[1]) end]],

                ['pytype', ['primitive', func (args) do pytype(args[0]) end]],

                ['print', ['primitive', func (args) do print(args[0]) end]],
                ['clock_ms', ['primitive', func (args) do clock_ms() end]]
            ]];
            eval := func (expr) do _eval(expr, global_env) end
        """)

        # Standard Library

        self.go(r"""
            stdlib := func () do
                go('None #rule [qq, _qq, EXPR, end]');
                go('
                    _defmacro := macro (name, params, body) do qq
                        !name := macro (!!params) do
                            !body
                        end
                    end end

                    #rule [defmacro, _defmacro, EXPR, with, PARAMS, do, EXPR, end]
                ');
                go('
                    defmacro _scope with (body) do qq
                        func () do !body end ()
                    end end

                    #rule [scope, _scope, EXPR, end]
                ');
                go('
                    defmacro _if with  (cnd, thn, *rest) do
                        __if len(rest) == 0 then qq scope
                            __if !cnd then !thn else None end
                        end end else
                            __if len(rest) == 1 then qq scope
                                __if !cnd then !thn else !rest[0] end
                            end end else qq scope
                                __if !cnd then !thn else _if(!!rest) end
                            end end end
                        end
                    end

                    #rule [if, _if, EXPR, then, EXPR, *[elif, EXPR, then, EXPR], ?[else, EXPR], end]
                ');
                go('
                    defmacro _aif with  (cnd, thn, *rest) do
                        __if len(rest) == 0 then qq scope
                            it := !cnd; __if it then !thn else None end
                        end end else
                            __if len(rest) == 1 then qq scope
                                it := !cnd; __if it then !thn else !rest[0] end
                            end end else qq scope
                                it := !cnd; __if it then !thn else _aif(!!rest) end
                            end end end
                        end
                    end

                    #rule [aif, _aif, EXPR, then, EXPR, *[elif, EXPR, then, EXPR], ?[else, EXPR], end]
                ');
                go('defmacro and with (a, b) do qq aif !a then !b else it end end end');
                go('defmacro or with (a, b) do qq aif !a then it else !b end end end')

            end
        """)

        # Interpreter

        self.go(r"""
            rules := new_env();
            go := func (src) do eval(parse(scan(src, rules), rules)) end;
            go_verbose := func (src) do
                print('src:', src);
                tokens := scan(src, rules);
                print('tokens:', tokens);
                print('rules:', rules);
                expr := parse(tokens, rules);
                print('expr:', expr);
                val := eval(expr);
                print('val:', val);
                val
            end;
            stdlib()
        """)

