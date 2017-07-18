class GPIO:
    def __getattr__(self, item):
        return self._noop()

    def _noop(self, *args, **kwargs):
        return
