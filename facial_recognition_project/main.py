#import openCV(cv2) library to use the webcam
import cv2
#import face_recognition library to use face recognition
import face_recognition
#import os library to use the operating system functions
import os


def load_known_faces(known_faces_dir):
    known_face_encodings = [] #list to store face encodings
    known_faces_names = [] #list to store names of the faces

    for filename in os.listdir(known_faces_dir):
        if filename.endswith((".jpg", ".png", ".jpeg")):
            #load the image from the file
            #os.path.join joins the directory and the filename to get the full path of the image
            image = face_recognition.load_image_file(os.path.join(known_faces_dir, filename))
            #get the face encodings form the image
            face_encodings = face_recognition.face_encodings(image)
            if face_encodings:  # check if any face encodings were found
                new_encoding = face_encodings[0]  # get the first face encoding
                #compare the new face encoding with the known face encodings
                matches = face_recognition.compare_faces(known_face_encodings, new_encoding)
                # if there is a match, it means the face already exists in the databas
                if matches:
                    print("face already exists in the database")
                    continue  # skip this image if the face already exists
                else: 
                    #adds the new face encoding to the list of known face encodings
                    known_face_encodings.append(new_encoding)
                    name = os.path.splitext(filename)[0]  # get the name from the filename
                    known_faces_names.append(name) #adds the name to the list of known faces names
            else: 
                print(f"No face found in {filename}, skipping...")
    return known_face_encodings, known_faces_names

#make a funciton for opening the webcam
def webcam():

    camera = cv2.VideoCapture(0) # make a varibleOpen the first camera
    #if the webcam is not opened, camera becomes cv2.VideoCapture(1) and opens the second camera
    if not camera.isOpened():
        camera = cv2.VideoCapture(1)
    #returns the second camera
    return camera
    #infinite loop to keep the webcam open

def capturedFrame(camera, known_face_encodings, known_faces_names):
    while True:
        #ret is boolean value that tells if the frame is read correctly
        #frame is set to the frame captured by the camera
        #read() function returns two values, ret and frame
        ret, frame = camera.read()
        #CVTColor function converts the frame from BGR to RGB color space
        #face_recognition library works with RGB color space
        #so we need to convert the frame to RGB color space
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        #face_recognition.face locations function detects faces in the frame
        face_locations = face_recognition.face_locations(rgb_frame)
        #face_recognition.face_encodings function encodes the faces detected in the frame
        # face_encodings function returns a list of face encodings
        face_encoding = face_recognition.face_encodings(rgb_frame, face_locations)
        #compare_faces function compares the face encodings with the known face encodings
        #it returens a list of boolean values to see if the face matches with the known faces

        #for loop to look through the face locations and face encodings
        #top, right, bottom, left are the coordinates of the face in the frame
        #zip function combines the face locations and face encodings into a single iterable
        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encoding):
            #compare the face encodings with the known face encodings to see if the face matches
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
            if matches:
                #if the face matches, face distance is calculated to find the closest match
                #face_distance function returns a list of distances between the face encodings and the known face
                face_distance = face_recognition.face_distance(known_face_encodings, face_encoding)
                #find the index of the smallest face distance
                smallest_distance_index = face_distance.argmin()
                #get the name of the person from the known faces names list
                name = known_faces_names[smallest_distance_index]
            else: "Unknown" #if the face does not match with any known faces, name is unkown
            #draw a rectangle around the face in the frame
            #top, left are the coordinates of the top left corner of the rectangle
            #right, bottom are the coordinates of the bottom right corner of the rectangle
            #(0,255,0) is the color of the rectangle in BGR format (green in this case)
            #2 is the thickness of the rectangle
            face_rectangle = cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            #put a label box for the name of the person
            #cv2.FILLED fills with the color specificed
            name_label_box = cv2.rectangle(frame, (left, bottom -20), (right, bottom), (0,255,0), cv2.FILLED)
            #put the name of the person in the label box
            #cv2.putText function puts the text on the frame
            #font is set to cv2.FONT_HERSHEY_SIMPLEX
            #0.5 is the font scale, (0,0,0) is the color of the text in BGR format (black in this case)
            #1 is the thickness of the text
            name_label = cv2.putText(frame, name, (left + 6, bottom - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,0), 1)



        #imshow allows to show a window with the name "webcam" and the frame captured by the camera
        cv2.imshow("webcam", frame)

        #waitkey waits for a key press for 1 millisecond
        #if 'q' is pressed, the loop breaks and webcam closed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    camera.release()  # release the camera so other resources can use it
    cv2.destroyAllWindows() #close all opencv windows

known_face_encodings, known_faces_names = load_known_faces("known_faces")

cam = webcam()
if cam.isOpened():
    capturedFrame(cam, known_face_encodings, known_faces_names)
else: print("no camera found")






