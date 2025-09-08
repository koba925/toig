class VariableNotFoundError(AssertionError):
    def __init__(self, name):
        self._name = name

class Environment:
    def __init__(self, parent=None):
        self._parent = parent
        self._vals = {}

    def __repr__(self):
        def keys():
            if "__builtins__" in self._vals:
                return "__builtins__"
            elif "__stdlib__" in self._vals:
                return "__stdlib__"
            else:
                return ", ".join([str(k) for k  in self._vals.keys()])

        if self._parent is None:
            return f"[{keys()}]"
        else:
            return f"[{keys()}] < {self._parent}"

    def __contains__(self, name):
        try:
            self.get(name)
            return True
        except VariableNotFoundError:
            return False

    def define(self, name, val):
        self._vals[name] = val
        return val

    def assign(self, name, val):
        if name in self._vals:
            self._vals[name] = val
            return val
        elif self._parent is not None:
            return self._parent.assign(name, val)
        else:
            raise VariableNotFoundError(name)

    def get(self, name):
        if name in self._vals:
            return self._vals[name]
        elif self._parent is not None:
            return self._parent.get(name)
        else:
            raise VariableNotFoundError(name)
