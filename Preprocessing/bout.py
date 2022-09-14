import os
from glob import glob
import shutil

import numpy as np
import pandas as pd
import datetime as dt

from tqdm import tqdm

bout_dir = os.path.join("Data","Bout")
if os.path.exists(bout_dir):
    shutil.rmtree(bout_dir)
os.makedirs(bout_dir)

minute_dir = os.path.join("Data","Minute")
if os.path.exists(minute_dir):
    shutil.rmtree(minute_dir)
os.makedirs(minute_dir)

for file in tqdm(sorted(glob(os.path.join("Data","Raws","*.csv")))):
    uid = os.path.splitext(os.path.basename(file))[0]
    step_count = pd.read_csv(file, index_col = None, header = 0)
    step_count.loc[:,'READABLE_START'] = pd.to_datetime(step_count["READABLE_START"])
    step_count.loc[:,'READABLE_END'] = pd.to_datetime(step_count["READABLE_END"])
    
    step_count.drop_duplicates(inplace = True)
    
    # Use same type of device in same time.
    # Possible, but only few of users show this behavior.
    # repeat_check = step_count.groupby(["START","DEVICE_TYPE"]).agg(cnt = ("DEVICE_UUID", "count"))
    # if not set(repeat_check['cnt']).issubset([1]):
    #     print(uid, "same type of device used in same time", "{:.1f}%({})".format(repeat_check.query('cnt > 1').shape[0]/repeat_check.shape[0] * 100, repeat_check.query('cnt > 1').shape[0]), sep= " : ")
    #     continue
    
    # All users were valid
    # Check Duration of each row
    check_timediff = step_count['END'].values - step_count['START'].values
    if not set(check_timediff).issubset([60*1000, 60*1000-1, 60* 1000 - 1000]):#precision of timestamp make such difference
        print(uid, "there is a row does not match duration", f"{set(check_timediff)}", sep= " : ")
        continue

    # All Users were valid.
    # Check Start of each row is Minute Level(seconds == 0)
    valid_start = True
    for val in step_count['START'].values:
        if val% 60000 != 0:
            valid_start = False
            continue
    if not valid_start:
        print(uid, "Start does not have minute level")
    
    # Trim first date and last date of each user
    first_date = step_count.iloc[0]['READABLE_START'].date() + dt.timedelta(days = 1)
    last_date = step_count.iloc[-1]['READABLE_END'].date()
    step_count.query("READABLE_START >= @first_date and READABLE_START < @last_date", inplace = True)
 


    step_count = step_count.groupby(['START','UTC','READABLE_START','DEVICE_TYPE','DEVICE_UUID']).agg(
        STEP = ('STEP', 'sum'),
    ).reset_index()
    step_count = step_count.groupby(['START','UTC','READABLE_START','DEVICE_TYPE']).agg(
        STEP = ('STEP', 'mean'),
    )
    step_count = step_count.unstack(level = 3, fill_value= 0)
    step_count.columns = [val + '_STEP' for val in step_count.columns.get_level_values(1)]
    step_count.reset_index(inplace = True, drop = False)

    step_count.to_csv(os.path.join(minute_dir, f"{uid}.csv"), index = False)

    # Aggregate Consecutive Step Count
    diff = [0,*step_count['START'].diff().values[1:]]

    not_consecutive = [0 if val//(60*1000) == 1 else 1 for val in diff]
    bout_idx = np.cumsum(not_consecutive)
    step_count['INDEX'] = bout_idx
    step_count = step_count.groupby("INDEX").agg(
        START = ('START', 'first'),
        END = ('START', 'last'),
        WEARABLE_STEP= ('WEARABLE_STEP','sum'),
        PHONE_STEP = ('PHONE_STEP','sum'))

    step_count.loc[:,'END'] = [val + 60 * 1000 for val in step_count['END'].values]
    step_count.loc[:,'DUT'] = (step_count['END'].values - step_count['START'].values)//(60* 1000)

    step_count.loc[:,'UTC'] = ['UTC+0900'] * step_count.shape[0]
    for col in ['START','END']:
        step_count.loc[:,'READABLE_'+col] = pd.to_datetime(step_count[col], unit = 'ms') + dt.timedelta(hours = 9)



    bout_types = np.zeros(step_count.shape[0])
    bout_types += (step_count['WEARABLE_STEP'].values > 0) * 2
    bout_types += (step_count['PHONE_STEP'].values > 0) 
    bout_types = bout_types.astype(int)
    bout_types -= 1
    TYPES = ['PHONE_ONLY','WEARABLE_ONLY','BOTH']
    bout_types = list(map(lambda x: TYPES[x], bout_types))
    step_count.loc[:, "BOUT_TYPE"] = bout_types

    steps = []
    for pstep, wstep, btype in step_count[['PHONE_STEP','WEARABLE_STEP','BOUT_TYPE']].values:
        if btype == "BOTH":
            steps.append((pstep + wstep)/2)
        else:
            steps.append(pstep+wstep)
    step_count.loc[:, 'STEP'] = steps

    step_count[['START','END','UTC','READABLE_START','READABLE_END',\
        "PHONE_STEP","WEARABLE_STEP",\
        "BOUT_TYPE", "STEP", "DUT"]].to_csv(os.path.join(bout_dir, f"{uid}.csv"),index = False)

