import io
import numpy as np
import torch
torch.set_num_threads(1)
import torchaudio
import matplotlib
import matplotlib.pylab as plt
torchaudio.set_audio_backend("soundfile")
import pyaudio

import scipy.io.wavfile as wf


RATE = 16000
FRAMES_PER_BUFFER = 1024
filename = "output.wav"
channels = 2
sample_format=pyaudio.paFloat32



model, utils = torch.hub.load(repo_or_dir='snakers4/silero-vad',
                              model='silero_vad',
                              force_reload=True)

(get_speech_timestamps,
 save_audio,
 read_audio,
 VADIterator,
 collect_chunks) = utils

# Taken from utils_vad.py
def validate(model,
             inputs: torch.Tensor):
    with torch.no_grad():
        outs = model(inputs)
    return outs

# Provided by Alexander Veysov
def int2float(sound):
    abs_max = np.abs(sound).max()
    sound = sound.astype('float32')
    if abs_max > 0:
        sound *= 1/32768
    sound = sound.squeeze()  # depends on the use case
    return sound

p = pyaudio.PyAudio()
info = p.get_host_api_info_by_index(0)
numdevices = info.get('deviceCount')

print(numdevices)

deviceIndex = 0

for i in range(0, numdevices):
    if (p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
        print(i,p.get_device_info_by_host_api_device_index(0, i).get('name'))
        if "snd_rpi_i2s_card" in p.get_device_info_by_host_api_device_index(0, i).get('name'):
            deviceIndex = i
            print("Input Device id ", i, " - ", p.get_device_info_by_host_api_device_index(0, i).get('name'))

  
stream = p.open(format=pyaudio.paFloat32,
                channels=2,
                rate=RATE,
                input=True,
                input_device_index=deviceIndex,
                frames_per_buffer=FRAMES_PER_BUFFER)

print("PyAudio configured")


data = np.array([[],[]], np.float32)
voiced_confidences = []

print("Started Recording")
for i in range(0, 60):
    
    audio_chunk = stream.read(FRAMES_PER_BUFFER, exception_on_overflow = False)

    

    # in case you want to save the audio later
    npAudioChunk = np.frombuffer(audio_chunk, dtype=np.float32)
    
    npAudioChunk = np.reshape(npAudioChunk, (FRAMES_PER_BUFFER, 2))
    data = np.append(data,npAudioChunk)
    
    audio_int16 = np.frombuffer(audio_chunk, np.int16);

    audio_float32 = int2float(audio_int16)
    
    # get the confidences and add them to the list to plot them later
    new_confidence = model(torch.from_numpy(audio_float32), 16000).item()
    voiced_confidences.append(new_confidence)
    
print("Stopped the recording")


print(np.max(data))
data = 2.*(data - np.min(data))/np.ptp(data)-1

splitData =  np.stack((data[::2], data[1::2]), axis=0)
splitDataT = splitData.T

wf.write(filename, RATE, splitDataT)


# plot the confidences for the speech

plt.figure(figsize=(20,6))
plt.plot(voiced_confidences)
plt.show()

