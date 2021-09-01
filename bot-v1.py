from PIL import Image
import pyautogui
import cv2
import numpy as np
import mss
import mss.tools
from time import sleep, time
from statistics import mean
import os
from multiprocessing import Process
from random import randint

os.chdir(os.path.dirname(os.path.abspath(__file__)))

def FindPositions(needle_img_path, haystack_img_path, threshold=0.5, debug_mode=None):
    haystack_img = cv2.imread(haystack_img_path, cv2.IMREAD_UNCHANGED)
    needle_img = cv2.imread(needle_img_path, cv2.IMREAD_UNCHANGED)
    needle_w = needle_img.shape[1]
    needle_h = needle_img.shape[0]

    method = cv2.TM_CCOEFF_NORMED
    result = cv2.matchTemplate(haystack_img, needle_img, method)

    locations = np.where(result >= threshold)
    locations = list(zip(*locations[::-1]))

    rectangles = []
    for loc in locations:
        rect = [int(loc[0]), int(loc[1]), needle_w, needle_h]
        rectangles.append(rect)
        rectangles.append(rect)

    rectangles, weights = cv2.groupRectangles(rectangles, groupThreshold=1, eps=0.5)
    points = []
    if len(rectangles):
        line_color = (0, 255, 0)
        line_type = cv2.LINE_4
        marker_color = (255, 0, 255)
        marker_type = cv2.MARKER_CROSS

        for (x, y, w, h) in rectangles:
            center_x = x + int(w / 2)
            center_y = y + int(h / 2)
            points.append((center_x, center_y))

            if debug_mode == 'rectangles':
                top_left = (x, y)
                bottom_right = (x + w, y + h)
                cv2.rectangle(haystack_img, top_left, bottom_right, color=line_color,
                             lineType=line_type, thickness=2)
            elif debug_mode == 'points':
                cv2.drawMarker(haystack_img, (center_x, center_y),
                              color=marker_color, markerType=marker_type,
                              markerSize=40, thickness=2)

        if debug_mode:
            cv2.imshow('Matches', haystack_img)
            cv2.waitKey()

    return points

def FindPixel(img_path='templates/test.png', pixel=(255, 232, 105), n=35):
    img = Image.open(img_path)
    w, h = img.size
    px = img.load()

    points = [[], []]
    for i in range(0, w, n):
        for j in range(0, h, n):
            if px[i, j] == pixel:
                points[0].append(i)
                points[1].append(j)

    return points

class GameObjects():
    def __init__(self):
        self.map = ((1725, 885), (1900, 1060))
        self.offmap_color = (185, 185, 185)
        self.enemycolor = (241, 78, 84)
        self.allicolor = (0, 178, 225)
        self.food1_color = (252, 229, 104)
        self.food2_color = (252, 118, 119)
        self.food3_color = (118, 141, 252)

class Bot():
    def __init__(self):
        self.analyze_rect=[(260, 25),(1665, 960)]
        self.hp = 100
        self.exp = 0
        self.status=[]
        self.GameObjects = GameObjects()

    def DoScreenshot(self, output="screen.png"):
        with mss.mss() as sct:
            monitor = {"top": 25, "left": 260, "width": 1405, "height": 935}
            sct_img = sct.grab(monitor)
            mss.tools.to_png(sct_img.rgb, sct_img.size, output=output)
        return output

    def SetCursor(self, x, y):
        pyautogui.moveTo(x, y)

    def CursorController(self):
        while True:
            image = self.DoScreenshot(output="cursor_screen")
            x, y = FindPixel(img_path=image, n=10)
            if x and y:
                self.SetCursor(self.analyze_rect[0][0]+x[0], self.analyze_rect[0][1]+y[0])

    def KeyboardController(self):
        key_x = ''
        key_y = ''
        caution = 0
        key_x_safe = ''
        key_y_safe = ''
        x_time = 0
        y_time = 0
        x_start = 0
        y_start = 0

        while True:
            image = self.DoScreenshot(output="keyboard_screen")
            key_x_new = ''
            key_y_new = ''
            x, y = FindPixel(img_path=image, pixel=self.GameObjects.enemycolor, n=20    )

            if x and y:
                caution = 3
                x = mean(x)
                y = mean(y)

                if x < 730:
                    key_x_new = "d"
                elif x > 730:
                    key_x_new = "a"

                if y < 500:
                    key_y_new = "s"
                elif y > 500:
                    key_y_new = "w"
            else:
                caution -= 1

            if caution >= 2:
                pyautogui.keyUp(key_x_safe)
                pyautogui.keyUp(key_y_safe)
                x_time += 1
                y_time += 1

                if(key_x != key_x_new):
                    pyautogui.keyUp(key_x)
                    pyautogui.keyDown(key_x_new)
                    key_x = key_x_new

                if(key_y != key_y_new):
                    pyautogui.keyUp(key_y)
                    pyautogui.keyDown(key_y_new)
                    key_y = key_y_new
            else:
                time_now = time()
                if x_start + x_time > time_now:
                    pyautogui.keyDown(key_x_safe)
                else:
                    pyautogui.keyUp(key_x_safe)
                    x_start = time_now
                    rand_x = randint(0, 1)
                    x_time = randint(2, 10)
                    if rand_x == 0:
                        key_x_safe = "w"
                    else:
                        key_x_safe = "s"

                if y_start + y_time > time_now:
                    pyautogui.keyDown(key_y_safe)
                else:
                    pyautogui.keyUp(key_y_safe)
                    y_start = time_now
                    rand_y = randint(0, 1)
                    y_time = randint(2, 10)
                    if rand_y == 0:
                        key_y_safe = "a"
                    else:
                        key_y_safe = "d"

def Play():
    bot = Bot()

    for i in range(10, 0, -1):
        print("Starting: "+str(i))
        sleep(1)

    print("Init processes")
    Keyboard_module = Process(target=bot.KeyboardController)
    Cursor_module = Process(target=bot.CursorController)
    print("Start processes")
    Keyboard_module.start()
    Cursor_module.start()

if __name__=="__main__":
    Play()