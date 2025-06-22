#!/bin/python
'''
mp4-resizer.py
22 Jun 2025
Jacob Schuetter

MP4-to-gif video converter & resizer for use in Anim component
'''
import sys, os
import av
from PIL import Image

if len(sys.argv) < 4:
    sys.exit("Usage: mp4-resizer.py    inPath    width    height    [fps]")
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
if not os.path.exists(input_file):
    sys.exit("Video file does not exist")
vid = av.open(input_file)
vidStream = vid.streams.video[0]
    
try: 
    to_width = int(to_width)
    to_height = int(to_height)
except ValueError: 
    sys.exit("Width and height must be integers")

if not to_fps: 
    to_fps = vidStream.average_rate
try: 
    to_fps = float(to_fps)
except ValueError: 
    sys.exit("FPS value must be int or float")
delay = 1000 / to_fps       # Convert fps to gif delay

# Declare output
file_base, _ = os.path.splitext(input_file)
output_file = file_base + "-resized.mp4"
# Check that filepath does not already exist
if os.path.exists(output_file):
    sys.exit(f"Output file {output_file} already exists. Please remove it or choose a different name.")

# Declare output
file_base, _ = os.path.splitext(input_file)
output_file = file_base + "-resized.gif"

# Downscale
print("Processing...")
frames = []
for pkt in vid.demux(vidStream):
    for frame in pkt.decode():
        # Convert frame to PIL
        frames.append(frame.to_image())
        frames[-1].thumbnail((to_width, to_height), Image.ANTIALIAS)
    
frames[0].save(output_file, save_all=True, append_images=frames[1:], duration=delay, loop=0)