import time
import threading
import tkinter as tk
import time
import cv2
import boto3
from PIL import Image, ImageTk


class RequestThread(threading.Thread):

    def __init__(self, img_raw, client):
        super(RequestThread, self).__init__()
        self._stopping = threading.Event()
        self.request_res = None
        self.img_raw = img_raw
        self.img_after = img_raw.copy()
        small_raw = cv2.resize(img_raw, dsize=(313, 235))
        self.img_small = ImageTk.PhotoImage(Image.fromarray(small_raw))
        self.metrics = {}
        self._target = self.do_request
        self._args = (img_raw, client)

    def stop(self):
        self._stopping.set()

    def stopped(self):
        return self._stopping.is_set()

    def do_nothing(self, *args):
        time.sleep(1)
        self.stop()

    def do_request(self, img_raw, client):
        print('Doing request')
        start_time = time.time()
        response = client.detect_faces(
            Image={
                'Bytes': cv2.imencode('.jpg', img_raw)[1].tostring()
            },
            Attributes=['ALL']
        )
        self.metrics['request_time'] = time.time() - start_time
        self.request_res = response['FaceDetails']
        # post-process data
        for face in self.request_res:
            cv2.rectangle(self.img_after,
                          (int(640 * face["BoundingBox"]["Left"]), int(480 * face["BoundingBox"]["Top"])),
                          (int(640 * (face["BoundingBox"]["Left"] + face["BoundingBox"]["Width"])),
                           int(480 * (face["BoundingBox"]["Top"] + face["BoundingBox"]["Height"]))),
                          (0, 255, 0),
                          2)
            for landmark in face["Landmarks"]:
                cv2.circle(self.img_after,
                           (int(640 * landmark["X"]), int(480 * landmark["Y"])),
                           2,
                           (255, 255, 0),
                           1)
        self.img_after = ImageTk.PhotoImage(Image.fromarray(self.img_after))
        self.stop()


class App:

    def __init__(self, window, camera):
        self.window: tk.Tk = window
        self.window.title('Demo for facial feature extraction with AWS'
                          ' Rekognition')
        self.canvas = tk.Canvas(self.window, width=1193, height=1000,
                                background='white')
        self.canvas.bind('<Button-1>', self.mouse1_click)
        self.canvas.pack()
        self.camera: cv2.VideoCapture = camera
        self.last_frame = None
        self.last_frame_raw = None
        # request
        # 0=unsent, 1=sent, 2=received
        self.request_state = 0
        self.request_thread = None
        self.request_responses = []
        self.request_frames = []
        # misc
        self.extracted_faces = []
        self.colour_mappings = {
            'CALM': '#337ab7',
            'HAPPY': '#5cb85c',
            'SURPRISED': '#f0ad4e',
            'SAD': '#5bc0de',
            'CONFUSED': '#999999',
            'DISGUSTED': '#515151',
            'ANGRY': '#d9534f'
        }
        self.emotions = list(self.colour_mappings.keys())
        # 0=calm, 1=happy, 2=surprised, 3=sad, 4=confused, 5=disgusted
        # 6=angry
        self.info_mode = [True] * 7
        # AWS
        self.aws_client = boto3.client('rekognition')
        self.auto_loop()
        self.window.mainloop()

    def auto_loop(self):
        # setup
        self.canvas.delete('all')
        # button
        btn_colour = ['#5cb85c', '#a0a0a0', '#5cb85c'][self.request_state]
        btn_text = ['Start', 'Pause', 'Resume'][self.request_state]
        self.canvas.create_rectangle(10, 10, 210, 70, fill=btn_colour)
        self.canvas.create_text(110, 40, fill='black', font='Arial 20 bold',
                                text=btn_text)
        # statistic selection
        # start x=10 y=370
        # "max" selection
        for i, (emo, col) in enumerate(self.colour_mappings.items()):
            # ytop=370+30*i
            self.canvas.create_rectangle(10, 370 + 30 * i, 30, 390 + 30 * i,
                                         fill=col, outline='')
            self.canvas.create_text(40, 380 + 30 * i, text=emo,
                                    font='Arial 14', anchor='w')
        for i, v in enumerate(self.info_mode):
            if not v:
                continue
            self.canvas.create_oval(15, 375 + 30 * i,
                                    25, 385 + 30 * i,
                                    fill='white', outline='')
        # camera
        img = self.camera.read()[1]
        img = cv2.resize(img, dsize=(640, 480))
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.last_frame_raw = img
        if not self.request_state:
            self.last_frame = ImageTk.PhotoImage(Image.fromarray(img))
            self.canvas.create_image(220, 10, anchor='nw',
                                     image=self.last_frame)
        else:
            self.last_frame = ImageTk.PhotoImage(Image.fromarray(
                cv2.resize(self.last_frame_raw, dsize=(200, 150))))
        # monitor request
        if self.request_state:
            self.canvas.create_image(10, 80, image=self.last_frame,
                                     anchor='nw')
            if self.request_thread.stopped():
                # finished one frame
                self.request_responses.insert(0,
                                              (self.request_thread.request_res,
                                               self.request_thread.img_raw,
                                               self.request_thread.img_after,
                                               self.request_thread.img_small,
                                               self.request_thread.metrics))
                # keep the last few finished frames
                self.request_responses = self.request_responses[:3]
                # refresh face data so it is up to date
                self.refresh_face_data()
                # start another request
                if self.request_state == 1:
                    self.request_thread = RequestThread(
                        self.last_frame_raw.copy(),
                        self.aws_client)
                    self.request_thread.start()

            # if can, show processed frames
            # raw, after, small -> r, a, s
            for i, (_, r, a, s, _) in enumerate(self.request_responses):
                if not i:  # == 0
                    # main picture frame size WxH 640x480 top left 220,10
                    self.canvas.create_image(220, 10, image=a, anchor='nw')
                # else:
                #    # old pictures, top left x=870 y=10+245(i-1)
                #    # height 235 width 313
                #    self.canvas.create_image(870, 10+245*(i-1), image=s, anchor='nw')

            # metrics
            if self.request_responses:
                metrics = [d[4]['request_time'] for d in self.request_responses
                           ]
                avg_time = round(sum(metrics) / len(metrics), 2)
                self.canvas.create_text(10, 240, text='Mean request time:\n'
                                                      f'{avg_time} seconds\nFaces:\n'
                                                      f'{len(self.request_responses[0][0])}',
                                        font='Arial 16', anchor='nw')

        self.extracted_faces.clear()
        if self.request_responses:
            if not self.extracted_faces:
                self.refresh_face_data()
            self.canvas.create_text(220, 500, text='Found faces and info',
                                    font='Arial 20', anchor='nw')
            dat = self.request_responses[0][0]
            for i, face in enumerate(dat):
                self.canvas.create_image(220, 550 + 60 * i,
                                         image=self.extracted_faces[i],
                                         anchor='nw')
                # emotions
                emos = face['Emotions']
                # summarise emotions
                summarised = {}
                for e in emos:
                    summarised[e['Type']] = e['Confidence']
                cnt = -1
                for ind, disp in enumerate(self.info_mode):
                    if not disp:
                        continue
                    cnt += 1
                    emo = self.emotions[ind]
                    prob = summarised[emo]
                    col = self.colour_mappings[emo]
                    # start X 276->356, spacing after 4 each
                    # X=276+84*cnt
                    self.canvas.create_rectangle(276 + 84 * cnt,
                                                 550 + 60 * i,
                                                 276 + 84 * cnt +
                                                 80 / 100 * prob,
                                                 560 + 60 * i,
                                                 fill=col,
                                                 outline='')
                    self.canvas.create_rectangle(276 + 84 * cnt,
                                                 550 + 60 * i,
                                                 356 + 84 * cnt,
                                                 560 + 60 * i,
                                                 fill='',
                                                 outline='black')
                    self.canvas.create_text(316 + 84 * cnt, 565 + 60 * i,
                                            text=f'{int(prob)}%',
                                            anchor='n', font='Arial 10')
                    self.canvas.create_text(316 + 84 * cnt, 580 + 60 * i,
                                            text=emo,
                                            anchor='n', font='Arial 10')

                    # set recurring event
        self.window.after(15, self.auto_loop)

    def mouse1_click(self, event):
        # START / STOP / RESET button
        if 10 <= event.x <= 210 and 10 <= event.y <= 70:
            if not self.request_state:  # == 0
                self.request_state = 1
                self.request_thread = RequestThread(self.last_frame_raw.copy(),
                                                    self.aws_client)
                self.request_responses.clear()
                self.request_thread.start()
            elif self.request_state == 1:
                self.request_state = 2
            else:
                self.request_state = 1
        # INFO_MODE SELECTION buttons
        if 10 <= event.x <= 30:
            sel = (event.y - 370) // 30
            off = (event.y - 370) % 30
            if off <= 19 and 0 <= sel <= 7:
                self.info_mode[sel] = not self.info_mode[sel]

    def refresh_face_data(self):
        self.extracted_faces.clear()
        dat = self.request_responses[0][0]
        ir = self.request_responses[0][1]  # original numpy array image
        for i, face in enumerate(dat):
            le = int(640 * face['BoundingBox']['Left'])  # left
            to = int(480 * face['BoundingBox']['Top'])  # top
            ri = le + int(640 * face['BoundingBox']['Width'])  # right
            bo = to + int(480 * face['BoundingBox']['Height'])  # bottom

            if (to < 0):
                to = 0
            if (le < 0):
                le = 0
            ext = ir[to:bo, le:ri]
            ext = cv2.resize(ext, dsize=(50, 50))
            self.extracted_faces.append(ImageTk.PhotoImage(Image.fromarray(ext)))


App(tk.Tk(), cv2.VideoCapture(0))