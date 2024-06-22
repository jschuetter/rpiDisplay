# rpiDisplay
An RGB matrix OS/driver for Raspberry Pi -- work in progress

## Setup requirements
Set up a virtual environment (recommended):
- Create the venv: `python -m venv .venv` (`.venv` will be the path of the venv - you may choose another name if you wish)
- Activate the venv: `source .venv/bin/activate`
	*N.B. the venv will need to be activated in every new terminal instance*

There are two options for installing dependencies: 
	1) Run setup.sh (assumes Python 3!) in the project root dir, or 
	2) Follow below instructions: 
		- Use `pip install` or `pip3 install` to install all dependencies in `requirements.txt`
		- Follow the rgbmatrix package installation instructions at https://github.com/hzeller/rpi-rgb-led-matrix/tree/master/bindings/python, using rgbmatrix-src as the root directory

N.B. if you need to uninstall the rgbmatrix pkg for any reason (outside a virtual environment), using `pip uninstall` will not work. The install files can be found under /usr/local/lib/pythonX.X/dist-packages/. Run `sudo rm -rf rgbmatrix*` to remove the package. 

Font sources: 
- bitmap-fonts: github.com/Tecate/bitmap-fonts
- ibm: github.com/farsil/ibmfonts
- spleen: github.com/fcambus/spleen
- basic: github.com/hzeller/rpi-rgb-matrix
