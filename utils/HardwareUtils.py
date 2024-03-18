#NOTE: ALL FUNCTIONS CAN BE BYPASSED
#Just call the object directly

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
from adafruit_motor import servo






class Hardware:

     def __init__(self):
          #setup all IO ports
          self.ledRed = digitalio.DigitalInOut(board.D11)
          self.ledGreen = digitalio.DigitalInOut(board.D9)
          self.ledBlue = digitalio.DigitalInOut(board.D10)

          self.ledEars = digitalio.DigitalInOut(board.D22)
          self.ledLaser = digitalio.DigitalInOut(board.D27)

          self.speakerMute = digitalio.DigitalInOut(board.D17)


          #set port direction as output
          self.ledRed.direction = digitalio.Direction.OUTPUT
          self.ledGreen.direction = digitalio.Direction.OUTPUT
          self.ledBlue.direction = digitalio.Direction.OUTPUT

          self.ledEars.direction = digitalio.Direction.OUTPUT
          self.ledLaser.direction = digitalio.Direction.OUTPUT

          self.speakerMute.direction = digitalio.Direction.OUTPUT

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


          


     class eyelids:
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
          self.picam2.close()


if __name__ == '__main__':
     hardware=Hardware()
     hardware.readPower()
     hardware.readGyro()
     print(hardware.getTouch(0))
     print(hardware.getTouchArray())

     eyelids = hardware.eyelids(hardware.servo1, hardware.servo2)
     eyelids.sleep()

     while True:
         hardware.flashlight(True)
         hardware.laser(True)
         hardware.ears(True)
         '''
         hardware.servo0.angle = 0
         hardware.servo1.angle = 0
         hardware.servo2.angle = 0
         ''' 
         #hardware.servo3.angle = 0
         #eyelids.awake()
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
        # hardware.servo3.angle = 90
         #eyelids.close()
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
