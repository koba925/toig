import time

from commons import ToigStr

def load(env):
    for name, func in _builtins.items():
        env.define(name, func)

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
    "len": lambda args: len(args[0]),
    "get_at": lambda args: args[0][args[1]],
    "set_at": _set_at,
    "slice": _slice,
    "set_slice": _set_slice,
    "append": lambda args: args[0].append(args[1]),
    "shift": lambda args: args[0].pop(0),

    "pytype": lambda args: type(args[0]),
    "is_bool": lambda args: type(args[0]) is bool,
    "is_int": lambda args: type(args[0]) is int,
    "is_str": lambda args: type(args[0]) is ToigStr,
    "is_array": lambda args: isinstance(args[0], list),
    "is_name": lambda args: type(args[0]) is str,

    "to_int": lambda args: int(args[0]),

    "print": lambda args: print(*args),
    "clock_ms": lambda args: time.perf_counter_ns() // 1_000_000,
    "error": lambda args: _error(args)
}
