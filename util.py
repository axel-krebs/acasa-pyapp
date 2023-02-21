# OO Utility constructs

def singleton(cls): # PEP 318
    instances = {}
    def getinstance(file_path):
        if cls not in instances:
            instances[cls] = cls(file_path)
        return instances[cls]
    return getinstance

def noninstantiable(cls):
    def __new__(cls, *args, **kwargs):
        raise RuntimeError('%s should not be instantiated' % cls)
    