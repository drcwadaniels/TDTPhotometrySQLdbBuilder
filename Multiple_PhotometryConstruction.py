import os
import re
import numpy as np
import pandas as pd
import pymysql 
import mysql.connector 
from mysql.connector import errorcode
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Float, Date, PrimaryKeyConstraint, VARCHAR, insert
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from datetime import date
import csv 
import matplotlib.pyplot as plt
from sqlalchemy.sql.sqltypes import DECIMAL
from tdt import read_block, epoc_filter, download_demo_data

#Photometry data location
datapath = "C:\\Users\\carte\\Dropbox\\Carter Local\\PostDocStuff\\RISDT\\PTone Fiber\\Photometry Data"

#Check to see which subjects have photometry data
folders = os.listdir(datapath)

def get_time(s465,s405):
    timex = []
    if len(s465) == 1:
        timex.append(np.linspace(1,len(s465[0].data), len(s465[0].data))/s465[0].fs)
    else:
        for i in range(0, len(s465)):
            timex.append(np.linspace(1,len(s465[i].data), len(s465[i].data))/s465[i].fs)
    return timex

def evaluate_rawdata(time,Subjects_465,Subjects_405, subjs):
    trim = []
    note = []
    if len(Subjects_465) == 1:
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
        for i in range(0, len(Subjects_465)):
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
            " the equivalent in matlab, which gives no errors it yielded the same answer")

    
    return [trimmed_time, dFF, std_dFF]


def send_fiber(data,subjects,session,notes):
    md= MetaData(engine)
    test_conn = engine.connect()
    for s in range(0,len(notes)):
        if not engine.dialect.has_table(test_conn,'photodata'):
            photodata = Table('photodata', md, 
                Column('idx', Integer, primary_key=True, nullable=False, autoincrement=True),
                Column('Subject',Integer), 
                Column('Session',String(length=10)), 
                Column('Note', String(length=100)), 
                Column('TimeX', DECIMAL(19,10)), 
                Column('dFF', DECIMAL(19,10)))
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
        
        print("pushing fiber data to SQL")
        #start session
        SQLsession = Session(engine)
        SQLsession.bulk_insert_mappings(photodata,data_list_dicts)
        SQLsession.flush()
        SQLsession.commit()
        print("fiber data pushed to SQL db for subject:"+subjects[s])
    SQLsession.close()

def sort_events(s,subjects,all_events):
    event_list_dict = []
    for i in range(0,len(subjects)):
        if not all_events[i]:
            print("empty events")
        else:
            for e in all_events[i]:
                subject_list = [int(subjects[i])]*len(e.onset)
                session_list = [s]*len(e.onset)
                name_list = [e.name]*len(e.onset)
                onset_list = e.onset.tolist()
                offset_list = e.offset.tolist()
                for j in range(0,len(onset_list)):
                    event_list_dict.append(dict(Subject = subject_list[j], Session = session_list[j],
                    Name = name_list[j], Onset = onset_list[j], Offset = offset_list[j]))
    return event_list_dict

def send_events(event_list_dict):
    md= MetaData(engine)
    test_conn = engine.connect()
    if not engine.dialect.has_table(test_conn,'eventdata'):
        eventdata = Table('eventdata', md, 
            Column('idx', Integer, primary_key=True, nullable=False, autoincrement=True),
            Column('Subject',Integer), 
            Column('Session',String(length=10)), 
            Column('Name', String(length=100)), 
            Column('Onset', DECIMAL(19,10)), 
            Column('Offset', DECIMAL(19,10)))
        md.create_all(engine)

    #pull table as a class
    Base = automap_base()
    Base.prepare(engine,reflect=True)
    eventdata = Base.classes.eventdata
        
    print("pushing event data to sql")
    #start session
    SQLsession = Session(engine)
    SQLsession.bulk_insert_mappings(eventdata,event_list_dict)
    SQLsession.flush()
    SQLsession.commit()
    print("event data pushed to SQL db for all subject")
    SQLsession.close()    

def pullfiberdata(s,f,import_tdt):
    Subjects_465 = []
    Subjects_405 = []
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
    processed_data = trim_and_process(trim,import_tdt.info.duration.seconds-1, time, Subjects_465, Subjects_405)
    send_fiber(processed_data,subjs,s,note)

def pulleventdata(s,f,import_tdt):
    eventsA = []
    eventsB = []
    if '&' in f:
        subjs = f.split()
        subjs.remove('&')
    else:
        subjs = [f]
    if len(subjs) == 1:
        test465A = import_tdt.streams['_465A'].data[1000]
        test465C = import_tdt.streams['_465C'].data[1000] 
        if test465A > test465C:
            eventsA.append(import_tdt.epocs.PC0_)
            eventsA.append(import_tdt.epocs.PC2_)
            eventsA.append(import_tdt.epocs.PC4_)
            eventsA.append(import_tdt.epocs.PC6_)
        else:
            eventsB.append(import_tdt.epocs.PC1_)
            eventsB.append(import_tdt.epocs.PC3_)
            eventsB.append(import_tdt.epocs.PC5_)
            eventsB.append(import_tdt.epocs.PC7_)
    else:
        eventsA.append(import_tdt.epocs.PC0_)
        eventsA.append(import_tdt.epocs.PC2_)
        eventsA.append(import_tdt.epocs.PC4_)
        eventsA.append(import_tdt.epocs.PC6_)
        eventsB.append(import_tdt.epocs.PC1_)
        eventsB.append(import_tdt.epocs.PC3_)
        eventsB.append(import_tdt.epocs.PC5_)
        eventsB.append(import_tdt.epocs.PC7_)
    all_events = [eventsA,eventsB]
    event_list_dict = sort_events(s,subjs,all_events)
    send_events(event_list_dict)


#Update data 
for f in folders:
    obtained_datapath = os.path.join(datapath,f)
    sessions = os.listdir(obtained_datapath)
    for s in sessions:
            final_datapath = os.path.join(obtained_datapath,s)
            import_tdt = read_block(final_datapath)
            engine = create_engine("mysql+pymysql://{user}:{pw}@localhost/{db}".format(user="root", pw="", db = "fiberptone"))
            pullfiberdata(s,f,import_tdt) 
            pulleventdata(s,f,import_tdt)         
        


        
