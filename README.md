# TDTPhotometrySQLdbBuilder

**A semi-automated protocol for building an SQL database from TDT Photometry data**

Photometry data collection inundates users with data, with a single session for a single animal potentially genrerating millions of datapoints. The amount of data can become unwieldly. Generating a protocol for best practices can also be difficult if protocols are not established and replicated across people and time. 

Here, I provide one route by which to initially process and store photometry data collected from a *TDT system* onto a SQL database via python. This SQL database can be queried from python or the user's preferred lanaguage. Below is a description of the script, the assumptions it makes about data organization, and the variables of the script that need to be changed to run locally. 

**Assumptions**
1. Each recording cohort's data should be stored in a folder labeled: XXX & YYY where XXX and YYY are the animal IDs. For example, 129 & 130
2. Within each folder, each recording session should be labeled with the date formated as DD-MM-YYYY, where D = day, M = month, and Y = year. For example, 01-20-2021
3. In each session folder, all of the data provided by the TDT photometry system 
These assumptioins are visualized in the figure below. 

![Assumptions](https://github.com/drcwadaniels/TDTPhotometrySQLdbBuilder/blob/main/assumptions_illustration.jpg)

**Variables to change**
1. datapath takes a string indicating where on your computer the photometrey data are stored
2. create_engine requires a path for the SQL database, a user name and password

 
