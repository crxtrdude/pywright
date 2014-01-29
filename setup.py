APP_NAME = 'PyWright'


cfg = {
    'name':APP_NAME,
    'version':'beta1',
    'description':'',
    'author':'',
    'author_email':'',
    'url':'',
    
    'py2exe.target':'',
    'py2exe.icon':'bb.ico', #64x64
    'py2exe.binary':APP_NAME, #leave off the .exe, it will be added
    
    'py2app.target':'',
    'py2app.icon':'icon.icns', #128x128
    
    'cx_freeze.cmd':'~/src/cx_Freeze-3.0.3/FreezePython',
    'cx_freeze.target':'',
    'cx_freeze.binary':APP_NAME,
    }
    
# usage: python setup.py command
#
# sdist - build a source dist
# py2exe - build an exe
# py2app - build an app
# cx_freeze - build a linux binary (not implemented)
#
# the goods are placed in the dist dir for you to .zip up or whatever...

from distutils.core import setup, Extension
try:
    import py2exe
except:
    pass

import sys
import glob
import os
import shutil

try:
    cmd = sys.argv[1]
except IndexError:
    print 'Usage: setup.py py2exe|py2app|cx_freeze'
    raise SystemExit

# utility for adding subdirectories
def add_files(dest,generator,ignorefiles=[],ignorefolders=[]):
    for dirpath, dirnames, filenames in generator:
        for name in ['CVS', '.svn']+ignorefolders:
            if name in dirnames:
                dirnames.remove(name)
        dest.extend([dirpath+"/"+x for x in dirnames])
        for name in filenames:
            if '~' in name: continue
            suffix = os.path.splitext(name)[1]
            if suffix in ['.pyc', '.pyo']+ignorefiles: continue
            if name[0] == '.': continue
            filename = os.path.join(dirpath, name)
            dest.append(filename)

# define what is our data
bexe = 1
bart = 1
bmusic = 0
data = []
if bexe:
    add_files(data,os.walk('fonts'))
    add_files(data,os.walk('sfx'))
    add_files(data,os.walk('art/general'))
    add_files(data,os.walk("core"),["cache"])
    data+=["core/cache"]
    data+=["games/","music/","movies/","downloads/"]
    data+=["doc.txt","changelog.txt","data.txt"]
    data+=["art/ev/","art/port/","art/fg/","art/bg/"]
    data+=["art/bg/"+x for x in os.listdir("art/bg/") if x.endswith(".png")]
    data+=["art/fg/"+x for x in os.listdir("art/fg/") if x.endswith(".png") or x.endswith(".gif") or x.endswith(".txt")]

# build the sdist target
if cmd == 'sdist' and bexe:
    f = open("MANIFEST.in","w")
    for l in data: f.write("include "+l+"\n")
    for l in src: f.write("include "+l+"\n")
    f.close()
    
    setup(
        name=cfg['name'],
        version=cfg['version'],
        description=cfg['description'],
        author=cfg['author'],
        author_email=cfg['author_email'],
        url=cfg['url'],
        )

# build the py2exe target
try:
    from py2exe.build_exe import py2exe
except:
    class py2exe:
        pass
class Py2exe(py2exe):
    def initialize_options(self):
        # Add a new "upx" option for compression with upx
        py2exe.initialize_options(self)
        self.upx = 0
    def copy_file(self, *args, **kwargs):
        # Override to UPX copied binaries.
        (fname, copied) = result = py2exe.copy_file(self, *args, **kwargs)
        basename = os.path.basename(fname)
        if (copied and self.upx and
            (basename[:6]+basename[-4:]).lower() != 'python.dll' and
            fname[-4:].lower() in ('.pyd', '.dll')):
            os.system('upx --best "%s"' % os.path.normpath(fname))
        return result
    def patch_python_dll_winver(self, dll_name, new_winver=None):
        # Override this to first check if the file is upx'd and skip if so
        if not self.dry_run:
            if not os.system('upx -qt "%s" >nul' % dll_name):
                if self.verbose:
                    print "Skipping setting sys.winver for '%s' (UPX'd)" % \
                          dll_name
            else:
                py2exe.patch_python_dll_winver(self, dll_name, new_winver)
                # We UPX this one file here rather than in copy_file so
                # the version adjustment can be successful
                if self.upx:
                    os.system('upx --best "%s"' % os.path.normpath(dll_name))
if cmd in ('script',) and bexe:
    dist_dir = "scriptdist"
    data_dir = dist_dir
    data+=["updater.py","PyWright.py"]
if cmd in ('py2exe',) and bexe:
    dist_dir = os.path.join('dist',cfg['py2exe.target'])
    data_dir = dist_dir
    
    dest = cfg['py2exe.binary']+'.py'
    
    setup(
        #zipfile=None,
        cmdclass = {"py2exe":Py2exe},
        options={'py2exe':{
            'dist_dir':dist_dir,
            'dll_excludes':['_dotblas.pyd',"cdrom.pyd"],
            'packages':['encodings','pygame','numpy'],
            'includes':['__future__'],
            'ignores':['numpy.distutils.tests'],
            'excludes':['curses','email','logging','numarray',
                                'Tkinter','tcl',"ssl",
                                "stringprep","StringIO","bz2","_ssl",
                                "doctest","optparse","popen2","Numeric","OpenGL",
                                "multiprocessing","compiler","distutils",
                                "setuptools","psyco"],
            'compressed':1,
            'bundle_files':2,
            'ascii':1
            }},
        windows=[{
            'script':"PyWright.py",
            'icon_resources':[(1,"art/general/bb.ico")],
            },
            {
            "script":"updater.py"}],
        )

# build the py2app target
if cmd == 'py2app' and bexe:
    dist_dir = os.path.join('dist',cfg['py2app.target']+'.app')
    #data_dir = os.path.join(dist_dir,'Contents','Resources')
    data_dir = 'dist'
    from setuptools import setup


    OPTIONS = {'argv_emulation': True}#, 'iconfile':cfg['py2app.icon']}

    setup(
        app=['PyWright_run.py'],
        data_files=[],
        options={'py2app': OPTIONS},
        setup_requires=['py2app'],
    )

# make the cx_freeze target
if cmd == 'cx_freeze' and bexe:
    dist_dir = os.path.join('dist',cfg['cx_freeze.target'])
    data_dir = dist_dir
    os.system('%s --install-dir %s --target-name %s run_game.py'%(cfg['cx_freeze.cmd'],cfg['cx_freeze.binary'],dist_dir))

# recursively make a bunch of folders
def make_dirs(dname_):
    parts = list(os.path.split(dname_))
    dname = None
    while len(parts):
        if dname == None:
            dname = parts.pop(0)
        else:
            dname = os.path.join(dname,parts.pop(0))
        if not os.path.isdir(dname):
            os.mkdir(dname)

# copy data into the binaries 
if cmd in ('py2exe','cx_freeze','script', 'py2app'):
    dest = data_dir
    for fname in data:
        print fname
        dname = os.path.join(dest,os.path.dirname(fname))
        make_dirs(dname)
        if not os.path.isdir(fname):
            print "copy",fname,dname
            shutil.copy(fname,dname)
if cmd == "py2exe":
    os.mkdir("library")
    for fname in os.listdir("extradlls"):
        shutil.copy("extradlls/"+fname,"library/"+fname)
if cmd=="py2exe":
    files = []
    dirs = []
    for fname in data+[x for x in os.listdir("dist") if not os.path.isdir("dist/"+x)]:
        inno = fname.replace("/","\\")
        if os.path.isdir("dist\\"+inno):
            dirs.append("Name: {app}\\"+fname+"\n")
        else:
            dest = ""
            if "\\" in inno:
                dest = inno[:inno.rfind("\\")]
            d = (inno,dest)
            files.append("Source: dist\%s; DestDir: {app}\%s; Flags: overwritereadonly\n"%d)
    #~ inno = open("setup.iss","w")
    #~ inno.write("""[Setup]
#~ AppName=PyWright
#~ AppVerName=PyWright Beta6
#~ DefaultDirName={pf}\PyWright
#~ DefaultGroupName=PyWright
#~ Compression=lzma
#~ OutputBaseFilename=pywright-beta6-setup
#~ PrivilegesRequired=none
#~ UninstallDisplayIcon={app}\PyWright.exe
#~ SetupIconFile=C:\Users\saluk\Desktop\dev\pyphoenix\PyWright_trunk\\bb.ico
#~ InternalCompressLevel=ultra64
#~ [Icons]
#~ Name: {group}\PyWright; Filename: {app}\PyWright.exe; WorkingDir: {app}
#~ Name: {group}\updater; Filename: {app}\updater.exe
#~ Name: {group}\uninstall; Filename: {app}\unins000.exe""")
    #~ inno.write("\n\n[Files]\n")
    #~ inno.writelines(files)
    #~ inno.write("\n[Dirs]\n")
    #~ inno.writelines(dirs)
    #~ inno.close()
