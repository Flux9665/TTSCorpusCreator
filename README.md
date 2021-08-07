### TTS Corpus Creator

A tool that makes creating text-to-speech corpora really easy.

---

To start a new corpus, create a directory inside the *Corpora* directory and give it the name you desire. In this
directory, create a file called *prompts.txt*, which should contain one utterance per line.

When you run *create_corpus.py*, a window will open up, which is controlled by keybinds only.

Enter the name of the corpus you want to record and hit /ENTER/. If you started on it in a prior session, it will load
and continue where you left off. If you start it for the first time, it will create the file that maps prompts to audios
and begin with the first prompt.

Then it will display a sentence. When you are ready, press and hold /CTRL/. While that key is pressed, your microphone
will record. After you release the key, the recording is done, and the wave will be displayed. If you are satisfied with
the wave (especially with the silence in the beginning and end, which should be as close to none as you can get), you
can hit /SPACE/, in order to save it to the corpus and advance to the next sentence. If you're not happy, hit
/BACKSPACE/ to discard the recording. Then you can record again with /CTRL/. When you are done with a session, press
/ESC/ to exit the program safely.

---

The format of the corpus is close to LJSpeech style, however it assumes the texts are normalized already. Instead of the
unnormalized text column, there is an IPA phonemized column.

The recordings are done in 16kHz, to safe space. For prosodically standard speech, 16kHz is enough in my opinion.
Emotional speech etc. requires a higher sampling rate, which can easily be changed in the code.