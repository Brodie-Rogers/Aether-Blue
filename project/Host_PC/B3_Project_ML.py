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
from sklearn.model_selection import cross_val_score
from sklearn.model_selection import RepeatedKFold
from math import sqrt
import tago
from scipy.spatial import distance

import xgboost as xgb
from xgboost import XGBRegressor


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
        self._lastTempUpdate = time.time()
        self._lastCountUpdate = time.time()
        self.co2Vals = [0,0]
        self.tvocVals = [0,0]
        self.temp = 0.0
        self.humid = 0.0
        self.predictedOccupancy = 0
        self.prevPredict = -1
        self.predictChanged = True
        self.counter = 0
        self.maxOccupancy = 3
        
        self.co2N1Avg = [0]*200
        self.co2N2Avg = [0]*200
        self.tvocN1Avg = [0]*200
        self.tvocN2Avg = [0]*200
        self.co2CombAvg = [0]*200
        self.tvocCombAvg = [0]*200
        self.co2MaxAvg = [0]*200
        self.tvocMaxAvg = [0]*200
        
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
        self.Frame6.grid(row=3, column=0, columnspan=2, sticky="nsew")      #06 Room Occupancy
                
        
        #Calling functions to create and display widgets in each panel
        self.titleFrame(self.Frame1)                 #01 Title
        self.connectionFrame(self.Frame2)            #02 Node 1
        self.timestampFrame(self.Frame3)             #03 Node 2
        self.node1Frame(self.Frame4)                 #04 Room Size
        self.node2Frame(self.Frame5)                 #05 Timestamp
        self.roomOccupancyFrame(self.Frame6)         #06 Room Occupancy
        
        #Read the data in and create/fit the ML model
        self.xgbDataDF = pd.read_csv("xgb_model_data.csv", header=0)
        X, y = self.xgbDataDF.loc[:,:"TVOC Max Avg"].values, self.xgbDataDF.loc[:,"No. People"].values
        self.xgbModel = XGBRegressor()
        self.xgbModel.fit(X, y)
        
        self._serialBuffer = ""                         #The serial buffer holding the received values
        self._serialPort = serial.Serial(port=self._portString, baudrate=9600, 
                                             bytesize=8, timeout=2, stopbits=serial.STOPBITS_ONE)
        self._portOpen = True
        
        self._progThread = threading.Thread(target=self.runProgram)
        self._webDBThread = threading.Thread(target=self.updateWebDB)
        self._progThread.start()
        self._webDBThread.start()        
        
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
            if (now - self._lastDBUpdate > 2 and self.counter == 200):

                #Sending CO2 data to web dashboard
                dbData = {
                    'variable': 'co2',
                    'value': round(sum(self.co2CombAvg)/len(self.co2CombAvg), 0),
                    'metadata': {'color': 'green'},
                }
                self._myDevice.insert(dbData)

                #Sending TVOC data to web dashboard
                dbData = {
                    'variable': 'TVOC',
                    'value': round(sum(self.tvocCombAvg)/len(self.tvocCombAvg), 0),
                    'metadata': {'color': 'blue'},
                }
                self._myDevice.insert(dbData)

                #Sending predicted occupancy data to web dashboard if changed
                if (self.predictChanged or now - self._lastCountUpdate > 10):

                    if (self.predictedOccupancy > self.maxOccupancy):
                        colour = {'color': 'red'}
                    else:
                        colour = {'color': 'green'}
                    
                    dbData = {
                        'variable': 'occupancy',
                        'value': self.predictedOccupancy,
                        'metadata': colour,
                    }
                    self._myDevice.insert(dbData)
                    self.predictChanged = False
                    self._lastCountUpdate = now

                self._lastDBUpdate = now

            if (now - self._lastTempUpdate > 5 and self.counter == 200):
                #Sending Temp and Humidity data to web dashboard
                dbData = {
                    'variable': 'temp',
                    'value': ("Temperature: " + str(self.temp) + " " + u'\N{DEGREE SIGN}' + "C" + "\r\n" + "Humidity: " + str(self.humid) + "%"),
                }
                self._myDevice.insert(dbData)
                
                self._lastTempUpdate = now
                
            sleep(0.01)

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
            self._message = re.search(r"#B3;\d{1,5},\d{1,5};\d{1,5},\d{1,5};\d{1,2}\.\d{1,2};\d{1,2}\.\d{1,2};\d{1,2}\.\d{1,2};\d{1,2}\.\d{1,2};!", self._serialBuffer).group()
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
        self.temp = round((float(data[3]) + float(data[5]))/2, 1)
        self.humid = round((float(data[4]) + float(data[6]))/2, 1)
        self.updateValueFields()
        self.updateTime()
        self.predictOccupancy()
        if (self.counter < 200):
            self.counter += 1


    """
    Does some signal processing to smooth the data.
    Predicts the occupancy in the room.
    """
    def predictOccupancy(self):

        #Getting the individual sensor CO2 and TVOC values
        self.co2N1Avg.pop(199)
        self.co2N1Avg.insert(0,int(self.co2Vals[0]))
        self.co2N2Avg.pop(199)
        self.co2N2Avg.insert(0,int(self.co2Vals[1]))                
        self.tvocN1Avg.pop(199)
        self.tvocN1Avg.insert(0,int(self.tvocVals[0]))
        self.tvocN2Avg.pop(199)
        self.tvocN2Avg.insert(0,int(self.tvocVals[1]))   

        #Getting the averaged CO2 values
        co2 = (int(self.co2Vals[0]) + int(self.co2Vals[1]))/2
        self.co2Max = max(int(self.co2Vals[0]), int(self.co2Vals[1]))
        self.co2CombAvg.pop(199)
        self.co2CombAvg.insert(0,co2)
        self.co2MaxAvg.pop(199)
        self.co2MaxAvg.insert(0,self.co2Max)     

        #Getting the averaged TVOC values
        tvoc = (int(self.tvocVals[0]) + int(self.tvocVals[1]))/2
        self.tvocMax = max(int(self.tvocVals[0]), int(self.tvocVals[1]))
        self.tvocCombAvg.pop(199)
        self.tvocCombAvg.insert(0,tvoc)
        self.tvocMaxAvg.pop(199)
        self.tvocMaxAvg.insert(0,self.tvocMax)

        row = [self.co2Vals[0], round(sum(self.co2N1Avg)/len(self.co2N1Avg), 0), self.co2Vals[1], round(sum(self.co2N2Avg)/len(self.co2N2Avg), 0),
               co2, round(sum(self.co2CombAvg)/len(self.co2CombAvg), 0), self.co2Max, round(sum(self.co2MaxAvg)/len(self.co2MaxAvg), 0),
               self.tvocVals[0], round(sum(self.tvocN1Avg)/len(self.tvocN1Avg), 0), self.tvocVals[1], round(sum(self.tvocN2Avg)/len(self.tvocN2Avg), 0),
               tvoc, round(sum(self.tvocCombAvg)/len(self.tvocCombAvg), 0), self.tvocMax, round(sum(self.tvocMaxAvg)/len(self.tvocMaxAvg), 0)]

        new_data = np.asarray([row])
        self.predictedOccupancy = int(round(self.xgbModel.predict(new_data)[0], 0))
        
        #New prediction
        if (self.prevPredict != self.predictedOccupancy):
            self.predictChanged = True
            self.prevPredict = self.predictedOccupancy
            try:
                if (self.predictedOccupancy > self.maxOccupancy):
                    self.roomOccCount.config(text=str(self.predictedOccupancy), font="bold", fg="red")
                    self._serialPort.write(str.encode('f'))
                else:
                    self.roomOccCount.config(text=str(self.predictedOccupancy), font="bold", fg="green")
                    self._serialPort.write(str.encode('o'))
            except:
                pass

        

    """
    Processes the raw CO2 and TVOC values received and calculates the room averages
    Assumes the number of CO2 and TVOC values are the same (one for each node)
    """
    def processRawVals(self, co2ValsList, tvocValsList):
        co2RetVals, tvocRetVals = [], []
        for i in range(len(co2ValsList)):
            co2RetVals.append(int(co2ValsList[i]))
            tvocRetVals.append(int(tvocValsList[i]))
        return co2RetVals, tvocRetVals
    
    
    """
    Updates each of the CO2 and TVOC value data fields on the GUI
    """
    def updateValueFields(self):
        self.n1co2Label.config(text=("CO2 Reading: " + '{0:{fill}6}'.format(self.co2Vals[0], fill=' ') + " ppm"), fg="black")
        self.n2co2Label.config(text=("CO2 Reading: " + '{0:{fill}6}'.format(self.co2Vals[1], fill=' ') + " ppm"), fg="black")
        self.n1tvocLabel.config(text=("TVOC Reading: " + '{0:{fill}5}'.format(self.tvocVals[0], fill=' ') + " ppb"), fg="black")
        self.n2tvocLabel.config(text=("TVOC Reading: " + '{0:{fill}5}'.format(self.tvocVals[1], fill=' ') + " ppb"), fg="black")


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
    Creates and displays the room occupancy frame
    @param - parent: The frame that contains the function widgets
    """
    def roomOccupancyFrame(self, parent):
        self.roomOccHeading = Label(parent, text="Room Occupancy Count", font="bold")
        self.roomOccCount = Label(parent, text="")
        self.roomOccHeading.grid(row=1, column=1, columnspan=2, sticky="nsew")
        self.roomOccCount.grid(row=2, column=1, columnspan=2, sticky="nsew")
    

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
