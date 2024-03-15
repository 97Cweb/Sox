from .python_run.piper import Piper
from functools import partial
from pathlib import Path
from nltk.tokenize import sent_tokenize
from pydub import AudioSegment

class SoxVoice:
    def __init__(self):
        soxVoicePath = "Voice/voice-sox/sox.onnx"
        voice = Piper(soxVoicePath)

        self.synthesize = partial(
            voice.synthesize,
            length_scale=1,
            noise_scale=0.667,
            noise_w=0.8,
        )

    def createLine(self,text):

        total=AudioSegment.silent(duration=1)
        sentences = sent_tokenize(text)
        for i in range(len(sentences)):
            print(sentences[i])
            wav_bytes = self.synthesize(sentences[i])
            tempPath = Path("temp.wav")
            tempPath.write_bytes(wav_bytes)
            
            wav = AudioSegment.from_wav("temp.wav")
            total += wav
            #if i < len(sentences)-1:
                #append silence
            total += AudioSegment.silent(duration=250)
                
                

        total.export("output.wav", format="wav")

