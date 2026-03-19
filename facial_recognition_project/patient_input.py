import datetime
from db_connection import (
    insert_patients,
    insert_contact,
    insert_relatives_contacts
)


def collect_patients_info():
    print("\n--- New Patient Registration ---")
    first_name = input("Enter First Name: ").strip()
    middle_name = input("Enter Middle Name (Press Enter if None): ").strip()
    if middle_name == "":
        middle_name = None
    last_name = input("Enter Last Name: ").strip()

    while True:
        age_input = input("What is your age: ").strip()
        if age_input.isdigit():
            age = int(age_input)
            break
        else:
            print("Input is not valid. Please enter a number.")

    while True:
        sex = input("What is your sex (M/F/Other): ").strip().capitalize()
        if sex in ("M", "Male"):
            sex = "M"
            sex_other = None
            break
        elif sex in ("F", "Female"):
            sex = "F"
            sex_other = None
            break
        elif sex in ("Other", "Others"):
            sex = "Other"
            sex_other = input("If other, what do you identify as: ").strip()
            break
        else:
            print("Invalid input. Please enter M, F, or Other.")

    # FIX: was datetime.now() — must be datetime.datetime.now()
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

    return personal_id


def collect_patients_contact(personal_id):
    print("\n--- Patient Contact Information ---")
    phone_number = input("Enter Phone Number: ").strip()
    email = input("Enter Email: ").strip()

    contact_id = insert_contact(
        personal_id=personal_id,
        phone_number=phone_number,
        email=email
    )

    return contact_id


def collect_relatives_contact(personal_id):
    print("\n--- Add a Relative ---")

    first_name = input("Relative First Name: ").strip()
    last_name = input("Relative Last Name: ").strip()
    relationship_type = input("Relationship Type (e.g. Son, Daughter, Spouse): ").strip()
    phone_number = input("Phone Number: ").strip()
    email = input("Email: ").strip()

    # FIX: Removed relative_id param — it's AUTO_INCREMENT, MySQL assigns it
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

    print(f"Relative added with ID {relative_id}.")
    return relative_id
