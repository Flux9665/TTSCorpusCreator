import os
import re
from multiprocessing import Manager

import PySimpleGUI as sg
import phonemizer
from pynput import keyboard

import parameters


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


class CorpusCreator:

    def __init__(self, corpus_name):
        """
        Load prompt list and prepare status quo
        """
        self.corpus_name = corpus_name
        self.resource_manager = Manager()
        self.datapoint = self.resource_manager.list()
        self.datapoint.append("")
        self.datapoint.append("")
        self.stop_flag = False
        self.index = self.resource_manager.list()
        self.audio_datapoint = self.resource_manager.list()
        self.lookup_path = "Corpora/{}/metadata.csv".format(corpus_name)
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
        TKinter really wants to stay in the main-thread, so this just starts the key-listener and then keeps updating the window.
        """
        listener = keyboard.Listener(on_press=self.handle_key)
        listener.start()

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
        listener.stop()
        window.close()

    def handle_key(self, key):
        # while key down: record.
        # After key no longer down, save audio as file named len(index)+1.wav.
        # Then call update_lookup
        # then call update datapoint and pass self.prompt_list[0]
        if key == keyboard.Key.ctrl_l:
            self.update_lookup()
            self.update_datapoint(self.prompt_list[0])
        elif key == keyboard.Key.esc:
            self.stop_flag = True


def cut_silence_from_begin_and_end():
    # normalize amplitude
    # add silence to beginning
    # add silence to end
    # apply vad
    pass
