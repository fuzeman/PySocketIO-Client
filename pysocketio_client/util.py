from threading import Timer


def has_binary(args):
    for arg in args:
        if type(arg) is bytearray:
            return True

    return False


def is_callable(value):
    return value and hasattr(value, '__call__')


def delayed_call(seconds, *args, **kwargs):
    def wrap(func):
        timer = Timer(seconds, func, args, kwargs)
        timer.start()

        func._timeout = timer
        return func

    return wrap


def delayed_cancel(func):
    timer = getattr(func, '_timeout', None)

    if not timer:
        return

    timer.cancel()
    setattr(func, '_timeout', None)
