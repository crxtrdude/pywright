import sys,os,traceback
android = None
try:
    import android
except:
    #This is really only for py2exe anyway, which I'm not using right now
    import urllib2,webbrowser,__future__,pygame,pygame.font,zipfile,traceback

if android:
    android.init()
    
def is_exe():
    return sys.argv and sys.argv[0].endswith(".exe")

if is_exe():
    from ctypes import c_int, WINFUNCTYPE, windll
    from ctypes.wintypes import HWND, LPCSTR, UINT
    prototype = WINFUNCTYPE(c_int, HWND, LPCSTR, LPCSTR, UINT)
    paramflags = (1, "hwnd", 0), (1, "text", "Hi"), (1, "caption", None), (1, "flags", 0)
    MessageBox = prototype(("MessageBoxA", windll.user32), paramflags)

    def show_popup(text):
        MessageBox(text=text, caption="Program Error")

abspath = os.path.abspath(os.curdir)
class Logger(object):
    def __init__(self):
        self.terminal = sys.stdout
        self.log = self.now = None
        if not android:
            self.log = open("loghistory.txt", "a")
            self.log.write("This log contains debugging and error messages from all runs.\n")
        if not android:
            self.now = open("lastlog.txt","w")
            self.now.write("This log contains debugging and error messages from the last run.\n")

    def write(self, message):
        self.terminal.write(message)
        if self.log:
            self.log.write(message)
        if self.now:
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
    if not is_exe():
        raise
    type, value, sys.last_traceback = sys.exc_info()
    lines = traceback.format_exception(type, value,sys.last_traceback)
    print("".join(lines))
    show_popup("Oh no, there's been an error:\nMore detailed info available in lastlog.txt."+"".join(lines))