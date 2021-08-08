import os
import re
from multiprocessing import Manager

import PySimpleGUI as sg
import phonemizer

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

    def update_lookup(self, datapoint):
        """
        Call this when the datapoint is recorded and saved. Load new Datapoint AFTER this has completed
        """
        with open(self.lookup_path, mode='r', encoding='utf8') as lookup_file:
            current_file = lookup_file.read()
        new_file = current_file + "\n" + "{}|{}|{}".format("{}.wav".format(len(self.index)), datapoint[0], datapoint[1])
        with open(self.lookup_path, mode='w', encoding='utf8') as lookup_file:
            lookup_file.write(new_file)
            if len(self.prompt_list) > 1:
                self.prompt_list.pop(0)
            else:
                import sys
                sys.exit()
            self.index.append("")

    def run(self):
        """
        TKinter really wants to stay in the main-thread, so this just starts the key-listener and then keeps updating the window.
        """
        # TODO start key listener here

        sg.theme('DarkGreen2')
        layout = [[sg.Text("", font="Any 20", size=(2000, 1), pad=((0, 0), (350, 20)), justification='center', key="sentence"), ],
                  [sg.Text("", font="Any 18", size=(2000, 1), pad=(0, 0), justification='center', key="phonemes"), ]]
        window = sg.Window(self.corpus_name, layout)
        window.read(5)
        window.bring_to_front()
        window.maximize()

        while True:
            event, values = window.read(200)
            window.force_focus()
            if event == sg.WIN_CLOSED:
                break
            window["sentence"].update(self.datapoint[0])
            window["phonemes"].update(self.datapoint[1])

        window.close()

    def handle_ctrl(self):
        # while key down: record.
        # After key no longer down, save audio as file named len(index)+1.wav.
        # Then call update_lookup
        # then call update datapoint and pass self.prompt_list[0]
        pass


def cut_silence_from_begin_and_end():
    pass
