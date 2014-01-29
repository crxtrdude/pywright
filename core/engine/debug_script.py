from script import Script
from core.core import *

class TextScript(Script):
    def __init__(self,*args):
        super(TextScript,self).__init__(*args)
        print "initialized TextScript"
    def enter_text(self,text):
        return True
    def enter_list(self,text):
        try:
            si = int(text)
        except:
            return
        self.list_ob.si = si
        self.list_ob.selected = self.list_ob.options[si]
        self.list_ob.enter_down()
        return True
    def execute_line(self,line):
        #print "execute:",repr(line)
        super(TextScript,self).execute_line(line)
    def call_func(self,command,args):
        if command == "textbox":
            txt = " ".join(args[1:]).replace("{n}","\n")
            tb = textbox(txt)
            tb.can_skip = True
            #tb.skipping = len(txt)
            tb.enter_down()
            tb.update()
            print tb.text.encode("utf8")
            x = self.get_input(self.enter_text)
        elif command == "showlist":
            super(TextScript,self).call_func(command,args)
            for o in self.obs:
                if isinstance(o,listmenu):
                    self.list_ob = o
            for i,opt in enumerate(self.list_ob.options):
                print i,opt[0]
            x = self.get_input(self.enter_list)
        else:
            super(TextScript,self).call_func(command,args)
    def get_input(self,func):
        while 1:
            x = raw_input()
            if x=="quit":
                sys.exit()
            if func(x):
                return x
    def draw(self,*args):
        pass

class DebugScript(Script):
    def __init__(self):
        super(DebugScript,self).__init__()
        self.char_cache = {}
    def update_objects(self):
        #~ for o in self.obs:
            #~ if isinstance(o,textbox):
                #~ for i in range(400):
                    #~ o.update()
                #~ o.forward()
            #~ else:
                #~ o.update()
        [x.update() for x in self.obs]
        return True
    def call_func(self,command,args):
        if command in ["set","setvar"]:
            super(DebugScript,self).call_func(command,args)
        if command == "char":
            if "hide" in args:
                return
            if "stack" not in args:
                for o in self.obs:
                    if isinstance(o,portrait):
                        o.delete()
            if tuple(args) in self.char_cache:
                c = self.char_cache[tuple(args)]
                self.obs.append(c)
            else:
                c = self._char(*args)
            assets.variables["_speaking_name"] = c.nametag.split("\n")[0]
            assets.variables["_speaking"] = c.id_name
            self.char_cache[tuple(args)] = c
        if command == "textbox":
            txt = " ".join(args[1:]).replace("{n}","\n")
            tb = textbox(txt)
            tb.can_skip = True
            #tb.skipping = len(txt)
            tb.enter_down()
            tb.update()
    def init(self,*args,**kwargs):
        self.old_stack = assets.stack[:]
        super(DebugScript,self).init(*args,**kwargs)
        self.si2 = 0
        self.kill = 0
        self.o = assets.variables.copy()
        assets.variables["_debug"] = "true"
    def delete(self):
        self.kill = 1
    def interpret(self):
        if self.si2>=len(self.scriptlines):
            self.delete()
            assets.variables.clear()
            assets.variables.update(self.o)
            assets.stack[:] = self.old_stack
            return True
        self.si = self.si2
        line = self.getline()
        self.si2 += 1
        if line:
            self.execute_line(line)
    def run_it(self):
        while not self.kill:
            self.update()
        errors = [o for o in self.obs if isinstance(o,error_msg)]
        return errors
    def run_lines(self,scene,lines,func):
        output = []
        for i,line in enumerate(lines):
            if func(line):
                output.append((scene,i+1,line))
        return output
    def _no_quote(self,line):
        line = line.strip()
        if line.startswith('"') and not line.endswith('"'):
            return True
    def debug_game(self,scope="current",method="run"):
        scenes = [assets.cur_script.scene]
        if scope == "all":
            scenes = os.listdir(assets.game)
        aerrors = []
        for scene in scenes:
            if scope=="all" and not scene.endswith(".txt"):
                continue
            print scene
            if method=="run":
                self.world.all = []
                self.init(scene)
                #self.scriptlines = assets.cur_script.scriptlines
                assets.stack.append(self)
                errors = self.run_it()
                print errors
                aerrors.extend(errors)
            elif method=="quote":
                lines = assets.raw_lines(scene,use_unicode=True)
                aerrors.extend(self.run_lines(scene,lines,self._no_quote))
        print aerrors
        if scope == "current":
            for err in reversed(aerrors):
                assets.cur_script.obs.append(err)