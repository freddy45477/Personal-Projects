import mysql.connector
from PIL import Image #import to pilloe to manipulate images
import io

full_image = Image.open



#get connection from mysqk
def get_db_connection():
    try:
        mydb = mysql.connector.connect(
            host = "localhost",
            user = "root",
            password = "password",
            database = "face_recognition_db"
        )
        print("Successfully connected to the database")
        return mydb  # <--- RETURN the connection
    except mysql.connector.Error as err:
        if err.errno == mysql.connector.errorcode.ER_ACCESS_DENIED_ERROR:
           print("Credentials not correct")
        elif err.errno == mysql.connector.errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)
        return None  # <--- Return None if connection fails

def insert_patients(first_name, middle_name, last_name, age, sex, sex_other, last_login):
    # Connect to the database
    conn = get_db_connection()
    if conn is None:
        print("Cannot insert patient without a database connection.")
        return

    # Cursor allows Python to interact with the database
    cursor = conn.cursor()

    # Query with placeholders
    sql_query = """
    INSERT INTO patients(first_name, middle_name, last_name, age, sex, sex_other, last_login)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    """

    # Tuple of values
    values = (first_name, middle_name, last_name, age, sex, sex_other, last_login)

    # Execute and commit
    cursor.execute(sql_query, values)
    conn.commit()  # <--- Save changes

    new_id = cursor.lastrowid
    cursor.close()
    conn.close()  # <--- Close the connection

    print(f"New patient {first_name} {last_name} registered successfully")
    return new_id



def insert_contact(personal_id, phone_number, email):
    #get db connection
    conn = get_db_connection()
    if conn is None:
        print("Cannot insert contact without database connection")
        return
    
    #open the cursor
    cursor = conn.cursor()

    #make sql query and placeholders
    sql_query = """
    INSERT INTO contacts(personal_id, phone_number, email)
    VALUES (%s, %s, %s)
    """
    #make a tuple for the values
    values = (personal_id, phone_number, email)

    #execute the query and values
    cursor.execute(sql_query, values)
    #save changes
    conn.commit()
    #get the new medication id
    new_contact_id = cursor.lastrowid
    #close cursor
    cursor.close()
    #close connection
    conn.close()
    
    print(f"Medication added: {phone_number}, {email}.")
    return new_contact_id

def insert_relatives_contacts(personal_id, relative_personal_id, relative_first_name, relative_last_name, relationship_type, phone_number, email, ):
    #get db connection
    conn = get_db_connection()
    if conn is None:
        print("Cannot insert contact without database connection")
        return
    
    #open the cursor
    cursor = conn.cursor()

    #make sql query and placeholders
    
    sql_query = """
    #INSERT INTO relatives_contacts(personal_id, relative_personal_id, relative_first_name, relative_last_name, relationship_type, phone_number, email)
    #VALUES (%s, %s, %s, %s, %s, %s, %s)
    #"""
    #make a tuple for the values
    values = (personal_id, relative_personal_id, relative_first_name, relative_last_name, relationship_type, phone_number, email)

    #execute the query and values
    cursor.execute(sql_query, values)
    #save changes
    conn.commit()
    #get the new medication id
    new_relative_contact_id = cursor.lastrowid
    #close cursor
    cursor.close()
    #close connection
    conn.close()
    
    print(f"contacts added: {relative_first_name} {relative_last_name}, {relationship_type}.")
    return new_relative_contact_id
