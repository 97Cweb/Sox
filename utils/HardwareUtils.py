#NOTE: ALL FUNCTIONS CAN BE BYPASSED
#Just call the object directly

import sys
import signal

import board

import digitalio
import time


#for gyro
import adafruit_mpu6050

#for touch
import adafruit_mpr121

#for voltage reading
import adafruit_ina260

#for servoDriver
from adafruit_pca9685 import PCA9685
from adafruit_motor import servo, stepper

#for stepperDriver
from adafruit_motorkit import MotorKit

#for i2c IO
from adafruit_mcp230xx.mcp23017 import MCP23017

#for speaker/mouth
import pyaudio
import wave
import numpy as np




class Hardware:

     def __init__(self):
         
          #setup all IO ports
          self.ledRed = digitalio.DigitalInOut(board.D11)
          self.ledGreen = digitalio.DigitalInOut(board.D9)
          self.ledBlue = digitalio.DigitalInOut(board.D10)

          self.ledEars = digitalio.DigitalInOut(board.D22)
          self.ledLaser = digitalio.DigitalInOut(board.D27)

         

          #set port direction as output
          self.ledRed.direction = digitalio.Direction.OUTPUT
          self.ledGreen.direction = digitalio.Direction.OUTPUT
          self.ledBlue.direction = digitalio.Direction.OUTPUT

          self.ledEars.direction = digitalio.Direction.OUTPUT
          self.ledLaser.direction = digitalio.Direction.OUTPUT

          
          #i2c setup
          i2c = board.I2C()  # uses board.SCL and board.SDA
          
          #voltage 
          self.power = adafruit_ina260.INA260(i2c, 0x41)
          
          #gyro
          self.gyro = adafruit_mpu6050.MPU6050(i2c, 0x69)
          #touch
          self.touch = adafruit_mpr121.MPR121(i2c, address= 0x5A)
          
          
          #servoDriver
          pca = PCA9685(i2c, address = 0x40)
          pca.frequency = 50
          
          #stepperDriver
          self.kit = MotorKit(address = 0x60)
          self.mcp = MCP23017(i2c, address=0x20)
          
          self.neckSensor = self.mcp.get_pin(0)
          
          
          self.servo0 = servo.Servo(pca.channels[0])
          self.servo0.set_pulse_width_range(500, 2500)
          self.servo1 = servo.Servo(pca.channels[1])
          self.servo1.set_pulse_width_range(500, 2500)
          self.servo2 = servo.Servo(pca.channels[2])
          self.servo2.set_pulse_width_range(500, 2500)
          self.servo3 = servo.Servo(pca.channels[3])
          self.servo3.set_pulse_width_range(500, 2000)
          self.servo4 = servo.Servo(pca.channels[4])
          self.servo4.set_pulse_width_range(500, 2500)
          self.servo5 = servo.Servo(pca.channels[5])
          self.servo5.set_pulse_width_range(500, 2500)
          self.servo6 = servo.Servo(pca.channels[6])
          self.servo6.set_pulse_width_range(500, 2500)
          self.servo7 = servo.Servo(pca.channels[7])
          self.servo7.set_pulse_width_range(500, 2500)
          self.servo8 = servo.Servo(pca.channels[8])
          self.servo8.set_pulse_width_range(500, 2500)
          self.servo9 = servo.Servo(pca.channels[9])
          self.servo9.set_pulse_width_range(500, 2500)
          self.servo10 = servo.Servo(pca.channels[10])
          self.servo10.set_pulse_width_range(500, 2500)
          
          self.neck = self.Neck(self.kit.stepper1, self.neckSensor)
          self.neck.home()
          
          self.eyelids = self.Eyelids(self.servo1, self.servo2)
          self.eyelids.awake()
          
          self.mouth = self.Chatter(self.servo0)
          self.mouth.talk("test.wav")


     class Neck:
         
        FORWARD = 2
        REVERSE = 1
        
        def __init__(self,stepper, sensor):
            
            self.sensor = sensor
            self.sensor.direction = digitalio.Direction.INPUT
            self.stepper = stepper
         
        def hard_step(self, direction = FORWARD):
             self.stepper.onestep(direction = direction, style= stepper.DOUBLE)
        def soft_step(self, direction = FORWARD):
            self.stepper.onestep(direction=direction, style = stepper.SINGLE)
            
        def release(self):
            self.stepper.release()
            
        def home(self):
            while not self.sensor.value:
                self.hard_step()
            self.soft_step(direction= self.REVERSE)
        
        


     class Eyelids:
         def __init__(self, upperServo, lowerServo):
             self.upperServo = upperServo
             self.lowerServo = lowerServo
             
         def blink(self):
             self.close()
             time.sleep(0.1)
             self.awake()
         def sleep(self):
             self.upperServo.angle = 180-10
             self.lowerServo.angle = 180-15
         def awake(self):
             self.upperServo.angle = 180-30
             self.lowerServo.angle = 180
         def close(self):
             self.upperServo.angle = 180
             self.lowerServo.angle = 180
             
     class Chatter:
        
        def __init__(self, mouthServo):
            self.restPos = 10 #degrees mouth closed position
            self.servo = mouthServo
            self.p = pyaudio.PyAudio()

            print("ChatterSox started")



        
        
        def talk(self, path):
            def setJaw(in_data, frame_count, time_info, status):
                data = waveFile.readframes(frame_count)
                channels = waveFile.getnchannels()
                volume = getTarget(data, channels) #volume is max 1
                offsetAngle = volume*10 #degrees
                
                self.servo.angle = self.restPos-offsetAngle
                return (data, pyaudio.paContinue)
            
            def getTarget(data, channels):
                levels = abs(np.frombuffer(data,dtype='<i2'))
                volume = get_avg(levels, channels)
                return volume

            def get_avg(levels, channels):
                if len(levels) == 0:
                    return 0
                avgVol = np.sum(levels)//len(levels)
                return avgVol/10000 #10000 is max in ChatterPi

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
            self.servo.angle = self.restPos



        def play(self,path):
            def callback(in_data, frame_count, time_info, status):
                data = waveFile.readframes(frame_count)
                return (data, pyaudio.paContinue)


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
            self.servo.angle = self.restPos
             



     def laser(self, status):
         self.ledLaser.value = status
         return True

     def flashlight(self, status):
         self.ledRed.value = status
         self.ledGreen.value = status
         self.ledBlue.value = status
         return True

     def ears(self, status):
         self.ledEars.value = status
         return True


     def readPower(self):
        print("Current:", self.power.current)
        print("Voltage:", self.power.voltage)
        print("Power:", self.power.power)

     def readGyro(self):
         print("Acceleration: X:%.2f, Y: %.2f, Z: %.2f m/s^2" % (self.gyro.acceleration))
         print("Gyro X:%.2f, Y: %.2f, Z: %.2f rad/s" % (self.gyro.gyro))
         print("Temperature: %.2f C" % self.gyro.temperature)
         print("")

     def getTouch(self, index):
         return self.touch[index].value

     def getTouchArray(self):
         array = [False]*12
         for i in range(12):
             array[i] = self.touch[i].value
         return array

     def close(self):
         self.__del__()
     def __del__(self):
         print("goodbye")
         self.neck.release()
         self.kit.stepper2.release()
         
         
         if hasattr(self, 'stream') and self.stream.is_active():
             self.stream.stop_stream()
             self.stream.close()
         if hasattr(self, 'p'):
             self.p.terminate()
         #self.picam2.close()


def testing(hardware):
    
    hardware.readPower()
    hardware.readGyro()
    print(hardware.getTouch(0))
    print(hardware.getTouchArray())

    

    
    
    
 
    while True:
        hardware.kit.stepper2.onestep()
        '''
        hardware.servo3.angle = 0
        time.sleep(1)
        hardware.servo3.angle = 180
        time.sleep(1)
   
        '''   
    '''
    hardware.flashlight(True)
    hardware.laser(True)
    hardware.ears(True)
    '''

        
    """
    while True:
         hardware.flashlight(True)
         hardware.laser(True)
         hardware.ears(True)
         eyelids.awake()
         '''
         hardware.servo4.angle = 0
         hardware.servo5.angle = 0
         hardware.servo6.angle = 0
         hardware.servo7.angle = 0
         hardware.servo8.angle = 0
         hardware.servo9.angle = 0
         hardware.servo10.angle = 0
         '''
         time.sleep(1)
         hardware.flashlight(False)
         hardware.laser(False)
         hardware.ears(False)         
         eyelids.close()
         ''' 
         hardware.servo4.angle = 180
         hardware.servo5.angle = 180
         hardware.servo6.angle = 180
         hardware.servo7.angle = 180
         hardware.servo8.angle = 180
         hardware.servo9.angle = 180
         hardware.servo10.angle = 180
         '''
         time.sleep(1)
         """


if __name__ == '__main__':
    
    hardware=Hardware()

    def signal_handler(sig, frame):
        print('You pressed Ctrl+C!')
        hardware.close()
        sys.exit(0)  

    
    signal.signal(signal.SIGINT, signal_handler)
    testing(hardware)
    
    signal.pause()
     