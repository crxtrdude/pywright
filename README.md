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
- Python 3.9 or newer (tested with 3.13)
- Pygame 2.6 or newer
- NumPy

Pygame and NumPy ship native wheels for Apple Silicon (M1 and later), so no Rosetta or Homebrew SDL is needed.

To set up and run from the repository root:

    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    python PyWright.py

To start a game directly, pass its folder: `python PyWright.py -run examples/court`.

To pack the file into an exe, you can use Py2Exe or Py2App for Windows and macOS respectively.

This version has Android functionality built in. Unfortunately, I don't know how to compile it (I might have a lead though on what he used)

### NOTES:
Movie playback is not available: pygame 2 removed the `pygame.movie` module, so the movie command reports an error instead of playing.

## License
Under the New BSD License. This engine uses some assets by Capcom. I might remove/change them from this repo to avoid some problems.

## Credits
- saluk - original author
- CRxTRDude - maintainance
