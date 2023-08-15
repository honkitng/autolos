# Autolos

## Overview

Python project for automating Aquilos 1 milling without AutoScript.

## Installation

### Precompiled binary

Copy `dist/` directory to the microscope PC and run `Autolos.exe`.

### Run from source code

Requires either a Python >=3.8 installation on the microscope PC or PyInstaller to package the project into an executable (must be done on a separate Windows PC running Windows 7/8/10/11) and run on the microscope PC.

#### Pyinstaller Command:

`pyinstaller Autolos.py --onefile -w --hidden-import pyautogui --hidden-import mss --hidden-import tkinter.filedialog --hidden-import tkinter.messagebox`

## Run Procedure

1. Follow the on-screen instructions & fill in the required inputs.
2. Allow the software to drive to each lamella point and click to move the stage to the milling position when prompted.
3. Let the software mill each lamella automatically (beam will be turned off at the end of the milling session).
