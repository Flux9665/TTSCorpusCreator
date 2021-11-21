### TTS Corpus Creator

A tool that makes creating text-to-speech corpora fairly easy. It was developed and tested under Windows, I heard that
the GUI backend might be a little more difficult to install on other systems.

---

To start a new corpus, create a directory inside the *Corpora* directory and give it the name you desire. In this
directory, create a file called *prompts.txt*, which should contain one utterance per line.

When you run *create_corpus.py*, you will be asked to enter the name of the corpus you want to record and
hit **[ENTER]**. If you started on it in a prior session, it will load and continue where you left off. If you start it
for the first time, it will create the file that maps prompts to audios and begin with the first prompt. A window will
open up, which is controlled by keybinds only.

The window will display a sentence. When you are ready, press and hold **[CTRL]**. While that key is pressed, your
microphone will record. After you release the key, the recording is done, the audio will be saved, and the lookup will
be updated. Then the next datapoint will be loaded. Then you can record again with **[CTRL]**. If you are not happy with
a recording, you can press **[ALT]** to go back to the last prompt and overwrite the last one you recorded. You can go
back multiple steps, but you have to re-record all of the ones you are going back over. When you are done with a
session, press **[ESC]** to exit the program safely.

---

The format of the corpus is close to LJSpeech style, however it assumes the texts are normalized already. Instead of the
unnormalized text column, there is an IPA phonemized column.

The recordings are done in 48kHz, since they can always be downsampled afterwards, and that should be enough for TTS.
For prosodically standard speech, even 16kHz is enough in my opinion. You can do super-resolution with a vocoder.

To change sampling rate or phonemizer language, take a look at the parameters.py file.

A bit of signal processing is applied to get a uniform loudness and silences are automatically removed from beginning
and end. Depending on your microphone, you might want to tweak some settings in the code. Just record a few samples and
see if they are fine before committing to something big.