from typing import Callable
from dataclasses import dataclass

ValueType = None | bool | int | Callable | list

class VariableNotFoundError(AssertionError):
    def __init__(self, name):
        self._name = name

class CustomRules(dict):
    pass

@dataclass
class Expr:
    elems: ValueType

def is_name_first(c): return c.isalpha() or c == "_"
def is_name_rest(c): return c.isalnum() or c == "_"
def is_name(expr): return isinstance(expr, str) and is_name_first(expr[0])
