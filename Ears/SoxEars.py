import torch
import pyaudio
import numpy as np
import scipy.io.wavfile as wf

import shlex
import subprocess
import sys
import threading
from faster_whisper import WhisperModel






from openwakeword.model import Model as wakeModel



try:
    from shlex import quote
except ImportError:
    print("bad import of quote")



class SoxEars():
    def __init__(self):
        #Global Vars
        self.RATE = 48000
        self.DESIRED_SAMPLE_RATE = 16000
        self.FRAMES_PER_BUFFER = 4096
        self.VOICE_IN_FILE = "voiceIn.wav"

        self.nonTalkingTimeElapsed = 0
        self.maxBufferSize = int(1 * self.RATE * 3.0) #float in seconds to save in prebuffer. 2*RATE due to stereo pickup
        self.preNonTalkingBuffer = np.array([], np.int16)
        self.postNonTalkingBuffer = np.array([], np.int16)

        self.frames = np.array([[], []], np.int16)  # Initialize array to store frames
        self.linearFrames = np.array([], np.int16)

        self.awake = True
        self.listening = True
        self.command = ""



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
                if "i2s" in p.get_device_info_by_host_api_device_index(0, i).get('name'):
                    deviceIndex = i
                    print("Input Device id ", i, " - ", p.get_device_info_by_host_api_device_index(0, i).get('name'))

          
        self.stream = p.open(format=pyaudio.paFloat32,
                        channels=2,
                        rate=self.RATE,
                        input=True,
                        input_device_index=deviceIndex,
                        frames_per_buffer=self.FRAMES_PER_BUFFER)

        print("PyAudio configured")

        self.vadModel, utils = torch.hub.load(repo_or_dir='/home/sox/Documents/Sox/.models/silero-vad-master',
                                      model='silero_vad',
                                      source='local',
                                      force_reload=True)

        (get_speech_timestamps,
         save_audio,
         read_audio,
         VADIterator,
         collect_chunks) = utils

        print("VAD Loaded")






        self.sttModel = WhisperModel("base.en",device="cpu", cpu_threads = 4, compute_type="float32")
        


        
        print("STT Model setup complete")

        self.wakeword_model =  wakeModel(
            wakeword_models=["/home/sox/Documents/Sox/.models/WakeWord/Hey_Socks.tflite"],
            )

        print("Wakeword Setup complete")
 
        

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


    # DISCLAIMER: This function is copied from https://github.com/nwhitehead/swmixer/blob/master/swmixer.py, 
    #             which was released under LGPL. 
    def resample_by_interpolation(self, signal, input_fs, output_fs):
    
        scale = output_fs / input_fs
        # calculate new length of sample
        n = round(len(signal) * scale)
    
        # use linear interpolation
        # endpoint keyword means than linspace doesn't go all the way to 1.0
        # If it did, there are some off-by-one errors
        # e.g. scale=2.0, [1,2,3] should go to [1,1.5,2,2.5,3,3]
        # but with endpoint=True, we get [1,1.4,1.8,2.2,2.6,3]
        # Both are OK, but since resampling will often involve
        # exact ratios (i.e. for 44100 to 22050 or vice versa)
        # using endpoint=False gets less noise in the resampled sound
        resampled_signal = np.interp(
            np.linspace(0.0, 1.0, n, endpoint=False),  # where to interpret
            np.linspace(0.0, 1.0, len(signal), endpoint=False),  # known positions
            signal,  # known data points
        )
        return resampled_signal

    def processAudio(self):
        # convert sample rate
        fs_new, audio = self.convert_samplerate(self.VOICE_IN_FILE, self.DESIRED_SAMPLE_RATE)

        print("Running inference.", file=sys.stderr)
        
        audio = audio.astype(np.float32)/32768.0 #convert back to float representation

        segments, info = self.sttModel.transcribe(audio)
        
        return list(segments)

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

            
            
            
            #tensor = self.resample_by_interpolation(decodedFloatSplit[0],self.RATE,16000)
            
            tensor = torch.from_numpy(decodedFloatSplit[0][1::3]) #lazy downsample, keep every 3rd piece
            speech_prob = self.vadModel(tensor, 16000).item()
            

            if speech_prob > 0.15:
                self.nonTalkingTimeElapsed = 0
                self.linearFrames = np.append(self.linearFrames, decodedInt)
                #print(len(linearFrames))
            else:
                #create prepend audio array
                self.preNonTalkingBuffer = np.append(self.preNonTalkingBuffer, decodedInt)

                if len(self.preNonTalkingBuffer) > self.maxBufferSize:
                    self.preNonTalkingBuffer = self.preNonTalkingBuffer[-self.maxBufferSize:]

                self.nonTalkingTimeElapsed += (self.FRAMES_PER_BUFFER / self.RATE)

                #record .5 second of silence
                if self.nonTalkingTimeElapsed <= 0.5:
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

                        
                        #4000 for dc offset remove
                        fullDecodedSplit = np.stack((self.linearFrames[::2] + 4000, self.linearFrames[1::2] + 4000),
                                                    axis=0)  # channels on separate axes
                        fullDecodedSplitTransposed = fullDecodedSplit.T

                        
                        
                        wf.write('voiceIn.wav', self.RATE, fullDecodedSplitTransposed)


                        self.frames = np.array([[], []])  # wipe out frames so audio is clear for next time
                        self.linearFrames = np.array([])

                        commandStated = ""
                        if not self.awake:
                            if lenLinearFrames < 500000:
                                self.tryWakeUp()
                                print("DONE short!")
                            else:
                                print("Too Long")

                        else:
                            print("here")
                            commandStated = self.processAudio()
                            self.command = commandStated
                            self.awake = False


                            '''
                            
                            speaker = authenticateVoice()
                            if speaker not None:
                                print("Yes" + speaker)
                        '''

        self.stream.close()
        #p.terminate()

    def tryWakeUp(self):
        fs_new, audio = self.convert_samplerate(self.VOICE_IN_FILE, self.DESIRED_SAMPLE_RATE)

        predictions = self.wakeword_model.predict_clip(audio)
        for prediction in predictions:
            for lbl in prediction.keys():
                print(prediction[lbl])
                if prediction[lbl] > 0.05:
                    print("Awake!")
                    self.awake = True
                    return True
        return False


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
        
