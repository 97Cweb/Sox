import pyaudio
import numpy as np
from openwakeword.model import Model as wakeModel

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 1280
audio = pyaudio.PyAudio()

info = audio.get_host_api_info_by_index(0)
numdevices = info.get('deviceCount')

deviceIndex = 0

for i in range(0, numdevices):
    if (audio.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
        print(i,audio.get_device_info_by_host_api_device_index(0, i).get('name'))
        if "i2s" in audio.get_device_info_by_host_api_device_index(0, i).get('name'):
            deviceIndex = i
            print("Input Device id ", i, " - ", audio.get_device_info_by_host_api_device_index(0, i).get('name'))


mic_stream = audio.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        input_device_index=deviceIndex,
                        frames_per_buffer=CHUNK)

wakeword_model =  wakeModel(
            wakeword_models=["/home/sox/Documents/Sox/.models/WakeWord/hey_socks.tflite"],
            )

if __name__ == "__main__":
    while True :
        liveAudio = np.frombuffer(mic_stream.read(CHUNK), dtype=np.int16)
        prediction = wakeword_model.predict(liveAudio)
        print(prediction)
        """
        if prediction["hey_socks"] >=0.5:
            print("yes?")
            """