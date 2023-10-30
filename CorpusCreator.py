import os
import time

import PySimpleGUI as sg
import numpy as np
import pyaudio
import pyloudnorm
import soundfile as sf
import torch
from pynput import keyboard
from torch.multiprocessing import Manager
from torch.multiprocessing import Process
from torchaudio.transforms import Resample

import parameters


class CorpusCreator:

    def __init__(self):
        """
        Load prompt list and prepare status quo
        """
        self.corpus_name = parameters.current_corpus_name
        self.index = Manager().list()
        self.meter = pyloudnorm.Meter(parameters.sampling_rate)
        self.resampler = Resample(orig_freq=parameters.sampling_rate, new_freq=16000)
        self.audio_save_dir = "Corpora/{}/".format(self.corpus_name)
        os.makedirs("Corpora/{}/unprocessed".format(self.corpus_name), exist_ok=True)
        self.record_flag = Manager().list()
        self.stop_recorder_process_flag = Manager().list()
        recorder_process = Process(target=self.recorder)
        recorder_process.start()
        self.stop_flag = False
        self.datapoint = "loading..."
        self.done_ones = list()
        self.lookup_path = f"Corpora/{self.corpus_name}/metadata.csv"
        with open(f"Corpora/{self.corpus_name}/prompts.txt", mode='r', encoding='utf8') as prompts:
            self.prompt_list = Manager().list(prompts.read().split("\n"))
        if not os.path.exists(self.lookup_path):
            with open(self.lookup_path, mode='w', encoding='utf8') as lookup_file:
                lookup_file.write("")
        else:
            for file in os.listdir("Corpora/{}".format(self.corpus_name)):
                if file.endswith(".wav"):
                    self.done_ones.append(self.prompt_list.pop(0))
                    self.index.append("")

        torch.hub._validate_not_a_forked_repo = lambda a, b, c: True  # torch 1.9 has a bug in the hub loading, this is a workaround
        # careful: assumes 16kHz or 8kHz audio
        self.silero_model, utils = torch.hub.load(repo_or_dir='snakers4/silero-vad',
                                                  model='silero_vad',
                                                  force_reload=False,
                                                  onnx=False,
                                                  verbose=False)
        (self.get_speech_timestamps,
         self.save_audio,
         self.read_audio,
         self.VADIterator,
         self.collect_chunks) = utils
        width, height = sg.Window.get_screen_size()
        self.scaling_factor = 1.5 * (height / 1080)  # this was developed on a 1080p display, so all UI elements need to be downscaled for smaller heights
        self.update_datapoint(self.prompt_list[0])

    def update_datapoint(self, sentence):
        """
        Load new datapoint for display and use
        """
        self.datapoint = sentence

    def update_lookup(self):
        """
        Call this when the datapoint is recorded and saved. Load new Datapoint AFTER this has completed
        """
        with open(self.lookup_path, mode='r', encoding='utf8') as lookup_file:
            current_file = lookup_file.read()
        new_file = current_file + "\n" + f"{len(self.index)}.wav|{self.datapoint}"
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
                           pad=((0, 0), (int(self.scaling_factor * 150), 0)),
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
            if not os.path.exists(self.audio_save_dir + f"{len(self.index) - 1}.wav") and os.path.exists(self.audio_save_dir + f"unprocessed/{len(self.index) - 1}.wav"):
                audio, sr = sf.read(self.audio_save_dir + f"unprocessed/{len(self.index) - 1}.wav")
                audio = self.apply_signal_processing(audio)
                sf.write(file=self.audio_save_dir + f"{len(self.index) - 1}.wav", data=audio, samplerate=parameters.sampling_rate)
            if event == sg.WIN_CLOSED or self.stop_flag:
                if os.path.exists(self.audio_save_dir + f"{len(self.index) - 1}.wav"):
                    break
            window["sentence1"].update("")
            window["sentence2"].update("")
            window["sentence3"].update(self.datapoint)
            if len(self.datapoint) > 45:
                prompt_list = self.datapoint[0].split()
                prompt1 = " ".join(prompt_list[:-int(len(prompt_list) / 2)])
                prompt2 = " ".join(prompt_list[-int(len(prompt_list) / 2):])
                window["sentence2"].update(prompt1)
                window["sentence3"].update(prompt2)
            if len(self.datapoint) > 90:
                prompt_list = self.datapoint[0].split()
                prompt1 = " ".join(prompt_list[:-int(len(prompt_list) / 3) * 2])
                prompt2 = " ".join(prompt_list[-int(len(prompt_list) / 3) * 2:-int(len(prompt_list) / 3)])
                prompt3 = " ".join(prompt_list[-int(len(prompt_list) / 3):])
                window["sentence1"].update(prompt1)
                window["sentence2"].update(prompt2)
                window["sentence3"].update(prompt3)
        self.stop_recorder_process_flag.append("")
        listener.stop()
        window.close()
        time.sleep(1)

    def handle_key_down(self, key):
        if key == keyboard.Key.ctrl_l and len(self.record_flag) == 0:
            self.record_flag.append("")
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
        if key == keyboard.Key.ctrl_l:
            while len(self.record_flag) > 0:
                self.record_flag.pop()
            self.update_lookup()
            if len(self.prompt_list) > 0:
                self.update_datapoint(self.prompt_list[0])

    def recorder(self):
        pa = pyaudio.PyAudio()
        while True:
            if len(self.stop_recorder_process_flag) != 0:
                pa.terminate()
                break
            if len(self.record_flag) != 0:
                stream = pa.open(format=pyaudio.paFloat32,
                                 channels=1,
                                 rate=parameters.sampling_rate,
                                 input=True,
                                 output=False,
                                 frames_per_buffer=1024,
                                 input_device_index=1)
                frames = list()
                while len(self.record_flag) != 0:
                    frames.append(np.frombuffer(stream.read(1024), dtype=np.float32))
                stream.stop_stream()
                stream.close()
                audio = np.hstack(frames)
                try:
                    sf.write(file=self.audio_save_dir + "unprocessed/{}.wav".format(len(self.index) - 1), data=audio, samplerate=parameters.sampling_rate)
                except ValueError:
                    print(
                        "Recording was too short! Remember that the recording goes for as long as you keep the CTRL button PRESSED and saves when you RELEASE.")
            else:
                time.sleep(0.01)

    def normalize_loudness(self, audio):
        loudness = self.meter.integrated_loudness(audio)
        loud_normed = pyloudnorm.normalize.loudness(audio, loudness, -30.0)
        peak = np.amax(np.abs(loud_normed))
        peak_normed = np.divide(loud_normed, peak)
        return peak_normed

    def apply_signal_processing(self, audio):
        loud_normed = self.normalize_loudness(audio)
        peak = np.amax(np.abs(loud_normed))
        peak_normed = np.divide(loud_normed, peak)
        with torch.inference_mode():
            resampled_16khz = self.resampler(torch.Tensor(peak_normed))
            speech_timestamps = self.get_speech_timestamps(resampled_16khz, self.silero_model, sampling_rate=16000)
        try:
            result = peak_normed[speech_timestamps[0]['start'] * (parameters.sampling_rate // 16000):speech_timestamps[-1]['end'] * (parameters.sampling_rate // 16000)]
            return result
        except IndexError:
            print("Audio might be too short to cut silences from front and back.")
        return peak_normed


if __name__ == '__main__':
    torch.multiprocessing.set_start_method("spawn", force=True)
    torch.multiprocessing.set_sharing_strategy('file_system')
    CorpusCreator().run()
