import json
import requests
class starwars:
    
    def __init__(self, number):
        self.number = number

    def __repr__(self):
            if self.number == str(1):
                return(str(api()))
            
            elif self.number == str(2):
                return(str(name()))

            elif self.number == str(3):
                return(gender())

            elif self.number == str(4):
                return(str(species()))

            elif self.number == str(5):
                return(skincolor())

            elif self.number == str(6):
                return(str(eyecolor()))

            elif self.number == str(7):
                return (str(datakeys()))

class files:
    def __init__(self, number):
        self.number = number

    def __repr__(self):

        with open ("swfile.txt", "w" ) as file:

            if self.number == str(2):
                file.write(name())
                file.close





def readfile():
    with open ("swfile.txt", "r") as file:
        read = file.read()
        return(read)

def api():
    response = requests.get("https://swapi.py4e.com/api/people/2/")
    forecast = json.loads(response.text)
    return ("the whole enchalada ", forecast)

def getapiinfo(a):
    response = requests.get("https://swapi.py4e.com/api/people/2/")
    forecast = json.loads(response.text)
    return (forecast[a])

def datakeys():
    response = requests.get("https://swapi.py4e.com/api/people/2/")
    forecast = json.loads(response.text)
    return(forecast.keys())



def gender():
        return(getapiinfo('gender'))

def films():
        return(getapiinfo('films'))

def species():
        return(getapiinfo('species'))

def skincolor():
        return(getapiinfo('skin_color'))

def eyecolor():
        return(getapiinfo('eye_color'))

def starships():
        return(getapiinfo('starships'))

def name():
        return(getapiinfo('name'))