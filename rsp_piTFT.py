# -------------------------------------------------------
# Final Project
# Name(NetID): Anzhou Li(al2627), Jiaying Zhang(jz2354)
# Date: December 14, 2024
# Project Name: Gesture RSP Game
# -------------------------------------------------------

import math
import os
import subprocess
import sys
import time
import RPi.GPIO as GPIO
import cv2
import mediapipe
import numpy as np
import pygame
from random import randint
from enum import Enum

# ----------------------------------------
# Basic Setting
# ----------------------------------------

# Gesture Parameter
class SelectionOption(Enum):
    ROCK = 1
    PAPER = 3
    SCISSOR = 2

# Page Parameter
MAIN_PAGE = 0
ROCK_PAPER_SCISSOR_PAGE = 1

# Define color
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
ORANGE = (255, 165, 0)
YELLOW = (255, 255, 0)

# Set piTFT & touchscreen environment variables
os.putenv('SDL_VIDEODRIVER', 'fbcon')
os.putenv('SDL_FBDEV', '/dev/fb0')
os.putenv('SDL_MOUSEDRV', 'dummy')
os.putenv('SDL_MOUSEDEV', '/dev/null')
os.putenv('DISPLAY',' ')

# Initialize Pygame
pygame.init()

handsModule = mediapipe.solutions.hands
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FPS, 5)
not_quit = 1

# Set screen
SCREEN_WIDTH = 320
SCREEN_HEIGHT = 240
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.mouse.set_visible(False)  # hide mouse

# Load main page background
background1 = pygame.image.load("/home/pi/Final_project/background1.jpg")  
background1 = pygame.transform.scale(background1, (SCREEN_WIDTH, SCREEN_HEIGHT))
# Load game page background
background2 = pygame.image.load("/home/pi/Final_project/background4.jpg")  
background2 = pygame.transform.scale(background2, (SCREEN_WIDTH, SCREEN_HEIGHT))  

# Load gesture images
rock = pygame.image.load("/home/pi/Final_project/rock.png")
rock = pygame.transform.scale(rock, (140, 116))
paper = pygame.image.load("/home/pi/Final_project/paper.png")
paper = pygame.transform.scale(paper, (112, 128))
scissor = pygame.image.load("/home/pi/Final_project/scissor.png")
scissor = pygame.transform.scale(scissor, (140, 140))

# Set fonts
font1 = pygame.font.Font(None, 40)

# Set text position
Welcome_text_pos = (45,100)
left_palyer_score_pos = (50,170)
right_palyer_score_pos = (250,50)
left_player_gesture_pos = (10,20)
right_player_gesture_pos = (185,80)
result_pos = (120,10)

# Set Gesture Text
Welcome_text = font1.render('Thumb-up to start', True, BLACK)
Left_win_text = font1.render('Left win', True, WHITE)
Right_win_text = font1.render('Right win', True, WHITE)
Draw_text = font1.render('Draw', True, WHITE)

# ----------------------------------------
# Set up GPIO 
# ----------------------------------------

# Set physical button to quit
BAILOUT_BUTTON_PIN = 17
GPIO.setmode(GPIO.BCM)
GPIO.setup(BAILOUT_BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Define callback function
def bailout_callback(channel):
    global not_quit
    print("physical button pressed, exiting program")
    cv2.destroyAllWindows()
    pygame.quit()
    cap.release()
    not_quit = 0
    GPIO.cleanup()
    subprocess.call(['sudo shutdown -h now'], shell=True)

GPIO.add_event_detect(BAILOUT_BUTTON_PIN, GPIO.FALLING, callback=bailout_callback, bouncetime=300)

# Set round button
ROUND_BUTTON_PIN = 22
GPIO.setmode(GPIO.BCM)
GPIO.setup(ROUND_BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Define callback function
def round_change(channel):
    global is_change
    print("new round!")
    is_change = 1
    time.sleep(2)

GPIO.add_event_detect(ROUND_BUTTON_PIN, GPIO.FALLING, callback=round_change, bouncetime=300)

# Set vibrators
LEFT_VIBRATOR_PIN = 19
GPIO.setmode(GPIO.BCM)
GPIO.setup(LEFT_VIBRATOR_PIN, GPIO.OUT)
RIGHT_VIBRATOR_PIN = 16
GPIO.setmode(GPIO.BCM)
GPIO.setup(RIGHT_VIBRATOR_PIN, GPIO.OUT)

pwm1 = GPIO.PWM(LEFT_VIBRATOR_PIN, 100)  # f = 100Hz
pwm1.start(0)  # Duty cycle = 0
pwm2 = GPIO.PWM(RIGHT_VIBRATOR_PIN, 100)  # f = 100Hz
pwm2.start(0)  # Duty cycle = 0

# ----------------------------------------
# Functions
# ----------------------------------------

# Draw the main page
def draw_main_page():
    screen.blit(background1, (0, 0))
    screen.blit(Welcome_text, Welcome_text_pos)
    pygame.display.flip()
    point_counter = [0, 0]
    return point_counter

# Draw the game page
def draw_rps_page(num, users, result_rsp, point_counter):
    global is_change
    screen.blit(background2, (0, 0))

    # Print Gestures
    print(num)
    if num == 2 and len(users) == num and is_change == 1:
        for i in range(num):
            if users[i] == SelectionOption.ROCK.value:
                screen.blit(rock, left_player_gesture_pos if i == 0 else right_player_gesture_pos)

            elif users[i] == SelectionOption.SCISSOR.value:
                screen.blit(scissor, left_player_gesture_pos if i == 0 else right_player_gesture_pos)

            elif users[i] == SelectionOption.PAPER.value:
                screen.blit(paper, left_player_gesture_pos if i == 0 else right_player_gesture_pos)

        # Print Result
        if result_rsp == 0: # left win
            if is_change == 1:
                point_counter[0] += 1
            screen.blit(Left_win_text, result_pos)
        elif result_rsp == 1: # right win
            if is_change == 1:
                point_counter[1] += 1
            screen.blit(Right_win_text, result_pos)
        elif result_rsp == 2: # draw
            screen.blit(Draw_text, result_pos)
    
    # Print Score
    for i in range(2):
        Score_text = font1.render(f'{point_counter[i]}', True, YELLOW)
        screen.blit(Score_text, left_palyer_score_pos if i == 0 else right_palyer_score_pos)

    return point_counter

# control the vibration motors
def vibration(result_rsp):
    global is_change
    if result_rsp == 0: 
        if is_change == 1:
            pwm1.ChangeDutyCycle(100)
            time.sleep(2)
            pwm1.ChangeDutyCycle(0)
            is_change = 0
    elif result_rsp == 1: 
        if is_change == 1:
            pwm2.ChangeDutyCycle(100)
            time.sleep(2)
            pwm2.ChangeDutyCycle(0)
            is_change = 0

# Get the coordinates of a specific point
def get_point(hands, point = 0):
    global frame1
    global results
    ret, frame = cap.read()

    # Setting Frame
    frame1 = cv2.resize(frame, (SCREEN_WIDTH, SCREEN_HEIGHT))
    frame1 = cv2.flip(frame1, 1)

    # Making Hand Outline
    results = hands.process(cv2.cvtColor(frame1, cv2.COLOR_BGR2RGB))
    get_x = []
    get_y = []
    num = 0
    valid_num = 0
    if results.multi_hand_landmarks != None:
        for handLandmarks in results.multi_hand_landmarks:
            get_x.append(handLandmarks.landmark[point].x)
            get_y.append(handLandmarks.landmark[point].y)
            for landmark in handLandmarks.landmark:
                if 0 <= landmark.x <= 1 and 0 <= landmark.y <= 1:
                    valid_num += 1
            # Count a valid hand only when all 21 points are detected
            if valid_num == 21:
                num += 1

            valid_num = 0
        return get_x, get_y, num
    else:
        return [0,0], [0,0], 0

# Calculate distance between two points
def distance_count(point1_x, point1_y, point2_x, point2_y):
    return ((point1_x-point2_x)**2+(point1_y-point2_y)**2)**0.5

# Analyze gestures
def gesture_detect(hands, num):
    global users
    base = 0.8
    thumb = 1.5
    users = np.zeros(num, dtype=int)
    thumb_result = []

    # Retrieve all points once to avoid redundant `get_point` calls
    pos_0_x, pos_0_y, _ = get_point(hands, 0)
    pos_2_x, pos_2_y, _ = get_point(hands, 2)
    pos_4_x, pos_4_y, _ = get_point(hands, 4)
    pos_5_x, pos_5_y, _ = get_point(hands, 5)
    pos_8_x, pos_8_y, _ = get_point(hands, 8)
    pos_16_x, pos_16_y, _ = get_point(hands, 16)

    # Determine the valid number of hands based on available data
    min_length = min(len(pos_0_x), len(pos_2_x), len(pos_4_x), len(pos_5_x), len(pos_8_x), len(pos_16_x) )
    num = min(num, min_length)  # Ensure `num` doesn't exceed the detected hands

    # Adjust the sequence based on the players' positions in the real word
    if num == 2 and pos_0_x[0] > pos_0_x[1]:
        pos_0_x[0], pos_0_x[1] = pos_0_x[1], pos_0_x[0]
        pos_2_x[0], pos_2_x[1] = pos_2_x[1], pos_2_x[0]
        pos_4_x[0], pos_4_x[1] = pos_4_x[1], pos_4_x[0]
        pos_5_x[0], pos_5_x[1] = pos_5_x[1], pos_5_x[0]
        pos_8_x[0], pos_8_x[1] = pos_8_x[1], pos_8_x[0]
        pos_16_x[0], pos_16_x[1] = pos_16_x[1], pos_16_x[0]

        pos_0_y[0], pos_0_y[1] = pos_0_y[1], pos_0_y[0]
        pos_2_y[0], pos_2_y[1] = pos_2_y[1], pos_2_y[0]
        pos_4_y[0], pos_4_y[1] = pos_4_y[1], pos_4_y[0]
        pos_5_y[0], pos_5_y[1] = pos_5_y[1], pos_5_y[0]
        pos_8_y[0], pos_8_y[1] = pos_8_y[1], pos_8_y[0]
        pos_16_y[0], pos_16_y[1] = pos_16_y[1], pos_16_y[0]


    for i in range(num):

        if i >= min_length:
            break

        # Calculate distances only if all necessary points are valid
        u0_dist_0_8 = distance_count(pos_0_x[i], pos_0_y[i], pos_8_x[i], pos_8_y[i])
        u0_dist_0_5 = distance_count(pos_0_x[i], pos_0_y[i], pos_5_x[i], pos_5_y[i])
        u0_dist_0_16 = distance_count(pos_0_x[i], pos_0_y[i], pos_16_x[i], pos_16_y[i])
        u0_dist_0_2 = distance_count(pos_0_x[i], pos_0_y[i], pos_2_x[i], pos_2_y[i])
        u0_dist_0_4 = distance_count(pos_0_x[i], pos_0_y[i], pos_4_x[i], pos_4_y[i])

        # selections detection
        if u0_dist_0_8 != 0 and u0_dist_0_16 != 0 and u0_dist_0_2 != 0:
            if u0_dist_0_5/u0_dist_0_8 >= base and u0_dist_0_5/u0_dist_0_16 >= base:
                users[i] = ROCK
            elif u0_dist_0_5/u0_dist_0_16 >= base and u0_dist_0_5/u0_dist_0_8 < base:
                users[i] = SCISSOR
            elif u0_dist_0_5/u0_dist_0_16 < base and u0_dist_0_5/u0_dist_0_8 < base:
                users[i] = PAPER
        
            # thumbs detection
            if (
                    u0_dist_0_8 != 0 and u0_dist_0_16 != 0
                    and u0_dist_0_5 / u0_dist_0_8 >= base
                    and u0_dist_0_5 / u0_dist_0_16 >= base
                    and u0_dist_0_4 / u0_dist_0_2 >= thumb
            ):
                if pos_4_y < pos_0_y:  # Thumbs-up
                    thumb_result.append(True)
                elif pos_4_y > pos_0_y:  # Thumbs-down
                    thumb_result.append(False)

    # Results analysis
    if len(thumb_result) >= 2 and thumb_result[0] and thumb_result[1]:  # Both thumbs-up are detected
        return users, num, 1
    elif len(thumb_result) == 2 and not thumb_result[0] and not thumb_result[1]:  # Both thumbs-down are detected
        return users, num, 2
    else:
        return users, num, 0

# Game result analysis
def rsp_result(users):
    if len(users) == 2:
        result = users[0] - users[1]
        if result == 0:
            return 2 # draw
        elif result < 0:
            if result == -1:
                return 0 # user0 win
            elif result ==-2:
                return 1 # user1 win
        elif result > 0:
            if result == 1:
                return 1 # user1 win
            elif result ==2:
                return 0 # user0 win
    else:
        return None
    
# ----------------------------------------
# Main
# ----------------------------------------

def main():
    global background
    global frame1
    global results
    global not_quit
    global users
    global is_change
    is_countdown = 0
    is_detect = 0
    users = []
    num = 0
    thumb = 0
    result_rsp = 3
    freq_count = 0
    current_page = MAIN_PAGE
    is_thumb_detect = 1
    is_change = 0
    try:
        with handsModule.Hands(static_image_mode=False, min_detection_confidence=0.8, min_tracking_confidence=0.8, max_num_hands=2) as hands:
            while not_quit:
                screen.fill(BLACK)
                # main page
                if current_page == MAIN_PAGE:
                    is_thumb_detect = 1
                    is_change = 0
                    is_detect = 0
                    point_counter = draw_main_page()
                # game page
                elif current_page == ROCK_PAPER_SCISSOR_PAGE:
                    is_detect = 1
                    is_thumb_detect = 0
                    point_counter = draw_rps_page(num, users, result_rsp, point_counter)
                    vibration(result_rsp)


                _, _, num = get_point(hands)

                if is_detect:
                    if freq_count == 3:
                        users, num, thumb = gesture_detect(hands, num)
                        result_rsp = rsp_result(users)
                        if thumb == 2:
                            print("Thumb-down all Down Detected!")
                            current_page = MAIN_PAGE
                            print(current_page, is_thumb_detect)
                        freq_count = 0
                    else:
                        freq_count+=1

                if is_thumb_detect and current_page == MAIN_PAGE:
                    print(current_page, is_thumb_detect)
                    if freq_count == 3:
                        _, _, thumb = gesture_detect(hands, num)
                        if thumb == 1:
                            print("Thumb-up all Up Detected!")
                            current_page = ROCK_PAPER_SCISSOR_PAGE
                            # vibration to indicate start
                            pwm1.ChangeDutyCycle(100)
                            pwm2.ChangeDutyCycle(100)
                            time.sleep(2)
                            pwm1.ChangeDutyCycle(0)
                            pwm2.ChangeDutyCycle(0)                           
                        freq_count = 0
                    else:
                        freq_count+=1

                pygame.display.flip()

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
    except KeyboardInterrupt:
        sys.exit()

if __name__ == '__main__':
    main()
