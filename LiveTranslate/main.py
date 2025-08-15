import pyaudio
from time import sleep
import io
import re
import inspect
import os
import vosk
import sys
import json
from datetime import datetime, timedelta
import schedule
import keyboard as kb
from tkinter import *
from tkinter import ttk
from google import generativeai as genai
from dotenv import load_dotenv



load_dotenv()
#genai.configure(api_key=os.environ['GEM_API_KEY'])
GUI = Tk()
sw, sh = GUI.winfo_screenwidth(), GUI.winfo_screenheight()
w = 1200
h = 100
print(sw, sh)
x, y = int((sw/2) - (w/2)), int(sh-(h*1.5))
GUI.geometry(f'{w}x{h}+{x}+{y}')
GUI.title('D-Net')
mainframe = ttk.Frame(GUI)
mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
GUI.columnconfigure(0, weight=1)
GUI.rowconfigure(0, weight=1)
GUI.attributes('-alpha', .2)
dtext = StringVar()
dtext_label = ttk.Label(mainframe, wraplength=w//2, textvariable=dtext, font=('Helvetica', 30)).place(relx=.5, rely=1, anchor='s')
dtext.set('this is a test')

import functions
from functions import *

FUNCS = {}
EVENTS = {}
SPEAK = True
SUB = True

'''
def isItFunny(t):
    p = """'is it kinda funny?'
    You will simply return 1 for 'funny' and 0 for not.

    Input:
    '###INPUT###'

    Do not say anything besides 1 OR 0.
    """
    config = genai.GenerationConfig(temperature=.1)
    M = genai.GenerativeModel(model='gemini-1.5-flash-001')
    r = str(m.generate_content(contents=[p.replace('###INPUT###', t)]).text).strip()

    print(r)
    return r
'''

print(translate('this is a test.', 'en', 'ja'))
#play_sound('sounds/laugh.mp3')

def toggle_speech():
    global SPEAK
    SPEAK = False if SPEAK else True

def clear_console():
    # Clear console screen for Windows
    if os.name == 'nt':
        _ = os.system('cls')
    # Clear console screen for Unix/Linux/MacOS
    else:
        _ = os.system('clear')

def bring_to_top(window):
    window.lift()
    window.attributes('-topmost', True)
    window.attributes('-topmost', False)

d = {'a':1, 'b':2, 'c':3, 'd':4, 'e':5}

def do_once(f, **args):
    f(**args)
    return schedule.CancelJob

def delkey(k):
    clear_console()
    del d[k]
    print(d)

def del_after(x):
    clear_console()
    ptime = mod_time(real_time(s=True), seconds=x)['mptime']
    ptime = datetime.strftime(ptime, '%H:%M:%S')
    print(ptime)
    schedule.every().day.at(ptime).do(lambda: do_once(delkey, k=list(d.keys())[0]))

def show_jobs():
    scheduled_jobs = schedule.get_jobs()
    if scheduled_jobs:
        print("Scheduled Jobs:")
        for job in scheduled_jobs:
            print(job)

def print_word(word):
    print(word)
    return word

def loadFunc(func, name=None, pat='^$'):
    global FUNCS
    if inspect.ismodule(func):
        for n, f in inspect.getmembers(func, inspect.isfunction):
            try:
                FUNCS.update({n:{'pat':re.compile(COMMAND_PATS[n]), 'func':[f]}})
            except KeyError:
                FUNCS.update({n:{'pat':re.compile(r'^$'), 'func':[f]}})
    if isinstance(func, list):
        FUNCS.update({name:{'pat':re.compile(pat), 'func':[f for f in func]}})
        for f in func:
            loadFunc(f)
    if inspect.isfunction(func):
        if func.__name__ not in list(FUNCS.keys()):
            FUNCS.update({func.__name__:{'pat':re.compile(pat), 'func':[func]}})

loadFunc(functions)
loadFunc(toggle_speech, 'Toggle Speech', r'^toggle speech$')
print('...')
#loadFunc([print_word, print_word, print_word], name='printWords', pat=r'print (\S*) (\S*) (\S*)')
FUNCS

def add_event(name, timestr, func):
    EVENTS[name] = {
        'time': timestr,
        'func': func
    }
    schedule.every().day().at(timestr).do_once(func)
    schedule.every().day().at(functions.mod_time(timestr, seconds=1)['mtime']).do_once()
    print(f'event {name} created at {timestr}')

def match_intent(txt, funcs_dict):
    matches = {}
    for func_name, data in funcs_dict.items():
        pat, func_list = data['pat'], data['func']
        matched = pat.match(txt)
        if matched:
            if func_name in matches:
                matches[func_name].extend(matched.groups())
            else:
                matches[func_name] = list(matched.groups(1))
    return matches

enmodelpath = 'model-small-en-us'
enmodel = vosk.Model(enmodelpath)
r = vosk.KaldiRecognizer(enmodel, 16000)
p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8192)

while True:
    GUI.update()
    bring_to_top(GUI)
    data = stream.read(4096, exception_on_overflow=False)
    output = ''
    if r.AcceptWaveform(data):
        res = json.loads(r.Result())
        intext = res['text'].replace('three', '3')

        if not intext:
            continue
        tr = translate(intext, 'en', 'ja')
        dtext.set(f'{intext}\n{tr}')
        GUI.update()
        bring_to_top(GUI)

        if SPEAK:
            TTS(tr)

        print(tr)
        stream.stop_stream()
        print(f'Input: {intext}')
        intents = match_intent(intext, FUNCS)

        if intents:
            print(intents)
        stream.start_stream()
        final = []

        for k in intents.keys():
            output = next((v['func'] for n, v in FUNCS.items() if n == k), None)

            if output:
                if len(output) > 1:
                    out = None
                    for step, f in enumerate(output):
                        try:
                            args = intents[k][step]
                        except IndexError:
                            args = out

                        out = f(args)
                        if inspect.isfunction(out):
                            out = out()
                        final.append(out)

                    output = out
                else:
                    output = output[0]() if inspect.isfunction(output[0]) else output[0]
                    final.append(output)

            if type(output) == 'function':
                output = output()
            stream.stop_stream()

            for f in final:
                FUNCS['TTS']['func'][0](f)
            output = ''
            sleep(.1)
            stream.start_stream()

        if 'terminate' in intext.lower():
            print('END')
            FUNCS['TTS']['func'][0]('terminated')
            stream.stop_stream()
            stream.close()
            GUI.destroy()
            break
