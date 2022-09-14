# Remove other data rather than step count
# Demographics can be found here.

import os
from glob import glob
import shutil

import pandas as pd
import numpy as np
import datetime as dt

from tqdm import tqdm

src =  os.path.join("/mnt","CarryingWearing","Raws")
target = "Data"

if os.path.exists(target):
    shutil.rmtree(target)
os.makedirs(os.path.join(target, "Raws"))

user_profiles = []
device_types = []
for folder in tqdm(sorted(os.listdir(src))):
    profile = {'UID': folder}
    # There are two types of step count csv file name due to difference of OS
    step_count_csvs_a = glob(os.path.join(src, folder,"**", "com.samsung.shealth.tracker.pedometer_step_count.*.csv"), recursive = True)
    step_count_csvs_b = glob(os.path.join(src, folder,"**", "com.samsung.health.step_count.*.csv"), recursive = True)
    if len(step_count_csvs_a) + len(step_count_csvs_b) != 1:
        print(folder, "Can not identify Step count file", f"A = {len(step_count_csvs_a)}, B = {len(step_count_csvs_b)}", sep = " : ")
        continue    
    # A is from Android B is IOS
    profile['TYPE'] = "A" if len(step_count_csvs_a) == 1 else "B"
    step_count_csv = (step_count_csvs_a + step_count_csvs_b)[0]
    profile['COLLECTED'] = step_count_csv.split('.')[-2]

    #get Demographics
    user_csvs = glob(os.path.join(src, folder, "**","com.samsung.health.user_profile.*.csv"), recursive = True)
    if len(user_csvs) != 1:
        print(folder, "Can not identify User file", f"{len(user_csvs)}", sep = " : ")
        continue
    
    n_cols = pd.read_csv(user_csvs[0], skiprows = [0], sep=',', nrows=1).shape[1] 
    user_profile = pd.read_csv(
        user_csvs[0],
        skiprows=[0],
        header=0,
        usecols= range(n_cols),
        index_col= None,
    )
    birth_date = user_profile.query("key == 'birth_date'")['text_value']
    if birth_date.shape[0] != 1:
        print(folder, "Can not identify birth_date", f"{birth_date}", sep = " : ")
        birth_date = np.nan
    else:
        birth_date = birth_date.values[0]
    profile['BIRTH'] = birth_date

    gender = user_profile.query("key == 'gender'")['text_value']
    if gender.shape[0] == 1:
        gender = gender.values[0]
    else:
        print(folder, "Can not identify gender", f"{gender}", sep = " : ")
        gender = np.nan
    profile['GENDER'] = gender

    # Remove Unneccessaries of step_count files
    n_cols = pd.read_csv(step_count_csv, skiprows = [0], sep=',', nrows=1).shape[1]
    step_count = pd.read_csv(step_count_csv,
                    skiprows= [0],
                    index_col= None, 
                    header = 0,
                    usecols = range(n_cols ),
                    encoding= "utf-8")
    step_count.columns = [val.split('.')[-1] for val in step_count.columns]
    for col in ['run_step', 'walk_step', 'duration']:
        if col not in step_count.columns:
            step_count.loc[:,col] = [np.nan] * step_count.shape[0]
    step_count.rename({
        'start_time': 'START',
        'end_time': 'END',
        'duration': 'DUT',
        'count': 'STEP',
        'speed': 'SPEED',
        'distance': 'DIST',
        'calorie': 'CAL',
        'deviceuuid': 'DEVICE_UUID',
        'run_step': 'RUN',
        'walk_step': 'WALK', 
    }, axis = 1, inplace = True)

    # Timestamp preprocessing into milliseconds of UTC+0000
    
    # Check UTC of step count data
    # P069, P104, P108 gives different time offset
    # They set country info to different country but stayed in UTC+0900.
    # offset = step_count['time_offset'].unique()
    # if len(offset) != 1:
    #     print(folder, "offset has changed", offset, sep= " : ")
    #     continue
    # if offset[0] not in [32400000, 'UTC+0900']:
    #     print(folder,  "offset is not UTC+0900", offset[0], sep = " : ")
    #     continue
    step_count.loc[:, 'UTC'] = ['UTC+0900'] * step_count.shape[0]

    # Readable timestamp used Korean AM/PM... remove it.
    for column in ['START','END']:
        ts = []
        for timestamp in step_count[column].values:
            if '오후' in timestamp:
                timestamp = ''.join(timestamp.split("오후"))
                tmp = dt.datetime.strptime(timestamp,"%Y. %m. %d.  %I:%M:%S")
                tmp += dt.timedelta(hours = 12)
            elif '오전' in timestamp:
                timestamp = ''.join(timestamp.split("오전"))
                tmp = dt.datetime.strptime(timestamp,"%Y. %m. %d.  %I:%M:%S")
            elif "-" in timestamp:
                tmp = dt.datetime.strptime(timestamp,"%Y-%m-%d %H:%M:%S.%f")
            else:
                tmp = dt.datetime.strptime(timestamp,"%Y. %m. %d. %H:%M:%S")
            # datetime object has default timezone as local, remove it.
            tmp = tmp.replace(tzinfo = dt.timezone.utc)
            ts.append(int(tmp.timestamp() * 1000))
        
        step_count.loc[:, column] = ts
    for column in ['START','END']:
        step_count.loc[:, 'READABLE_' + column] = pd.to_datetime(step_count[column], unit = 'ms') + dt.timedelta(hours = 9)
    
    # Get Device Profile
    device_csvs = glob(os.path.join(src, folder,"**", "com.samsung.health.device_profile.*.csv"),recursive=True)
    if len(device_csvs) != 1:
        print(folder, "Can not identify device", f"{len(device_csvs)}", sep = " : ")
        continue
    n_cols = pd.read_csv(device_csvs[0], skiprows = [0], sep=',', nrows=1).shape[1]
    device_profile = pd.read_csv(
        device_csvs[0],
        skiprows=[0],
        header=0,
        usecols= range(n_cols),
        index_col= False,
    )
    logged = step_count['DEVICE_UUID'].unique()
    device_profile.query("deviceuuid in @logged", inplace = True)
    wearables = device_profile.query("device_group == 360003")['name'].unique()
    phones = device_profile.query("device_group == 360001")['model'].unique()
    if len(wearables) == 0:
        print(folder, "No wearables are used in the periods", sep = " : ")
        continue
    if len(phones) == 0:
        print(folder, "No smartphones are used in the periods", sep = " : ")
        continue
    use_samsung = True
    for phone in phones:
        if 'SM-' not in phone:
            print(folder, "Smartphone not from Samsung {}".format(phone), sep = " : ")
            use_samsung = False
    if not use_samsung:
        continue
    profile['WEARABLES'] =  ', '.join(wearables)
    profile['PHONES'] =  ', '.join(phones)
    user_profiles.append(profile)

    for group, uuid, model, name in device_profile[['device_group', 'deviceuuid','model','name']].values:
        if group == 360003:
            device_types.append({'UID': folder, 'DEVICE_UUID': uuid, 'TYPE': 'WEARABLE', 'MODEL': name })
        elif group == 360001:
            device_types.append({'UID': folder, 'DEVICE_UUID': uuid, 'TYPE': 'PHONE', 'MODEL': model})

    wearable_uuid = device_profile.query("device_group == 360003")['deviceuuid'].unique()
    phone_uuid = device_profile.query("device_group == 360001")['deviceuuid'].unique()
    step_count.loc[:,"DEVICE_TYPE"] = ["WEARABLE" if val in wearable_uuid \
        else ("PHONE" if val in phone_uuid else "UNKNOWN") \
        for val in step_count['DEVICE_UUID'].values]

    step_count.sort_values(by='START', inplace = True)
    step_count[['START','END','UTC', 'READABLE_START', 'READABLE_END',\
        'STEP', 'RUN','WALK', 'SPEED', 'DUT', 'DIST', 'CAL',\
        'DEVICE_UUID', 'DEVICE_TYPE']].to_csv(os.path.join(target, "Raws", folder +".csv"), index = False)

pd.DataFrame(user_profiles).to_csv(os.path.join(target, "meta.csv"), index = False)
pd.DataFrame(device_types).to_csv(os.path.join(target, "device_type.csv"), index = False)
