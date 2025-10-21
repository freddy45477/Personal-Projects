
from Class import starwars
from Class import files

def starwarsinfo():

    while True:
        selection = int(input("select a number: "))
        if selection == 1:
            print (starwars(str(selection)))
            answer = input ("dodo you want to save in your file? y/n ")
            if answer == "y":
                files("[date: {'name': 'C-3PO', 'height': '167', 'mass': '75', 'hair_color': 'n/a', 'skin_color': 'gold', 'eye_color': 'yellow', 'birth_year': '112BBY', 'gender': 'n/a', 'homeworld': 'https://swapi.py4e.com/api/planets/1/', 'films': ['https://swapi.py4e.com/api/films/1/', 'https://swapi.py4e.com/api/films/2/', 'https://swapi.py4e.com/api/films/3/', 'https://swapi.py4e.com/api/films/4/', 'https://swapi.py4e.com/api/films/5/', 'https://swapi.py4e.com/api/films/6/'], 'species': ['https://swapi.py4e.com/api/species/2/'], 'vehicles': [], 'starships': [], 'created': '2014-12-10T15:10:51.357000Z', 'edited': '2014-12-20T21:17:50.309000Z', 'url': 'https://swapi.py4e.com/api/people/2/'})]")
            else: continue

        elif selection == 2:
            print (starwars(str(selection)))
            answer = input("do you want to save in your file? y/n ")
            if answer == "y":
                files("[name: C-3PO]")
            else: continue

        elif selection == 3:
            print(starwars( str(selection)))
            answer = input("do you want to save in your file? y/n ")
            if answer == "y":
                files("[gender: n/a]")
            else: continue

        elif selection == 4:
            print(starwars( str(selection)))
            answer = input("do you want to save in your file? y/n ")
            if answer == "y":
                files("[specie:'https://swapi.py4e.com/api/species/2/']")
            else: continue

        elif selection == 5:
            print(starwars( str(selection)))
            answer = input("do you want to save in your file? y/n ")
            if answer == "y":
                files("[skin color: gold]")
            else: continue
        
        elif selection == 6:
            print(starwars( str(selection)))
            answer = input("do you want to save in your file? y/n ")
            if answer == "y":
                files("[eye color: yellow]")
            else: continue
        
        elif selection == 7:
            print(starwars( str(selection)))
            answer = input("do you want to save in your file? y/n ")
            if answer == "y":
                 files("dict_keys(['name', 'height', 'mass', 'hair_color', 'skin_color', 'eye_color', 'birth_year', 'gender', 'homeworld', 'films', 'species', 'vehicles', 'starships', 'created', 'edited', 'url'])")
            else: continue

        elif selection == 8:
            break

        else: 
            print ("invalid pin")
            continue

def files(a):
    with open ("swfile.txt", "a") as file:
        file.write(a)
        file.close()

def menu():
    print ("----------------")
    print("1: Entire information")
    print("2:Name")
    print("3: gender")
    print("4: specie")
    print ("5: skin color")
    print ("6: eye color")
    print ("7: all the keys")
    print ("8: quit")
    print ("----------------")


def main():
    menu()
    starwarsinfo()

if __name__ == "__main__":
    main()
