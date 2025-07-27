# toig

実験用のトイ言語です。実用性はまったくありません。

mainブランチは最小限の機能をシンプルに実装したものです。
Pythonの配列でソース（ASTともいう）を書いてフィボナッチ数が求められる程度。

```py
    run(["define", "fib", ["func", ["n"],
            ["if", ["equal", "n", 0], 0,
            ["if", ["equal", "n", 1], 1,
            ["add", ["fib", ["sub", "n", 1]], ["fib", ["sub", "n", 2]]]]]]])
    run(["fib", 10])
```

そこを起点に[ブランチを分けながら](https://github.com/koba925/toig/branches)いろいろ試しています。

[いま一番進んでいるあたり](https://github.com/koba925/toig/compare/tail_call_optimization)では字句解析・構文解析がついてて継続とマクロとカスタム文法で拡張できるようになってて末尾呼び出し最適化を実装したりしています。

try-catch ぽいものを実装したところ

```
    # try-catchの実装

    raise := func (e) do error(q(raised_outside_of_try), e) end;
    _try := macro (try_expr, exc_var, exc_expr) do qq scope
        prev_raise := raise;
        letcc escape do
            raise = func (!(exc_var)) do escape(!(exc_expr)) end;
            !(try_expr)
        end;
        raise = prev_raise
    end end end;

    # try-catchのカスタム文法定義

    #rule [try, _try, EXPR, catch, NAME, do, EXPR, end]

    # テスト

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
```

ジェネレータを実装して簡単な並行処理をやってみたところ

```
    # ジェネレータ生成マクロの実装

    __stdlib_gfunc := macro (params, body) do qq
        func (!!(params[1:])) do
            yd := nx := None;
            yield := func (x) do letcc cc do nx = cc; yd(x) end end;
            next := func () do letcc cc do yd = cc; nx(None) end end;
            nx := func (_) do !(body); yield(None) end;
            next
        end
    end end

    # ジェネレータ生成のカスタム文法定義

    #rule [gfunc, __stdlib_gfunc, PARAMS, do, EXPR, end]

    # ジェネレータを使った簡単な並行処理

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

    start()
```

Zennのスクラップブックに進捗（というか落書き）を書いています。

* [トイ言語実験日記（マクロと継続）](https://zenn.dev/kb84tkhr/scraps/133254ba6599e4)
* [トイ言語実験日記２（構文解析とカスタム文法）](https://zenn.dev/kb84tkhr/scraps/344aa65443b4f3)
* [トイ言語実験日記３（ステートマシンでマクロと継続）](https://zenn.dev/kb84tkhr/scraps/446dd0e90c3fc3)
* [トイ言語実験日記４（テーマ未定)](https://zenn.dev/kb84tkhr/scraps/6f94737d864eef)

よろしかったらこちらもご覧ください。こちらは実験っぽいことはせず普通に？書いています。

* [350行くらいのPythonで作るプログラミング言語実装超入門](https://zenn.dev/kb84tkhr/books/mini-interpreter-in-350-lines)

その後の拡張の記事。

* https://zenn.dev/topics/minilang
