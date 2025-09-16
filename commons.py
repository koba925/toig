from typing import Callable

class CustomRules(dict):
    pass

class ToigStr(str):
    pass

ValueType = None | bool | int | ToigStr | Callable | list

def is_name_first(c): return c.isalpha() or c == "_"
def is_name_rest(c): return c.isalnum() or c == "_"
def is_name(expr): return isinstance(expr, str) and is_name_first(expr[0])
