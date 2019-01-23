from imutils.video import VideoStream
from imutils.video import FPS
from scipy.interpolate import interp1d
import numpy as np
import argparse
import imutils
import nt as nt
import requests
import cv2
import time

# parse arguments
ap = argparse.ArgumentParser()
ap.add_argument("-r", "--roborio", nargs="?", default="roborio-5024-frc.local", help="address to the roborio")
ap.add_argument("-l", "--lower", nargs="+", type=int, default=[44, 0, 210], help="HSV lower bounds")
ap.add_argument("-u", "--upper", nargs="+", type=int, default=[104, 13, 255], help="HSV upper bounds")
ap.add_argument("-v", "--video", help="path to the video file")
args = vars(ap.parse_args())

print("Starting network tables...")
# intialize the network tables
nt.init(args["roborio"])
print("Is it blocking?")

# set the video stream
if args.get("video", True):
    vs = cv2.VideoCapture(args["video"])
    if vs.isOpened():
        width = int(vs.get(3))
        height = int(vs.get(4))
else:
    vs = VideoStream(src=0).start()
    if vs.stream.isOpened():
        width = int(vs.stream.get(3))
        height = int(vs.stream.get(4))

fps = FPS().start()

# allow the camera or video file to load
time.sleep(2.0)

# set some variables
lower = tuple(args["lower"]) # lower bounds of retro-reflective tape
upper = tuple(args["upper"]) # upper bounds of retro-reflective tape
centerX = width // 2         # center x-value of frame

# keep looping
while True:
    # grab the current frame
    frame = vs.read()

    # handle the gram from VideoCapture or VideoStream
    frame = frame[1] if args.get("video", False) else frame

    # if we are viewing a video and did not grab a frame, we are at end of video
    if frame is None:
        break

    # resize the frame, blur it, and convert it to the HSV colour space
    resized = imutils.resize(frame, width=600)
    blurred = cv2.GaussianBlur(resized, (11, 11), 0)
    hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
    # ratio = frame.shape[0] / float(resized.shape[0])

    # construct a mask for the bounds, then erode and dilate
    mask = cv2.inRange(hsv, lower, upper)
    mask = cv2.erode(mask, None, iterations=2)
    mask = cv2.dilate(mask, None, iterations=2)

    # find contours in the mask
    cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)
    
    # find closest contours to center on each side
    min_left = 0
    min_right = width
    left_contour = None
    right_contour = None
    
    for c in cnts:
        area = cv2.contourArea(c)
        # print("Area: ", area)
        if area > 100: # ignore any noise
            M = cv2.moments(c)
            cX = int((M["m10"] / M["m00"]))
            cY = int((M["m01"] / M["m00"]))

            ((x, y), radius) = cv2.minEnclosingCircle(c)
            cv2.circle(resized, (int(x), int(y)), int(radius), (255, 255, 0), 1) # draw a blue cirle around the contour
           
            # find the contours closest to the center x-value of the frame
            if cX > centerX:
                if cX < min_right:
                    min_right = cX
                    right_contour = c
            else:
                if cX > min_left:
                    min_left = cX
                    left_contour = c
    
    # draw a yellow circle around nearest contours
    if right_contour is not None:
        ((rX, rY), radius) = cv2.minEnclosingCircle(right_contour)
        cv2.circle(resized, (int(rX), int(rY)), int(radius), (0, 255, 255), 1)
        
    if left_contour is not None:
        ((lX, lY), radius) = cv2.minEnclosingCircle(left_contour)
        cv2.circle(resized, (int(lX), int(lY)), int(radius), (0, 255, 255), 1)
        
    # print("cX: {:.2f}, lX: {:.2f}, rX: {:.2f}".format(centerX, lX, rX))
    # interpolate the distance between the centers of the two nearest contours for 11.5 inches
    distance = interp1d([lX, rX], [0, 11.5])
    try:
        offset = distance(centerX)
    except ValueError:
        print("Error in interpolation")
        pass
        
    direction = "left" if 5.75 - offset > 0 else "right" if 5.75 - offset < 0 else "center"
    print("The robot is {:.2f} inches to the {} of center.".format(abs(5.75 - offset), direction))

    # send the data to the roborio
    nt.publish(direction, abs(5.75 - offset))
    
    # draw center line
    cv2.line(resized, (centerX, 0), (centerX, height), (255, 255, 255), 1)
    
    # show the frame to our screen and increment the frame counter
    cv2.imshow("Frame:", resized)
    
    # update the FPS counter
    fps.update()

    # if the 'q' key is pressed, stop the loop
    key = cv2.waitKey(1) & 0xFF
    if key == ord("q"):
        break

# stop the timer and display FPS information
fps.stop()
print("[INFO] elasped time: {:.2f}".format(fps.elapsed()))
print("[INFO] FPS: {:.2f}".format(fps.fps()))

# close the video stream
if not args.get("video", False):
    vs.stop()
else:
    vs.release()

# close all windows
cv2.destroyAllWindows()
