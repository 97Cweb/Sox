import torch
import pyaudio
import numpy as np
import scipy.io.wavfile as wf
from stt import Model, version
import wave
import shlex
import subprocess
import sys
from pydub import AudioSegment, effects



try:
    from shlex import quote
except ImportError:
    print("bad import of quote")

print("Finished imports")



#Global Vars
RATE = 16000
FRAMES_PER_BUFFER = 1024
VOICE_IN_FILE = "voiceIn.wav"

nonTalkingTimeElapsed = 0
maxBufferSize = int(2 * RATE * 1.0) #float in seconds to save in prebuffer. 2*RATE due to stereo pickup
preNonTalkingBuffer = np.array([], np.int16)
postNonTalkingBuffer = np.array([], np.int16)

frames = np.array([[], []], np.int16)  # Initialize array to store frames
linearFrames = np.array([], np.int16)

wakeWord = "hey socks".strip()



torch.set_num_threads(1)

#configure pyAudio and setup correct mics
p = pyaudio.PyAudio()
info = p.get_host_api_info_by_index(0)
numdevices = info.get('deviceCount')

deviceIndex = 0

for i in range(0, numdevices):
    if (p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
        print(p.get_device_info_by_host_api_device_index(0, i).get('name'))
        if p.get_device_info_by_host_api_device_index(0, i).get('name') == "dmic_sv":
            deviceIndex = i
            print("Input Device id ", i, " - ", p.get_device_info_by_host_api_device_index(0, i).get('name'))

stream = p.open(format=pyaudio.paFloat32,
                channels=2,
                rate=RATE,
                input=True,
                input_device_index=deviceIndex,
                frames_per_buffer=1024)

print("PyAudio configured")

model, utils = torch.hub.load(repo_or_dir='/home/sox/Documents/Models/silero-vad-master',
                              model='silero_vad',
                              source='local',
                              force_reload=True)

(get_speech_timestamps,
 save_audio,
 read_audio,
 VADIterator,
 collect_chunks) = utils

print("VAD Loaded")


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


def convert_samplerate(audio_path, desired_sample_rate):
    sox_cmd = "sox {} --type raw --bits 16 --channels 1 --rate {} --encoding signed-integer --endian little --compression 0.0 --no-dither - ".format(
        quote(audio_path), desired_sample_rate
    )
    try:
        output = subprocess.check_output(shlex.split(sox_cmd), stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        raise RuntimeError("SoX returned non-zero status: {}".format(e.stderr))
    except OSError as e:
        raise OSError(
            e.errno,
            "SoX not found, use {}hz files or install it: {}".format(
                desired_sample_rate, e.strerror
            ),
        )

    return desired_sample_rate, np.frombuffer(output, np.int16)


def processAudio():
    # convert sample rate
    fs_new, audio = convert_samplerate(VOICE_IN_FILE, desired_sample_rate)

    print("Running inference.", file=sys.stderr)

    sttOutput = sttModel.stt(audio).lower().strip()
    return sttOutput

print("Functions Defined")


sttModel = Model("/home/sox/.local/share/coqui/models/English STT v1.0.0-huge-vocab/model.tflite")
sttModel.enableExternalScorer(
    "/home/sox/.local/share/coqui/models/English STT v1.0.0-huge-vocab/huge-vocabulary.scorer")
# sttModel.addHotWord("socks", 7)  # no more than +20.0
sttModel.addHotWord("socks", 10)  # no more than +20.0
sttModel.addHotWord("hey", 7)  # no more than +20.0
sttModel.addHotWord("so", -4)  # no more than +20.0
sttModel.addHotWord("he", -4)  # no more than +20.0
sttModel.addHotWord("ho", -4)  # no more than +20.0
sttModel.addHotWord("saw", -4)  # no more than +20.0

desired_sample_rate = sttModel.sampleRate()

print("STT Model setup complete")

awake = False
listening = True
print("ready!")
while True:
    if not listening:
        if not play_obj.is_playing():
            listening = True
            speakerOn.value = False
    else:
        
        data = stream.read(FRAMES_PER_BUFFER, exception_on_overflow=False)
        decodedFloat = np.frombuffer(data, np.float32)
        decodedInt = float2pcm(decodedFloat, 'int16')

        decodedFloatSplit = np.stack((decodedFloat[::2], decodedFloat[1::2]), axis=0)  # channels on separate axes

        tensor = torch.from_numpy(decodedFloatSplit[0])

        speech_prob = model(tensor, 16000).item()

        if speech_prob > 0.05:
            nonTalkingTimeElapsed = 0
            linearFrames = np.append(linearFrames, decodedInt)
            #print(len(linearFrames))
        else:
            #create prepend audio array
            preNonTalkingBuffer = np.append(preNonTalkingBuffer, decodedInt)

            if len(preNonTalkingBuffer) > maxBufferSize:
                preNonTalkingBuffer = preNonTalkingBuffer[-maxBufferSize:]

            nonTalkingTimeElapsed += (FRAMES_PER_BUFFER / RATE)

            #record 1 second of silence
            if nonTalkingTimeElapsed <= 1.0:
                postNonTalkingBuffer = np.append(postNonTalkingBuffer, decodedInt)

            #after 1 second of silence, convert array to audio
            else:
                # convert to wav
                if len(linearFrames) > 0:
                    lenLinearFrames = len(linearFrames)

                    linearFrames = np.append(linearFrames, postNonTalkingBuffer)
                    linearFrames = np.append(preNonTalkingBuffer, linearFrames)
                    postNonTalkingBuffer = []
                    preNonTalkingBuffer = []
                    linearFrames = linearFrames.astype(np.int16)

                    fullDecodedSplit = np.stack((linearFrames[::2], linearFrames[1::2]),
                                                axis=0)  # channels on separate axes
                    fullDecodedSplitTransposed = fullDecodedSplit.T
                    wf.write('voiceIn.wav', 16000, fullDecodedSplitTransposed)

                    frames = np.array([[], []])  # wipe out frames so audio is clear for next time
                    linearFrames = np.array([])

                    commandStated = ""
                    if not awake:
                        print(lenLinearFrames)
                        if lenLinearFrames < 50000:
                            commandStated = processAudio()
                            print(commandStated)
                            print("DONE short!")
                        else:
                            print("Too Long")

                    else:
                        commandStated = processAudio()
                        print(commandStated)

                        wav = synthesizer.tts(commandStated)
                        synthesizer.save_wav(wav,"output.wav")

                        listening = False
                        #play audio
                        speakerOn.value = True
                        wave_obj = sa.WaveObject.from_wave_file("output.wav")
                        play_obj = wave_obj.play()
                        #play_obj.wait_done()
                        print("DONE long!")
                        awake = False


                    if commandStated == wakeWord:
                        print("Yes?")
                        awake = True
                        '''
                        
                        speaker = authenticateVoice()
                        if speaker not None:
                            print("Yes" + speaker)
                    '''

stream.close()
p.terminate()


