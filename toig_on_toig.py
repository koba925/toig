import pytest

from test_commons import BaseTest

class BaseToigOnToigTest(BaseTest):
    @pytest.fixture(autouse=True)
    def setup_eval(self):

        # Utilities

        self.go(r"""
            is_space := func (c) do c == " " or c == "\n" end;
            is_digit := func (c) do "0" <= c and c <= "9" end;
            is_alphabet := func (c) do
                ("A" <= c and c <= "Z") or  ("a" <= c and c <= "z")
            end
        """)

        self.go("""
            is_name_first := func (c) do is_alphabet(c) or c == "_" end;
            is_name_rest := func (c) do
                is_name_first(c) or is_digit(c)
            end
        """)

        self.go("""
            contains := runc (a, l) do
                for e in l do
                    if a == e then return(True) end
                end;
                False
            end
        """)

        # Scanner

        self.go(r"""
            scan := func (src) do
                pos := 0;
                token := "";

                advance := func () do pos = pos + 1 end;

                current_char := func () do
                    if pos < len(src) then src[pos] else "$EOF" end
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
                    if token == "None" then None
                    elif token == "True" then True
                    elif token == "False" then False
                    else token end
                end;

                raw_string := func () do
                    advance();
                    while (c := current_char()) != "'" do
                        if c == "$EOF" then error(c) end;
                        append_char()
                    end;
                    advance();
                    ["$STR", token]
                end;

                string := func () do
                    advance();
                    while (c := current_char()) != "\"" do
                        if c == "$EOF" then error(c) end;
                        if c == "\\" then
                            advance();
                            c := current_char();
                            if c == "$EOF" then error(c) end;
                            if c == "n" then token = token + "\n"
                            else token = token + c end;
                            advance()
                        else
                            append_char()
                        end
                    end;
                    advance();
                    ["$STR", token]
                end;

                get_token := func () do
                    token = "";

                    while is_space(current_char()) do advance() end;

                    c := current_char();
                    if c == "$EOF" then "$EOF"
                    elif is_name_first(c) then
                        name()
                    elif is_digit(c) then
                        word(is_digit);
                        to_int(token)
                    elif c == "'" then
                        raw_string()
                    elif c == "\"" then
                        string()
                    else error(c) end
                end;

                tokens := [];
                while True do
                    token := get_token();
                    append(tokens, token);
                    if token == "$EOF" then break() end
                end;
                tokens
            end
        """)

        # Parser

        self.go("""
            parse := func (tokens) do
                pos := 0;

                current_token := func () do tokens[pos] end;
                advance := func() do
                    pos = pos + 1;
                    tokens[pos - 1]
                end;

                primary := func () do
                    advance()
                end;

                expression := func () do
                    primary()
                end;

                expr := expression();
                if current_token() != "$EOF" then
                    error(current_token())
                end;
                expr
            end
        """)

        # Evaluator

        self.go("""
            define := runc (env, name, val) do
                for p in env[1] do
                    if p[0] == name then p[1] = val; return(val) end
                end;
                append(env[1], [name, val]);
                return(val)
            end
        """)

        self.go("""
            assign := runc (env, name, val) do
                for p in env[1] do
                    if p[0] == name then p[1] = val; return(val) end
                end;
                if env[0] != None then
                    assign(env[0], name, val)
                else
                    error("Not found:", name)
                end
            end
        """)

        self.go("""
            get := runc (env, name) do
                for p in env[1] do
                    if p[0] == name then return(p[1]) end
                end;
                if env[0] != None then
                    get(env[0], name)
                else
                    error("Not found:", name)
                end
            end
        """)

        self.go("""
            _eval := func (expr, env) do
                # print("eval", expr);
                if expr == None then
                    None
                elif is_bool(expr) or is_int(expr) then
                    expr
                elif is_str(expr) then
                    get(env, expr)
                elif expr[0] == "$STR" then
                    expr[1]
                elif expr[0] == "func" then
                    ["closure", expr[1], expr[2], env]
                elif expr[0] == "define" then
                    define(env, expr[1], _eval(expr[2], env))
                elif expr[0] == "assign" then
                    assign(env, expr[1], _eval(expr[2], env))
                elif expr[0] == "seq" then
                    val := None;
                    for e in expr[1:] do
                        val = _eval(e, env)
                    end;
                    val
                elif expr[0] == "if" then
                    if _eval(expr[1], env) then
                        _eval(expr[2], env)
                    else
                        _eval(expr[3], env)
                    end
                else
                    op_val := _eval(expr[0], env);
                    args_val := map(expr[1:], func (arg) do _eval(arg, env) end);
                    apply(op_val, args_val)
                end
            end
        """)

        self.go("""
            apply := func (op_val, args_val) do
                if op_val[0] == "primitive" then
                    op_val[1](args_val)
                else
                    env := [op_val[3], []];
                    for name_val in zip(op_val[1], args_val) do
                        define(env, name_val[0], name_val[1])
                    end;
                    _eval(op_val[2], env)
                end
            end
        """)

        self.go("""
            global_env := [None, [
                ["add", ["primitive", func (args) do args[0] + args[1] end]],
                ["sub", ["primitive", func (args) do args[0] - args[1] end]],
                ["equal", ["primitive", func (args) do args[0] == args[1] end]],
                ["print", ["primitive", func (args) do print(args[0]) end]]
            ]];
            eval := func (expr) do _eval(expr, global_env) end
        """)

        # Interpreter

        self.go("""
            go := func (src) do eval(parse(scan(src))) end
        """)
