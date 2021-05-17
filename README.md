# Air Quality and Room Occupancy Sensing Network

## Aether-Blue



## Team Members
#### Riley Norris (44781796)
#### Brodie Rogers (45299823)

---

## Project Overview

This project aims to implement a room occupancy sensing system that uses on-board Thingy52 environmental sensors to measure the number of people in a room. This project has real-world relevance with current social restrictions in place that limit the number of people allowed in indoor spaces.

## Project Performance

The performance of the project will be measured using a number of metrics to determine the overall quality of the project outcome. The key-performance indicators used to measure this are displayed below:

Key-Performance Indicator  | Status | Target
---------------------------|--------|------------------------------------
Reliable Bluetooth Network |Good    | Stable ( < 2% communication issues)

## System Overview

See the ____.pdf document in the git repository for a graphical system overview of the project.

## Sensor Integration

**CCS811 (Gas Sensor)**  
This gas sensor is used to measure the CO2 levels. The sensor will be read by the Thingy52 at a 4Hz rate.

## Wireless Network Communication

The wireless network model being used for this project is Bluetooth Low-Energy (BLE) implemented as a Broadcast/Observer model.  
Thingy52 sensor nodes will broadcast sensor values to a nRF52840 Dongle at the same rate that sensor values are read from the device.  
The Dongle will serialise the data and send through the PC script which will then display it graphically on a graphical user interface (GUI) and also on a web dashboard such as Tagio.

## Algorithm Schemes

Preliminary testing will use a k-nearest neighbours (kNN) model however it is not expected that this model will produce sufficient results for the project.  
Based on other published works in this research area, a support-vector machine (SVM) model will also be implemented to try and improve reliability and accuracy of the model.  
Testing will be required to determine whether the model is accurate enough to use a regression model with rounding to the nearest occupant count or whether classification is a more suitable method and occupancy count should be grouped in intervals of 0, 1-2, 3-5, 6-10 people for example.

## Equipment

For this project to be implemented, the following equipment is required:

* 2 x Thingy52 devices
* 1 x nRF52840 Dongle
* 1 x PC with Python 3.8 distribution installed (along with required python packages) and internet connection

## Progress

The progress for this project will be tracked in the table below and documents the date at which any notable progression is achieved.

Progress | Date
---------|-----
Thingy52 -> nRF52840 Dongle BLE communication setup and working | 17/05/2021
nRF52840 Dongle serialisation to PC setup and working | 17/05/2021
Thingy52 reading from CCS811 (CO2 Gas Sensor) setup and working | 17/05/2021
PC python script reading serialised data and displaying to GUI | 17/05/2021