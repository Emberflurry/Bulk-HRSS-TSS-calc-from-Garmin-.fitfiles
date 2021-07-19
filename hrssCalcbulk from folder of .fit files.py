import os
import datetime
from fitparse import *
import pandas as pd
import numpy as np
from tqdm import tqdm
from datetime import datetime
import re
# import matplotlib.pyplot as plt  (not needed I guess)

directory = 'fitfiles' #may want to make this more flexible--ie: not just in the directory of the code...works for now tho and not bad.

# HRSS Calc--PERSONAL INFO--REQUIRED FOR CALCULATIONS TO BE ACCURATE
lthr = 191.0  #heart rate(bpm) at lactate threshold
my_maxhr = 212 #max heart rate(bpm)
my_rhr = 50 #resting heart rate(bpm)
my_sex = "MALE"

eulersNum = 2.7182818 #duh

if my_sex == "MALE":
    my_baseconstant = .64
    my_yvalue = 1.92
else:
    my_yvalue = 1.67
    my_baseconstant = .86
#component calcs of the multi-part exponential HRSS equation:
my_hrrAtLT = ( (lthr - my_rhr) / (my_maxhr - my_rhr) )
sixtyatLTHR_SS = 60 * my_hrrAtLT * my_baseconstant * (eulersNum ** (my_yvalue * my_hrrAtLT)) #aka "N" in relevant equations
N_ova_hundy = sixtyatLTHR_SS / 100
hundy_ova_N = 100 / sixtyatLTHR_SS


#if files need renaming INTEGRATE IN THE FUTURE!!!! ESPECIALLY WITH FULL GARMIN->OUTPUT WORKFLOW AUTO!!!
"""rename_dict = {'FIT': 'fit'}
for filename in os.listdir(directory):
    base_file, ext = os.path.splitext(filename)
    ext = ext.replace('.','')
    if ext in rename_dict:
        new_ext = rename_dict[ext]
        new_file = base_file + '.' + new_ext
        old_path = os.path.join(directory, filename)
        new_path = os.path.join(directory, new_file)
        os.rename(old_path, new_path)"""

def load_workout(workout_file):
    """
    Load fitfile and transforms
    it into a pandas Dataframe.
    Nan Values are replaced.
    """
    fitfile = FitFile(workout_file)
    #This is an ugly hack to avoid timing issues
    while True:
        try:
            fitfile.messages
            break
        except KeyError:
            continue
    #Get all data messages that are of type "record"
    workout = []
    for record in fitfile.get_messages('record'):
        r = {}
        #Go through all the data entries in this record
        for record_data in record:
            r[record_data.name] = record_data.value
        #add the record(s) to the workout file
        workout.append(r)

    #not used, don't remember why, but im not touching it.
    """workout_df = pd.DataFrame(workout)
    workout_df.fillna(method='ffill', inplace=True)
    workout_df.fillna(method='backfill', inplace=True)"""

    #save as a df (specifically a numpy array)
    workout = np.array(workout)
    return workout

def get_date(workout_df):
    #pass the workout df, returns the date
    workout_date = workout_df['timestamp'][0].date()
    return workout_date

def gett_date(string):
    #splits a date that is input for future timestamp parsing
    split = []
    for i in re.split("-|T|:| ", string)[:-1]:
        if (i[0] == '0'):
            i = i[1:]
        split.append(eval(i))
    date = datetime(split[0], split[1], split[2], split[3], split[4], split[5])
    return date

def difference_between_dates(date1, date2):
    #parses timestamps (which are still stored as date data (haha)) for changes in time between recordings
    secs = (date2 - date1).seconds
    mins = (secs / 60)
    return round(mins,4)  #NEW, ROUNDS TO 4 DP

# Loop through fitfile directory, load hr data, calculate HRSS
for filename in tqdm(os.listdir(directory)):
    if filename.endswith('.fit'):
        workout = load_workout((os.path.join(directory, filename)))

        if 'heart_rate' in workout[0]:
            #printing first 2 rows to manually check presence/forms
            print(workout[0])
            print(workout[1])
            print(filename)

            #for HRSS: form is SUM (Ti*HRRi*baseconst * e^(yval*HRRi) ) * 100/(60*HHRlt*basconst * e^(yval*HRRlt) )
            #simplified: SUM (ATERM) * BTERM
            #workflow is: calc aterm*bterm indiv, then sum

            instantChT = [] #list of "instantaneous" changes in time
            for i in range(len(workout) - 1):
                # print(workout[i])
                instantChT.append(difference_between_dates(workout[i]["timestamp"], workout[i + 1]["timestamp"]))
            print(instantChT) #this works

            instantHr = [] #list of (hopefully corresponding) instantaneous heart rate readings
            for i in range(len(workout) - 1):
                instantHr.append(workout[i]["heart_rate"])
            print(instantHr)

            HRRi = [] #list of instantaneous heart rate reserve values
            for i in range(len(instantHr)):
                HRRi.append((instantHr[i]-my_rhr)/(my_maxhr-my_rhr))
            print(HRRi)

            AtermBterm=[] #see simplified equation roughly 20 lines above
            for i in range(len(instantChT)):
                AtermBterm.append( (instantChT[i]*HRRi[i]*my_baseconstant*(eulersNum**(my_yvalue*HRRi[i])) )*hundy_ova_N)
            print(AtermBterm)
            print(sum(AtermBterm))

        else:
            print("issue w HR in: " + filename + "  :_(...either lacking HR data or is mislabeled, i think.")
            continue
   #HERE COULD ADD THE FIT->fit CONVERTER CODE TO FIX IF ENDS IN .FIT and not .fit
            
                    
