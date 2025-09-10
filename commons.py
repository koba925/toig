from typing import Callable

ValueType = None | bool | int | Callable | list

class CustomRules(dict):
    pass

def is_name_first(c): return c.isalpha() or c == "_"
def is_name_rest(c): return c.isalnum() or c == "_"
def is_name(expr): return isinstance(expr, str) and is_name_first(expr[0])
