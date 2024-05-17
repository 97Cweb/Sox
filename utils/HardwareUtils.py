#NOTE: ALL FUNCTIONS CAN BE BYPASSED
#Just call the object directly
import atexit
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
         
          atexit.register(self.__del__)
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
         
        def step(self, direction = 1):
             self.stepper.onestep(direction = direction, style= stepper.DOUBLE)
            
        def release(self):
            self.stepper.release()
            
        def home(self):
            while not self.sensor.value:
                self.step()
        


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


     def __del__(self):
         self.neck.release()
         self.picam2.close()



if __name__ == '__main__':
    
     time.sleep(10)
     hardware=Hardware()
     hardware.readPower()
     hardware.readGyro()
     print(hardware.getTouch(0))
     print(hardware.getTouchArray())

     

     
     
     
     ''' 
     for i in range(100):
         neck.step()
         time.sleep(0.01)
         
     for i in range(100):
        neck.step(neck.REVERSE)
        time.sleep(0.01)
    
     neck.release()
     '''
     
     
     time.sleep(1)
     
     '''
     while True:
         
         print()
         #time.sleep(0.02)
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
          '''
          hardware.servo0.angle = 0
          hardware.servo1.angle = 0
          hardware.servo2.angle = 0
          '''

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
          '''
          hardware.servo0.angle = 180
          hardware.servo1.angle = 180
          hardware.servo2.angle = 180
          ''' 
         
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