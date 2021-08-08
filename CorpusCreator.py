import multiprocessing
import os
import re
import time
from multiprocessing import Manager
from multiprocessing import Process

import PySimpleGUI as sg
import numpy
import phonemizer
import pyaudio
import pyloudnorm
import soundfile as sf
import torch
from pynput import keyboard
from torchaudio.transforms import Vad as VoiceActivityDetection

import parameters


class CorpusCreator:

    def __init__(self, corpus_name):
        """
        Load prompt list and prepare status quo
        """
        multiprocessing.set_start_method('spawn', force=False)
        self.corpus_name = corpus_name
        self.resource_manager = Manager()
        self.datapoint = self.resource_manager.list()
        self.datapoint.append("")
        self.datapoint.append("")
        self.record_flag = self.resource_manager.list()
        self.stop_flag = False
        self.stop_recorder_process_flag = self.resource_manager.list()
        self.index = self.resource_manager.list()
        self.vad = self.vad = VoiceActivityDetection(sample_rate=parameters.sampling_rate)
        self.meter = pyloudnorm.Meter(parameters.sampling_rate)
        self.pyaudio = pyaudio.PyAudio()
        self.lookup_path = "Corpora/{}/metadata.csv".format(corpus_name)
        self.audio_save_dir = "Corpora/{}/".format(corpus_name)
        with open("Corpora/{}/prompts.txt".format(corpus_name), mode='r', encoding='utf8') as prompts:
            self.prompt_list = self.resource_manager.list(prompts.read().split("\n"))
        if not os.path.exists(self.lookup_path):
            with open(self.lookup_path, mode='w', encoding='utf8') as lookup_file:
                lookup_file.write("")
        else:
            for file in os.listdir("Corpora/{}".format(corpus_name)):
                if file.endswith(".wav"):
                    self.prompt_list.pop(0)
                    self.index.append("")
        self.update_datapoint(self.prompt_list[0])

    def update_datapoint(self, sentence):
        """
        Load new datapoint for display and use
        """
        self.datapoint[0] = sentence
        self.datapoint[1] = phonemize(sentence)

    def update_lookup(self):
        """
        Call this when the datapoint is recorded and saved. Load new Datapoint AFTER this has completed
        """
        with open(self.lookup_path, mode='r', encoding='utf8') as lookup_file:
            current_file = lookup_file.read()
        new_file = current_file + "\n" + "{}|{}|{}".format("{}.wav".format(len(self.index)), self.datapoint[1], self.datapoint[0])
        with open(self.lookup_path, mode='w', encoding='utf8') as lookup_file:
            lookup_file.write(new_file)
            if len(self.prompt_list) > 1:
                self.prompt_list.pop(0)
            else:
                self.stop_flag = True
            self.index.append("")

    def run(self):
        """
        TKinter really wants to stay in the main-thread, so this just starts the key-listener and recording process and then keeps updating the window.
        """
        listener = keyboard.Listener(on_press=self.handle_key_down, on_release=self.handle_key_up)
        listener.start()

        Process(target=self.recorder, daemon=True).start()  # TODO FIXME this causes a crash

        sg.theme('DarkGreen2')
        layout = [[sg.Text("", font="Any 20", size=(2000, 1), pad=((0, 0), (350, 20)), justification='center', key="sentence"), ],
                  [sg.Text("", font="Any 18", size=(2000, 1), pad=(0, 0), justification='center', key="phonemes"), ],
                  [sg.Text("Left CTRL-Key for push-to-talk, ESC-Key to exit", font="Any 10", size=(2000, 1), pad=((0, 0), (300, 0)),
                           justification='center', ), ]]
        window = sg.Window(self.corpus_name, layout)
        window.read(5)
        window.bring_to_front()
        window.maximize()

        while True:
            event, values = window.read(200)
            if event == sg.WIN_CLOSED or self.stop_flag:
                break
            window["sentence"].update(self.datapoint[0])
            window["phonemes"].update(self.datapoint[1])
        self.stop_recorder_process_flag.append("")
        listener.stop()
        window.close()
        self.pyaudio.terminate()

    def handle_key_down(self, key):
        if key == keyboard.Key.ctrl_l:
            self.record_flag.append("")
        elif key == keyboard.Key.esc:
            self.stop_flag = True

    def handle_key_up(self, key):
        if key == keyboard.Key.ctrl_l:
            self.record_flag.clear()
            self.update_lookup()
            self.update_datapoint(self.prompt_list[0])

    def recorder(self):
        while True:
            if len(self.stop_recorder_process_flag) != 0:
                break
            elif len(self.record_flag) != 0:
                stream = self.pyaudio.open(format=pyaudio.paInt16,
                                           channels=1,
                                           rate=parameters.sampling_rate,
                                           input=True,
                                           frames_per_buffer=1024)
                frames = list()
                while len(self.record_flag) != 0:
                    frames.append(stream.read(1024))
                stream.stop_stream()
                stream.close()
                audio = self.apply_signal_processing(frames)
                sf.write(file=self.audio_save_dir + "{}.wav".format(len(self.index) + 1), data=audio, samplerate=parameters.sampling_rate)
            else:
                time.sleep(0.01)

    def normalize_loudness(self, audio):
        loudness = self.meter.integrated_loudness(audio)
        loud_normed = pyloudnorm.normalize.loudness(audio, loudness, -30.0)
        peak = numpy.amax(numpy.abs(loud_normed))
        peak_normed = numpy.divide(loud_normed, peak)
        return peak_normed

    def cut_silence_from_begin_and_end(self, audio):
        silence = torch.zeros([10000])
        no_silence_front = self.vad(torch.cat((silence, torch.Tensor(audio), silence), 0))
        reversed_audio = torch.flip(no_silence_front, (0,))
        no_silence_back = self.vad(torch.Tensor(reversed_audio))
        unreversed_audio = torch.flip(no_silence_back, (0,))
        return unreversed_audio.detach().numpy()

    def apply_signal_processing(self, audio):
        audio = self.normalize_loudness(audio)
        return self.cut_silence_from_begin_and_end(audio)


def phonemize(text):
    phones = phonemizer.phonemize(text,
                                  language_switch='remove-flags',
                                  backend="espeak",
                                  language=parameters.phonemizer_language,
                                  preserve_punctuation=True,
                                  strip=True,
                                  punctuation_marks=';:,.!?¡¿—…"«»“”~/',
                                  with_stress=True).replace(";", ",").replace("/", " ") \
        .replace(":", ",").replace('"', ",").replace("-", ",").replace("-", ",").replace("\n", " ") \
        .replace("\t", " ").replace("¡", "").replace("¿", "").replace(",", "~")
    phones = re.sub("~+", "~", phones)
    return phones
