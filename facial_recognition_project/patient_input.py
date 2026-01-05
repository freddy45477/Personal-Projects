import os
from image_handler import (
    save_image_for_patient
)

from db_connection import (
    get_db_connection,
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
        if sex in ("O", "Other","Others"):
            sex = "Other"
            sex_other = input("If others, what do you identify as: ")
            break
        elif sex in ("M", "Male"):
            sex = "Male"
            sex_other = None
            break
        elif sex in ("F", "Female"):
            sex = "Female"
            sex_other = None 
            break
        else:
            print("invalid input")


    last_login = datetime.datetime.now()

    personal_id = insert_patients(
        first_name=first_name,
        middle_name=middle_name,
        last_name=last_name,
        age=age,
        sex=sex,
        sex_other=sex_other,
        last_login=last_login
    )

    print(f"Patient added with ID {personal_id}.")

    return personal_id

    
def collect_patients_contact(personal_id):
    phone_number = input("Enter Phone Number: ")
    email = input("Enter Email: ")

    contact_id = insert_contact(
        personal_id=personal_id,
        phone_number=phone_number,
        email=email
    )

    print(f"Patient Contact added with ID {personal_id}.")

    return contact_id

def collect_relatives_contact(personal_id, image_path):
    print ("\n--- Add a Relative ---")

    #ask the user's relative information
    first_name = input("Relative First Name: ").strip()
    last_name = input("Relative Last Name: ").strip()
    relationship_type = input("Relationship Type: ").strip()
    phone_number = input("Phone Number: ").strip()
    email = input("Email: ").strip()

    #insert the information into the db
    relative_id = insert_relatives_contacts(
        personal_id=personal_id,
        relative_first_name=first_name,
        relative_last_name=last_name,
        relationship_type=relationship_type,
        phone_number=phone_number,
        email=email,
        thumbnail=None,
        full_image_path=None
    )
    print(f"relative added with ID {relative_id}.")


    full_image_path, thumbnail_bytes = save_image_for_patient(personal_id, relative_id, image_path)

    if thumbnail_bytes is None or full_image_path is None:
        print(f"Skipping database update for relative ID {relative_id} because image could not be saved")
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        sql_query = """
        UPDATE relatives_contacts
        SET thumbnail = %s,
            full_image_path = %s
        WHERE relative_id = %s
        """
        
        values = (thumbnail_bytes, full_image_path, relative_id)
        cursor.execute(sql_query, values)
        conn.commit()
        cursor.close()
        conn.close()

        print(f"relative image updated for ID {relative_id}.")


    return relative_id

def add_relative_image(personal_id, relative_id, image_path):
    
    pass
