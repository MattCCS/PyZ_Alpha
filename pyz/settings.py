
import os

THIS_FILE = os.path.realpath(__file__)
PROJECT_PATH = os.path.dirname(THIS_FILE)
GAMEDATA_PATH = os.path.join(PROJECT_PATH, "gamedata")

####################################
# GAMEDATA

def absolutize_gamedata(path):
    return os.path.join(GAMEDATA_PATH, path)

ATTRIBUTES_PATH = absolutize_gamedata("attributes.json")
PARAMETERS_PATH = absolutize_gamedata("parameters.json")
LOAD_ORDER      = absolutize_gamedata("load_order.txt")

####################################

LOG_FUNCTIONS = False

####################################

RAYTABLE_DIR = "RAYTABLES/"

WIDTH  = 80
HEIGHT = 24

DIMENSIONS = 2

MAX_RADIUS = 32 # 64
SHELL_ACCURACY = 1 # 1 = 1.0 diff, 2 = 0.5 diff, etc.

ARC_ACCURACY = 1 # 1 = 360, 2 = 720, etc.
