import pyaudio
import numpy as np
from openwakeword.model import Model as wakeModel

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 48000
CHUNK = 3072  # Increased buffer size, 3*1024 as wee only keep 1/3 for wakeword detection
audio = pyaudio.PyAudio()

info = audio.get_host_api_info_by_index(0)
numdevices = info.get('deviceCount')

deviceIndex = 0

for i in range(0, numdevices):
    if (audio.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
        print(i, audio.get_device_info_by_host_api_device_index(0, i).get('name'))
        if "i2s" in audio.get_device_info_by_host_api_device_index(0, i).get('name'):
            deviceIndex = i
            print("Input Device id ", i, " - ", audio.get_device_info_by_host_api_device_index(0, i).get('name'))

mic_stream = audio.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        input_device_index=deviceIndex,
                        frames_per_buffer=CHUNK)

wakeword_model = wakeModel(
    wakeword_models=["/home/sox/Documents/Sox/.models/WakeWord/hey_socks.tflite"],
    #enable_speex_noise_suppression=True,
    vad_threshold=0.05
)

if __name__ == "__main__":
    didHearName = False
    try:
        while True:
            try:
                liveAudio = np.frombuffer(mic_stream.read(CHUNK, exception_on_overflow=False), dtype=np.int16)
                downSampledAudio = liveAudio[0::3]
                prediction = wakeword_model.predict(downSampledAudio)
                #print(prediction)
                
                if prediction["hey_socks"] >= 0.3:
                    didHearName = True
                elif didHearName:
                    didHearName=False
                    print("yes?")
                    
                    
                
            except IOError as e:
                print(f"Error reading audio stream: {e}")
    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        mic_stream.stop_stream()
        mic_stream.close()
        audio.terminate()
