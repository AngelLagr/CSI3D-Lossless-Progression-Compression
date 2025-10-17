

class GlobalReference:
    __Registry = dict()

    @staticmethod
    def get(key):
        return GlobalReference.__Registry[key] if key in GlobalReference.__Registry else None
    
    @staticmethod
    def _register(ref):
        GlobalReference.__Registry[ref] = ref

    @staticmethod
    def _unregister(ref):
        del GlobalReference.__Registry[ref]

    def __init__(self):
        GlobalReference._register(self)

    def __del__(self):
        GlobalReference._unregister(self)

    def __key(self):
        return NotImplemented

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        if isinstance(other, GlobalReference):
            return self.__key() == other.__key()
        return NotImplemented