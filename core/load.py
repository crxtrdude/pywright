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
        o = evidence(props["id"],page=props["page"])
    if cls == "char":
        o = portrait(*args)
        if "blinkspeed" in props:
            o.blink_sprite.blinkspeed = props["blinkspeed"]
        if "blinkemo" in props:
            o.set_blink_emotion(props["blinkemo"])
        if "tsprite" in props:
            for k in props["tsprite"]:
                setattr(o.talk_sprite,k,props["tsprite"][k])
        if "bsprite" in props:
            for k in props["bsprite"]:
                setattr(o.blink_sprite,k,props["bsprite"][k])
    if cls == "mesh":
        print "load mesh",args
        o = mesh(*args)
        print "mesh loaded",o
        def f(o=o,props=props):
            o.load(script)
    if cls == "surf3d":
        print "load surf3d"
        o = surf3d(*args)
    if cls == "ev_menu":
        items = []
	for x in props["items"]:
	    if isinstance(x,dict):
	        items.append(evidence(x["id"],page=x["page"]))
	    else:
	        items.append(evidence(x))
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
    if cls in ["fadeanim","tintanim"]:
        print cls
        o = {"fadeanim":fadeanim,"tintanim":tintanim}[cls]()
        def f(o=o,props=props):
            o.obs = []
            for o2 in script.obs:
                if getattr(o2,"id_name",None) in props["ob_ids"]:
                    o.obs.append(o2)
    if cls == "textbox":
        o = textbox(*args)
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
        o = ws_button(None,props["s_text"])
        if props.get("s_graphic",""):
            graphic = props["s_graphic"]
            graphic = assets.open_art(graphic)[0]
            o.graphic = graphic
        def func(*args):
            script.goto_result(props["s_macroname"])
        setattr(o,props["s_text"].replace(" ","_"),func)
        if props["hold_func"]:
            setattr(o,"hold_down_over",func)
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