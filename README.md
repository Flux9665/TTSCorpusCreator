### TTS Corpus Creator

A tool that makes creating text-to-speech corpora really easy.

---

To start a new corpus, create a directory inside the *Corpora* directory and give it the name you desire. In this
directory, create a file called *prompts.txt*, which should contain one utterance per line.

When you run *create_corpus.py*, you will be asked to enter the name of the corpus you want to record and hit /ENTER/.
If you started on it in a prior session, it will load and continue where you left off. If you start it for the first
time, it will create the file that maps prompts to audios and begin with the first prompt. A window will open up, which
is controlled by keybinds only.

The window will display a sentence. When you are ready, press and hold /CTRL/. While that key is pressed, your
microphone will record. After you release the key, the recording is done, the audio will be saved, and the lookup will
be updated. Then the next datapoint will be loaded. Then you can record again with /CTRL/. When you are done with a
session, press /ESC/ to exit the program safely.

---

The format of the corpus is close to LJSpeech style, however it assumes the texts are normalized already. Instead of the
unnormalized text column, there is an IPA phonemized column.

The recordings are done in 16kHz, to safe space. For prosodically standard speech, 16kHz is enough in my opinion.
Emotional speech etc. requires a higher sampling rate, which can easily be changed.

To change sampling rate or phonemizer language, take a look at the parameters.py file.

A bit of signal processing is applied to get a uniform loudness and silences are automatically removed from beginning
and end. Depending on your microphone, you might want to tweak some settings in the code or remove the call to the
signal processing part entirely and save unedited audio. Just record a few samples and see if they are fine before
committing to something big.