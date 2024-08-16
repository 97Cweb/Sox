import pyaudio
import numpy as np
from openwakeword.model import Model as wakeModel

FORMAT = pyaudio.paFloat32
CHANNELS = 2
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

# From https://gist.github.com/HudsonHuang/fbdf8e9af7993fe2a91620d3fb86a182
def float2pcm(sig, dtype='int16'):
    """Convert floating point signal with a range from -1 to 1 to PCM.
    Any signal values outside the interval [-1.0, 1.0) are clipped.
    No dithering is used.
    Note that there are different possibilities for scaling floating
    point numbers to PCM numbers, this function implements just one of
    them.  For an overview of alternatives see
    http://blog.bjornroche.com/2009/12/int-float-int-its-jungle-out-there.html
    Parameters
    ----------
    sig : array_like
        Input array, must have floating point type.
    dtype : data type, optional
        Desired (integer) data type.
    Returns
    -------
    numpy.ndarray
        Integer data, scaled and clipped to the range of the given
        *dtype*.
    See Also
    --------
    pcm2float, dtype
    """
    sig = np.asarray(sig)
    if sig.dtype.kind != 'f':
        raise TypeError("'sig' must be a float array")
    dtype = np.dtype(dtype)
    if dtype.kind not in 'iu':
        raise TypeError("'dtype' must be an integer type")

    i = np.iinfo(dtype)
    abs_max = 2 ** (i.bits - 1)
    offset = i.min + abs_max
    return (sig * abs_max + offset).clip(i.min, i.max).astype(dtype)

    
if __name__ == "__main__":
    didHearName = False
    try:
        while True:
            try:
                liveAudio = np.frombuffer(mic_stream.read(CHUNK, exception_on_overflow=False), dtype=np.float32)
                stackedAudio = np.stack((liveAudio[::2], liveAudio[1::2]), axis=0)  # channels on separate axes
                leftTrack = stackedAudio[0]
                downSampledAudio = leftTrack[0::3] #left track only
                pcmDownSampledAudio = float2pcm(downSampledAudio)
                prediction = wakeword_model.predict(pcmDownSampledAudio)
                
                
                if prediction["hey_socks"] >= 0.1:
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
