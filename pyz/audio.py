
import os
import random
import subprocess
import threading

if __name__ == '__main__':
    import settings
else:
    from pyz import settings

####################################

SOUNDS_DIR = os.path.join(settings.PROJECT_PATH, "sounds") # we'll always type 'sounds' otherwise.

####################################

# PLAYING = set()

# def __play(path):
#     PLAYING.add(path)
#     subprocess.call(["afplay", path])
#     PLAYING.discard(path)

# def _play(path):
#     if path in PLAYING:
#         return
#     t = threading.Thread(target=__play, args=(path,))
#     t.start()
#     # __play(path)

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

def absolutize(relpath):
    return os.path.join(SOUNDS_DIR, relpath)

def random_file_from_dir(path):
    return random.choice([f for f in os.listdir(path) if not f.startswith('.')])

####################################

def stop_all_sounds():
    os.system("ps ax | grep afplay | awk '{print $1}' | xargs kill")

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
