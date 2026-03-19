# Alzheimer Care — Patient Recognition System

A facial recognition desktop app for Alzheimer patient care.
Recognizes patients by face, displays their profile and relatives.

---

## Setup

### 1. Install Python dependencies

```bash
pip install mysql-connector-python opencv-python face-recognition Pillow
```

> On some systems, `face_recognition` requires `cmake` and `dlib`:
> ```bash
> pip install cmake dlib face-recognition
> ```

### 2. Set up MySQL database

1. Open MySQL and run the schema:
   ```bash
   mysql -u root -p < setup_database.sql
   ```
2. Update credentials in `db_connection.py` if needed:
   ```python
   host="localhost", user="root", password="your_password"
   ```

### 3. Run the app

```bash
python app.py
```

---

## Features

| Feature | Description |
|---|---|
| **Home / Camera** | Live webcam feed with real-time face recognition |
| **Register Patient** | Form to register new patients with face capture or photo upload |
| **Patient Info** | Search patients by ID or name, view full profile |
| **Relatives** | View family member cards with photos, add new relatives |

## Keyboard Shortcuts (while camera is running)

| Key | Action |
|---|---|
| `R` | Register current face |
| `Q` | Quit camera |
| `Space` | Capture photo (in capture dialogs) |

---

## Bugs Fixed

| File | Bug | Fix |
|---|---|---|
| `patient_input.py` | `datetime.now()` — incorrect call | Changed to `datetime.datetime.now()` |
| `db_connection.py` | `insert_relatives_contacts` SQL query was accidentally commented out inside the triple-quoted string | Moved `#` comments outside the SQL string |
| `db_connection.py` | `insert_relatives_contacts` accepted `relative_id` as a parameter even though it's `AUTO_INCREMENT` | Removed `relative_id` parameter |
| `patient_input.py` | `collect_relatives_contact` passed `relative_id` to `insert_relatives_contacts` | Removed that argument |
| `main.py` | `cam` on its own line did nothing | Changed to `cam.release()` |
| `image_handler.py` | `os.mkdir` fails if parent folder doesn't exist | Changed to `os.makedirs(..., exist_ok=True)` |
| `setup_database.sql` | No schema existed | Created with correct FK constraints and AUTO_INCREMENT on `relative_id` |

---

## Project Structure

```
alzheimer_app/
├── app.py                 ← Main GUI application (run this)
├── main.py                ← Original CLI/camera script (fixed)
├── db_connection.py       ← All MySQL queries (fixed)
├── patient_input.py       ← Patient data input helpers (fixed)
├── image_handler.py       ← Image save/capture utilities (fixed)
├── setup_database.sql     ← Run once to create the database
├── known_faces/           ← Registered face images (auto-created)
├── unknown_faces/         ← Unrecognized face snapshots (auto-created)
└── relative_images/       ← Relative photos by patient ID (auto-created)
```
