# -*- coding: utf-8 -*-
"""
Created on Thu May 20 16:19:07 2021

@author: Riley
"""

import serial
import re
import csv
import time

calCO2 = 0
calTVOC = 0
count = 0
co2N1Avg = [0]*200
co2N2Avg = [0]*200
tvocN1Avg = [0]*200
tvocN2Avg = [0]*200
co2CombAvg = [0]*200
tvocCombAvg = [0]*200
co2MaxAvg = [0]*200
tvocMaxAvg = [0]*200

rows = [["N1 CO2 Raw", "N1 CO2 Avg", "N2 CO2 Raw", "N2 CO2 Avg", 
         "CO2 Comb Raw", "CO2 Comb Avg", "CO2 Max Raw", "CO2 Max Avg", 
         "N1 TVOC Raw", "N1 TVOC Avg", "N2 TVOC Raw", "N2 TVOC Avg", 
         "TVOC Comb Raw", "TVOC Comb Avg", "TVOC Max Raw", "TVOC Max Avg", 
         "No. People", "Time", "Index"]]

numPeople = input("Enter number of people: ")
go = input("Start calibration: ")
if (go == "y"):
    
    startTime = time.time()
    serialBuffer = ""
    serialPort = serial.Serial("COM12", baudrate=9600, bytesize=8, timeout=2, stopbits=serial.STOPBITS_ONE)
    
    #Calibrate for 20 minutes
    while(time.time() - startTime < 1200):
        
        if (serialPort.in_waiting > 0):
            
            character = serialPort.read().decode('ascii')
            serialBuffer += character
            
            #Checking for valid message
            try:
                message = re.search(r"#B3;\d{1,5},\d{1,5};\d{1,5},\d{1,5};!", serialBuffer).group()
                serialBuffer = ""
                data = message.split(";")
                co2Data = data[1].split(",")
                tvocData = data[2].split(",")
                
                #Getting the individual sensor CO2 and TVOC values
                co2N1Avg.pop(199)
                co2N1Avg.insert(0,int(co2Data[0]))
                co2N2Avg.pop(199)
                co2N2Avg.insert(0,int(co2Data[1]))                
                tvocN1Avg.pop(199)
                tvocN1Avg.insert(0,int(tvocData[0]))
                tvocN2Avg.pop(199)
                tvocN2Avg.insert(0,int(tvocData[1]))   

                #Getting the averaged CO2 values
                co2 = (int(co2Data[0]) + int(co2Data[1]))/2
                calCO2 += co2
                co2Max = max(int(co2Data[0]), int(co2Data[1]))
                co2CombAvg.pop(199)
                co2CombAvg.insert(0,co2)
                co2MaxAvg.pop(199)
                co2MaxAvg.insert(0,co2Max)     
                
                #Getting the averaged TVOC values
                tvoc = (int(tvocData[0]) + int(tvocData[1]))/2
                calTVOC += tvoc
                tvocMax = max(int(tvocData[0]), int(tvocData[1]))
                tvocCombAvg.pop(199)
                tvocCombAvg.insert(0,tvoc)
                tvocMaxAvg.pop(199)
                tvocMaxAvg.insert(0,tvocMax)

                #Creating the rows for sending to the CSV file
                row = [co2Data[0], round(sum(co2N1Avg)/len(co2N1Avg), 0), co2Data[1], round(sum(co2N2Avg)/len(co2N2Avg), 0),
                       co2, round(sum(co2CombAvg)/len(co2CombAvg), 0), co2Max, round(sum(co2MaxAvg)/len(co2MaxAvg), 0),
                       tvocData[0], round(sum(tvocN1Avg)/len(tvocN1Avg), 0), tvocData[1], round(sum(tvocN2Avg)/len(tvocN2Avg), 0),
                       tvoc, round(sum(tvocCombAvg)/len(tvocCombAvg), 0), tvocMax, round(sum(tvocMaxAvg)/len(tvocMaxAvg), 0),
                       numPeople, round(time.time()-startTime, 4), count]
                if (count > 200):
                    rows.append(row)
                count += 1
                
            except:
                pass
        
#Recording finished, close the serial port
serialPort.close()
    
#Write the data to a csv file
with open ('co2_tvoc_3_people.csv', 'w', encoding='utf8', newline='') as csvwritefile:
    csvwriter = csv.writer(csvwritefile, delimiter=',')     
    csvwriter.writerows(rows)