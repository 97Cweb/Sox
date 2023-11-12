#based heavily off of https://github.com/ViennaMike/ChatterPi
#servo is a servo from adafruit_pca9675's PCA9685 and adafriot_motor's servo
#speakerEnabled is the io port for (un)muting the speaker defined using the library DigitalIO

import wave
import pyaudio
import time
import numpy as np
class ChatterSox:
    def __init__(self, servo, speakerEnabled):
        self.servo = servo
        self.speakerEnabled = speakerEnabled
        self.p = pyaudio.PyAudio()
        self.speakerEnabled.value = False
        print("ChatterSox started")

    def __del__(self):
        self.speakerEnabled.value = True

    
    
    def talk(self, path):
        def setJaw(in_data, frame_count, time_info, status):
            data = waveFile.readframes(frame_count)
            channels = waveFile.getnchannels()
            jawTarget = getTarget(data, channels)
            self.servo.angle = min(jawTarget*90,90)
            return (data, pyaudio.paContinue)
        
        def getTarget(data, channels):
            levels = abs(np.frombuffer(data,dtype='<i2'))
            volume = get_avg(levels, channels)
            return volume

        def get_avg(levels, channels):
            avgVol = np.sum(levels)//len(levels)
            return avgVol/4000 #4000 is max in ChatterPi

        self.speakerEnabled.value = True
        #stream audio file
        waveFile = wave.open(path,'rb')
        fileSampleWidth = waveFile.getsampwidth()
        self.stream = self.p.open(format=self.p.get_format_from_width(fileSampleWidth),
                            channels=waveFile.getnchannels(),
                            rate=waveFile.getframerate(),
                            frames_per_buffer = 1024,
                            output=True,
                            stream_callback=setJaw)
        while self.stream.is_active():
            time.sleep(0.1)
        self.servo.angle = 0

        self.speakerEnabled.value = False

    def play(self,path):
        def callback(in_data, frame_count, time_info, status):
            data = waveFile.readframes(frame_count)
            return (data, pyaudio.paContinue)

        self.speakerEnabled.value = True
        waveFile = wave.open(path,'rb')
        fileSampleWidth = waveFile.getsampwidth()
        self.stream = self.p.open(format=self.p.get_format_from_width(fileSampleWidth),
                            channels=waveFile.getnchannels(),
                            rate=waveFile.getframerate(),
                            frames_per_buffer = 1024,
                            output=True,
                            stream_callback=callback)
        while self.stream.is_active():
            time.sleep(0.1)
        self.servo.angle = 0
        
        self.speakerEnabled.value = False


    

    
