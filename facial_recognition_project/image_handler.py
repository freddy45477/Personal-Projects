import os
import cv2

def ensure_patient_folder(personal_id):
    base_dir = "relative_images"
    patient_dir = os.path.join(base_dir, str(personal_id))
    # FIX: Use os.makedirs with exist_ok=True to handle nested directory creation safely
    os.makedirs(patient_dir, exist_ok=True)
    return patient_dir


def save_image_for_patient(personal_id, relative_id, image_path):
    patient_folder = ensure_patient_folder(personal_id)

    image = cv2.imread(image_path)
    if image is None:
        print("Error: Image could not be read")
        return None, None

    # Create a thumbnail (100x100) and convert to bytes for MySQL BLOB
    thumbnail = cv2.resize(image, (100, 100))
    _, buffer = cv2.imencode('.jpg', thumbnail)
    thumbnail_bytes = buffer.tobytes()

    # Save the full image to the patient's folder
    filename = f"relative_face_{relative_id}.jpg"
    full_image_path = os.path.join(patient_folder, filename)
    cv2.imwrite(full_image_path, image)
    print(f"Image saved to {full_image_path}")

    return thumbnail_bytes, full_image_path


def capture_face_from_camera(save_path):
    """Open camera, let user take a photo, save to save_path. Returns True on success."""
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        cap = cv2.VideoCapture(1)

    if not cap.isOpened():
        print("Error: No camera found")
        return False

    print("Camera open. Press SPACE to capture, Q to cancel.")
    captured = False

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        # Show countdown overlay
        display = frame.copy()
        cv2.putText(display, "Press SPACE to capture | Q to cancel",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 150), 2)
        cv2.imshow("Capture Relative Photo", display)

        key = cv2.waitKey(1) & 0xFF
        if key == ord(' '):
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            cv2.imwrite(save_path, frame)
            captured = True
            print(f"Photo captured: {save_path}")
            break
        elif key == ord('q'):
            print("Capture cancelled.")
            break

    cap.release()
    cv2.destroyAllWindows()
    return captured
