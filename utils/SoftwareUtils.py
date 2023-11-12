import socket
import re
import wikipedia
from requests import get
from requests import post
import json

intents = {'intents': [{'tag': 'greeting', 'patterns': ['Hi', 'Hey', 'Hello'], 'responses': ['Hey :-)', 'Hello', 'Hi there']}, {'tag': 'status', 'patterns': ['How are you?', 'Status report', 'Status'], 'responses': ['Checking battery']}, {'tag': 'wikipedia', 'patterns': ['what does  mean?', 'Can you search for', 'What is', 'What is a ', 'Who is ', 'When is', 'Describe for me', 'Describe'], 'responses': ['Looking on Wikipedia', 'Found something']}, {'tag': 'goodbye', 'patterns': ['Bye', 'See you later', 'Goodbye', 'Bye Sox'], 'responses': ['See you later', 'Have a nice day', 'Bye!']}, {'tag': 'thanks', 'patterns': ['Thanks', 'Thank you', "That's helpful", "Thank's a lot!"], 'responses': ['Happy to help!', 'Any time!']}, {'tag': 'alarm', 'patterns': ['Set alarm for eight pm', 'Wake me at five'], 'responses': ['Alarm set']}, {'tag': 'timer', 'patterns': ['Set timer for five minutes', 'Set alarm for five minutes from now', 'Wake me in an hour'], 'responses': ['Timer set']}, {'tag': 'weather', 'patterns': ["What's the weather today?", 'Is it sunny?', 'Is it raining?', 'Is it snowing?', 'What is the weather today'], 'responses': ['According to the window, it is glass']}, {'tag': 'internet', 'patterns': ['Do you have internet connection?', 'Are you connected?', 'Internet status', 'Test connection'], 'responses': ['Searching for the Internet']}, {'tag': 'homeAssistant', 'patterns': ['turn on', 'turn off', 'detected', 'open', 'close', 'set', 'mode'], 'responses': ['Sending to Home Assistant']}, {'tag': 'flashlightOn', 'patterns': ['turn on flashlight'], 'responses': ['Flashlight On']}, {'tag': 'flashlightOff', 'patterns': ['turn off flashlight'], 'responses': ['Flashlight Off']}, {'tag': 'laserOn', 'patterns': ['turn on laser'], 'responses': ['Laser On']}, {'tag': 'laserOff', 'patterns': ['turn off laser'], 'responses': ['Laser Off']}]}
def stripPatterns(sentence, intent, intents):
    intentsArray = intents['intents']
    for i in range(len(intentsArray)):
        if intentsArray[i]['tag'] == intent:
            for pattern in intentsArray[i]['patterns']:
                wordsInPattern = pattern.lower().split(' ')
                for word in wordsInPattern:
                    regular_expression = rf"\b{word}\b"
                    sentence =  re.sub(regular_expression, "", sentence)

    return sentence.strip()

#def createAlarm:

#def deleteAlarm:

#def createTimer:

#def deleteTimer:

def onInternet(host="8.8.8.8",port=53,timeout=3):

    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error as ex:
        print(ex)
        return False



def getWiki(sentence, intents):
    sentence = stripPatterns(sentence, 'wikipedia', intents)
    if sentence != "":
        try:
            print("according to Wikipedia, ", wikipedia.summary(sentence, sentences=1, auto_suggest=False))
        except wikipedia.exceptions.DisambiguationError as e:
            print ("There are several options for that.")
            print (e.options)
        except wikipedia.exceptions.PageError:
            print ("That page does not exist, sorry")

def sendToHA(sentence):
    HAurl ='http://homeassistant.local:8123/api/conversation/process'
    HAToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJjMTcyZWEyYTZjMzI0OGM5OTliNDVmNjg4Yjc5YjE0OSIsImlhdCI6MTY4NTAzNTE0OCwiZXhwIjoyMDAwMzk1MTQ4fQ.7QwnpM1fdB9ftXETRA0XX5wYvNtTKfQneRM8MOfsnAU'
    HAheaders = {
        "Authorization": 'Bearer ' + HAToken,
        "content-type": "application/json",
    }


    #try to send it to home assistant
    HABody = {
        'text': sentence,
        'language':'en'
        }
    response = post(HAurl, headers = HAheaders, json = HABody)
    jstring = response.text
    jsonReturn = json.loads(jstring)
    print("home replied", jsonReturn["response"]["speech"]["plain"]["speech"])

                
if __name__ == '__main__':
    print(getWiki("what is weather", intents))
