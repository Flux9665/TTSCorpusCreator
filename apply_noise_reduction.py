"""
optionally apply noisereduction after you are done recording a corpus.

You have to record a bit (>5s) of prototypical noise/silence in your recording
setup and place it in the Corpus directory named "prototypical_silence.wav".
Then you can call this script and spectral gating will be applied to all of your
recordings with the prototypical noise. The recordings will not be overwritten,
but instead moved to a new subdirectory, similar to the unprocessed recordings.
"""

import os
import shutil

import noisereduce
import soundfile as sf

import parameters

silence, sr = sf.read("Corpora/prototypical_silence.wav")

current_corpus = parameters.current_corpus_name

os.makedirs(f"Corpora/{current_corpus}/pre_noisereduce")

for audio in os.listdir(f"Corpora/{current_corpus}"):
    if ".wav" in audio:
        sample, sr = sf.read(f"Corpora/{current_corpus}/{audio}")
        shutil.move(f"Corpora/{current_corpus}/{audio}", f"Corpora/{current_corpus}/pre_noisereduce/{audio}")
        nr_sample = noisereduce.reduce_noise(y=sample, sr=sr, y_noise=silence, stationary=True)
        sf.write(f"Corpora/{current_corpus}/{audio}", nr_sample, sr)
