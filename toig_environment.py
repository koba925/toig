class Environment:
    def __init__(self, parent=None):
        self._parent = parent
        self._vals = {}

    def __repr__(self):
        if "__builtins__" in self._vals:
            this_env = "builtins"
        elif "__stdlib__" in self._vals:
            this_env = "stdlib"
        else:
            this_env = self._vals
        return f"{this_env} > {self._parent}"

    def define(self, name, val):
        self._vals[name] = val

    def assign(self, name, val):
        if name in self._vals:
            self._vals[name] = val
        elif self._parent is not None:
            self._parent.assign(name, val)
        else:
            assert False, f"name '{name}' is not defined"

    def get(self, name):
        if name in self._vals:
            return self._vals[name]
        elif self._parent is not None:
            return self._parent.get(name)
        else:
            assert False, f"name '{name}' is not defined"

    def extend(self, params, args):
        def _extend(params, args):
            if params == [] and args == []: return {}
            assert len(params) > 0, \
                f"Argument count doesn't match: `{params}, {args}` @ extend"
            match params[0]:
                case str(param):
                    assert len(args) > 0, \
                        f"Argument count doesn't match: `{params}, {args}` @ extend"
                    env.define(param, args[0])
                    _extend(params[1:], args[1:])
                case ["*", rest]:
                    rest_len = len(args) - len(params) + 1
                    assert rest_len >= 0, \
                        f"Argument count doesn't match: `{params}, {args}` @ extend"
                    env.define(rest, args[:rest_len])
                    _extend(params[1:], args[rest_len:])
                case unexpected:
                    assert False, f"Unexpected param at extend: {unexpected}"

        env = Environment(self)
        _extend(params, args)
        return env

