
# -----------------------------------------------------------------------------

from threading import Lock

# -----------------------------------------------------------------------------
class Singleton(object):

    _instance = None
    _initialized = False

    # -------------------------------------------------------------------------
    def __new__(cls):
        
        lock = Lock()
        with lock:
            
            if cls._instance is None:
                cls._instance = super(Singleton, cls).__new__(cls)

            return cls._instance

    # -------------------------------------------------------------------------
    def __init__(self):

        if self.__class__._initialized:
            return

        self.init()
        self.__class__._initialized = True

