import os
import datetime
from fitparse import *
import pandas as pd
import numpy as np
# import matplotlib.pyplot as plt  (not needed I guess)
from tqdm import tqdm
from datetime import datetime
import re

lthr = 191.0  # Lactate Threshold Heart Rate Value
my_ftp = 250  # Functional Threshold Power
# start_date = datetime.date(2020, 3, 1)
# end_date = datetime.date.today()
directory = 'fitfiles'

# experimental, for variableHRsamplingInterval management + accurate TRIMP calc
eulersNum = 2.7182818
my_maxhr = 212
my_rhr = 50
my_sex = "MALE"
if my_sex == "MALE":
    my_baseconstant = .64
    my_yvalue = 1.92
else:
    my_yvalue = 1.67
    my_baseconstant = .86
my_hrrAtLT = ( (lthr - my_rhr) / (my_maxhr - my_rhr) )
sixtyatLTHR_SS = 60 * my_hrrAtLT * my_baseconstant * (eulersNum ** (my_yvalue * my_hrrAtLT))
N_ova_hundy = sixtyatLTHR_SS / 100
hundy_ova_N = 100 / sixtyatLTHR_SS

#if files need renaming
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
    :param workout_file:
    :return dataframe:
    """
    # Load the fitfile
    fitfile = FitFile(workout_file)

    # This is an ugly hack to avoid timing issues
    while True:
        try:
            fitfile.messages
            break
        except KeyError:
            continue

    # Get all data messages that are of type record
    workout = []
    for record in fitfile.get_messages('record'):
        r = {}
        # Go through all the data entries in this record
        for record_data in record:
            r[record_data.name] = record_data.value

        workout.append(r)
    """workout_df = pd.DataFrame(workout)
    workout_df.fillna(method='ffill', inplace=True)
    workout_df.fillna(method='backfill', inplace=True)"""
    workout = np.array(workout)
    return workout

def get_date(workout_df):
    """
    Gets the workout date.
    :param workout_df:
    :return date:
    """
    workout_date = workout_df['timestamp'][0].date()

    return workout_date

def gett_date(string):
    split = []
    for i in re.split("-|T|:| ", string)[:-1]:
        if (i[0] == '0'):
            i = i[1:]
        split.append(eval(i))
    date = datetime(split[0], split[1], split[2], split[3], split[4], split[5])
    return date

def difference_between_dates(date1, date2):
    secs = ((date2 - date1).seconds)
    # minutes = (date2 - date1).minutes
    # hours = (date2 - date1).hours * 60
    days = (date2 - date1).days * 24 * 60 * 60
    return secs + days

# Loop through fitfile directory
for filename in tqdm(os.listdir(directory)):
    if filename.endswith('.fit'):
        workout = load_workout((os.path.join(directory, filename)))

        if 'heart_rate' in workout[0]:
            print(workout[0])
            print(workout[1])
            print(workout[2])
            print(filename)

            #NOTE 7/19/21 IT WORKS FINE TO HERE, BUT SOMETHING IS OFF W THE HRSS/TSS/TRIMP CALC--NEED TO REWORK/REORGANIZE/REDO!!!


            deltaTs = [] # CURRENTLY IN SECONDS
            for i in range(len(workout) - 1):
                # print(workout[i])
                deltaTs.append(difference_between_dates(workout[i]["timestamp"], workout[i + 1]["timestamp"]))
            #print(deltaTs)

            hartreight = [] #list of instantaneous heart rate readings
            for i in range(len(workout) - 1):
                hartreight.append(workout[i]["heart_rate"])
            #print(hartreight)
            HRrez = [(i - my_rhr)/(my_maxhr - my_rhr) for i in hartreight]
            #print(HRrez)
            HRrezXtime = [(deltaTs[i]) * (HRrez[i]) for i in deltaTs]
            #print(HRrezXtime)
            HRrezXtimeXbase = [i * my_baseconstant for i in range(len(HRrezXtime))]
            #print(HRrezXtimeXbase)

            HRrezXyvalue = [i * my_yvalue for i in HRrez]
            #print(HRrezXyvalue)
            etotheHRrezYvalue = [eulersNum ** i for i in HRrezXyvalue]
            #print(etotheHRrezYvalue)

            rawHR_TSS_list = [(HRrezXtimeXbase[i]) * (etotheHRrezYvalue[i]) for i in range(len(HRrezXtimeXbase))]
            #print(rawHR_TSS_list)

            TRIMPexp_inseconds = sum(rawHR_TSS_list)
            #print(TRIMPexp_inseconds)

            TRIMPexp = TRIMPexp_inseconds /60
            print(TRIMPexp)

            HR_SS = TRIMPexp * (hundy_ova_N)
            print(HR_SS)



            ''' or maybe use this formula if the above does not match up... hmmmmmm
            yonk = sum((deltaTs[i] * HRR1[i] * my_baseconstant * (eulersNum ** (my_yvalue * HRR1[i]))) * hundy_ova_N 
                for i in deltaTs)'''

        else:
            print("issue w HR in: " + filename + "  :(")
            continue
            # File does not contain power/HR
