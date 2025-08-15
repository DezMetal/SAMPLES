import pyttsx3
from datetime import datetime, timedelta
import io
from argostranslate import package
import argostranslate.translate
import pyautogui
import simpleaudio as sa


engine = pyttsx3.init()
VIDS = ['HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\TTS_MS_EN-US_DAVID_11.0',
'HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\TTS_MS_EN-US_ZIRA_11.0',
'HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\TTS_MS_JA-JP_HARUKA_11.0']
VID = VIDS[2]
RATE = 140
VOL = .9
engine.setProperty('voice', VID)
engine.setProperty('rate', RATE)
engine.setProperty('volume', VOL)
TRANS_ENABLED = False
COMMAND_PATS = {
    'getTime': '.*(what(.?s| is) the time|what time is it|do you know what time it is|tell me the time)',
    'TTS': '^$'
}

def install_trans_models(from_code, to_code):
    global TRANS_ENABLED
    try:
        print(f'installing translation models from {from_code}, to {to_code}...')
        package.update_package_index()
        available_packages = package.get_available_packages()
        package_to_install = next(filter(lambda x: x.from_code == from_code and x.to_code == to_code, available_packages))
        package.install_from_path(package_to_install.download())
        TRANS_ENABLED = True
        print('success :)\n')
    except Exception as e:
        print(f'installation failed :(\n{e}')

def mod_time(t, **by):
    f = '%I:%M:%S%p'if t.count(':') == 2 else '%I:%M%p'
    p = datetime.strptime(t, f).time()
    d = datetime.combine(datetime.today(), p)
    mod = timedelta(**by)
    mptime = d + mod
    mtimestr = datetime.strftime(mptime, '%I:%M:%S%p')
    return {'ogtime': t, 'modby': by, 'mptime': mptime, 'mtime': mtimestr}

def real_time(s=False, p=True):
    f = '%I:%M:%S%p'if s else '%I:%M%p'
    f = f.replace('%p', '') if not p else f
    print(datetime.now().strftime(f))
    return datetime.now().strftime(f)

def getTime(*args):
    t = datetime.now().strftime('%I:%M %p')
    return t

def TTS(t, s=True):
    engine.setProperty('voice', VID)
    engine.setProperty('rate', RATE)
    engine.setProperty('volume', VOL)
    astream = io.BytesIO()
    astream.seek(0)
    engine.say(t)
    engine.runAndWait()
    if s:
        engine.save_to_file(t, astream)
        return astream

def translate(t, _from, _to, speak=False):
    if not TRANS_ENABLED:
        install_trans_models(_from, _to)
    trans = ''
    try:
        trans = argostranslate.translate.translate(t, _from, _to)
    except Exception as e:
        print(e)
    finally:
        if speak:
            TTS(trans)
        return trans
