
import argparse
import datetime
import imutils
import math
import cv2
import numpy as np
import tkinter as tk
from PIL import ImageTk, Image


down = 0
up = 0

def distance (x,y,p1,p2):
    a = (p2[1] - p1[1])
    b = (p1[0] - p2[0])
    c = (p1[1] * p2[0] - p1[0] * p2[1])
    sqrt_val = a ** 2 + b ** 2
    val = abs((a * x + b * y + c) / math.sqrt(sqrt_val))
    return val


def intersection(x, y, p1,p2, pre_coords,margin):
    val = distance(x, y, p1,p2)
    if len(pre_coords)>0:
        pre_val = distance(pre_coords[-1][0] , pre_coords[-1][1], p1,p2)
        if pre_val < margin:
            return False

    if(val< margin):
        return True
    else:
        return False

# going down return true, up return false, none means still
def direction(current_cord, pre_coords):
    if len(pre_coords):
        y_cord = [c[1] for c in pre_coords]
        dir = current_cord[1] - np.mean(y_cord)
        if len(pre_coords)> 15:
            cord = [c[1] for c in pre_coords[-15:]]
            if np.mean(cord) - pre_coords[-16][1] < 0 and dir > 0:
                return False
            elif np.mean(cord) - pre_coords[-16][1] > 0 and dir < 0:
                return True

        if dir > 0:
            return True
        elif dir <0:
            return False
    return None


def isLeft(a, b, c):
    return ((b[0] - a[0])*(c[1]- a[1]) - (b[1] - a[1])*(c[0] - a[0])) > 0;
#
# def inputLineVal():
#     default = [(400,0), (800,450),(350, 0), (750, 450)]
#     try:
#         print("Enter the position of blue line:")
#         print("Enter the coordinate of the first point:")
#
#         blue_cord1_x = int(input("first_point x value (default: 400):  "))
#
#         print("Enter the coordinate of the second point :")
#         blue_cord2_x = int(input("second_point x value(default: 800):  "))
#
#         print("Enter the position of red line:")
#         print("Enter the coordinate of the first point:")
#
#         red_cord1_x = int(input("first_point x value(default: 350):  "))
#
#         print("Enter the coordinate of the second point:")
#         red_cord2_x = int(input("second_point x value(default: 750):  "))
#
#     except:
#         return default
#
#     if blue_cord1_x > 800 or blue_cord2_x > 800 or red_cord1_x > 800 or red_cord2_x > 800:
#         return default
#
#     return [(blue_cord1_x, 0), (blue_cord2_x, 450), (red_cord1_x, 0), (red_cord2_x, 450)]

def inputMarginOfError():
    default = 15
    try:
        margin = int(input("Enter the margin of error for crossing the line(default: 15)"))
    except:
        return default
    else:
        return margin

if __name__ == "__main__":
    camera = cv2.VideoCapture("test2.mp4")
    firstFrame = None
    pre_cords = []
    # loop over the frames of the video
    # lineVal = inputLineVal()
    # margin = inputMarginOfError()
    count = 0
    while True:
        # grab the current frame and initialize the occupied/unoccupied
        # text
        (grabbed, frame) = camera.read()
        # if the frame could not be grabbed, then we have reached the end
        # of the video
        if not grabbed:
            break

        # resize the frame, convert it to grayscale, and blur it
        frame = imutils.resize(frame, width=800)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        # if the first frame is None, initialize it
        if firstFrame is None:
            firstFrame = gray
            continue

        frameDelta = cv2.absdiff(firstFrame, gray)
        thresh = cv2.threshold(frameDelta, 25, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)
        cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]

        cv2.line(frame, (100,0),(200,450) ,(250, 0, 1), 2)  # blue line

        # cv2.line(frame, lineVal[2], lineVal[3], (0, 0, 255), 2)  # red line

        for c in cnts:
            if cv2.contourArea(c) < 12000:
                continue
            (x, y, w, h) = cv2.boundingRect(c)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            rectagleCenterPont = ((x + x + w) // 2, (y + y + h) // 2)
            cv2.circle(frame, rectagleCenterPont, 1, (0, 0, 255), 5)


            ifBlueLine= intersection((x + x + w) // 2, (y + y + h) // 2, (100,0),(200,450), pre_cords,15)
            # ifRedLine= intersection((x + x + w) // 2, (y + y + h) // 2,lineVal[2], lineVal[3], pre_cords,15)

            isGoingDown = direction(rectagleCenterPont, pre_cords)

            # print(distance((x + x + w) // 2, (y + y + h) // 2, lineVal[2], lineVal[3]), "     ifRed: " ,ifRedLine)



            if (ifBlueLine and not isLeft(((x + x + w) // 2, (y + y + h) // 2),(100,0),(200,450) )) :
                print(isGoingDown)

                down +=1
                # print(distance((x + x + w) // 2, (y + y + h) // 2, lineVal[0], lineVal[1]))
                # print(rectagleCenterPont)
                input("")


            if (ifBlueLine and  isLeft(((x + x + w) // 2, (y + y + h) // 2),(100,0),(200,450))) :
                print(isGoingDown)
                up +=1
                input("")
                # print(distance((x + x + w) // 2, (y + y + h) // 2, lineVal[2], lineVal[3]))
                # print(rectagleCenterPont)


           # if(ifRedLine):
               # print(distance((x + x + w) // 2, (y + y + h) // 2, lineVal[2], lineVal[3]), "     ifRed: " ,ifRedLine, "      isGoingDown: ", isGoingDown, "          isLeft", isLeft(((x + x + w) // 2, (y + y + h) // 2), lineVal[2],lineVal[3]))
            pre_cords.append(rectagleCenterPont)

        #     # draw the text and timestamp on the frame
        #     # show the frame and record if the user presses a key
            #cv2.imshow("Thresh", thresh)
            # cv2.imshow("Frame Delta", frameDelta)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        cv2.putText(frame, "Up: {}".format(str(up)), (10, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        cv2.putText(frame, "Down: {}".format(str(down)), (10, 70),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        cv2.putText(frame, datetime.datetime.now().strftime("%A %d %B %Y %I:%M:%S%p"),
                    (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)

        cv2.imshow("Security Feed", frame)


    # cleanup the camera and close any open windows
    camera.release()
    cv2.destroyAllWindows()



