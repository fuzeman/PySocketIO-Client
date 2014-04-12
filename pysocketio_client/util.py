def has_binary(args):
    for arg in args:
        if type(arg) is bytearray:
            return True

    return False


def is_callable(value):
    return value and hasattr(value, '__call__')
