# TTS_Corpus_Creator
A tool that makes creating text-to-speech corpora really easy.


corpus.txt should contain the utterances you want to record, one utterance per line

When you run create_corpus.py, a window will open up, which is controlled by keybinds only. 

Enter the name that you give to your corpus. If the corpus already exists, it will load it and continue where you left off. If it does not exist, it will create one. 

Then it will display a sentence. When you are ready, press and hold /CTRL/. While that key is pressed, your microphone will record. After you release the key, the recording is done, and the wave will be displayed. If you are satisfied with the wave (especially with the silence in the beginning and end, which should be as close to none as you can get), you can hit /SPACE/, in order to save it to the corpus and advance to the next sentence. If you're not happy, hit /BACKSPACE/ to discard the recording. Then you can record again with /CTRL/. When you are done with a session, press /ESC/ to exit the program safely.