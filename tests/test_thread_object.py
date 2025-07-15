import _auto_run_with_pytest  # noqa
import threading
from walytis_offchain.threaded_object import DedicatedThreadClass, run_on_dedicated_thread


class TestClass(DedicatedThreadClass):
    
    def __init__(self):
        DedicatedThreadClass.__init__(self)
    @run_on_dedicated_thread
    def add(self, a, b):
        return (a+b, threading.current_thread().ident)
    def termiante(self):
        DedicatedThreadClass.terminate()

def test_thread_object():
    test_obj = TestClass()
    sum, thread_id = test_obj.add(2, 3)
    print(sum)
    test_obj.terminate()
    assert sum == 5 and thread_id != threading.current_thread().ident
    
