from openwakeword.model import Model as wakeModel
from scipy.io import wavfile

wakeword_model =  wakeModel(
            wakeword_models=["/home/sox/Documents/Sox/.models/WakeWord/Hey_Socks.tflite"],
            )
samplerate, audio = wavfile.read('downsampled.wav')
print(audio)
predictions = wakeword_model.predict_clip(audio, padding = 0)
print(predictions)