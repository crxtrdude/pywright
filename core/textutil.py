import re
import core

class markup:
    pass
class markup_color(markup):
    def __init__(self,color=None,revert=False):
        self.color = color
        self.revert = revert
    def addcharsto(self,list):
        list.append(self)
    def __repr__(self):
        return "color: %s %s"%(self.color,self.revert)

class markup_command(markup):
    def __init__(self,command,args):
        self.command = command
        self.args = args
    def addcharsto(self,list):
        list.append(self)
    def __repr__(self):
        return "command: %s %s"%(self.command,self.args)
        
class plain_text:
    def __init__(self,text):
        self.text = text
    def addcharsto(self,list):
        list.extend(self.text)
        
def to_markup(text):
    if not text.startswith("{") or not text.endswith("}"):
        return plain_text(text)
    if not text.startswith("{"):
        raise "{ mismatch"
    if not text.endswith("}"):
        raise "} mismatch"
    text = text[1:-1]
    if not text:
        return markup_command("","")
    if text[0]=="c" and (len(text)==1 or text[1].isdigit() or text[1]==" "):
        if len(text)==1:
            return markup_color(revert=True)
        return markup_color(core.color_str(text[1:]))
    macro_args = text.split(" ",1)+[""]
    return markup_command(macro_args[0],macro_args[1])

class markup_text:
    """Some text that has annotations"""
    def __init__(self,text):
        print "markup",text
        markupre = re.compile("{.*?}")
        text_segments = markupre.split(text)
        markup_segments = markupre.findall(text)
        l = text_segments
        self._text = []
        while 1:
            if not l:
                break
            to_markup(l.pop(0)).addcharsto(self._text)
            if l == text_segments:
                l = markup_segments
            else:
                l = text_segments
        print "REPR TEXT:",repr(self._text)
    def chars(self):
        return self._text
    def text(self):
        return u"".join([x for x in self._text if not hasattr(x,"addcharsto")])

markup_text("This is a test")
markup_text("The cliche macro: Or my name isn't {$lb}$_speaking_name{$rb}")