from typing import Callable

class CustomRules(dict):
    pass

class ToigStr(str):
    def __repr__(self):
        return f"ToigStr({super().__repr__()})"

    def __hash__(self):
        return super().__hash__()

    def __eq__(self, other):
        return isinstance(other, ToigStr) and super().__eq__(other)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __add__(self, other):
        result = super().__add__(other)
        return self.__class__(result)

    def __mul__(self, other):
        result = super().__mul__(other)
        return self.__class__(result)

    def __getitem__(self, key):
        result = super().__getitem__(key)
        return self.__class__(result)

ValueType = None | bool | int | ToigStr | Callable | list

def is_name_first(c): return c.isalpha() or c == "_"
def is_name_rest(c): return c.isalnum() or c == "_"
def is_name(expr): return isinstance(expr, str) and is_name_first(expr[0])
