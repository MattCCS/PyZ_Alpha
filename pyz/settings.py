
import os

THIS_FILE = os.path.realpath(__file__)
PROJECT_PATH = os.path.dirname(THIS_FILE)

####################################

RAYTABLE_DIR = "RAYTABLES/"

WIDTH  = 80
HEIGHT = 24

DIMENSIONS = 2

MAX_RADIUS = 32 # 64
SHELL_ACCURACY = 1 # 1 = 1.0 diff, 2 = 0.5 diff, etc.

ARC_ACCURACY = 1 # 1 = 360, 2 = 720, etc.
