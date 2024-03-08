from BrainTrainer.SoxBrain import SoxBrain
from SoxVoice.SoxVoice import SoxVoice
from SoxEars.SoxEars import SoxEars
from utils.SoftwareUtils import *
from utils.HardwareUtils import Hardware
from utils.ChatterSox import ChatterSox


soxEars = SoxEars()

hardware = Hardware()
soxVoice = SoxVoice()

soxBrain = SoxBrain("Sox", filePath = "BrainTrainer/")
intents = soxBrain.getIntents()
chatterSox = ChatterSox(hardware.servo0, hardware.speakerMute)






def askSox(sentence):
    
    
    intent, suggestedResponse = soxBrain.ask(sentence)
    if intent == 'internet':
        print(onInternet())
    elif intent == 'wikipedia':
        if not onInternet():
            print("Sorry, I cannot reach the internet. Perhaps you can help?")
            return
        getWiki(sentence, intents)
        
    elif intent == "laserOn":
        hardware.laser(True)
    elif intent == "laserOff":
        hardware.laser(False)
    elif intent == "flashlightOn":
        hardware.flashlight(True)
    elif intent == "flashlightOff":
        hardware.flashlight(False)
    elif intent == 'homeAssistant':
        sendToHA(sentence)
    else:
        print (intent, suggestedResponse)

#soxVoice.createLine("hello. I am Sox. Your Personal Companion Robot.")
#chatterSox.play("output.wav")


if __name__ == '__main__':
    soxEars.startThreadedListening()
    while True:
        cmd = soxEars.getCommand()
        if cmd != "":
            print(cmd)
        
        sentence = input("You: ")
        if sentence == "quit":
            break
        askSox(sentence)
