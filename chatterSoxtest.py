import time

from utils.ChatterSox import ChatterSox
from utils.HardwareUtils import Hardware

if __name__ == "__main__":
    hardware = Hardware()
    #create chatterSox instance
    #pass in path of wav file to play
    chatterSox = ChatterSox(hardware.servo3)
    
    chatterSox.talk("output.wav")

    time.sleep(1)
    chatterSox.play("0.wav")
