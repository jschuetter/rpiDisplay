#!/bin/bash
# Install rgbmatrix pkg 
# Source: https://github.com/hzeller/rpi-rgb-led-matrix/tree/master/bindings/python
pushd ./rgbmatrix-src/
sudo apt-get update && sudo apt-get install python3-dev python3-pillow -y
make build-python PYTHON=$(command -v python3)
sudo make install-python PYTHON=$(command -v python3)
popd

# Install other dependencies
python3 -m pip install --upgrade pip
pip3 install -rU requirements.txt
