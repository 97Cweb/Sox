from openwakeword.model import Model as wakeModel

wakeword_model =  wakeModel(
            wakeword_models=["/home/sox/Documents/Sox/.models/WakeWord/Hey_Socks.tflite"],
            )

print("Wakeword Setup complete")