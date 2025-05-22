# rpiDisplay
An RGB matrix OS/driver for Raspberry Pi -- work in progress

## Setup requirements
There are two options for installing dependencies: 
1) Run setup.sh (assumes Python 3!) in the project root dir, or 
2) Follow below instructions: 
		- Use `pip install` or `pip3 install` to install all dependencies in `requirements.txt`
		- Follow the rgbmatrix package installation instructions at https://github.com/hzeller/rpi-rgb-led-matrix/tree/master/bindings/python, using rgbmatrix-src as the root directory

#### Setup notes: 
* The rgbmatrix library requires root privileges to run smoothly (in order to access low-level hardware for initialization - see https://github.com/hzeller/rpi-rgb-led-matrix/tree/master for more information). This results in a couple of things: 
	- All scripts must be run as root user (i.e. using `sudo python3` or `sudo python`)
	- All packages must also be installed with sudo as well
	- Virtual environments *will not work*, as root user will not see packages installed in venv
* N.B. if you need to uninstall the rgbmatrix pkg for any reason (outside a virtual environment), using pip uninstall will not work. The install files can be found under `/usr/local/lib/pythonX.X/dist-packages/` (X.X is usually 2.7 or 3.7). Run `sudo rm -rf rgbmatrix*` to remove the package.
* If Python cannot find the dotenv module, uninstall it using `pip3 uninstall` and `pip uninstall`, then re-run the setup script or reinstall the dependency manually

Font sources: 
- bitmap-fonts: github.com/Tecate/bitmap-fonts
- ibm: github.com/farsil/ibmfonts
- spleen: github.com/fcambus/spleen
- basic: github.com/hzeller/rpi-rgb-matrix

## Modules
### BasicClock
A basic clock display with date and time displayed in 24-hour format hh:mm:ss. 

### Editor
A dev tool designed for laying out new modules. 
Note that this is *not* designed for creating fully-fledged modules. It has no ability to dynamically-assign element content or create animated elements. It is only for creating the general layout without having to trial-and-error things into place. 