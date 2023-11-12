from utils.HardwareUtils import Hardware
import time
hardware = Hardware()
while True:
         hardware.servo0.angle = 0
         #hardware.servo1.angle = 0
         #hardware.servo2.angle = 0
         #hardware.servo3.angle = 0
         #hardware.servo4.angle = 0
         #hardware.servo5.angle = 0
         #hardware.servo6.angle = 0
         #hardware.servo7.angle = 0
         #hardware.servo8.angle = 0
         #hardware.servo9.angle = 0
         #hardware.servo10.angle = 0
         time.sleep(0.5)
         hardware.servo0.angle = 180
         #hardware.servo1.angle = 180
         #hardware.servo2.angle = 180
         #hardware.servo3.angle = 180
         #hardware.servo4.angle = 180
         #hardware.servo5.angle = 180
         #hardware.servo6.angle = 180
         #hardware.servo7.angle = 180
         #hardware.servo8.angle = 180
         #hardware.servo9.angle = 180
         #hardware.servo10.angle = 180
         time.sleep(0.5)
