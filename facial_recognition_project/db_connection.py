import mysql.connector

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

def insert_patients(first_name, middle_name, last_name, age, sex, sex_other, health_condition, last_login):
    # Connect to the database
    conn = get_db_connection()
    if conn is None:
        print("Cannot insert patient without a database connection.")
        return

    # Cursor allows Python to interact with the database
    cursor = conn.cursor()

    # Query with placeholders
    sql_query = """
    INSERT INTO patients(first_name, middle_name, last_name, age, sex, sex_other, health_conditions, last_login)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """

    # Tuple of values
    values = (first_name, middle_name, last_name, age, sex, sex_other, health_condition, last_login)

    # Execute and commit
    cursor.execute(sql_query, values)
    conn.commit()  # <--- Save changes

    new_id = cursor.lastrowid
    cursor.close()
    conn.close()  # <--- Close the connection

    print(f"New patient {first_name} {last_name} registered successfully")
    return new_id

def insert_health_issues(personal_id, issue_name, diagnosed_date, status, description):
    #make only certain statuses to be accepted
    valid_statuses = {"Active", "Resolved", "Chronic"}
    #if the status is not in the valid status set then print msg
    if status not in valid_statuses:
        print (f"invalid status: {status}. Must be one of {valid_statuses}")
        return #stop function is it is invalid
    
    #connect to the database
    conn = get_db_connection()
    if conn is None:
        print("Cannot insert health issue information because database is not connected")
        return
    #allow cursor to allow python to interact with the database
    cursor = conn.cursor()

    #make a query with placeholders
    sql_query = """
    INSERT INTO health_issues(personal_id, issue_name, diagnosed_date, status, description)
    VALUES (%s, %s, %s, %s, %s)
    """

    #tuple of the values
    values = (personal_id, issue_name, diagnosed_date, status, description)

    #make cursor execute the query
    cursor.execute(sql_query, values)
    #save changeds
    conn.commit()
    #get the new health id added
    new_health_id = cursor.lastrowid
    #close cursor
    cursor.close()
    #close connection
    conn.close()

    print(f"Health information added: {issue_name}")
    return new_health_id

def insert_symptom(personal_id, symptom_name, start_date, status, notes):
    #make valid statuses for the status
    valid_statuses = {"ongoing", "resolved"}
    #if status is not in valid_statuses, print msg
    if status not in valid_statuses:
        print(f"invalid status {status}. Must be one of {valid_statuses}")
        return #stop if it is invalid
    
    #get db connection
    conn = get_db_connection()
    #if none connection, print msg and stop
    if conn is None:
        print("Cannot insert symptoms without a database connection.")
        return
    #open cursor to allow pyton to interact with mysql
    cursor = conn.cursor()
    
    #create sql query to insert
    sql_query = """
    INSERT INTO symptom_table(personal_id, symptom_name, start_date, status, notes)
    VALUES (%s, %s, %s, %s, %s)
    """
    #create a tuple to insert with the query
    values = (personal_id, symptom_name, start_date, status, notes)

    #execute it
    cursor.execute(sql_query, values)
    #save changes
    conn.commit()
    # get the new symptom id
    new_symptom_id = cursor.lastrowid
    #close cursor
    cursor.close()
    #close connection
    conn.close()

    print(f"New symptom added: {symptom_name}")
    return new_symptom_id

def insert_medication(personal_id, medication_name, dosage, frequency, start_date, end_date, status, type, notes):
    #make valid statuses
    valid_statuses = {"ongoing", "completed", "discontinued"}
    #if status is not in valid statuses, then stop
    if status not in valid_statuses:
        print(f"Invalid status: {status}. Must be one of {valid_statuses}")
        return

    #get db connection
    conn = get_db_connection()
    if conn is None:
        print("Cannot insert symptom without database connection")
        return
    
    #open the cursor
    cursor = conn.cursor()

    #make sql query and placeholders
    sql_query = """
    INSERT INTO medication(personal_id, medication_name, dosage, frequency, start_date, end_date, status, type, notes)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    #make a tuple for the values
    values = (personal_id, medication_name, dosage, frequency, start_date, end_date, status, type, notes)

    #execute the query and values
    cursor.execute(sql_query, values)
    #save changes
    conn.commit()
    #get the new medication id
    new_medication_id = cursor.lastrowid
    #close cursor
    cursor.close()
    #close connection
    conn.close()
    
    print(f"Medication added: {medication_name}.")
    return new_medication_id

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

def insert_relatives_contacts(personal_id, relative_personal_id, relative_first_name, relative_last_name, relationship_type, phone_number, email):
    #get db connection
    conn = get_db_connection()
    if conn is None:
        print("Cannot insert contact without database connection")
        return
    
    #open the cursor
    cursor = conn.cursor()

    #make sql query and placeholders
    sql_query = """
    INSERT INTO relatives_contacts(personal_id, relative_personal_id, relative_first_name, relative_last_name, relationship_type, phone_number, email)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
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

if __name__ == "__main__":
    # Test inserting one patient
    new_patient_id = insert_patients(
        first_name="Alice",
        middle_name="",
        last_name="Smith",
        age=28,
        sex="Female",
        sex_other=None,
        health_condition="Healthy",
        last_login="2025-08-28"
    )
    print(f" Inserted patient with ID: {new_patient_id}")

