print("## const_cps")
def const_cps(c):
    return lambda cont: cont(c)

const_cps(5)(print)

import operator as op

print("## binop_cps_full")
def binop_cps_full(op, a_cps, b_cps):
    return lambda cont: a_cps(lambda a: b_cps(lambda b: cont(op(a, b))))

print("## equal_cps")
def equal_cps(a, b, cont): cont(a == b)

equal_cps(5, 5, print)
equal_cps(5, 6, print)


print("## equal_cps_curried")
def equal_cps_curried(a, b): return lambda cont: cont(a == b)

equal_cps_curried(5, 5)(print)
equal_cps_curried(5, 6)(print)


print("## equal_cps_full")
def equal_cps_full(a_cps, b_cps):
    return binop_cps_full(op.eq, a_cps, b_cps)

equal_cps_full(const_cps(5), const_cps(5))(print)
equal_cps_full(const_cps(5), const_cps(6))(print)


print("## add_cps")
def add_cps(a, b, cont): cont(a + b)

add_cps(5, 6, print)
add_cps(5, 6, lambda r: add_cps(r, 7, print))


print("## add_cps_curried")
def add_cps_curried(a, b): return lambda cont: cont(a + b)

add_cps_curried(5, 6)(print)


print("## add_cps_full")
def add_cps_full(a_cps, b_cps):
    return binop_cps_full(op.add, a_cps, b_cps)

add_cps_full(const_cps(5), const_cps(6))(print)


print("## sub_cps_full")
def sub_cps_full(a_cps, b_cps):
    return binop_cps_full(op.sub, a_cps, b_cps)

sub_cps_full(const_cps(5), const_cps(6))(print)


print("## mul_cps_full")
def mul_cps_full(a_cps, b_cps):
    return binop_cps_full(op.mul, a_cps, b_cps)

mul_cps_full(const_cps(5), const_cps(6))(print)

print("## add_cps_full_more_curried")
def add_cps_full_more_curried(a_cps):
    return lambda b_cps: lambda cont: a_cps(lambda a: b_cps(lambda b: cont(a + b)))

add_cps_full_more_curried(const_cps(5))(const_cps(6))(print)


print("## less_cps_full")
def less_cps_full(a_cps, b_cps):
    return binop_cps_full(op.lt, a_cps, b_cps)

less_cps_full(const_cps(5), const_cps(6))(print)
less_cps_full(const_cps(5), const_cps(5))(print)
less_cps_full(const_cps(6), const_cps(5))(print)


print("## if_cps")
def if_cps(cnd_cps, thn_cps, els_cps, cont):
    cnd_cps(lambda cnd: thn_cps(cont) if cnd else els_cps(cont))

if_cps(lambda cont: equal_cps(5, 5, cont),
       lambda cont: cont("Yes"),
       lambda cont: cont("No"),
       print)
if_cps(lambda cont: equal_cps(5, 6, cont),
       lambda cont: cont("Yes"),
       lambda cont: cont("No"),
       print)
if_cps(lambda cont: equal_cps(5, 5, cont),
       const_cps("Yes"),
       const_cps("No"),
       print)
if_cps(lambda cont: equal_cps(5, 6, cont),
       const_cps("Yes"),
       const_cps("No"),
       print)


print("## if_cps/equal_cps_curried/add_cps_curried")
if_cps(equal_cps_curried(5, 5),
       const_cps("Yes"),
       const_cps("No"),
       print)
if_cps(equal_cps_curried(5, 6),
       const_cps("Yes"),
       const_cps("No"),
       print)


print("## if_cps/equal_cps_curried/add_cps_curried")
if_cps(add_cps_curried(5, 6)(lambda r: equal_cps_curried(r, 11)),
       const_cps("Yes"),
       const_cps("No"),
       print)
if_cps(add_cps_curried(5, 6)(lambda r: equal_cps_curried(r, 12)),
       const_cps("Yes"),
       const_cps("No"),
       print)
if_cps(equal_cps_full(const_cps(5), const_cps(5)),
       const_cps("Yes"),
       const_cps("No"),
       print)
if_cps(equal_cps_full(const_cps(5), const_cps(6)),
       const_cps("Yes"),
       const_cps("No"),
       print)


print("## if_cps_full")
def if_cps_full(cnd_cps, thn_cps, els_cps):
    return cnd_cps(lambda cnd: thn_cps if cnd else els_cps)

if_cps_full(
    equal_cps_full(add_cps_full(const_cps(5), const_cps(6)), const_cps(11)),
    const_cps("Yes"),
    const_cps("No")
)(print)
if_cps_full(
    equal_cps_full(add_cps_full(const_cps(5), const_cps(6)), const_cps(12)),
    const_cps("Yes"),
    const_cps("No")
)(print)


print("## if_cps_delayed")
def if_cps_delayed(cnd_cps, thn_cps, els_cps):
    return cnd_cps(lambda cnd: thn_cps() if cnd else els_cps())

if_cps_delayed(
    equal_cps_full(add_cps_full(const_cps(5), const_cps(6)), const_cps(11)),
    lambda: const_cps("Yes"),
    lambda: const_cps("No")
)(print)
if_cps_delayed(
    equal_cps_full(add_cps_full(const_cps(5), const_cps(6)), const_cps(12)),
    lambda: const_cps("Yes"),
    lambda: const_cps("No")
)(print)


print("## first_cps_full")
def first_cps_full(l_cps):
    return lambda cont: l_cps(lambda l: cont(l[0]))

first_cps_full(const_cps([5, 6, 7]))(print)


print("## rest_cps_full")
def rest_cps_full(l_cps):
    return lambda cont: l_cps(lambda l: cont(l[1:]))

rest_cps_full(const_cps([5, 6, 7]))(print)


print("## foldl_cps")
def foldl_cps(l, f, init, cont):
    if l == []:
        cont(init)
    else:
        f(init, l[0], lambda r: foldl_cps(l[1:], f, r, cont))

foldl_cps([5, 6, 7], add_cps, 0, print)


print("## foldl_cps_curried")
def foldl_cps_curried(l, f, init):
    return lambda cont: (
        cont(init) if l == []
        else f(init, l[0])(lambda r: foldl_cps_curried(l[1:], f, r)(cont))
    )

foldl_cps_curried([5, 6, 7], add_cps_curried, 0)(print)


print("## foldl_cps3_full - inifinite loop, skipped")

def foldl_cps_full(l, f, init):
    return if_cps_full(
        equal_cps_full(l, const_cps([])),
        init,
        foldl_cps_full(rest_cps_full(l), f, f(init, first_cps_full(l)))
    )

# foldl_cps_full(const_cps([5, 6, 7]), add_cps_full, const_cps(0))(print)


print("## foldl_cps_delayed")
def foldl_cps_delayed(l, f, init):
    return if_cps_delayed(
        equal_cps_full(l, const_cps([])),
        lambda: init,
        lambda: foldl_cps_delayed(rest_cps_full(l), f, f(init, first_cps_full(l)))
    )

foldl_cps_delayed(const_cps([5, 6, 7]), add_cps_full, const_cps(0))(print)


print("## map_cps")
def map_cps(l, f, cont):
    if l == []:
        cont([])
    else:
        f(l[0], lambda r: map_cps(l[1:], f, lambda r2: cont([r] + r2)))

map_cps([5, 6, 7], lambda a, cont: add_cps(a, 1, cont), print)


print("## map_cps_foldl")
def map_cps_foldl(l, f, cont):
    foldl_cps(l, lambda acc, e, cont: f(e, lambda r: cont(acc + [r])), [], cont)

map_cps_foldl([5, 6, 7], lambda a, cont: add_cps(a, 1, cont), print)


print("## map_cps_curried")
def map_cps_curried(l, f_curried):
    return lambda cont: (
        cont([]) if l == [] else
        f_curried(l[0])(lambda r: map_cps_curried(l[1:], f_curried)(lambda r2: cont([r] + r2))))

map_cps_curried([5, 6, 7], lambda a: add_cps_curried(a, 1))(print)


print("## map_cps_curried_def")
def map_cps_curried_def(l, f_curried):
    def _map(l, cont):
        if l == []:
            cont([])
        else:
            f_curried(l[0])(lambda r: _map(l[1:], lambda r2: cont([r] + r2)))

    return lambda cont: _map(l, cont)

map_cps_curried_def([5, 6, 7], lambda a: add_cps_curried(a, 1))(print)


print("## array_cps_full")
def array_cps_full(*es_cps_full):
    return (const_cps([]) if es_cps_full == () else
            es_cps_full[0](lambda r: add_cps_full(
                const_cps([r]),
                array_cps_full(*es_cps_full[1:]))))

# def array_cps_full(e_cps_full):
#     return lambda cont: cont([e_cps_full(lambda r: r)])

array_cps_full()(print)
array_cps_full(const_cps(5))(print)
array_cps_full(const_cps(5), const_cps(6))(print)
array_cps_full(add_cps_full(const_cps(5), const_cps(6)))(print)


print("## map_cps_delayed")
def map_cps_delayed(l_cps, f):
    return if_cps_delayed(
        equal_cps_full(l_cps, const_cps([])),
        lambda: const_cps([]),
        lambda: add_cps_full(
            array_cps_full(f(first_cps_full(l_cps))),
            map_cps_delayed(rest_cps_full(l_cps), f)))

map_cps_delayed(
    const_cps([5, 6, 7]),
    lambda a_cps_full: add_cps_full(a_cps_full, const_cps(1))
)(print)
map_cps_delayed(
    const_cps([5, 6, 7]),
    add_cps_full_more_curried(const_cps(1))
)(print)


print("## map_cps_delayed_foldl")
def map_cps_delayed_foldl(l_cps, f):
    return foldl_cps_delayed(l_cps,
        lambda acc_cps_full, e_cps_full: add_cps_full(
            acc_cps_full,
            array_cps_full(f(e_cps_full))),
        const_cps([]))

map_cps_delayed_foldl(
    const_cps([5, 6, 7]),
    lambda a_cps_full: add_cps_full(a_cps_full, const_cps(1))
)(print)


print("## set_cps_full/get_cps_full")
env = {}

def set_cps_full(name, val_cps):
    env[name] = val_cps
    return val_cps

def get_cps_full(name):
    return env[name]

set_cps_full("i", const_cps(5))(print)
get_cps_full("i")(print)
set_cps_full("i", add_cps_full(get_cps_full("i"), const_cps(6)))(print)


print("## do_cps_full")
def do_cps_full(*exprs):
    def _do_cps_full(exprs, r, cont):
        if len(exprs) == 0: cont(r)
        else: exprs[0](lambda r: _do_cps_full(exprs[1:], r, cont))

    return lambda cont: _do_cps_full(exprs, None, cont)

do_cps_full()(print)
do_cps_full(
    set_cps_full("i", const_cps(5)),
    set_cps_full("i", add_cps_full(get_cps_full("i"), const_cps(1)))
)(print)
get_cps_full("i")(print)

print("## print_cps")
def print_cps_full(val_cps):
    return lambda cont: val_cps(lambda val: (print(val), cont(None))[1])

print_cps_full(const_cps(5))(print)
print_cps_full(if_cps_full(
    equal_cps_full(add_cps_full(const_cps(5), const_cps(6)), const_cps(11)),
    const_cps("Yes"),
    const_cps("No")
))(print)
print_cps_full(if_cps_full(
    equal_cps_full(add_cps_full(const_cps(5), const_cps(6)), const_cps(12)),
    const_cps("Yes"),
    const_cps("No")
))(print)
do_cps_full(
    print_cps_full(const_cps(5)),
    print_cps_full(const_cps(6))
)(print)

print("## while_cps_delayed")
def while_cps_delayed(cnd_cps_delayed, body_cps_delayed):
    def _while_cps_delayed(r, cont):
        cnd_cps_delayed()(lambda cnd:
            cont(r) if not cnd
            else body_cps_delayed()(lambda r: _while_cps_delayed(r, cont)))

    return lambda cont: _while_cps_delayed(None, cont)

set_cps_full("fac", const_cps(1))(lambda r: r)
set_cps_full("i", const_cps(1))(lambda r: r)
while_cps_delayed(
    lambda: less_cps_full(get_cps_full("i"), const_cps(6)),
    lambda: do_cps_full(
        set_cps_full("fac", mul_cps_full(get_cps_full("fac"), get_cps_full("i"))),
        set_cps_full("i", add_cps_full(get_cps_full("i"), const_cps(1)))))(print)
get_cps_full("i")(print)
get_cps_full("fac")(print)


print("## factorial_cps")

cc = print

def factorial_cps(n, cont):
    global cc
    if n == 0:
        cont(1)
    else:
        if n == 3: cc = cont
        factorial_cps(n - 1, lambda r: cont(n * r))

factorial_cps(5, print)

cc(3)


print("## factorial_cps_delayed")
def factorial_cps_delayed(n_cps_full):
    return if_cps_delayed(
        equal_cps_full(n_cps_full, const_cps(0)),
        lambda: const_cps(1),
        lambda: mul_cps_full(
            n_cps_full,
            factorial_cps_delayed(sub_cps_full(n_cps_full, const_cps(1)))))

factorial_cps_delayed(const_cps(5))(print)


print("## factorial_cps_cc")
def factorial_cps_cc(n_cps_full):
    return lambda cont: if_cps_delayed(
        equal_cps_full(n_cps_full, const_cps(0)),
        lambda: const_cps(1),
        lambda: do_cps_full(
            if_cps_delayed(
                equal_cps_full(n_cps_full, const_cps(3)),
                lambda: set_cps_full("cc", const_cps(cont)),
                lambda: const_cps(None)
            ),
            mul_cps_full(
                n_cps_full,
                factorial_cps_cc(sub_cps_full(n_cps_full, const_cps(1)))))
    )(cont)

factorial_cps_cc(const_cps(0))(print)
factorial_cps_cc(const_cps(1))(print)
factorial_cps_cc(const_cps(2))(print)
factorial_cps_cc(const_cps(5))(print)

get_cps_full("cc")(const_cps(3))

# def factorial_cps(n, cont):
#     if n == 1:
#         cont(1)
#     else:
#         factorial_cps(n - 1, lambda r: cont(n * r))

#   factorial(4, print)
# = factorial(3, λ r1: print(4 * r1))
# = factorial(2, λ r2: (λ r1: print(4 * r1))(3 * r2))
# = factorial(1, λ r3: (λ r2: (λ r1: print(4 * r1))(3 * r2))(2 * r3))
# = (λ r3: (λ r2: (λ r1: print(4 * r1))(3 * r2))(2 * r3))(1)
# = (λ r2: (λ r1: print(4 * r1))(3 * r2))(2 * 1)
# = (λ r1: print(4 * r1))(3 * (2 * 1))
# = print(4 * (3 * (2 * 1)))

print("## factorial_cps_trampoline")
def factorial_cps_trampoline(n, cont):
    if n == 1:
        return lambda: cont(1)
    else:
        return lambda: factorial_cps_trampoline(n - 1, lambda r: lambda: cont(n * r))

def trampoline(computation):
    while callable(computation):
        computation = computation()

#   factorial(4, print)
# = λ: factorial(3, λ r1: λ: print(4 * r1)) # → computation

#   computation()
# = (λ: factorial(3, λ r1: λ: print(4 * r1)))()
# = factorial(3, λ r1: λ: print(4 * r1))
# = λ: factorial(2, λ r2: λ: (λ r1: λ: print(4 * r1))(3 * r2)) # → computation

#   computation()
# = (λ: factorial(2, λ r2: λ: (λ r1: λ: print(4 * r1))(3 * r2)))()
# = factorial(2, λ r2: λ: (λ r1: λ: print(4 * r1))(3 * r2))
# = λ: factorial(1, λ r3: λ: (λ r2: λ: (λ r1: λ: print(4 * r1))(3 * r2))(2 * r3)) # → computation

#   computation()
# = (λ: factorial(1, λ r3: λ: (λ r2: λ: (λ r1: λ: print(4 * r1))(3 * r2))(2 * r3)))()
# = factorial(1, λ r3: λ: (λ r2: λ: (λ r1: λ: print(4 * r1))(3 * r2))(2 * r3))
# = λ: (λ r3: λ: (λ r2: λ: (λ r1: λ: print(4 * r1))(3 * r2))(2 * r3))(1) # → computation

#   computation()
# = (λ: (λ r3: λ: (λ r2: λ: (λ r1: λ: print(4 * r1))(3 * r2))(2 * r3))(1))()
# = (λ r3: λ: (λ r2: λ: (λ r1: λ: print(4 * r1))(3 * r2))(2 * r3))(1)
# = λ: (λ r2: λ: (λ r1: λ: print(4 * r1))(3 * r2))(2 * 1) # → computation

#   computation()
# = (λ: (λ r2: λ: (λ r1: λ: print(4 * r1))(3 * r2))(2 * 1))()
# = (λ r2: λ: (λ r1: λ: print(4 * r1))(3 * r2))(2 * 1)
# = λ: (λ r1: λ: print(4 * r1))(3 * (2 * 1)) # → computation

#   computation()
# = (λ: (λ r1: λ: print(4 * r1))(3 * (2 * 1)))()
# = (λ r1: λ: print(4 * r1))(3 * (2 * 1))
# = λ: print(4 * (3 * (2 * 1))) # → computation

#   computation()
# = (λ: print(4 * (3 * (2 * 1))))()
# = print(4 * (3 * (2 * 1))) # → computation

trampoline(factorial_cps_trampoline(1500, print))
