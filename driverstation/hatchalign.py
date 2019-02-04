#!/usr/env/python3

# import libraries
import numpy as np
import cv2
import urllib.request

stream = urllib.request.urlopen('http://localhost:6050/frame.mjpg')

bytes = ''
while True:
    bytes += stream.read(1024)
    a = bytes.find('\xff\xd8')
    b = bytes.find('\xff\xd9')
    if a != -1 and b != -1:
        jpg = bytes[a : b + 2]
        bytes = bytes[b + 2:]

        image = cv2.imdecode(np.fromstring(jpg, dtype=np.uint8), cv2.CV_LOAD_IMAGE_COLOR)

        cv2.imshow('Image', image)

        if cv2.waitKey(1) == 27:
            exit(0)

