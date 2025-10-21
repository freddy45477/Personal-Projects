
import json
import requests

class starwars:

    def __init__(self, number):
            self.number  = number

    def __repr__(self):
        o = "hello " + str(self.number)

        p = "make " + str(self.number)

        return (o + p)

def api():

    response = requests.get("https://swapi.py4e.com/api/people/5/")

    forecast = json.loads(response.text)

    return ("the whole enchalada ", forecast)

def getapiinfo(a):
    response = requests.get("https://swapi.py4e.com/api/people/5/")
    forecast = json.loads(response.text)
    return (forecast[a])

def datakeys():
    response = requests.get("https://swapi.py4e.com/api/people/5/")
    forecast = json.loads(response.text)
    return(forecast.keys())



    def gender():
        return(getapiinfo('gender'))

    def films():
        return(getapiinfo('films'))

    def species():
        return(getapiinfo('species'))

    def vehicles():
        return(getapiinfo('vehicles'))

    def starships():
        return(getapiinfo('starships'))

    def name():
        return(getapiinfo('name'))
        


def menu():
        print("select a number: ")
        print("1 get the entire information ")
        print("2 for the films ")
        print("3 for the gender ")
        print("4 for the starships ")
        print("5 for the character name")
        print("6 for keys ")


def options():
     while True:
        selection = int(input(" "))
        
        if selection == 1:
            print(api())
          
        elif selection == 2:
            print (films())
        
        if selection == 3:
            print (gender())
        
        elif selection == 4:
            print (starships())

        elif selection == 5:
            print (name())

        elif selection == 6:
            print (datakeys())
        

            

def main():
    menu()
    options()


if __name__ == "__main__":
    main()






