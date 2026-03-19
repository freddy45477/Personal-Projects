import mysql.connector
from PIL import Image
import io

# Get connection from MySQL
def get_db_connection():
    try:
        mydb = mysql.connector.connect(
            host="localhost",
            user="root",
            password="password",
            database="face_recognition_db"
        )
        print("Successfully connected to the database")
        return mydb
    except mysql.connector.Error as err:
        if err.errno == mysql.connector.errorcode.ER_ACCESS_DENIED_ERROR:
            print("Credentials not correct")
        elif err.errno == mysql.connector.errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)
        return None


def insert_patients(first_name, middle_name, last_name, age, sex, sex_other, last_login):
    conn = get_db_connection()
    if conn is None:
        print("Cannot insert patient without a database connection.")
        return None

    cursor = conn.cursor()

    sql_query = """
    INSERT INTO patients(first_name, middle_name, last_name, age, sex, sex_other, last_login)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    values = (first_name, middle_name, last_name, age, sex, sex_other, last_login)

    cursor.execute(sql_query, values)
    conn.commit()

    new_id = cursor.lastrowid
    cursor.close()
    conn.close()

    print(f"New patient {first_name} {last_name} registered successfully")
    return new_id


def get_patient_by_id(personal_id):
    conn = get_db_connection()
    if conn is None:
        print("Cannot query without a database connection.")
        return None

    cursor = conn.cursor(dictionary=True)

    sql_query = """
    SELECT p.*, c.phone_number, c.email
    FROM patients p
    LEFT JOIN contacts c ON p.personal_id = c.personal_id
    WHERE p.personal_id = %s
    """
    cursor.execute(sql_query, (personal_id,))
    patient = cursor.fetchone()
    cursor.close()
    conn.close()
    return patient


def get_patient_by_name(name):
    """Search patient by first or last name"""
    conn = get_db_connection()
    if conn is None:
        return None

    cursor = conn.cursor(dictionary=True)
    sql_query = """
    SELECT p.*, c.phone_number, c.email
    FROM patients p
    LEFT JOIN contacts c ON p.personal_id = c.personal_id
    WHERE p.first_name LIKE %s OR p.last_name LIKE %s
    """
    search = f"%{name}%"
    cursor.execute(sql_query, (search, search))
    patients = cursor.fetchall()
    cursor.close()
    conn.close()
    return patients


def get_relatives_by_patient(personal_id):
    """Get all relatives for a given patient"""
    conn = get_db_connection()
    if conn is None:
        return []

    cursor = conn.cursor(dictionary=True)
    sql_query = """
    SELECT * FROM relatives_contacts
    WHERE personal_id = %s
    """
    cursor.execute(sql_query, (personal_id,))
    relatives = cursor.fetchall()
    cursor.close()
    conn.close()
    return relatives


def insert_contact(personal_id, phone_number, email):
    conn = get_db_connection()
    if conn is None:
        print("Cannot insert contact without database connection")
        return None

    cursor = conn.cursor()

    sql_query = """
    INSERT INTO contacts(personal_id, phone_number, email)
    VALUES (%s, %s, %s)
    """
    values = (personal_id, phone_number, email)

    cursor.execute(sql_query, values)
    conn.commit()

    new_contact_id = cursor.lastrowid
    cursor.close()
    conn.close()

    print(f"Contact added: {phone_number}, {email}.")
    return new_contact_id


# FIX: Removed relative_id from parameters (it's AUTO_INCREMENT in MySQL)
# FIX: SQL query was accidentally commented out inside the triple-quoted string
def insert_relatives_contacts(personal_id, relative_first_name, relative_last_name,
                               relationship_type, phone_number, email,
                               thumbnail=None, full_image_path=None):
    conn = get_db_connection()
    if conn is None:
        print("Cannot insert contact without database connection")
        return None

    cursor = conn.cursor()

    sql_query = """
    INSERT INTO relatives_contacts(personal_id, relative_first_name, relative_last_name,
                                    relationship_type, phone_number, email, thumbnail, full_image_path)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    values = (personal_id, relative_first_name, relative_last_name,
              relationship_type, phone_number, email, thumbnail, full_image_path)

    cursor.execute(sql_query, values)
    conn.commit()

    new_relative_id = cursor.lastrowid
    cursor.close()
    conn.close()

    print(f"Relative added: {relative_first_name} {relative_last_name}, {relationship_type}.")
    return new_relative_id


def update_relative_image(relative_id, thumbnail, full_image_path):
    conn = get_db_connection()
    if conn is None:
        print("Cannot update image without database connection")
        return False

    cursor = conn.cursor()

    sql_query = """
    UPDATE relatives_contacts
    SET thumbnail = %s,
        full_image_path = %s
    WHERE relative_id = %s
    """
    values = (thumbnail, full_image_path, relative_id)

    cursor.execute(sql_query, values)
    conn.commit()

    cursor.close()
    conn.close()

    print(f"Image updated for relative_id {relative_id}")
    return True


def update_patient_last_login(personal_id):
    """Update last login timestamp when patient is recognized"""
    import datetime
    conn = get_db_connection()
    if conn is None:
        return False

    cursor = conn.cursor()
    sql_query = """
    UPDATE patients SET last_login = %s WHERE personal_id = %s
    """
    cursor.execute(sql_query, (datetime.datetime.now(), personal_id))
    conn.commit()
    cursor.close()
    conn.close()
    return True


def delete_patient(personal_id):
    """
    Delete a patient and all related records (contacts, relatives).
    The ON DELETE CASCADE on FK constraints handles relatives and contacts automatically.
    """
    conn = get_db_connection()
    if conn is None:
        print("Cannot delete patient without database connection")
        return False

    cursor = conn.cursor()

    # Get patient name for logging before deleting
    cursor.execute("SELECT first_name, last_name FROM patients WHERE personal_id = %s",
                   (personal_id,))
    row = cursor.fetchone()
    name = f"{row[0]} {row[1]}" if row else f"ID {personal_id}"

    cursor.execute("DELETE FROM patients WHERE personal_id = %s", (personal_id,))
    conn.commit()

    affected = cursor.rowcount
    cursor.close()
    conn.close()

    if affected:
        print(f"Patient {name} (ID {personal_id}) deleted — contacts and relatives removed via CASCADE.")
        return True
    else:
        print(f"No patient found with ID {personal_id}")
        return False


def delete_relative(relative_id):
    """Delete a single relative record."""
    conn = get_db_connection()
    if conn is None:
        return False

    cursor = conn.cursor()
    cursor.execute("DELETE FROM relatives_contacts WHERE relative_id = %s", (relative_id,))
    conn.commit()
    affected = cursor.rowcount
    cursor.close()
    conn.close()
    print(f"Relative ID {relative_id} deleted.")
    return affected > 0


# ── Calendar / Events ─────────────────────────────────────────────────────────

def create_events_table():
    """Create the events table if it doesn't exist yet."""
    conn = get_db_connection()
    if conn is None:
        return False
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patient_events (
            event_id      INT          NOT NULL AUTO_INCREMENT,
            personal_id   INT          NOT NULL,
            title         VARCHAR(120) NOT NULL,
            description   TEXT         DEFAULT NULL,
            event_date    DATE         NOT NULL,
            start_time    TIME         DEFAULT NULL,
            end_time      TIME         DEFAULT NULL,
            color         VARCHAR(20)  DEFAULT '#2DD4BF',
            all_day       TINYINT(1)   DEFAULT 0,
            created_at    DATETIME     DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (event_id),
            CONSTRAINT fk_event_patient
                FOREIGN KEY (personal_id) REFERENCES patients(personal_id)
                ON DELETE CASCADE ON UPDATE CASCADE,
            INDEX idx_events_date (personal_id, event_date)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    conn.commit()
    cursor.close()
    conn.close()
    return True


def get_events_for_month(personal_id, year, month):
    """Return all events for a patient in a given month."""
    conn = get_db_connection()
    if conn is None:
        return []
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT * FROM patient_events
        WHERE personal_id = %s
          AND YEAR(event_date)  = %s
          AND MONTH(event_date) = %s
        ORDER BY event_date, start_time
    """, (personal_id, year, month))
    events = cursor.fetchall()
    cursor.close()
    conn.close()
    return events


def get_events_for_day(personal_id, date_str):
    """Return all events for a patient on a specific date (YYYY-MM-DD)."""
    conn = get_db_connection()
    if conn is None:
        return []
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT * FROM patient_events
        WHERE personal_id = %s AND event_date = %s
        ORDER BY all_day DESC, start_time
    """, (personal_id, date_str))
    events = cursor.fetchall()
    cursor.close()
    conn.close()
    return events


def insert_event(personal_id, title, description, event_date,
                 start_time, end_time, color, all_day):
    conn = get_db_connection()
    if conn is None:
        return None
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO patient_events
            (personal_id, title, description, event_date, start_time, end_time, color, all_day)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (personal_id, title, description, event_date,
          start_time, end_time, color, all_day))
    conn.commit()
    event_id = cursor.lastrowid
    cursor.close()
    conn.close()
    print(f"Event '{title}' created on {event_date}")
    return event_id


def update_event(event_id, title, description, event_date,
                 start_time, end_time, color, all_day):
    conn = get_db_connection()
    if conn is None:
        return False
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE patient_events
        SET title=%s, description=%s, event_date=%s,
            start_time=%s, end_time=%s, color=%s, all_day=%s
        WHERE event_id=%s
    """, (title, description, event_date,
          start_time, end_time, color, all_day, event_id))
    conn.commit()
    cursor.close()
    conn.close()
    return True


def delete_event(event_id):
    conn = get_db_connection()
    if conn is None:
        return False
    cursor = conn.cursor()
    cursor.execute("DELETE FROM patient_events WHERE event_id = %s", (event_id,))
    conn.commit()
    affected = cursor.rowcount
    cursor.close()
    conn.close()
    return affected > 0