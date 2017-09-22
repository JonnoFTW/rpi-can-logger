class GPIO(object):
    BOARD = 0
    OUT = 1

    def output(self, *args, **kwargs):
        pass

    def setup(self, *args, **kwargs):
        pass

    def __getattr__(self, item):
        def wrapper(*args, **kwargs):
            pass

        return wrapper

    def cleanup(self, *args, **kwargs):
        pass

    def setwarnings(self, *args, **kwargs):
        pass

    def setmode(self, *args, **kwargs):
        pass
