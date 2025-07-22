#import openCV(cv2) library to use the webcam
import cv2

#make a funciton for opening the webcam
def webcam():

    camera = cv2.VideoCapture(0) # make a varibleOpen the first camera
    #if the webcam is not opened, camera becomes cv2.VideoCapture(1) and opens the second camera
    if not camera.isOpened():
        camera = cv2.VideoCapture(1)
    #returns the second camera
    return camera
    #infinite loop to keep the webcam open

def capturedFrame(camera):
    while True:
        #ret is boolean value that tells if the frame is read correctly
        #frame is set to the frame captured by the camera
        #read() function returns two values, ret and frame
        ret, frame = camera.read()

        #imshow allows to show a window with the name "webcam" and the frame captured by the camera
        cv2.imshow("webcam", frame)

        #waitkey waits for a key press for 1 millisecond
        #if 'q' is pressed, the loop breaks and webcam closed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    camera.release()  # release the camera so other resources can use it
    cv2.destroyAllWindows() #close all opencv windows


cam = webcam()
if cam.isOpened():
    capturedFrame(cam)
else: print("no camera found")






