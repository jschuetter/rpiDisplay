#!/usr/bin/env python
'''
gif-resizer.py
14 Jun 2025
Jacob Schuetter

Helper script for resizing GIF animations for display on matrix
'''
import time, sys, os

from PIL import Image


if len(sys.argv) < 4:
    sys.exit("Usage: gif-resizer.py    inPath    width    height    [fps]")
else:
    input_file = sys.argv[1]
    to_width = sys.argv[2]
    to_height = sys.argv[3]
    try: 
        # Try to get fps argument
        to_fps = sys.argv[4]
    except IndexError: 
        # If fps not provided, take delay from image (below)
        to_fps = None

# Open image file & do input validation
gif = Image.open(input_file)
try:
    num_frames = gif.n_frames
except Exception:
    sys.exit("Provided image is not a .gif")


try: 
    to_width = int(to_width)
except ValueError: 
    sys.exit("Width and height must be integers")
try: 
    to_height = int(to_height)
except ValueError: 
    sys.exit("Width and height must be integers")

# Calculate .gif delay (ms between frames) from fps
if not to_fps: 
    # If fps value not provided, take from original file
    delay = gif.info["duration"]
else: 
    # Else, validate fps value and calculate delay
    try: 
        to_fps = float(to_fps)
    except ValueError: 
        sys.exit("FPS value must be int or float")
    delay = 1000 // to_fps

file_base, _ = os.path.splitext(input_file)
output_file = file_base + "-resized.gif"


print("Processing...")
frames = []
for idx in range(0, num_frames):
    gif.seek(idx)
    # must copy the frame out of the gif, since thumbnail() modifies the image in-place
    frames.append(gif.copy())
    frames[-1].thumbnail((to_width, to_height), Image.ANTIALIAS)
    frames[-1].convert("RGB")
# Close the gif file to save memory now that we have copied out all of the frames
gif.close()

frames[0].save(output_file, save_all=True, append_images=frames[1:], duration=200, loop=0)