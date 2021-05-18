"""
@author: Riley Norris and Brodie Rogers
@course: CSSE4011
Project
"""

import tkinter as tk
from tkinter import *
import tkinter.font
import serial
import threading
import re
import numpy as np
import math
import time
from time import sleep
from datetime import datetime
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsRegressor
from sklearn.metrics import mean_squared_error
from math import sqrt
import tago
from scipy.spatial import distance


"""
Kalman class for the Kalman Filter which takes in measured values and outputs
an estimated position based on previous predictions.
x_hat class attribute is the estimate position from the Kalman filter
# Code from Chapter 10 of Machine Learning: An Algorithmic Perspective
# by Stephen Marsland (http://seat.massey.ac.nz/personal/s.r.marsland/MLBook.html)
#Provided CSSE4011 Staff for Prac 4
"""
class Kalman:
    def __init__(self, x_init, cov_init, meas_err, proc_err):
        self.ndim = len(x_init)
        self.A = np.eye(self.ndim)        #state transition model
        self.H = np.eye(self.ndim)        #observation model
        self.x_hat =  x_init
        self.cov = cov_init
        self.Q_k = np.eye(self.ndim)*proc_err   #covariance matrix of process noise
        self.R = np.eye(len(self.H))*meas_err   #covariance matrix of observation noise
        
    def update(self, obs, meas_err):

        #Update the measurement error
        self.R = np.eye(len(self.H))*meas_err #covariance matrix of observation noise   

        # Make prediction
        self.x_hat_est = np.dot(self.A,self.x_hat)
        self.cov_est = np.dot(self.A,np.dot(self.cov,np.transpose(self.A))) + self.Q_k

        # Update estimate
        self.error_x = obs - np.dot(self.H,self.x_hat_est)
        self.error_cov = np.dot(self.H,np.dot(self.cov_est,np.transpose(self.H))) + self.R
        self.K = np.dot(np.dot(self.cov_est,np.transpose(self.H)),np.linalg.inv(self.error_cov))
        self.x_hat = self.x_hat_est + np.dot(self.K,self.error_x)
        if self.ndim>1:
            self.cov = np.dot((np.eye(self.ndim) - np.dot(self.K,self.H)),self.cov_est)
        else:
            self.cov = (1-self.K)*self.cov_est 

            

"""
Prac3 Interface Class
Reads encoded serial data from base node and estimates mobile node positions
using RSSI and Ultrasonic values. Displays position to GUI.
"""
class Prac4Interface(Frame):

    def __init__(self, master):

        Frame.__init__(self, master)

        self._master = master
                    
        self._portString = "COM6"                       #The sting value of the port as COM6
        self._portOpen = False                          
        self._nodeP = {0:(0,0), 1:(2.5,0), 2:(5.5,0), 3:(8,0), 4:(0,4), 5:(2.5,4), 6:(5.5,4), 7:(8,4)}
        self._ndim = 2
        self._myDevice = tago.Device('48bf7c9b-b465-49c2-aa55-117cda12c04d')
        self._lastDBUpdate = time.time()
        self.co2Vals = [0,0]
        self.tvocVals = [0,0]
        
        self._m1kFilter = Kalman(np.array([4, 2]), np.eye(self._ndim),0.01, 2e-5)
        
        #Building the frames for the main interface
        self.Frame1 = Frame(self, bg="SlateGray1", width=900, height=50, highlightbackground="black", highlightthickness=1)     #01 Title
        self.Frame2 = Frame(self, width=450, height=50, highlightbackground="black", highlightthickness=1)                      #02 Node 1
        self.Frame3 = Frame(self, width=450, height=50, highlightbackground="black", highlightthickness=1)                      #03 Node 2
        self.Frame4 = Frame(self, width=450, height=100, highlightbackground="black", highlightthickness=1)                     #04 Room Size 
        self.Frame5 = Frame(self, width=450, height=100, highlightbackground="black", highlightthickness=1)                     #05 Ventilation
        self.Frame6 = Frame(self, width=900, height=100, highlightbackground="black", highlightthickness=1)                     #06 Room Occupancy
        
        #Setting up the grid layout for the main interface
        self.Frame1.grid(row=0, column=0, columnspan=2, sticky="nsew")      #01 Title
        self.Frame2.grid(row=1, column=0, sticky="nsew")                    #02 Node 1
        self.Frame3.grid(row=1, column=1, sticky="nsew")                    #03 Node 2
        self.Frame4.grid(row=2, column=0, sticky="nsew")                    #04 Room Size
        self.Frame5.grid(row=2, column=1, sticky="nsew")                    #05 Ventilation
        self.Frame6.grid(row=3, column=0, columnspan=2, sticky="nsew")       #06 Room Occupancy
                
        
        #Calling functions to create and display widgets in each panel
        self.titleFrame(self.Frame1)                 #01 Title
        self.connectionFrame(self.Frame2)              #04 Node 1
        self.timestampFrame(self.Frame3)             #05 Node 2
        self.node1Frame(self.Frame4)                 #02 Room Size
        self.node2Frame(self.Frame5)                 #03 Timestamp
        self.roomOccupancyFrame(self.Frame6)         #06 Room Occupancy

        
        self._serialBuffer = ""                         #The serial buffer holding the received values
        self._serialPort = serial.Serial(port=self._portString, baudrate=9600, 
                                             bytesize=8, timeout=2, stopbits=serial.STOPBITS_ONE)
        self._portOpen = True
        
        self._progThread = threading.Thread(target=self.runProgram)
        #self._webDBThread = threading.Thread(target=self.updateWebDB)
        self._progThread.start()
        #self._webDBThread.start()        
        
    def __del__(self):
        self._serialPort.close()
        self._progThread.join()
        self._webDBThread.join()


    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    Runs a recursive loop which handles the updating of the interface display
    and the serial communication
    Sends to the web dashboard every 1 second
    """
    def updateWebDB(self):
        
        while(True):
            now = time.time()
            if (now - self._lastDBUpdate > 1):
                dbData = {
                    'variable': 'co2ppm',
                    'value': self.convertCO2ForWeb(self.co2Vals),
                    'metadata': {'color': 'green'},
                }
                self._myDevice.insert(dbData)
                self._lastDBUpdate = now
            sleep(0.01)


    """
    Converts the Ultrasonic values to a string format to send to the Web Dashboard
    @param: usVals - The list of ultrasonic values
    """
    def convertCO2ForWeb(self, co2Vals):
        return int("1" + '{0}{1}{2}'.format(str(co2Vals[0]).zfill(4), str(co2Vals[1]).zfill(4), 
                                         str(co2Vals[2]).zfill(4)))
    

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    Runs a recursive loop which handles the updating of the interface display
    and the serial communication
    """
    def runProgram(self):     
        
        while(True):
            
            if (self._portOpen == True):
                
                #If the serial port has a message
                if (self._serialPort.in_waiting > 0):
                    
                    #Read the character and decode
                    character = self._serialPort.read().decode('ascii')
                    
                    #Add the character to the buffer
                    self._serialBuffer += character
                    
                    #Checking for valid message
                    self.checkSerialBuffer()
       
        
    """"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""  
       
    """
    Checks the serial buffer for a message from the NRF52840 Dongle
    """        
    def checkSerialBuffer(self):
        
        try:
            self._message = re.search(r"#B3;\d{1,4},\d{1,4};!", self._serialBuffer).group()
            self._serialBuffer = ""
            self.decodeAndFilter()
        except:
            pass
        
        
    """
    Decodes the serial message and updates each of the fields on the GUI
    Averages the CO2 sensor values and feeds into the ML model
    Displays the estimated room occupancy count on GUI and Web Dashboard
    Expecting string of the form:
    #B3;_,_;_,_;!
    """     
    def decodeAndFilter(self):

        data = self._message.split(";")
        self.co2Vals, self.tvocVals = self.processRawVals(data[1].split(","), data[2].split(","))
        self.updateValueFields()

        
    """
    Processes the raw CO2 and TVOC values received and calculates the room averages
    Assumes the number of CO2 and TVOC values are the same (one for each node)
    """
    def processRawVals(self, co2ValsList, tvocValsList):
        co2RetVals, tvocRetVals = [], []
        for i in range(len(co2ValsList)):
            co2RetVals.append(int(co2ValsList[i]))
            tvocRetVals.append(int(tvocValsList[i]))
        co2RetVals.append(int(sum(co2RetVals)/len(co2RetVals)))
        tvocRetVals.append(int(sum(tvocRetVals)/len(tvocRetVals)))
        return co2RetVals, tvocRetVals
    
    
    """
    Updates each of the CO2 and TVIC value data fields on the GUI
    """
    def updateValueFields(self):
        self.n1co2Label.config(text=("CO2 Reading: " + str(self.co2Vals[0]) + "ppm"), fg="black")
        self.n2co2Label.config(text=("CO2 Reading: " + str(self.co2Vals[1]) + "ppm"), fg="black")
        self.n1tvocLabel.config(text=("TVOC Reading: " + str(self.tvocVals[0]) + "ppb"), fg="black")
        self.n2tvocLabel.config(text=("TVOC Reading: " + str(self.tvocVals[1]) + "ppb"), fg="black")


    """
    Updates the timestamp for when the data was received
    """
    def updateTime(self):
        timeStamp = datetime.now()
        self.timestampLabel.config(text=("{0:02d}:{1:02d}:{2:02d}:{3:03d} AM".format(timeStamp.hour,
                                                                               timeStamp.minute,
                                                                               timeStamp.second,
                                                                               int(timeStamp.microsecond/1000))))
    
    
    """
    Creates and displays the Heading Label
    @param - parent: The frame that contains the function widgets
    """
    def titleFrame(self, parent):
        self.heading = Label(parent, bg="SlateGray1", fg="midnight blue",
                             text="Air Quality and Room Occupancy Sensing Network", 
                             font=('Arial',20))
        self.heading.pack(anchor='n', pady=10)   
        
    """
    Creates and displays the Connection Panel
    @param - parent: The frame that contains the function widgets
    """
    def connectionFrame(self, parent):
        self.connectionHeading = Label(parent, text="Connection Status", font="bold")
        self.disconnectDevButton = Button(parent, text="Disconnect", command=self.disconnectPort)    #Not initially displayed
        self.connectionHeading.grid(row=1, column=1, sticky='w')
        self.disconnectDevButton.grid(row=2, column=1, sticky='w')
        
        
    """
    Disconnects the device serial port
    """
    def disconnectPort(self):
        self._portOpen = False
        self._serialPort.close()
     
        
    """
    Creates and displays the Node 1 Frame
    @param - parent: The frame that contains the function widgets
    """
    def node1Frame(self, parent):
        self.node1Label = Label(parent, text="Node 1", font="bold")
        self.n1co2Label = Label(parent, text="CO2 Reading:")
        self.n1tvocLabel = Label(parent, text="TVOC Reading:")
        self.node1Label.grid(row=1, column=1, sticky='w')
        self.n1co2Label.grid(row=2, column=1, sticky='w')
        self.n1tvocLabel.grid(row=3, column=1, sticky='w')


    """
    Creates and displays the Node 2 Frame
    @param - parent: The frame that contains the function widgets
    """        
    def node2Frame(self, parent):
        self.node2Label = Label(parent, text="Node 2", font="bold")
        self.n2co2Label = Label(parent, text="CO2 Reading:")
        self.n2tvocLabel = Label(parent, text="TVOC Reading:")
        self.node2Label.grid(row=1, column=1, sticky='w')
        self.n2co2Label.grid(row=2, column=1, sticky='w')
        self.n2tvocLabel.grid(row=3, column=1, sticky='w')
      
    
    """
    Creates and displays the room size frame
    @param - parent: The frame that contains the function widgets
    """
    def roomSizeFrame(self, parent):
        self.roomSizeHeading = Label(parent, text="Room Size", font="bold")
        self.roomVolume = Label(parent, text="")
        self.changeRoomDimension = Button(parent, text="Set", command=self.changeDimensions)
        
        
    """
    Creates and displays the Time Stamp Panel
    @param - parent: The frame that contains the function widgets
    """
    def timestampFrame(self, parent):
        self.timestampHeading = Label(parent, text="Data Timestamp", font="bold")
        self.timestampLabel = Label(parent, text=" ")
        self.timestampHeading.grid(row=1, column=1, sticky='w')
        self.timestampLabel.grid(row=2, column=1, sticky='w')
        
    
    """
    Allows the user to change the dimensions of the room
    """
    def changeDimensions(self):
        pass
    
    
    """
    Creates and displays the room occupancy frame
    @param - parent: The frame that contains the function widgets
    """
    def roomOccupancyFrame(self, parent):
        self.roomOccHeading = Label(parent, text="Room Occupancy Count", font="bold")
        self.roomOccCount = Label(parent, text="")
        self.roomOccHeading.grid(row=1, column=1, sticky="n")
        self.roomOccCount.grid(row=2, column=1, sticky="n")
    

"""
Main function
"""
def main():

    root = tk.Tk()
    root.title("CSSE4011 Practical 4")
    Prac4 = Prac4Interface(root).pack(side="top", fill="both", expand=True)
    root.mainloop()


if __name__ == "__main__":
    main()