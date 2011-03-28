c:\python26\python -OO setup.py py2exe
c:\python26\python -OO setup.py script
7za.exe -aoa x dist\library.zip -olibrary\
rd library\core /s /q
del dist\library.zip
cd library\
..\7za.exe a -tzip -mx9 ..\dist\library.zip -r
cd ..
rd library /s /q

rem upx --best dist\*.*

rem rename dist PyWright
rem 7za.exe a -tzip -mx9 ..\PyWright_0.95_rc2.win.zip PyWright
rem rename PyWright dist

rem rename scriptdist PyWright
rem 7za.exe a -tzip -mx9 ..\PyWright_0.95_rc2.src.zip PyWright
rem rename PyWright scriptdist

pause