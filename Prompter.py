import os
import re
import time
from multiprocessing import Manager

import PySimpleGUI as sg
import phonemizer
from pynput import keyboard

import parameters


class Prompter:

    def __init__(self):
        """
        Load prompt list and prepare status quo
        """
        self.corpus_name = parameters.current_corpus_name
        self.index = Manager().list()
        self.stop_flag = False
        self.datapoint = Manager().list()
        self.datapoint.append("")
        self.datapoint.append("")
        self.done_ones = list()
        self.lookup_path = "Corpora/{}/metadata.csv".format(self.corpus_name)
        with open("Corpora/{}/prompts.txt".format(self.corpus_name), mode='r', encoding='utf8') as prompts:
            self.prompt_list = Manager().list(prompts.read().split("\n"))
        if not os.path.exists(self.lookup_path):
            with open(self.lookup_path, mode='w', encoding='utf8') as lookup_file:
                lookup_file.write("")
        else:
            with open(self.lookup_path, mode='r', encoding='utf8') as lookup_file:
                lines = lookup_file.read().split("\n")
            for _ in lines:
                self.prompt_list.pop(0)
                self.index.append("")
        self.update_datapoint(self.prompt_list[0])
        width, height = sg.Window.get_screen_size()
        self.scaling_factor = height / 1080  # this was developed on a 1080p display, so all UI elements need to be downscaled for smaller heights

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
            lookup_file.write(new_file.strip("\n"))
            if len(self.prompt_list) > 1:
                self.done_ones.append(self.prompt_list.pop(0))
            else:
                self.stop_flag = True
            self.index.append("")

    def run(self):
        """
        TKinter really wants to stay in the main-thread, so this just starts the key-listener and recording process and then keeps updating the window.
        """
        listener = keyboard.Listener(on_press=self.handle_key_down, on_release=self.handle_key_up)
        listener.start()

        sg.theme('DarkGreen2')
        layout = [[sg.Text("",
                           font=f"Any {int(self.scaling_factor * 20)}",
                           size=(int(self.scaling_factor * 2000), 1),
                           pad=((0, 0), (int(self.scaling_factor * 350), 0)),
                           justification='center',
                           key="sentence1"), ],
                  [sg.Text("", font=f"Any {int(self.scaling_factor * 20)}",
                           size=(int(self.scaling_factor * 2000), 1),
                           pad=(0, 0),
                           justification='center',
                           key="sentence2"), ],
                  [sg.Text("", font=f"Any {int(self.scaling_factor * 20)}",
                           size=(int(self.scaling_factor * 2000), 1),
                           pad=((0, 0), (0, int(self.scaling_factor * 30))),
                           justification='center',
                           key="sentence3"), ],
                  [sg.Text("", font=f"Any {int(self.scaling_factor * 18)}",
                           size=(int(self.scaling_factor * 2000), 1),
                           pad=(0, 0),
                           justification='center',
                           key="phonemes1"), ],
                  [sg.Text("", font=f"Any {int(self.scaling_factor * 18)}",
                           size=(int(self.scaling_factor * 2000), 1),
                           pad=(0, 0),
                           justification='center',
                           key="phonemes2"), ],
                  [sg.Text("", font=f"Any {int(self.scaling_factor * 18)}",
                           size=(int(self.scaling_factor * 2000), 1),
                           pad=(0, 0),
                           justification='center',
                           key="phonemes3"), ],
                  [sg.Text("Left CTRL-Key for push-to-talk, ESC-Key to exit, ALT-Key to redo the last prompt",
                           font=f"Any {int(self.scaling_factor * 10)}",
                           size=(int(self.scaling_factor * 2000), 1),
                           pad=((0, 0), (int(self.scaling_factor * 300), 0)),
                           justification='center', ), ]]
        window = sg.Window(self.corpus_name, layout)
        window.read(5)
        window.bring_to_front()
        window.maximize()

        while True:
            event, values = window.read(200)
            if event == sg.WIN_CLOSED or self.stop_flag:
                break
            window["sentence1"].update("")
            window["sentence2"].update("")
            window["phonemes2"].update("")
            window["phonemes3"].update("")
            window["sentence3"].update(self.datapoint[0])
            window["phonemes1"].update(self.datapoint[1])
            if len(self.datapoint[0]) > 45:
                prompt_list = self.datapoint[0].split()
                promt1 = " ".join(prompt_list[:-int(len(prompt_list) / 2)])
                promt2 = " ".join(prompt_list[-int(len(prompt_list) / 2):])
                window["sentence2"].update(promt1)
                window["sentence3"].update(promt2)
            if len(self.datapoint[1]) > 45:
                phoneme_list = self.datapoint[1].split()
                phonemes1 = " ".join(phoneme_list[:-int(len(phoneme_list) / 2)])
                phonemes2 = " ".join(phoneme_list[-int(len(phoneme_list) / 2):])
                window["phonemes1"].update(phonemes1)
                window["phonemes2"].update(phonemes2)
            if len(self.datapoint[0]) > 90:
                prompt_list = self.datapoint[0].split()
                promt1 = " ".join(prompt_list[:-int(len(prompt_list) / 3) * 2])
                promt2 = " ".join(prompt_list[-int(len(prompt_list) / 3) * 2:-int(len(prompt_list) / 3)])
                promt3 = " ".join(prompt_list[-int(len(prompt_list) / 3):])
                window["sentence1"].update(promt1)
                window["sentence2"].update(promt2)
                window["sentence3"].update(promt3)
            if len(self.datapoint[1]) > 90:
                phoneme_list = self.datapoint[1].split()
                phonemes1 = " ".join(phoneme_list[:-int(len(phoneme_list) / 3) * 2])
                phonemes2 = " ".join(phoneme_list[-int(len(phoneme_list) / 3) * 2:-int(len(phoneme_list) / 3)])
                phonemes3 = " ".join(phoneme_list[-int(len(phoneme_list) / 3):])
                window["phonemes1"].update(phonemes1)
                window["phonemes2"].update(phonemes2)
                window["phonemes3"].update(phonemes3)
        listener.stop()
        window.close()
        time.sleep(1)

    def handle_key_down(self, key):
        if key == keyboard.Key.ctrl_l:
            self.update_lookup()
            if len(self.prompt_list) > 0:
                self.update_datapoint(self.prompt_list[0])
        elif key == keyboard.Key.esc:
            self.stop_flag = True
        elif key == keyboard.Key.alt or key == keyboard.Key.alt_l:
            self.go_back()

    def go_back(self):
        """
        go back to the previous sentence and re-record it
        """
        if len(self.done_ones) > 0:
            with open(self.lookup_path, mode='r', encoding='utf8') as lookup_file:
                current_file = lookup_file.read()
            new_file = "\n".join(current_file.split("\n")[:-1]).strip("\n")
            with open(self.lookup_path, mode='w', encoding='utf8') as lookup_file:
                lookup_file.write(new_file)
            self.prompt_list.insert(0, self.done_ones.pop())
            self.index.pop()
            self.update_datapoint(self.prompt_list[0])

    def handle_key_up(self, key):
        pass


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
