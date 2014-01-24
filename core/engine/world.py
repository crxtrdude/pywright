from core.core import assets

def argsort(list,arg="pri",get=getattr):
    def _cmp(a,b):
        return cmp(get(a,arg),get(b,arg))
    list.sort(_cmp)

class mylist(list): pass
class World:
    """A collection of objects"""
    def __init__(self,obs=None):
        if not obs: obs = []
        self.all = obs[:]
        for o in self.all:
            o.cur_script = assets.cur_script
    def render_order(self):
        """Return a list of objects in the order they should
        be rendered"""
        n = mylist(self.all[:])
        if assets.variables.get("_layering_method","zorder") == "zorder":
            argsort(n,"z")
        else:
            pass
        oldapp = n.append
        def _app(ob):
            self.append(ob)
            oldapp(ob)
        n.append = _app
        return n
    def update_order(self):
        """Return a list of objects in the order they
        should be updated"""
        n = self.all[:]
        argsort(n,"pri")
        return n
    def select(self):
        """Return a list of objects that match the query"""
    def append(self,ob):
        self.all.append(ob)
        ob.cur_script = assets.cur_script
    def extend(self,obs,unique=True):
        if unique:
            for o in obs:
                if o not in self.all:
                    self.all.append(o)
        else:
            self.all.extend(o)
    def remove(self,ob):
        self.all.remove(ob)