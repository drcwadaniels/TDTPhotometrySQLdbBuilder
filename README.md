# TDTPhotometrySQLdbBuilder

**A semi-automated protocol for building an SQL database from TDT Photometry data**

*Read all of the below information, it is important to understand the assumptions, variables, and two scripts available*

Photometry data collection inundates users with data, with a single session for a single animal potentially genrerating millions of data points. The amount of data can become unwieldly. Generating a protocol for best practices can also be difficult if protocols are not established and replicated across people and time. 

Here, I provide one route by which to initially process and store photometry data collected from a [TDT system](https://www.tdt.com/) into a SQL database via python. SQL databases can be queried from python or the user's preferred lanaguage. Below is a description of the script, the assumptions it makes about data organization, the variables of the script that need to be changed to run locally, and two versions of the script available to the user.  

**A brief description of the code**

Once you hit run, it will loop through all of your data, importing data using the TDT python package and plotting it so that you may then annotate it. If all looks good you reply 'y' and if you need to make any changes/annotations you reply 'n'. Note, my code assumes that although you may have been collecting signal starting at t=0, nothing useable was obtained in the first 2-3 minutes of recording. Nevertheless, once you reply 'n' you will be asked where to trim it (any number between 1 and the end of your recording in seconds) and to provide any notes that may be useful for when you further analyze the data. It will then normalize the GCAMP signal by the ISOS signal. Once it has normalized those signals it will then reorganize the data into a list of dictionaries so that it may be bulk written to the SQL dB using SQL alchemy. While this last portion of the script is somewhat slow, its speed depends on the resolution with which you collected your photometry signal. Higher resolution = higher processing time. 

**Assumptions**

1. Each recording cohort's data should be stored in a folder labeled: XXX & YYY where XXX and YYY are the animal IDs. For example, 129 & 130
2. Within each folder, each recording session should be labeled with the date formated as DD-MM-YYYY, where D = day, M = month, and Y = year. For example, 01-20-2021
3. In each session folder, all of the data provided by the TDT photometry system 
These assumptioins are visualized in the figure below. 

![Assumptions](https://github.com/drcwadaniels/TDTPhotometrySQLdbBuilder/blob/main/assumptions_illustration.jpg)

**Variables to change**

1. datapath takes a string indicating where on your computer the photometrey data are stored
2. create_engine requires a path for the SQL database, a user name, password, and dB name

Once data are organized according to the above assumptions and variables updated, the script itself will look for a table with the name photodata, create it if it does not exist, and then start looping through the sessions of each recording cohort to process and store data in the SQL dB. 


4. (@ line 17)
```python
datapath = "C:\\Users\\carte\Dropbox\\Carter Backup\\PostDocStuff\\RISDT\\GCamp6f PTone (6 succesful surgeries thus far)\\Photometry Data"
```

2.  (@ line 130)
```python
engine = create_engine("mysql+pymysql://{user}:{pw}@localhost/{db}".format(user="", pw="", db = "gcampptone2"))
```

**Python files**

1. PhotometryConstruct.py assumes all data have been collcted and you just need to build up your dB. 
2. Coming Soon: DayOfPhotometry.py assumes you update data everyday and thus it only needs to be run at the end of data collection for that day

You may modify these script at will, but do please make attributions where appropriate. 
