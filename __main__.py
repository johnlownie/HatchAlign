from imutils.video import VideoStream
from scipy.interpolate import interp1d
import numpy as np
import argparse
import imutils
import nt as nt
import sys
import requests
import cv2
import time

# parse arguments
ap = argparse.ArgumentParser()
ap.add_argument("-r", "--roborio", nargs="?", default="roborio-5024-frc.local", help="address to the roborio")
ap.add_argument("-l", "--lower", nargs="+", type=int, default=[90, 224, 76], help="HSV lower bounds")
ap.add_argument("-u", "--upper", nargs="+", type=int, default=[106, 255, 255], help="HSV upper bounds")
ap.add_argument("-v", "--video", help="path to the video file")
args = vars(ap.parse_args())

# check for roborio
try:
	# requests.get("http://" + args["roborio"] + ":1181")
	requests.get("http://192.168.24.80")
except:
	print("FATAL! Roborio not found")
	exit(1)

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

# allow the camera or video file to load
time.sleep(2.0)

# set some variables
left   = interp1d([1, width / 2], [-1, 0])
right  = interp1d([width / 2 + 1, width], [0, 1])
lower = tuple(args["lower"]) # lower bounds of retro-reflective tape
upper = tuple(args["upper"]) # upper bounds of retro-reflective tape

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
    ratio = frame.shape[0] / float(resized.shape[0])

    # construct a mask for the color "green", then erode and dilate
    mask = cv2.inRange(hsv, (20, 60, 50), (37, 250, 250))
    mask = cv2.erode(mask, None, iterations=2)
    mask = cv2.dilate(mask, None, iterations=2)

    # find contours in the mask and initialize the current (x, y) center of the ball
    # cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    # cnts = imutils.grab_contours(cnts)
    
    # for c in cnts:
    #     M = cv2.moments(c)
    #     cX = int((M["m10"] / M["m00"]) * ratio)
    #     cY = int((M["m01"] / M["m00"]) * ratio)
    
    #     (xg, yg, wg, hg) = cv2.boundingRect(c)
    #     if wg > 10 and hg > 10:
    #         # draw the circle and centroid on the frame then update tracking points
    #         cv2.rectangle(frame, (xg, yg), (xg + wg, yg + hg), (0, 255, 0), 2)

    # show the frame to our screen and increment the frame counter
    cv2.imshow("Frame:", mask)

    # if the 'q' key is pressed, stop the loop
    key = cv2.waitKey(1) & 0xFF
    if key == ord("q"):
        break

# close the video stream
if not args.get("video", False):
    vs.stop()
else:
    vs.release()

# close all windows
cv2.destroyAllWindows()