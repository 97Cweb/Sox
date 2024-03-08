import openwakeword
from openwakeword.model import Model

model = Model(
    wakeword_models=["/home/sox/Documents/Sox/WakeWord/Hey_Socks.tflite"],
    )


prediction = model.predict(frame)
