import nltk
nltk.download('punkt')

import openwakeword
from openwakeword.model import Model

# One-time download of all pre-trained models (or only select models)
openwakeword.utils.download_models(["hey_jarvis_v0.1"])

'''
# Instantiate the model(s)
model = Model(
    wakeword_models=["path/to/model.tflite"],  # can also leave this argument empty to load all of the included pre-trained models
)
'''