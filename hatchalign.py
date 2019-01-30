# import necessary libraries
import numpy as np
import argparse
import cv2
import imutils
import sys
import time
import threading

from imutils.video import VideoStream
from imutils.video import FPS
from networktables import NetworkTables
from networktables import NetworkTablesInstance
from scipy.interpolate import interp1d

# parse arguments
ap = argparse.ArgumentParser()
ap.add_argument("-r", "--roborio", nargs="?", default="192.168.24.25", help="address to the roborio")
ap.add_argument("-l", "--lower", nargs="+", type=int, default=[113, 0, 197], help="HSV lower bounds")
ap.add_argument("-u", "--upper", nargs="+", type=int, default=[157, 10, 255], help="HSV upper bounds")
ap.add_argument("-v", "--video", help="path to the video file")
ap.add_argument("-s", "--show", nargs="?", const="show", help="display a window of the frames")
args = vars(ap.parse_args())

# connect to the roborio network tables
print("Connecting to ", args["roborio"])
NetworkTables.initialize(server=args["roborio"])
livewindow = NetworkTablesInstance.getDefault().getTable("Shuffleboard/LiveWindow")

# set the video stream
if args.get("video", True):
    # vs = cv2.VideoCapture(args["video"])
    vs = cv2.VideoCapture(args["video"])
    if vs.isOpened():
        width = int(vs.get(3))
        height = int(vs.get(4))
    else:
        sys.exit("Cannot open video")
else:
    vs = VideoStream(src=0).start()
    if vs.stream.isOpened():
        width = int(vs.stream.get(3))
        height = int(vs.stream.get(4))
    else:
        sys.exit("Cannot open stream")

fps = FPS().start()

# allow networktables, camera or video file to load
time.sleep(2.0)

print("Video source W:", width, " - H:", height)

# set some variables
lower = tuple(args["lower"]) # lower bounds of retro-reflective tape
upper = tuple(args["upper"]) # upper bounds of retro-reflective tape
centerX = 300         # center x-value of frame
lX = lY = rX = rY = 0

# keep looping
while True:
    # grab the current frame
    frame = vs.read()

    # handle the gram from VideoCapture or VideoStream
    frame = frame[1] if args.get("video", False) else frame

    # if we are viewing a video and did not grab a frame, we are at end of video
    if frame is None:
        break
    
    # update the FPS counter
    fps.update()

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
    min_right = 600
    left_contour = None
    right_contour = None
    
    for c in cnts:
        area = cv2.contourArea(c)
        # print("ML: ", min_left, " - MR: ", min_right)
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
        
    # interpolate the distance between the centers of the two nearest contours for 11.5 inches
    if lX > 0 and rX > 0:
        # print("cX: {:.2f}, lX: {:.2f}, rX: {:.2f}".format(centerX, lX, rX))
        try:
            distance = interp1d([lX, rX], [0, 11.5])
            distance_from_left = distance(centerX)
            offset_from_center = 5.75 - distance_from_left
        
            direction = "left" if offset_from_center > 0 else "right" if offset_from_center < 0 else "center"
            # print("The robot is {:.2f} inches to the {} of center.".format(abs(offset_from_center), direction))

            # send the data to the roborio
            livewindow.putNumber("Offset", offset_from_center)
        except (NameError, ValueError) as e:
            print("Error in interpolation",e)
            pass
    
    # draw center line
    cv2.line(resized, (centerX, 0), (centerX, height), (255, 255, 255), 1)
    
    # show the frame to our screen and increment the frame counter
    if args.get("show", True):
        cv2.imshow("Frame:", resized)

        # if the 'q' key is pressed, stop the loop
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break

# stop the timer and display FPS information
fps.stop()
print("Elasped time: {:.2f}".format(fps.elapsed()))
print("FPS: {:.2f}".format(fps.fps()))

# close the video stream
if not args.get("video", False):
    vs.stop()
else:
    vs.release()

# close all windows
cv2.destroyAllWindows()

