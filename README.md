# PyWright
Python game engine for running visual novel games similar to the Phoenix Wright series

This program, a 'case maker', was created to enable fans to produce their own fan cases based on the Phoenix Wright series of games. It consists of an engine to run the games. Games themselves are scripted in "wrightscript", and several of them can be downloaded from within the program itself.

## Features
  * Fully functional scripting language, "WrightScript", based on a mishmash of BASIC and Python
  * Animated sprites and text with sophisticated dialog engine
  * Music, sound effects, other special effects
  * Customizable
  * Multiple saved games
  * Works identically on Windows, Mac, Linux and Android
  * Stay up to date by downloading engine patches and supported games from the engine itself
  * Multiple display options

## History
This project was started in 2007 as a personal project by Saluk. After showing it to other Phoenix Wright fans on the court-records forums, it has grown and evolved through their feedback. It is the dedicated members there who have actually made the games that are available.

## Requirements for building/running from source
You will need the following:
- Python 2.7
- Pygame 1.9.1
- NumPy 1.6.2

To pack the file into an exe, you can use Py2Exe or Py2App for Windows and OS X respectively.

This version has Android functionality built in. Unfortunately, I don't know how to compile it (I might have a lead though on what he used)

### NOTES:
The reason why a older version needs to be used (as of this writing the most recent version is 1.10) because of the color tinting problem.
If you suffer from this, use the suggested version. Otherwise, a new NumPy could be used.

Also if you suffer problems from missing SimpleJSON, then you can do install so using PIP.

## License
Under the New BSD License. This engine uses some assets by Capcom. I might remove/change them from this repo to avoid some problems.

## Credits
- saluk - original author
- CRxTRDude - maintainance
