import cv2 #cv2 is the OpenCV library for computer vision
import threading #threading is used to run the webcam in a separate thread
import datetime # datetime is used to get current date and time
import face_recognition #face_recognition is used for face detection and recognition

known_faces_dir = "known_faces"  # directory containing known faces

latest_frame = None#global variable to store latest frame
#function opens the camera
def open_webcam():
    #try to open the first camera
    camera = cv2.VideoCapture(0)

    #if the first camera is not opened, try to open the second camera
    if not camera.isOpened():
        camera = cv2.VideoCapture(1)
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)

        for i in range(20):  # try to open the camera 20 times
            ret, frame = camera.read()


    return camera

def capture_frame(camera):
    global latest_frame  # use the global variable to store the latest frame
    while True:
        #read the frame from the camera
        ret, frame = camera.read()
        #if ret is true, it means the frame is read correctly

        if ret:
            latest_frame = frame  # update the global variable with the latest frame


    cv2.destroyAllWindows()  # close the window when 'q' is pressed



def face_recognition_loop():
    while True:
        if latest_frame is not None:  # check if the latest frame is available
            copy = latest_frame.copy() #create a copy of the latest frame
            rgb_image = cv2.cvtColor(copy, cv2.COLOR_BGR2RGB) #convert the copy from BGR to RGB color space
            face_locations = face_recognition.face_locations(rgb_image) # detect faces in the RGB image
            face_encoding = face_recognition.face_encodings(rgb_image, face_locations) #encode the face in the RGB image and face locations
            #initialize lists to store known face encodings and names
            names = ["Unknown"] * len(face_locations)  # default name if no match is found
            draw_faces_on_frame(copy, face_locations, names) #draw the faces on the frame
            cv2.imshow("Webcam", copy)  # show the frame with the faces drawn on it
            
        #wait for 1 millisecond to check for key presses
        if cv2.waitKey(1) & 0xFF == ord('q'):  # if 'q' is pressed, exit the loop
            break

def draw_faces_on_frame(frame, face_locations, names):
    #for each face location and name, draw a rectangle around the face and put the name on the frame
    #zip combines the face locations and names into pairs
    for (top, right, bottom, left), name in zip(face_locations, names):
       #draw a rectangle around the face, 0 is the color of the rectangle (green), 2 is the thickness of the rectangle
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
        #put the name of the person on the frame
        #cv2.filled is used to fill the rectangle with color
        cv2.rectangle(frame, (left, bottom - 25), (right, bottom), (0, 255, 0), cv2.FILLED)
        #puttext is used to put the name on the frame
        cv2.putText(frame, name, (left + 6, bottom - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)


#open camera
camera = open_webcam()
#start a thread to capture frames from the camera
thread = threading.Thread(target = capture_frame, args=(camera,), daemon=True)
thread.start()  # start the thread to capture frames
face_recognition_loop()  # start the face recognition loop