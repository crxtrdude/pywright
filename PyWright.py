import sys,os,traceback
android = None
try:
    import android
except:
    #This is really only for py2exe anyway, which I'm not using right now
    import urllib2,webbrowser,__future__,pygame,pygame.font,zipfile,traceback

if android:
    android.init()

if "PyWright.exe" in sys.argv:
    from ctypes import c_int, WINFUNCTYPE, windll
    from ctypes.wintypes import HWND, LPCSTR, UINT
    prototype = WINFUNCTYPE(c_int, HWND, LPCSTR, LPCSTR, UINT)
    paramflags = (1, "hwnd", 0), (1, "text", "Hi"), (1, "caption", None), (1, "flags", 0)
    MessageBox = prototype(("MessageBoxA", windll.user32), paramflags)

    def show_popup(text):
        MessageBox(text=text, caption="PyWright Error")

abspath = os.path.abspath(os.curdir)
class Logger(object):
    def __init__(self):
        self.terminal = sys.stdout
        self.log = open("loghistory.txt", "a")
        self.log.write("This log contains debugging and error messages from all runs.\n")
        self.now = open("lastlog.txt","w")
        self.now.write("This log contains debugging and error messages from the last run.\n")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
        self.now.write(message)
#~ import gc
#~ gc.enable()
#~ gc.set_debug(gc.DEBUG_LEAK)

sys.stderr = sys.stdout = Logger()
sys.path.insert(0,"")
try:
    from core import libengine
    libengine.run()
except:
    if "PyWright.exe" not in sys.argv:
        raise
    type, value, sys.last_traceback = sys.exc_info()
    lines = traceback.format_exception(type, value,sys.last_traceback)
    print "".join(lines)
    show_popup("Oh no, there's been an error:\nplease post lastlog.txt to pywright.dawnsoft.org or http://forums.court-records.net/games/pywright-beta10-rls-website-growing-faq-started-t9544.html\n\n"+"".join(lines))