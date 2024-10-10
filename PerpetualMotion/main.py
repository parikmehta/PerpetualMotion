# ////////////////////////////////////////////////////////////////
# //                     IMPORT STATEMENTS                      //
# ////////////////////////////////////////////////////////////////
import os
import math
import sys
import time
import threading

from kivy.properties import ObjectProperty

os.environ["DISPLAY"] = ":0.0"

from kivy.app import App
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import *
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.slider import Slider
from kivy.uix.image import Image
from kivy.uix.behaviors import ButtonBehavior
from kivy.clock import Clock
from kivy.animation import Animation
from functools import partial
from kivy.config import Config
from kivy.core.window import Window
from pidev.kivy import DPEAButton
from pidev.kivy import PauseScreen
from time import sleep
from dpeaDPi.DPiComputer import *
from dpeaDPi.DPiStepper import *

# ////////////////////////////////////////////////////////////////
# //                     HARDWARE SETUP                         //
# ////////////////////////////////////////////////////////////////
"""Stepper Motor goes into MOTOR 0 )
    Limit Switch associated with Stepper Motor goes into HOME 0
    One Sensor goes into IN 0
    Another Sensor goes into IN 1
    Servo Motor associated with the Gate goes into SERVO 1
    Motor Controller for DC Motor associated with the Stairs goes into SERVO 0"""


# ////////////////////////////////////////////////////////////////
# //                      GLOBAL VARIABLES                      //
# //                         CONSTANTS                          //
# ////////////////////////////////////////////////////////////////

OPEN = [False, 90]
CLOSE = [True, 35]
YELLOW = .180, 0.188, 0.980, 1
BLUE = 0.917, 0.796, 0.380, 1
RAMP_SPEED = 20
MICROSTEPPING = 8
STARTING_POS_PUSH = 0
END_POS_PUSH = -230
STAIRCASE_SPEED = 40


# ////////////////////////////////////////////////////////////////
# //            DECLARE APP CLASS AND SCREENMANAGER             //
# //                     LOAD KIVY FILE                         //
# ////////////////////////////////////////////////////////////////
class MyApp(App):
    def build(self):
        self.title = "Perpetual Motion"
        return sm

Builder.load_file('main.kv')
Window.clearcolor = (.1, .1,.1, 1) # (WHITE)



# ////////////////////////////////////////////////////////////////
# //                    SLUSH/HARDWARE SETUP                    //
# ////////////////////////////////////////////////////////////////
#Creating Screen Manager, dpistepper anddpicomputer objects
sm = ScreenManager()
dpiStepper = DPiStepper()
dpiComputer = DPiComputer()

#Initializing Stepper and Computer and their communication. Enabling motors
dpiComputer.initialize()
if dpiStepper.initialize() != True:
    print("Can't communicate with DPiStepper Board.")
dpiStepper.enableMotors(True)

#Setting microstepping of motor
dpiStepper.setMicrostepping(MICROSTEPPING)

#Setting initial speed and accel of motor.
speedAccel = 200 * MICROSTEPPING
dpiStepper.setSpeedInStepsPerSecond(0, speedAccel)
dpiStepper.setSpeedInStepsPerSecond(0, speedAccel)


# ////////////////////////////////////////////////////////////////
# //                       MAIN FUNCTIONS                       //
# //             SHOULD INTERACT DIRECTLY WITH HARDWARE         //
# ////////////////////////////////////////////////////////////////

def initializePerpetualMotionMachine():

    #Send the pusher back home. Checks if the home switch is engaged, else will move it 10 mm back.

    while (dpiStepper.getStepperStatus(0)[3] == False):
        dpiStepper.moveToHomeInMillimeters(0, 1, RAMP_SPEED, 1000000000000)
    STARTING_POS_PUSH = dpiStepper.getCurrentPositionInMillimeters(0)[1]
    HOME = True

    #Initializing Servo to closed position
    dpiComputer.writeServo(1, CLOSE[1])
    CLOSE[0] = True
    OPEN[0] = False
    dpiComputer.writeServo(0, 90)

def moveRampUp():
    #Moves the ramp up. Uses the set speed.
    dpiStepper.setSpeedInMillimetersPerSecond(0, RAMP_SPEED)

    dpiStepper.moveToAbsolutePositionInMillimeters(0, END_POS_PUSH, True)
    sleep(0.2)

def moveRampDown():
    dpiStepper.moveToHomeInMillimeters(0, 1, RAMP_SPEED, -1000000000)

def openGate():
    #Opens then shuts the gate
    dpiComputer.writeServo(1, OPEN[1])
    CLOSE[0] = False
    OPEN[0] = True
    while dpiComputer.readDigitalIn(1) != False:
        sleep(0.01)
    dpiComputer.writeServo(1, CLOSE[1])
    CLOSE[0] = True
    OPEN[0] = False

def turnOnStairCase():
    dpiComputer.writeServo(0, 90 - STAIRCASE_SPEED)


def turnOffStairCase():
    dpiComputer.writeServo(0, 90)

def updateRampSpeed(speed):
    global RAMP_SPEED
    RAMP_SPEED = speed

def updateStaircaseSpeed(speed):
    global STAIRCASE_SPEED
    STAIRCASE_SPEED = speed


    
# ////////////////////////////////////////////////////////////////

# //        DEFINE MAINSCREEN CLASS THAT KIVY RECOGNIZES        //
# //                                                            //
# //   KIVY UI CAN INTERACT DIRECTLY W/ THE FUNCTIONS DEFINED   //
# //     CORRESPONDS TO BUTTON/SLIDER/WIDGET "on_release"       //
# //                                                            //
# //   SHOULD REFERENCE MAIN FUNCTIONS WITHIN THESE FUNCTIONS   //
# //      SHOULD NOT INTERACT DIRECTLY WITH THE HARDWARE        //
# ////////////////////////////////////////////////////////////////
class MainScreen(Screen):

    staircaseSpeedText = '0'
    rampSpeed = RAMP_SPEED
    staircaseSpeed = STAIRCASE_SPEED
    rampSpeedLabel = ObjectProperty(None)

    staircaseSpeedLabel = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        self.initialize()

    def toggleGate(self):
        openGate()


    def toggleStaircase(self):
        turnOnStairCase()
        sleep(10)
        turnOffStairCase()
        
    def toggleRamp(self):
        moveRampUp()
        moveRampDown()

        
    def auto(self):
        openGate()
        moveRampUp()
        turnOnStairCase()
        moveRampDown()
        sleepDuration = RAMP_SPEED * 0.1
        sleep(sleepDuration)
        turnOffStairCase()



        
    def setRampSpeed(self, speed):
        updateRampSpeed(speed)
        self.rampSpeed = speed
        self.rampSpeedLabel.text = 'Ramp Speed: ' + str(self.rampSpeed)
        
    def setStaircaseSpeed(self, speed):
        updateStaircaseSpeed(int(speed))
        self.staircaseSpeed = int(speed)
        self.staircaseSpeedLabel.text = 'Staircase Speed: ' + str(self.staircaseSpeed)
        
    def initialize(self):
        initializePerpetualMotionMachine()

    def resetColors(self):
        self.ids.gate.color = YELLOW
        self.ids.staircase.color = YELLOW
        self.ids.ramp.color = YELLOW
        self.ids.auto.color = BLUE
    
    def quit(self):
        print("Exit")
        MyApp().stop()

sm.add_widget(MainScreen(name = 'main'))

# ////////////////////////////////////////////////////////////////
# //                          RUN APP                           //
# ////////////////////////////////////////////////////////////////
if __name__ == "__main__":
    # Window.fullscreen = True
    # Window.maximize()
    MyApp().run()
