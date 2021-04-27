import os
import re
import numpy as np
import pandas as pd
import pymysql 
import mysql.connector 
from mysql.connector import errorcode
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Float, Date, PrimaryKeyConstraint, VARCHAR
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from datetime import date
import csv 
import matplotlib.pyplot as plt
from tdt import read_block, epoc_filter, download_demo_data

def get_time(s465,s405):
    timex = []
    if len(s465) == 1:
        timex.append(np.linspace(1,len(s465[0].data), len(s465[0].data))/s465[0].fs)
    else:
        for i in range(0, len(s465)):
            timex.append(np.linspace(1,len(s465[i].data), len(s465[i].data))/s465[i].fs)
    return timex

def evaluate_rawdata(t,s465,s405, subjs):
    trim = []
    note = []
    if len(s465) == 1:
        fig1 = plt.figure()
        plt.plot(time[0],Subjects_465[0].data, color='green', label = 'Gcamp6f')
        plt.plot(time[0],Subjects_405[0].data, color='blueviolet', label = 'ISOS')
        plt.ylabel('mV')
        plt.xlabel('Seconds')
        plt.title('Subject:' + subjs[0])
        plt.show()
        while True:
            try:
                proceed = str(input("Does everything look okay?"))
                if proceed == 'y':
                    trim.append(100)
                    note.append('All good')
                    break
                elif proceed == 'n':
                    trim.append(int(input("Where should the trim begin?")))
                    note.append(str(input("Anything to record about these data")))
                    break
            except ValueError:
                print("Please enter y or n")
            continue
    else:
        for i in range(0, len(s465)):
            fig1 = plt.figure()
            plt.plot(time[i],Subjects_465[i].data, color='green', label = 'Gcamp6f')
            plt.plot(time[i],Subjects_405[i].data, color='blueviolet', label = 'ISOS')
            plt.ylabel('mV')
            plt.xlabel('Seconds')
            plt.title('Subject:'+ subjs[i])
            plt.show()
            while True:
                try:
                    proceed = str(input("Does everything look okay?"))
                    if proceed == 'y':
                        trim.append(100)
                        note.append('All good')
                        break
                    elif proceed == 'n':
                        trim.append(int(input("Where should the trim begin?")))
                        note.append(str(input("Anything to record about these data")))
                        break
                except ValueError:
                    print("Please enter y or n")
            continue

    return trim, note


def trim_and_process(trim,end,timex,s465,s405):
    # trim data
    trimmed_s465 = []
    trimmed_s405 = []
    trimmed_time = []
    dFF = []
    std_dFF = []
    baseline = []
    y_all = []
    y_df = []
    s_ind = []
    e_ind = []
    if len(s465) == 1:
        s_ind.append(np.where(timex[0] > trim[0])[0][0])
        e_ind.append(np.where(timex[0]  > end)[0][0])
        trimmed_time.append(timex[0][s_ind[0]:e_ind[0]])
        trimmed_s465.append(s465[0].data[s_ind[0]:e_ind[0]])
        trimmed_s405.append(s405[0].data[s_ind[0]:e_ind[0]])

        #process data
        baseline.append(np.polyfit(np.array(trimmed_s405[0]), np.array(trimmed_s465[0]), 1))
        y_all.append(np.multiply(baseline[0][0], np.array(trimmed_s405[0])) + baseline[0][1])
        y_df.append(np.array(trimmed_s465[0]) - y_all[0])
        dFF.append(np.multiply(100,np.divide(y_df[0],y_all[0])))
        std_dFF.append(np.std(dFF[0]))
    else:
        for i in range(0, len(s465)):
            s_ind.append(np.where(timex[i] > trim[i])[0][0])
            e_ind.append(np.where(timex[i]  > end)[0][0])
            trimmed_time.append(timex[i][s_ind[i]:e_ind[i]])
            trimmed_s465.append(s465[i].data[s_ind[i]:e_ind[i]])
            trimmed_s405.append(s405[i].data[s_ind[i]:e_ind[i]])

            #process data
            baseline.append(np.polyfit(np.array(trimmed_s405[i]), np.array(trimmed_s465[i]), 1))
            y_all.append(np.multiply(baseline[i][0], np.array(trimmed_s405[i])) + baseline[i][1])
            y_df.append(np.array(trimmed_s465[i]) - y_all[i])
            dFF.append(np.multiply(100,np.divide(y_df[i],y_all[i])))
    print("you can ignore that warning: when comparing polyfit to" +
            " the equivalent in matlab, which gives no errors and yielded the same answer")

    
    return [trimmed_time, dFF, std_dFF]


def send_sql(data,subjects,session,notes):
    #sql engine for pandas (presumably)
    engine = create_engine("mysql+pymysql://{user}:{pw}@localhost/{db}".format(user="", pw="", db = "gcampptone2"))
    md= MetaData(engine)
    for s in range(0,len(notes)):
        if not engine.dialect.has_table(engine,'photodata'):
            photodata = Table('photodata', md, 
                Column('idx', Integer, primary_key=True, nullable=False, autoincrement=True),
                Column('Subject',Integer), 
                Column('Session',String(length=10)), 
                Column('Note', String(length=100)), 
                Column('TimeX', Float), 
                Column('dFF', Float))
            md.create_all(engine)

        #pull table as a class
        Base = automap_base()
        Base.prepare(engine,reflect=True)
        photodata = Base.classes.photodata

        #create data dictionary
        list_session = [session]*len(data[0][s])
        list_subject = [subjects[s]]*len(data[0][s])
        list_notes =  [notes[s]]*len(data[0][s])
        print("reorganizing data for push to sql")
        data_list_dicts = []
        for i in range(0, len(data[0][s])):
            data_list_dicts.append(dict(Subject=list_subject[i], Session=list_session[i],
            Note=list_notes[i], TimeX=data[0][s][i].tolist(), dFF=data[1][s][i].tolist()))
        
        print("beginning push to SQL")
        #start session
        SQLsession = Session(engine)
        SQLsession.bulk_insert_mappings(photodata,data_list_dicts)
        SQLsession.flush()
        SQLsession.commit()
        print("data pushed to SQL db for subject:"+subjects[s])
    SQLsession.close()


#Photometry data location
datapath = "C:\\Users\\carte\Dropbox\\Carter Backup\\PostDocStuff\\RISDT\\GCamp6f PTone (6 succesful surgeries thus far)\\Photometry Data"

#Check to see which subjects have photometry data
folders = os.listdir(datapath)

#Update data 
for f in folders:
    obtained_datapath = os.path.join(datapath,f)
    sessions = os.listdir(obtained_datapath)
    for s in sessions:
        Subjects_465 = []
        Subjects_405 = []
        final_datapath = os.path.join(obtained_datapath,s)
        import_tdt = read_block(final_datapath)
        if '&' in f:
            subjs = f.split()
            subjs.remove('&')
        else:
            subjs = [f]
        if len(subjs) == 1:
            test465A = import_tdt.streams['_465A'].data[1000]
            test465C = import_tdt.streams['_465C'].data[1000] 
            if test465A > test465C:
                Subjects_465.append(import_tdt.streams['_465A'])
                Subjects_405.append(import_tdt.streams['_405A'])
            else:
                Subjects_465.append(import_tdt.streams['_465C'])
                Subjects_405.append(import_tdt.streams['_405C'])

        else:
            Subjects_465.append(import_tdt.streams['_465A'])
            Subjects_405.append(import_tdt.streams['_405A'])
            Subjects_465.append(import_tdt.streams['_465C'])
            Subjects_405.append(import_tdt.streams['_405C'])
        time = get_time(Subjects_465,Subjects_405)
        trim, note = evaluate_rawdata(time, Subjects_465, Subjects_405, subjs)
        processed_data = trim_and_process(trim,import_tdt.info.duration.seconds, time, Subjects_465, Subjects_405)
        send_sql(processed_data,subjs,s,note)            
        

        
        
