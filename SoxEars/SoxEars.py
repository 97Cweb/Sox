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
import threading



try:
    from shlex import quote
except ImportError:
    print("bad import of quote")



class SoxEars():
    def __init__(self):
        #Global Vars
        self.RATE = 16000
        self.FRAMES_PER_BUFFER = 1024
        self.VOICE_IN_FILE = "voiceIn.wav"

        self.nonTalkingTimeElapsed = 0
        self.maxBufferSize = int(2 * self.RATE * 1.0) #float in seconds to save in prebuffer. 2*RATE due to stereo pickup
        self.preNonTalkingBuffer = np.array([], np.int16)
        self.postNonTalkingBuffer = np.array([], np.int16)

        self.frames = np.array([[], []], np.int16)  # Initialize array to store frames
        self.linearFrames = np.array([], np.int16)

        self.wakeWord = "hey socks".strip()



        torch.set_num_threads(1)

        #configure pyAudio and setup correct mics
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

        self.stream = p.open(format=pyaudio.paFloat32,
                        channels=2,
                        rate=self.RATE,
                        input=True,
                        input_device_index=deviceIndex,
                        frames_per_buffer=1024)

        print("PyAudio configured")

        self.model, utils = torch.hub.load(repo_or_dir='/home/sox/Documents/Models/silero-vad-master',
                                      model='silero_vad',
                                      source='local',
                                      force_reload=True)

        (get_speech_timestamps,
         save_audio,
         read_audio,
         VADIterator,
         collect_chunks) = utils

        print("VAD Loaded")




        print("Functions Defined")


        self.sttModel = Model("/home/sox/.local/share/coqui/models/English STT v1.0.0-huge-vocab/model.tflite")
        self.sttModel.enableExternalScorer(
            "/home/sox/.local/share/coqui/models/English STT v1.0.0-huge-vocab/huge-vocabulary.scorer")
        self.sttModel.addHotWord("socks", 10)  # no more than +20.0
        self.sttModel.addHotWord("hey", 7)  # no more than +20.0
        self.sttModel.addHotWord("so", -4)  # no more than +20.0
        self.sttModel.addHotWord("he", -4)  # no more than +20.0
        self.sttModel.addHotWord("ho", -4)  # no more than +20.0
        self.sttModel.addHotWord("saw", -4)  # no more than +20.0
        self.sttModel.addHotWord("i", -4)  # no more than +20.0
        self.sttModel.addHotWord("the", -4)  # no more than +20.0
        self.sttModel.addHotWord("thought", -20)  # no more than +20.0
        self.sttModel.addHotWord("though", -20)  # no more than +20.0

        self.desired_sample_rate = self.sttModel.sampleRate()

        print("STT Model setup complete")


        self.awake = False
        self.listening = True
        self.command = ""

    # From https://gist.github.com/HudsonHuang/fbdf8e9af7993fe2a91620d3fb86a182
    def float2pcm(self,sig, dtype='int16'):
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


    def convert_samplerate(self,audio_path, desired_sample_rate):
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


    def processAudio(self):
        # convert sample rate
        fs_new, audio = self.convert_samplerate(self.VOICE_IN_FILE, self.desired_sample_rate)

        print("Running inference.", file=sys.stderr)

        sttOutput = self.sttModel.stt(audio).lower().strip()
        return sttOutput

    def getCommand(self):
        command = self.command
        self.command = ""
        return command

    

    def startListening(self):
        print("ears ready")
        while True:
            data = self.stream.read(self.FRAMES_PER_BUFFER, exception_on_overflow=False)
            decodedFloat = np.frombuffer(data, np.float32)
            decodedInt = self.float2pcm(decodedFloat, 'int16')

            decodedFloatSplit = np.stack((decodedFloat[::2], decodedFloat[1::2]), axis=0)  # channels on separate axes

            tensor = torch.from_numpy(decodedFloatSplit[0])

            speech_prob = self.model(tensor, 16000).item()

            if speech_prob > 0.05:
                nonTalkingTimeElapsed = 0
                self.linearFrames = np.append(self.linearFrames, decodedInt)
                #print(len(linearFrames))
            else:
                #create prepend audio array
                self.preNonTalkingBuffer = np.append(self.preNonTalkingBuffer, decodedInt)

                if len(self.preNonTalkingBuffer) > self.maxBufferSize:
                    self.preNonTalkingBuffer = self.preNonTalkingBuffer[-self.maxBufferSize:]

                self.nonTalkingTimeElapsed += (self.FRAMES_PER_BUFFER / self.RATE)

                #record 1 second of silence
                if self.nonTalkingTimeElapsed <= 1.0:
                    self.postNonTalkingBuffer = np.append(self.postNonTalkingBuffer, decodedInt)

                #after 1 second of silence, convert array to audio
                else:
                    # convert to wav
                    if len(self.linearFrames) > 0:
                        lenLinearFrames = len(self.linearFrames)

                        self.linearFrames = np.append(self.linearFrames, self.postNonTalkingBuffer)
                        self.linearFrames = np.append(self.preNonTalkingBuffer, self.linearFrames)
                        self.postNonTalkingBuffer = []
                        self.preNonTalkingBuffer = []
                        self.linearFrames = self.linearFrames.astype(np.int16)

                        fullDecodedSplit = np.stack((self.linearFrames[::2], self.linearFrames[1::2]),
                                                    axis=0)  # channels on separate axes
                        fullDecodedSplitTransposed = fullDecodedSplit.T
                        wf.write('voiceIn.wav', 16000, fullDecodedSplitTransposed)

                        frames = np.array([[], []])  # wipe out frames so audio is clear for next time
                        self.linearFrames = np.array([])

                        commandStated = ""
                        if not self.awake:
                            print(lenLinearFrames)
                            if lenLinearFrames < 50000:
                                commandStated = self.processAudio()
                                print(commandStated)
                                print("DONE short!")
                            else:
                                print("Too Long")

                        else:
                            print("here")
                            commandStated = self.processAudio()
                            print(commandStated)
                            self.command = commandStated
                            self.awake = False


                        if commandStated == self.wakeWord:
                            print("Yes?")
                            self.awake = True
                            '''
                            
                            speaker = authenticateVoice()
                            if speaker not None:
                                print("Yes" + speaker)
                        '''

        stream.close()
        p.terminate()

    def startThreadedListening(self):
        threadedListening = threading.Thread(target = self.startListening,daemon = True)
        threadedListening.start()

if __name__ == '__main__':
    soxEars  = SoxEars()
    soxEars.startThreadedListening()
    while True:
        cmd = soxEars.getCommand()
        if cmd != "":
            print(cmd)
        
