
import os
import random
import re
import subprocess
import threading
import time

if __name__ == '__main__':
    import settings
else:
    from pyz import settings

####################################

SOUNDS_DIR = os.path.join(settings.PROJECT_PATH, "sounds") # we'll always type 'sounds' otherwise.

####################################

STAND_DICT = {
    0: 'prone',
    1: 'crouching',
    2: 'standing',
}

SPEED_DICT = {
    0: 0.5, # sneaking
    1: 1.0, # walking
    2: 2.0, # sprinting
}

LOOP_DICT = {
    "swamp":       (0.9, 1.0),
    "waterbridge": (0.9, 0.5),
}

LOOP = True

####################################

def absolutize(relpath):
    return os.path.join(SOUNDS_DIR, relpath)

def random_file_from_dir(path):
    return random.choice([f for f in os.listdir(path) if not f.startswith('.')])

####################################

def get_duration(path):
    data = subprocess.check_output(['afinfo', path])
    return float(re.search(r'estimated duration: ([^\s]+)\s', data).group(1)) # seconds

def _rough_loop(path, times, factor=0.9, volume=1.0):
    dur = get_duration(path)
    for _ in xrange(times):
        if not LOOP:
            break
        _play(path, volume=volume)
        time.sleep(dur*factor)

def rough_loop(relpath, times, factor=0.9, volume=1.0):
    t = threading.Thread(target=_rough_loop, args=(absolutize(relpath), times, factor, volume))
    t.daemon = True # continue after program ends -- so long as we set LOOP=False, that's fine
    t.start()

def stop_all_sounds():
    global LOOP
    LOOP = False
    os.system("ps ax | grep afplay | awk '{print $1}' | xargs kill")

####################################

def _play(path, volume=1.0):
    # print path, volume
    subprocess.Popen(["afplay", path, '--volume', str(volume)])

def play(relpath, volume=1.0):
    _play(absolutize(relpath), volume=volume)

def play_material(material_dir, volume=1.0):
    fname = random_file_from_dir(absolutize(material_dir))
    play(os.path.join(material_dir, fname), volume)

def play_movement(stand_state, sneakwalksprint, material):
    # material should refer to directory -- we choose randomly from there
    play_material(os.path.join("movement", STAND_DICT[stand_state], material), volume=SPEED_DICT[sneakwalksprint])

def play_attack(weapon, material, volume=1.0):
    relpath = "weapons/{}/{}".format(weapon, material)
    fname = random_file_from_dir(absolutize(relpath))
    play(os.path.join(relpath, fname), volume=volume)

####################################

if __name__ == '__main__':
    # files = []
    # files.append('/Users/Matt/Documents/CLASS_FOLDERS/Fall 2013/Game Interface Design/Final Project/Group3Version2/resources/sounds/click.wav')
    # files.append('/Users/Matt/Documents/CLASS_FOLDERS/Fall 2013/Game Interface Design/Final Project/Group3Version2/resources/sounds/shell.wav')
    # files.append('/Users/Matt/Documents/CLASS_FOLDERS/Fall 2013/Game Interface Design/Final Project/Group3Version2/resources/sounds/pistol_shot.wav')
    # files.append('/Users/Matt/Documents/CLASS_FOLDERS/Fall 2013/Game Interface Design/Final Project/Group3Version2/resources/sounds/pistol_reload.wav')

    # for path in files:
    #     play(path)
    play_movement(2, 1, 'dirt')
