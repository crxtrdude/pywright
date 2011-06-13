import re
import pygame

class markup:
    def addcharsto(self,list):
        list.append(self)
class markup_color(markup):
    def __init__(self,color=None,revert=False):
        self.color = color.strip()
        self.revert = revert
        self._color = None
    def __repr__(self):
        return "color: %s %s"%(self.color,self.revert)
    def __str__(self):
        if self.revert:
            return "{c}"
        else:
            return "{c "+self.color+"}"
    def getcolor(self):
        import core
        if not self._color:
            self._color = core.color_str(self.color)
        return self._color

class markup_command(markup):
    def __init__(self,command,args):
        self.command = command
        self.args = args
    def __repr__(self):
        return "command: %s %s"%(self.command,self.args)
    def __str__(self):
        if self.args:
            return "{%s %s}"%(self.command,self.args)
        else:
            return "{%s}"%(self.command,)
            
class markup_variable(markup):
    def __init__(self,var):
        self.variable = var
    def __str__(self):
        return "{$%s}"%(self.variable,)
    def __repr__(self):
        return "variable: %s"%self.variable
        
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
        return markup_color(text[1:])
    if text.startswith("$"):
        return markup_variable(text[1:])
    macro_args = text.split(" ",1)+[""]
    return markup_command(macro_args[0],macro_args[1])

class markup_text:
    """Some text that has annotations"""
    def __init__(self,text,commands=True):
        self.commands = commands
        if isinstance(text,markup_text):
            return text
        self._text = []
        if commands:
            markupre = re.compile("{.*?}")
            text_segments = markupre.split(text)
            markup_segments = markupre.findall(text)
            l = text_segments
            while 1:
                if not l:
                    break
                to_markup(l.pop(0)).addcharsto(self._text)
                if l == text_segments:
                    l = markup_segments
                else:
                    l = text_segments
        else:
            self._text = [c for c in text]
    def chars(self):
        return self._text
    def text(self):
        """Returns full text without markup"""
        return u"".join([x for x in self._text if not hasattr(x,"addcharsto")])
    def fulltext(self):
        """Return full text markup included"""
        return u"".join([str(x) for x in self._text])
    def strip(self):
        t = markup_text("")
        l = self._text[:]
        if not l:
            return t
        while l and l[0]==" ":
            l = l[1:]
        while l and l[-1]==" ":
            l = l[:-1]
        t._text = l
        return t
    def __getitem__(self,i):
        return self._text[i]
    def __repr__(self):
        return self.fulltext()
    def __len__(self):
        return len(self._text)
    def replace(self,*args):
        self.__init__(self.fulltext().replace(*args),self.commands)
    def m_replace(self,pattern,func):
        """pattern is a function run on each character, func is how to
        replace that character. Generally used to replace macros with text
        in some way"""
        nt = []
        for c in self._text:
            if pattern(c):
                nt.append(func(c))
            else:
                nt.append(c)
        self._text = nt

line = markup_text("This is a variable: {$varX}")
line.m_replace(lambda c:hasattr(c,"variable"),lambda c:"VAR:"+c.variable)
assert str(line)=="This is a variable: VAR:varX"

def markup_text_list(list):
    t = markup_text("")
    for l in list:
        t._text.extend(l._text)
    return t
    
assert str(markup_text_list([markup_text("Some text."),markup_text("Some more text.")])) == "Some text.Some more text."
            
class ImgFont(object):
    lastcolor = [255,255,255]
    prevcolor = [255,255,255]
    def __init__(self,img,pwfont=None):
        self.img = pygame.image.load(img)
        self.img.set_colorkey([255,255,255])
        self.colors = {}
        self.chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ "+\
         "abcdefghijklmnopqrstuvwxyz"+\
         "!?.;[](){}\"\"@#:+,/*'_\t\r%\b~<>&`^-"
        self.width = {"":0}
        self.start = {}
        self.quote = 0
        if pwfont:
            self.fnt = pwfont
        else:
            self.fnt = assets.get_font("tb")
    def get_char(self,t,color=[255,255,255]):
        if not self.colors.get(tuple(color),None):
            self.colors[tuple(color)] = pygame.Surface(self.img.get_size())
            self.colors[tuple(color)].fill(color)
            self.colors[tuple(color)].blit(self.img,[0,0])
        if (t,tuple(color)) in self.colors:
            return self.colors[(t,tuple(color))]
        surf = self.fnt.render(t,0,color)
        metrics = self.fnt.metrics(t)[0]
        start = metrics[0]
        starty = max(metrics[2],0)
        edge = min(metrics[4],surf.get_width())
        self.width[t] = edge#edge+1-start
        #FIXME: hack for shorter spaces with pwinternational font, better is to fix the actual font
        if t==" ":
            self.width[t] = 3
        self.start[t] = start
        self.colors[t,tuple(color)] = surf
        return surf
    def split_line(self,text,max_width):
        """Returns the line split at the point to equal a desired width"""
        if not isinstance(text,markup_text):
            text = markup_text(text)
        left = [markup_text("")]
        right = [markup_text("")]
        which = left
        width = 0
        wb = 0
        for i,c in enumerate(text._text):
            if isinstance(c,markup):
                cwidth = 0
            else:
                if c not in self.width:
                    self.get_char(c)
                cwidth = self.width[c]
            if which == left and width+cwidth>max_width:
                r = which.pop(-1)
                which = right
                right.insert(0,markup_text(r.fulltext()[1:]))
            elif c == " ":
                if not which[-1] or which[-1][-1]!=" ":
                    which.append(markup_text(""))
            width+=cwidth
            which[-1]._text.append(c)
        return markup_text_list(left),markup_text_list(right)
    def render(self,text,color=[255,255,255],return_size=False):
        """return a surface with rendered text
        color = the starting color"""
        if not isinstance(text,markup_text):
            text = markup_text(text)
        self.quote = 0
        chars = []
        width = 0
        parse = True
        for c in text.chars():
            if isinstance(c,markup):
                chars.append([c,None])
            else:
                print "COLOR1:",color
                char = self.get_char(c,color)
                chars.append([c,char])
                width+=self.width.get(c,8)
        if return_size:
            return width
        surf = pygame.Surface([width,20])
        x = 0
        for c,img in chars:
            if not img:
                if isinstance(c,markup_color):
                    if c.revert:
                        ImgFont.prevcolor,color = color,ImgFont.prevcolor
                    elif c.getcolor() and c.getcolor() != color:
                        ImgFont.prevcolor = color
                        color = c.getcolor()
                        print "COLOR3:",color
            else:
                print "COLOR2:",color
                surf.blit(self.get_char(c,color),[x,0])
                x += self.width.get(c,8)
            ImgFont.lastcolor = color
        surf.set_colorkey([0,0,0])
        return surf
    def size(self,text):
        """return the size of the text if it were rendered"""
        return self.render(text,[0,0,0],return_size=True)
    def get_linesize(self):
        """return hieght in pixels for a line of text"""
    def get_height(self):
        """return height in pixels of rendered text - average for each glyph"""
    def get_ascent(self):
        """return hieght in pixels from font baseline to top"""
    def get_descent(self):
        """return number of pixels from font baseline to bottom"""

def wrap_text(lines,font,width,wrap=True):
    lines = [markup_text(l) for l in lines]
    page = []
    while lines:
        line = lines.pop(0)
        if wrap:
            left,right = font.split_line(line,width)
        else:
            left,right = line,markup_text("")
        page.append(left)
        if right.strip():
            if not lines: lines.append(markup_text(""))
            lines[0] = markup_text_list([right,markup_text(u" "),lines[0]])
    return page

markup_text("This is a test")
markup_text("The cliche macro: Or my name isn't {$lb}$_speaking_name{$rb}")