import mysql.connector
from PIL import Image #import to pilloe to manipulate images
import shutil
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

def insert_relatives_contacts(relative_id, personal_id, relative_first_name, relative_last_name, relationship_type, phone_number, email, thumbnail=None, full_image_path=None):
    #get db connection
    conn = get_db_connection()
    if conn is None:
        print("Cannot insert contact without database connection")
        return
    
    #open the cursor
    cursor = conn.cursor()

    #make sql query and placeholders
    
    sql_query = """
    #INSERT INTO relatives_contacts(relative_id, personal_id, relative_first_name, relative_last_name, relationship_type, phone_number, email, thumbnail, full_image_path)
    #VALUES (%s, %s, %s, %s, %s, %s, %s)
    #"""
    #make a tuple for the values
    values = (relative_id, personal_id, relative_first_name, relative_last_name, relationship_type, phone_number, email, thumbnail, full_image_path)

    #execute the query and values
    cursor.execute(sql_query, values)
    #save changes
    conn.commit()
    #get the new medication id
    new_relative_id = cursor.lastrowid
    #close cursor
    cursor.close()
    #close connection
    conn.close()
    
    print(f"contacts added: {relative_first_name} {relative_last_name}, {relationship_type}.")
    return new_relative_id

def update_relative_image(relative_id, thumbnail, full_image_path):
    #get the connection to the db
    conn = get_db_connection()
    #if no connection, print msg
    if conn is None:
        print("Cannot insert contact without database connection")
        return
    #open the cursor
    cursor = conn.cursor()
    
    #make the sql_query to insert into the db
    sql_query = """
    UPDATE relatives_contacts
    SET thumbnail = %s,
        full_image_path = %s
    WHERE relative_id = %s
    """
    #get the values of the input
    values = (thumbnail, full_image_path, relative_id)

    #execute the sql query with the values
    cursor.execute(sql_query, values)
    #commit the changes, save them
    conn.commit()

    #close cursor(interaction with python and mysql)
    cursor.close()
    #close connection
    conn.close()

    print(f"image updated for relative_id {relative_id}")
    return True



