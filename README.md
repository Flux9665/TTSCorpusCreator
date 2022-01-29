### TTS Corpus Creator

A tool that makes creating text-to-speech corpora fairly easy. It was developed and tested under Windows, I heard that
the GUI backend might be a little more difficult to install on other systems. There is an example setup that I used 
myself called FluxVoiceGerman. It uses a subset of the prompts of the preview of the second iteration of the 
[Thorsten corpus](https://github.com/thorstenMueller/deep-learning-german-tts).

---

#### Installation

`pip install -r requirements.txt` should suffice. Tested with python 3.8

---

#### Instructions

To start a new corpus, create a directory inside the `Corpora` directory and give it the name you desire. In this
directory, create a file called `prompts.txt`, which should contain one utterance per line. Update
the `current_corpus_name` property of the `parameters.py` file. You should update the other settings as well, while you
are there.

To record a corpus, run `create_corpus.py`. If you started on it in a prior session, it will load and continue where you
left off. If you start it for the first time, it will create the file that maps prompts to audios and begin with the
first prompt. A window will open up, which is controlled by keybinds only.

The window will display a sentence. When you are ready, press and hold **[CTRL]**. While that key is pressed, your
microphone will record. After you release the key, the recording is done, the audio will be saved, and the lookup will
be updated. Then the next datapoint will be loaded. Then you can record again with **[CTRL]**. If you are not happy with
a recording, you can press **[ALT]** to go back to the last prompt and overwrite the last one you recorded. You can go
back multiple steps, but you have to re-record all of the ones you are going back over. When you are done with a
session, press **[ESC]** to exit the program safely.

---

#### Additional Info

The format of the corpus is close to LJSpeech style, however it assumes the texts are normalized already. Instead of the
unnormalized text column, there is an IPA phonemized column.

The recordings are done in 48kHz, since they can always be downsampled afterwards, and that should be enough for TTS.
For prosodically standard speech, even 16kHz is enough in my opinion. You can do super-resolution with a vocoder.

To change sampling rate or phonemizer language, take a look at the `parameters.py` file.

A bit of signal processing is applied to get a uniform loudness and silences are automatically removed from beginning
and end. Depending on your microphone, you might want to tweak some settings in the code. Just record a few samples and
see if they are fine before committing to something big. Unprocessed audio is also saved in the `raw` subfolder that
will be created in the corpus directory when you run it first.

After you are done, you can record some prototypical environment noise (just record for a few seconds without saying 
anything) and place it into the `Corpora` directory named `prototypical_silence.wav`. Then you can run 
`apply_noise_reduction.py` in order to remove the prototypical noise from all recordings in the corpus that is currently 
selected. As always when something is applied to the signal, a backup copy of the original will be created, in case you 
don't like the result and want to go back.

---

#### List to do:
- Figure out available screen resolution and change the size of the text accordingly.
