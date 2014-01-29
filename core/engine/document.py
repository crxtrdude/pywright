def category(cat,type=None):
    def _dec(f):
        f.cat = cat
        if type:
            f.ftype = type
        f.name = [""]
        return f
    return _dec
class DOCTYPE():
    def __init__(self,name,description="",default=None):
        self.name = name
        self.description = description
        self.default = default
    def __repr__(self):
        s = self.__class__.__name__+" ( "+self.name+":"+self.description+" ) "
        if self.default is not None:
            s+="default:"+repr(self.default)
        return s
class COMBINED(DOCTYPE):
    """Set of arguments joined as text"""
class KEYWORD(DOCTYPE):
    """A value assigned by name"""
class TOKEN(DOCTYPE):
    """This exact token string may be present"""
class VALUE(DOCTYPE):
    """A named value, assigned by position"""
class ETC(DOCTYPE):
    """Each following argument is a separate entity, all potentially optional"""
class CHOICE():
    """One of these options should be present here"""
    def __init__(self,options):
        self.options = options
    def __repr__(self):
        return self.__class__.__name__+" ["+" ".join(repr(o) for o in self.options)+"]"