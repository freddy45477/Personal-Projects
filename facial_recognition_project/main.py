import cv2
import face_recognition
import os
import datetime
import threading

from db_connection import (
    insert_patients,
    insert_contact,
    insert_relatives_contacts,
    update_patient_last_login,
    get_patient_by_id,
)
from patient_input import (
    collect_patients_info,
    collect_patients_contact,
)

latest_frame = None
lock = threading.Lock()
last_unknown_face_path = ""


def load_known_faces(known_faces_dir):
    known_face_encodings = []
    known_faces_names = []

    if not os.path.exists(known_faces_dir):
        os.makedirs(known_faces_dir, exist_ok=True)
        return known_face_encodings, known_faces_names

    for filename in os.listdir(known_faces_dir):
        if filename.lower().endswith((".jpg", ".png", ".jpeg")):
            image = face_recognition.load_image_file(os.path.join(known_faces_dir, filename))
            face_encodings = face_recognition.face_encodings(image)
            if face_encodings:
                new_encoding = face_encodings[0]
                matches = face_recognition.compare_faces(known_face_encodings, new_encoding)
                if True not in matches:
                    known_face_encodings.append(new_encoding)
                    name = os.path.splitext(filename)[0]
                    known_faces_names.append(name)
                else:
                    print(f"Face already exists for {filename}, skipping...")
            else:
                print(f"No face found in {filename}, skipping...")

    return known_face_encodings, known_faces_names


def open_webcam():
    camera = cv2.VideoCapture(0)
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    # Warm up frames
    for _ in range(20):
        camera.read()

    if not camera.isOpened():
        camera = cv2.VideoCapture(1)
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        for _ in range(20):
            camera.read()

    return camera


def capture_frames(camera):
    global latest_frame
    while True:
        ret, frame = camera.read()
        if ret:
            with lock:
                latest_frame = frame


def face_recognition_loop(known_face_encodings, known_faces_names):
    global last_unknown_face_path
    saved_unknown = False
    unknown_face_detected = False

    os.makedirs("unknown_faces", exist_ok=True)

    while True:
        with lock:
            if latest_frame is None:
                continue
            frame = latest_frame.copy()
            clean_frame = latest_frame.copy()

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings_list = face_recognition.face_encodings(rgb_frame, face_locations)

        unknown_face_detected = False

        for (top, right, bottom, left), face_enc in zip(face_locations, face_encodings_list):
            matches = face_recognition.compare_faces(known_face_encodings, face_enc)
            if True in matches:
                face_distances = face_recognition.face_distance(known_face_encodings, face_enc)
                best_idx = face_distances.argmin()
                name = known_faces_names[best_idx]
            else:
                name = "Unknown"
                unknown_face_detected = True
                if not saved_unknown:
                    face_crop = clean_frame[top:bottom, left:right]
                    filename = datetime.datetime.now().strftime("unknown_face_%Y-%m-%d_%H-%M-%S") + ".jpg"
                    filepath = os.path.join("unknown_faces", filename)
                    cv2.imwrite(filepath, face_crop)
                    print(f"Saving unknown face image to {filepath}")
                    saved_unknown = True
                    last_unknown_face_path = filepath

            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.rectangle(frame, (left, bottom - 20), (right, bottom), (0, 255, 0), cv2.FILLED)
            cv2.putText(frame, name, (left + 6, bottom - 6),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)

        if not unknown_face_detected:
            saved_unknown = False

        cv2.imshow("Alzheimer Care - Face Recognition", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('r'):
            if face_locations:
                known_face_encodings, known_faces_names = register_face(
                    clean_frame, face_locations, known_face_encodings, known_faces_names
                )

    cv2.destroyAllWindows()


def register_face(current_frame, face_locations, known_face_encodings, known_faces_names):
    global last_unknown_face_path

    if not face_locations:
        print("No face detected")
        return known_face_encodings, known_faces_names

    top, right, bottom, left = face_locations[0]
    face_image = current_frame[top:bottom, left:right]
    face_enc = face_recognition.face_encodings(current_frame, [face_locations[0]])[0]

    matches = face_recognition.compare_faces(known_face_encodings, face_enc)
    if True in matches:
        print("Face is already registered")
        return known_face_encodings, known_faces_names

    new_name = input("Enter full name: ").strip()
    known_face_encodings.append(face_enc)
    known_faces_names.append(new_name)

    os.makedirs("known_faces", exist_ok=True)

    personal_id = collect_patients_info()
    print(f"New patient inserted with ID {personal_id}")

    contact_id = collect_patients_contact(personal_id)
    print(f"Contact inserted with ID {contact_id}")

    # Remove the temp unknown face file if it exists
    if last_unknown_face_path and os.path.exists(last_unknown_face_path):
        os.remove(last_unknown_face_path)
        last_unknown_face_path = None

    # Save known face image
    filename = f"{new_name}.jpg"
    filepath = os.path.join("known_faces", filename)
    cv2.imwrite(filepath, face_image)
    print(f"New face registered: {filepath}")

    return known_face_encodings, known_faces_names


def main():
    known_face_encodings, known_faces_names = load_known_faces("known_faces")

    cam = open_webcam()
    if cam.isOpened():
        thread = threading.Thread(target=capture_frames, args=(cam,), daemon=True)
        thread.start()
        face_recognition_loop(known_face_encodings, known_faces_names)
        # FIX: was just `cam` on its own line — must call .release()
        cam.release()
    else:
        print("No camera found")


if __name__ == "__main__":
    main()
