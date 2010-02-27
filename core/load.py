import gui
from core import *

def load(script,olist):
    f = None
    cls,args,props = olist

    if cls == "bg":
        o = bg()
    if cls == "testimony_blink":
        o = testimony_blink(*args)
    if cls == "fg":
        o = fg()
    if cls in ["bg","fg","testimony_blink"]:
        for p in props:
            setattr(o,p,props[p])
        o.load(o.name)
    if cls == "evidence":
        o = evidence(props["id"])
    if cls == "char":
        o = portrait(*args)
    if cls == "ev_menu":
        items = [evidence(x) for x in props["items"]]
        del props["items"]
        o = evidence_menu(items)
        for p in props:
            setattr(o,p,props[p])
        o.layout()
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
    if cls == "fadeanim":
        o = fadeanim()
        def f(o=o,props=props):
            o.obs = []
            for o2 in script.obs:
                if getattr(o2,"id_name",None) in props["ob_ids"]:
                    o.obs.append(o2)
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
    if cls == "penalty":
        o = penalty(*args)
    if cls == "menu":
        o = menu()
        def f(o=o,props=props):
            if o.options and not getattr(o,"selected",""):
                o.selected = o.options[0]
    if cls == "listmenu":
        o = listmenu()
    if cls == "examinemenu":
        o = examine_menu(props["hide"])
        o.bg = []
        def f(o=o,props=props):
            for o2 in script.obs:
                if getattr(o2,"id_name",None) in props["bg_ids"]:
                    o.bg.append(o2)
    if cls == "guiWait":
        o = guiWait()
        o.script = script
    if cls == "button":
        o = gui.button(None,props["s_text"])
        if props.get("s_graphic",""):
            graphic = props["s_graphic"]
            graphic = assets.open_art(graphic)[0]
            o.graphic = graphic
        def func(*args):
            script.goto_result(props["s_macroname"])
        setattr(o,props["s_text"].replace(" ","_"),func)
        print o
    if cls == "waitenter":
        o = waitenter()
    if cls == "delay":
        o = delay()
    if cls == "timer":
        o = timer()
        o.script = script
    for p in props:
        setattr(o,p,props[p])
    o.cur_script = script
    return o,f