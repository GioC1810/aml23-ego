import os
import pickle
import pandas as pd
import numpy as np
import math
import torch

from scipy.signal import butter, lfilter
import matplotlib.pyplot as plt


def lowpass_filter(data, cutoff_freq, sampling_rate, order=4):
    nyquist = 0.5 * sampling_rate
    normal_cutoff = cutoff_freq / nyquist
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    y = lfilter(b, a, data)
    return y

def preprocessing(emg_data, duration):

    sampling_rate=len(emg_data)/duration
    # Apply low-pass filter
    filtered_emg=lowpass_filter(emg_data, cutoff_frequency, sampling_rate)

            
    # Jointly normalize and shift to the range [-1, 1]
    min_value = np.amin(filtered_emg,axis=0, keepdims=True)
    max_value = np.amax(filtered_emg,axis=0, keepdims=True)
    normalized_and_shifted_data = 2 * (filtered_emg - min_value) / (max_value - min_value) - 1
    #print(normalized_and_shifted_data)
    return normalized_and_shifted_data

def create_subactions(action_data, segment_duration=5, overlap=1):
    """
    Create subactions from the given action interval and return information for each subaction.

    Parameters:
    - action_data: Dictionary containing information about the action instance.
    - segment_duration: Duration of each subaction in seconds.
    - overlap: Overlapping duration between consecutive subactions in seconds.
    - num_subactions: Number of subactions to create.

    Returns:
    - List of dictionaries, each containing information about a subaction.
    """

    start_time_s = action_data['start_time_s']
    end_time_s = action_data['end_time_s']
    duration_s = action_data['duration_s']

    # Calculate the number of subactions
    num_subactions = math.ceil(duration_s/segment_duration)

    subactions_info = []

    data_left=preprocessing(action_data['emg_data_left'], duration_s)
    data_right=preprocessing(action_data['emg_data_right'],duration_s)
    
    # print("Original LEFT: ", action_data["emg_data_left"].shape[0])
    # print("Original RIGHT: ", action_data["emg_data_right"].shape[0])

    row_matrix = max(data_left.shape[0],data_right.shape[0]) // num_subactions

    for i in range(num_subactions):

        subaction_start_time = start_time_s + i * (segment_duration - overlap)
        subaction_end_time = subaction_start_time + segment_duration


        start_index = i * row_matrix
        end_index = (i + 1) * row_matrix
        emg_data_subsample_l = data_left[start_index:end_index, :]
   
        emg_data_subsample_r = data_right[start_index:end_index, :]
        
        emg_data_subsample_len = min(emg_data_subsample_l.shape[0], emg_data_subsample_r.shape[0])

        # Concatenazione lungo l'asse 1 (orizzontale)
        emg_data_final = np.concatenate((emg_data_subsample_l[0:emg_data_subsample_len, :], emg_data_subsample_r[0:emg_data_subsample_len, :]), axis=1)

        #print("LEFT: ",emg_data_subsample_l.shape[0])
        #print("RIGHT ", emg_data_subsample_r.shape[0])
        #print("FINAL ", emg_data_final.shape[0])
   
   

        if emg_data_final.shape[0] > 0:
   
            subaction_data = {
                'label': action_data['label'],
                'index': action_data['index'],
                'start_time_s': subaction_start_time,
                'end_time_s': subaction_end_time,
                'duration_s': segment_duration,
                'emg_data': emg_data_final,
            }
            subactions_info.append(subaction_data)
            
    return subactions_info
cutoff_frequency = 5  # Cutoff frequency in Hz


# Percorso della cartella di cui vogliamo ottenere i nomi dei file
cartella = './EMG_data/'

# Ottieni i nomi dei file nella cartella
nomi_file = os.listdir(cartella)
videos_name=[]
split="train"
""" # formato esempio emg-data-S05_2-left-test.pkl
for file in nomi_file:
    print(file)
    if file== 'emg_spectrogram_train.pkl' or 'emg_spectrogram_test.pkl' :
        continue
    video=file.split("-")[2]
    train=file.split("-")[3].split(".")[0]==split
    if train:
        videos_name.append(video)
"""

# Ottieni i nomi dei file nella cartella
my_dict={}
nomi_file = os.listdir(cartella)
for file in nomi_file:
    
    if file.startswith("emg-data-S"):
        print("Elaborating  file ", file)
        is_right_split=file.split("-")[3].split(".")[0]==split
    
        if is_right_split :
            with open(cartella+file, 'rb') as f_pickle:
                dati=pickle.load(f_pickle)
                df=pd.DataFrame(dati)
                for d in dati:

                    subactions=create_subactions(d)

                    for s in subactions:
                        next_key = len(my_dict) 
                        #print(next_key)
                        my_dict[next_key] = {"emg_data":s['emg_data'],"label":s['label']}
                

print(len(my_dict))
with open('./emg_data_preprocessed_'+split+'.pkl', 'wb') as f_pickle:
    pickle.dump(my_dict, f_pickle)