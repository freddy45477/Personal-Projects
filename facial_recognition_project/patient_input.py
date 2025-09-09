from db_connection import (
    insert_patients,
    insert_contact,
    insert_relatives_contacts
)

import datetime

def collect_patients_info():
    first_name = input("Enter First Name: ").strip()
    middle_name = input("Enter Middle Name(Press Enter if None): ").strip()
    if middle_name == "":
        middle_name = None
    last_name = input("Enter Last Name: ").strip()

         
    while True:
        age_input = input("What is you age: ").strip()
        if age_input.isdigit():
            age = int(age_input)
            break
        else:
            print ("Input is not Valid")
    
    while True:
        sex = input("What is your sex(M/F/Others): ").strip().capitalize()
        if sex == "Others":
            sex_other = input("If others, what do you identify as: ")
            break
        elif sex in ("M", "Male"):
            sex_other = None
            break
        elif sex in ("F", "Female"):
            sex_other = None 
            break
        else:
            print("invalid input")


    last_login = datetime.now()

    personal_id = insert_patients(
        first_name=first_name,
        middle_name=middle_name,
        last_name=last_name,
        age=age,
        sex=sex,
        sex_other=sex_other,
        last_login=last_login
    )

    return personal_id

    
def collect_patients_contact(personal_id):
    phone_number = input("Enter Phone Number: ")
    email = input("Enter Email: ")

    contact_id = insert_contact(
        personal_id=personal_id,
        phone_number=phone_number,
        email=email
    )

    return contact_id