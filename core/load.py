import gui
from core import *

def load(script,olist):
    f = None
    cls,args,props = olist
    if cls == "delay":
        o = delay()
    if cls == "waitenter":
        o = waitenter()
    if cls == "guiWait":
        o = guiWait()
        o.script = script
    if cls == "button":
        print args
        script._gui("gui","Button",*args)
        return None,f
    if cls == "menu":
        o = menu()
        def f(o=o,props=props):
            if o.options and not getattr(o,"selected",""):
                o.selected = o.options[0]
    if cls == "testimony_blink":
        o = testimony_blink(*args)
    if cls == "penalty":
        o = penalty(*args)
    if cls == "textbox":
        o = textbox()
    if cls == "textblock":
        o = textblock(*args)
    if cls == "uglyarrow":
        o = uglyarrow()
        if props.get("_tb",""):
            def f(o=o,props=props):
                for tb in script.world.all:
                    if isinstance(tb,textbox):
                        o.textbox = tb
                o.update()
    if cls == "examinemenu":
        o = examine_menu(props["hide"])
        o.bg = []
        def f(o=o,props=props):
            for o2 in script.obs:
                if getattr(o2,"id_name",None) in props["bg_ids"]:
                    o.bg.append(o2)
    if cls == "scroll":
        o = scroll()
        def f(o=o,props=props):
            o.obs = []
            for o2 in script.obs:
                if getattr(o2,"id_name",None) in props["ob_ids"]:
                    o.obs.append(o2)
    if cls == "zoomanim":
        o = zoomanim()
        def f(o=o,props=props):
            o.obs = []
            for o2 in script.obs:
                if getattr(o2,"id_name",None) in props["ob_ids"]:
                    o.obs.append(o2)
    if cls == "rotateanim":
        o = rotateanim()
        def f(o=o,props=props):
            o.obs = []
            for o2 in script.obs:
                if getattr(o2,"id_name",None) in props["ob_ids"]:
                    o.obs.append(o2)
    if cls == "bg":
        o = bg()
    if cls == "fg":
        o = fg()
    if cls == "ev_menu":
        items = [evidence(x) for x in props["items"]]
        del props["items"]
        o = evidence_menu(items)
        for p in props:
            setattr(o,p,props[p])
        o.layout()
    if cls == "evidence":
        o = evidence(props["id"])
    if cls == "char":
        o = portrait(*args)
    if cls in ["bg","fg","testimony_blink"]:
        for p in props:
            setattr(o,p,props[p])
        o.load(o.name)
    if 1:
        for p in props:
            setattr(o,p,props[p])
    o.cur_script = script
    return o,f