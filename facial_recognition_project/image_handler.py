import os
import cv2

def ensure_patient_folder(personal_id):
    base_dir = "relative_images"
    #if relative_images doesnt exist
    #make it
    if not os.path.exists(base_dir):
        os.mkdir(base_dir)
    
    #take the relative_images dir and the personal_id
    #if the personal_id doesn't exist in relative_images
    #make it
    patient_dir = os.path.join(base_dir, str(personal_id))
    if not os.path.exists(patient_dir):
        os.mkdir(patient_dir)
    
    return patient_dir

def save_image_for_patient(personal_id, image_path):
    #check if the relative folder is ther
    patient_folder = ensure_patient_folder(personal_id)
    #then put the image file in there
    uploaded_image_path = os.path.join(patient_folder, "face.jpg")
    
    #read the images in the path
    image = cv2.imread(image_path)
    #if there is none, print msg
    if image is None:
        print("Error: Image could not be read")
        return
    #write to the folder to save the image there
    cv2.imwrite(uploaded_image_path, image)
    print(f"image saved to {uploaded_image_path}")

    





