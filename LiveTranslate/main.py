from playsound import playsound as ps
from googletrans import Translator
from random_user_agent.params import SoftwareName, OperatingSystem
from random_user_agent.user_agent import UserAgent
import speech_recognition as sr
from threading import Thread
from gtts import gTTS
import keyboard as kb
import time
import os
import pyttsx3
import re



class PhraseTimer:
    def __init__(self):
        self.started = False
        self.timer = 0
        self.limit = 5
        self.phrase_parts = []
        self.phrase = ''
        T = Thread(target=self.tick)
        T.start()

    def reset(self):
        self.timer = 0
        self.limit = 5
        self.phrase_parts = []
        self.phrase = ''

    def processPhrase(self):
        global said
        said = ' '.join(self.phrase_parts)
        print('<{}>'.format(said))
        self.reset()

    def tick(self):
        if not self.started:
            print('PhraseTimer Started')
            self.started = True
        while self.started:
            time.sleep(1)
            self.timer +=1
            if self.timer >= self.limit:
                self.processPhrase()



LOGGING = False
VOICE_ON = True


def call_back(r, audio):
    global said, listening, PC, VOICE_ON
    if listening:
        try:
            if MODE == 'en':
                said = r.recognize_google(audio, language='en-gb')

            else:
                said = r.recognize_google(audio, language='ja-jp')

            if said.lower() in ['enable voice']:
                VOICE_ON = True
            if said.lower() in ['disable voice']:
                VOICE_ON = False

            Z = Thread(target=do, daemon=True)
            Z.start()

        except sr.UnknownValueError:
            pass


prox = {'a': '72.237.90.70', 'http': '198.12.148.76', 'b': '8.38.238.214',
            'c': '167.99.4.65', 'd': '192.200.200.78', 'e': '1207.191.15.166',
            'f': '24.106.221.230', 'g': '74.209.191.66', 'h': '50.236.148.254',
            'i': '/104.156.251.31', 'j': '64.227.63.204'}

software_names = [SoftwareName.CHROME.value]
os_names = [OperatingSystem.WINDOWS.value,
            OperatingSystem.LINUX.value, OperatingSystem.ANDROID.value]
uAgent_rotator = UserAgent(
    software_names=software_names,
    operating_systems=os_names, limit=200)
uAgent = uAgent_rotator.get_random_user_agent()

MODE = 'en'

r = sr.Recognizer()
m = sr.Microphone(0)
with m as source:
    print('calibrating...')
    r.adjust_for_ambient_noise(source)
    print('-done-')

listening = True
said = ''
tran = ''
PC = False

audio_filter = re.compile('(.*\\.(mp3|ogg|flac|wav))( .*)?')




run = True


def APP():
    global said, listening, PC, MODE
    while run:
        # if kb.is_pressed('t+r'):
        # time.sleep(.5)
        # translator = Translator()
        # n = input('enter text to translate >>>')
        # print(n + '\n' + translator.translate(n).text)

        if said.lower() in ['change language mode', 'change language', 'switch language mode', 'switch language',
                         'change mode', 'モードを変更', '言語を変更']:
            if MODE == 'en':
                MODE = 'ja'
                listening = False
                speak('language set to japanese', lang='en-gb')
            else:
                MODE = 'en'
                listening = False
                speak('language set to English')


def speak(text='', lang='en-gb', *args):
    global said, listening, PC, LOGGING
    said = ''
    for arg in args:
        if arg == 'end_log':
            LOGGING = False
            ps('computer.mp3')
            kb.press_and_release('alt+/')
    if not re.match(audio_filter, text):
        try:
            tts = gTTS(text, lang=lang)
            filename = 'voice.mp3'
            tts.save(filename)
            ps('silence.wav')
            ps(filename)
            os.remove(filename)
        except AssertionError:
            pass
    else:
        if not text == '':
            filename = re.match(audio_filter, text).group(1)
            ps(filename)
            if not re.match(audio_filter, text).group(3) == '':
                t = re.match(audio_filter, text).group(3)
                tts = gTTS(t, lang=lang)
                tts.save('voice.mp3')
                ps('silence.wav')
                ps('voice.mp3')
                os.remove('voice.mp3')
    PC = False
    time.sleep(3)
    listening = True


def do():
    global listening, said, tran, VOICE_ON


    if not said == '':
        print(said)

        translator = Translator(user_agent=uAgent, proxies=prox)
        L = translator.detect(said)
        if L.lang == 'ja':
            try:
                tran = translator.translate(said, src='ja', dest='en').text
                print(tran)
                if VOICE_ON:
                    listening = False
                    speak(tran, lang='en-gb')
            except TypeError:
                print('UwU')
        else:
            try:
                print('--')
                tran = translator.translate(said, src='en', dest='ja').text
                print(tran)
                if VOICE_ON:
                    listening = False
                    speak(tran, lang='ja')
            except Exception as e:
                print(e)




r.listen_in_background(m, call_back, phrase_time_limit=10)


T1 = Thread(target=APP)
T2 = Thread(target=do)
T1.start()
T2.start()
