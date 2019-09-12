import datetime
import imutils
import math
import cv2
import numpy as np
import tkinter as tk
from PIL import ImageTk, Image
import threading
import tkinter.messagebox

class App:

    def __init__(self, window):
        self.down = 0
        self.up = 0
        self.pause = False
        self.delay = 2
        self.imageOnCanvas = None
        self.stopEvent = threading.Event()
        self.camera = self.camera = cv2.VideoCapture("test2.mp4")
        self.ctrlButtonText = ["start", "pause", "resumed"]
        self.videoStatus =0
        self.afterId = None
        self.frame = None
        self.down = 0
        self.up = 0
        self.currentFrame = None
        self.firstFrame = None
        self.pre_cords = []
        self.input = None
        self.marginError = 20
        self.drawRed = None

        self.lastShape = None
        self.clickNumber = 0
        self.red_x1 = 350
        self.red_y1 = 0

        self.red_x2 = 750
        self.red_y2 = 450

        self.blue_x1 = 400
        self.blue_y1 = 0

        self.blue_x2 = 800
        self.blue_y2 = 450

        self.window:  tk.Tk = window
        self.window.geometry("1200x1200")
        self.window.title ("People Counting")
        self.canvas = tk.Canvas(self.window, width = 800, height = 450, background = "white")
        self.canvas.pack(pady=30)
        (grabbed, frame) = self.camera.read()
        if grabbed:
            self.currentFrame = imutils.resize(frame, width=800)
            self.displayFrame = ImageTk.PhotoImage(Image.fromarray(self.currentFrame))
            self.initialFrame = self.displayFrame
            self.canvas.create_image(0, 0, image=self.displayFrame, anchor='nw')

        label = tk.Label(self.window, text="Enter margin of error: ")
        label.pack()

        self.input = tk.Entry(window)
        self.btn = tk.Button(self.window, text=self.ctrlButtonText[self.videoStatus], width=20, height =2, command = self.onClick)
        self.input.pack(pady = 10)
        self.btn.pack()

        row = tk.Frame(self.window)
        row.pack(fill=tk.X, pady=5)
        self.btnRedLine = tk.Button(row, text="Draw Red",width=20, height =2 , command = self.startDrawingRed)
        self.btnBlueLine = tk.Button(row, text="Draw Blue",width=20, height =2,command = self.startDrawingBlue )
        self.clearbtn = tk.Button(row, text="Redraw lines", width=20, height =2,command = self.clearSetting)


        self.btnRedLine.pack(side = tk.LEFT,padx = 5)

        self.btnBlueLine.pack(side = tk.LEFT)
        self.clearbtn.pack(side = tk.RIGHT, padx =100)
        self.window.mainloop()



    def playVideo(self):
        # self.camera = cv2.VideoCapture("test2.mp4")
        (grabbed, frame) = self.camera.read()
        if grabbed:
            self.currentFrame = imutils.resize(frame, width=800)
            shouldPause = self.processFrame()
            self.displayFrame = ImageTk.PhotoImage(Image.fromarray(self.currentFrame))
            if self.imageOnCanvas is None:
                self.canvas.create_image(0,0,image = self.displayFrame, anchor ='nw')
            else:
                self.canvas.itemconfig(self.imageOnCanvas, image = self.displayFrame)

            if shouldPause:
                if self.afterId is not None:
                    self.window.after_cancel(self.afterId)
                self.videoStatus = 2
                self.updateButton()


            else:
                self.afterId = self.window.after(self.delay, self.playVideo)

        else:
            self.videoStatus = 0
            self.updateButton()

    def onClick(self):
        if (self.videoStatus == 0):
            isDefault = True
            try:
                inputMargin = int(self.input.get())
                if int(inputMargin) >200:
                    isDefault = tkinter.messagebox.askyesno("Wrong input value", "Input must less than 100, do you want to "
                                                                                 "run the program with the default margin error value? ")
                else:
                    self.marginError = int(inputMargin)

            except ValueError:
                isDefault = tkinter.messagebox.askyesno("Wrong input value" , "Input must be integer, do you want to "
                                                                    "run the program with the default margin error value? ")
            print(isDefault)
            if isDefault is False:
                return
            else:
                self.marginError = 15

        if self.videoStatus == 0: # if start
            self.up = 0
            self.down = 0
            self.camera = cv2.VideoCapture("test2.mp4")
            self.videoStatus = 1
            self.playVideo()


        elif self.videoStatus ==1: # if pause
            self.window.after_cancel(self.afterId)
            self.videoStatus = 2

        elif self.videoStatus ==2: # resumed
            self.videoStatus =1
            self.playVideo()

        self.updateButton()


    def processFrame(self):
        shouldPause = False
        gray = cv2.cvtColor(self.currentFrame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        if self.firstFrame is not None:

            cv2.line(self.currentFrame, (self.red_x1,self.red_y1), (self.red_x2,self.red_y2), (250, 0, 1), 2)  # blue line

            cv2.line(self.currentFrame,(self.blue_x1,self.blue_y1), (self.blue_x2,self.blue_y2) , (0, 0, 255), 2)  # red line

            frameDelta = cv2.absdiff(self.firstFrame, gray)
            thresh = cv2.threshold(frameDelta, 25, 255, cv2.THRESH_BINARY)[1]
            thresh = cv2.dilate(thresh, None, iterations=2)
            cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]

            for c in cnts:
                if cv2.contourArea(c) < 12000:
                    continue
                (x, y, w, h) = cv2.boundingRect(c)
                cv2.rectangle(self.currentFrame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                rectagleCenterPont = ((x + x + w) // 2, (y + y + h) // 2)
                cv2.circle(self.currentFrame, rectagleCenterPont, 1, (0, 0, 255), 5)
                ifBlueLine = self.intersection((x + x + w) // 2, (y + y + h) // 2, (self.blue_x1,self.blue_y1), (self.blue_x2,self.blue_y2), self.pre_cords, self.marginError)
                ifRedLine = self.intersection((x + x + w) // 2, (y + y + h) // 2,(self.red_x1,self.red_y1), (self.red_x2,self.red_y2), self.pre_cords, self.marginError)
                isGoingDown = self.direction(rectagleCenterPont, self.pre_cords)

                if (ifBlueLine and isGoingDown) :
                    shouldPause = True
                    self.down += 1

                if (ifRedLine and not isGoingDown) :

                    shouldPause = True
                    self.up +=1

                self.pre_cords.append(rectagleCenterPont)

            cv2.putText(self.currentFrame, "Up: {}".format(str(self.up)), (10, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
            cv2.putText(self.currentFrame, "Down: {}".format(str(self.down)), (10, 70),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
            cv2.putText(self.currentFrame, datetime.datetime.now().strftime("%A %d %B %Y %I:%M:%S%p"),
                        (10, self.currentFrame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)
        else:
            self.firstFrame = gray
        return shouldPause

    def updateButton(self):
        self.btn['text'] = self.ctrlButtonText[self.videoStatus]

    def distance(self, x, y, p1, p2):
        a = (p2[1] - p1[1])
        b = (p1[0] - p2[0])
        c = (p1[1] * p2[0] - p1[0] * p2[1])
        sqrt_val = a ** 2 + b ** 2
        val = abs((a * x + b * y + c) / math.sqrt(sqrt_val))
        return val

    def intersection(self, x, y, p1, p2, pre_coords, margin):
        val = self.distance(x, y, p1, p2)
        if len(pre_coords) > 0:
            pre_val = self.distance(pre_coords[-1][0], pre_coords[-1][1], p1, p2)
            if pre_val < margin:
                return False

        if (val < margin):
            return True
        else:
            return False

    # going down return true, up return false, none means still
    def direction(self, current_cord, pre_coords):
        if len(pre_coords):
            y_cord = [c[1] for c in pre_coords]
            dir = current_cord[1] - np.mean(y_cord)
            if len(pre_coords) > 15:
                cord = [c[1] for c in pre_coords[-15:]]
                if np.mean(cord) - pre_coords[-16][1] < 0 and dir > 0:
                    return False
                elif np.mean(cord) - pre_coords[-16][1] > 0 and dir < 0:
                    return True
            if dir > 0:
                return True
            elif dir < 0:
                return False
        return None

    def __del__(self):
        print("end program")
        if self.camera is not None:
            if self.camera.isOpened():
                self.camera.release()

    def onLeftButtonDown(self, event):
        if self.drawRed is True:
            self.red_x1 = event.x
            self.red_y1 = event.y
        else:
            self.blue_x1 = event.x
            self.blue_y1 = event.y

    def onLeftButtonUp(self, event):

        try:
            self.canvas.delete(self.lastShape)
        except:
            pass
        if self.drawRed is True:
            self.red_x2 = event.x
            self.red_y2 = event.y
            self.red = self.canvas.create_line(self.red_x1, self.red_y1, self.red_x2, self.red_y2, fill='red')

        else:
            self.blue_x2 = event.x
            self.blue_y2 = event.y
            self.blue = self.canvas.create_line(self.blue_x1, self.blue_y1, self.blue_x2, self.blue_y2, fill='blue')

        msg = "Are you sure to set this line as "
        if self.drawRed:
            msg += "red line?"
        else:
            msg += "blue line?"

        isSure = tkinter.messagebox.askyesno("set Line Value", msg)
        if isSure:
            if self.drawRed:
                self.btnRedLine['state'] = 'disabled'
            else:
                self.btnBlueLine['state'] = 'disabled'

            self.unbindDrawing()
        else:
            if self.drawRed:
                self.canvas.delete(self.red)
            else:
                self.canvas.delete(self.blue)
        print("red: ", self.red_x1, self.red_x2)
        print("blue: ", self.blue_x1, self.blue_x2)


    def onLeftButtonMove(self, event):
        try:
            self.canvas.delete(self.lastShape)
        except:
            pass
        if self.drawRed is True:
            self.lastShape = self.canvas.create_line(self.red_x1, self.red_y1, event.x, event.y, fill="red")
        else:
            self.lastShape = self.canvas.create_line(self.blue_x1, self.blue_y1, event.x, event.y, fill="blue")


    def onRightButtonClick(self, event):
        try:
            if self.drawRed is True:
                self.canvas.delete(self.red)
            else:
                self.canvas.delete(self.blue)
        except:
            return

    def bindDrawing(self):
        self.bindDown = self.canvas.bind('<Button-1>', self.onLeftButtonDown)
        self.bindUp = self.canvas.bind('<ButtonRelease-1>', self.onLeftButtonUp)
        self.bindMove = self.canvas.bind('<B1-Motion>', self.onLeftButtonMove)
        self.bindDelete = self.canvas.bind('<Button-3>', self.onRightButtonClick)

    def unbindDrawing(self):
        self.canvas.unbind('<Button-1>',self.bindDown)
        self.canvas.unbind('<ButtonRelease-1>', self.bindUp)
        self.canvas.unbind('<B1-Motion>', self.bindMove)
        self.canvas.unbind('<Button-3>', self.bindDelete)

    def startDrawingRed(self):
        self.drawRed = True
        self.bindDrawing()

    def startDrawingBlue(self):
        self.drawRed = False
        self.bindDrawing()

    def clearSetting(self):
        if self.videoStatus == 0:
            self.btnBlueLine['state'] = tk.NORMAL
            self.btnRedLine['state'] = tk.NORMAL
            if self.firstFrame is not None:
                self.canvas.delete('all')
                self.canvas.create_image(0, 0, image=self.initialFrame, anchor='nw')
            else:
                try:
                    self.canvas.delete(self.blue)
                    self.canvas.delete(self.red)
                except:
                    pass

App(tk.Tk())

