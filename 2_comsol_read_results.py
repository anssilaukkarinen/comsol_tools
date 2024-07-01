# -*- coding: utf-8 -*-
"""
Created on Fri Jun 28 15:28:29 2024

@author: laukkara


Read in data
- This is tailored separately for each results file as needed

Calculate indicators
- This might be ok to do here, because here it is easier to set the 
  sensitivity classes etc

Save data to file
- No analysis is done here, everything is done later in other files


[T] = degC
[RH] = 0...100 %


Sensitivity classes:
    - wood: vs, 0.5
    - MW: mr, 0.1
    - vapor barrier: mr, 0.1

"""

import os
import pickle
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import helper



# The folders can be changed as needed
input_folder = r'S:\91202_Rakfys_yhteiset\Tiiliverhous\2_Laskenta\results_data'
output_folder = r'S:\91202_Rakfys_yhteiset\Tiiliverhous\2_Laskenta\results_data'


# input_folder = r'C:\Temp\tiiliverhous\results_data'
# output_folder = r'C:\Temp\tiiliverhous\results_data'


if not os.path.exists(output_folder):
    os.makedirs(output_folder)




data = {}


#############



# 

print('Reading data from case0...')

case_folder = 'case0'

fname = os.path.join(input_folder,
                     case_folder,
                     'Esimerkki_2D_puurankaseina_2024-06-27_results.txt')

column_names = ['n_vent',
                'time',
                'T_wood_e_up',
                'RH_wood_e_up',
                'T_wb_i_up',
                'RH_wb_i_up',
                'T_ins_i_up',
                'RH_ins_i_up']

df_all = pd.read_csv(fname,
                 sep=r'\s+',
                 skiprows=5,
                 header=None,
                 names=column_names,
                 dtype=np.float64)


cols_to_groupby = ['n_vent']

points_for_mould_index = [['wood_e_up', 'vs', 'vs', 0.5],
                          ['wb_i_up', 'mr', 'mr', 0.1],
                          ['ins_i_up', 'mr', 'mr', 0.1]]




# Group rows according to parameter columns
grouped = df_all.groupby(by=cols_to_groupby)

for key in grouped.groups.keys():
    # For each parameter combination
    
    # Extract rows belonging to that group, keep the last 8760 hours
    # and reset index to between 0...8759
    
    if type(key) == float or type(key) == str:
        # The key has length 1
        # get_group needs a length-1 tuple as input
        df = grouped.get_group( (key,) )
    
    else:
        df = grouped.get_group(key)
    
        
    df = df.iloc[-8760:, :].copy()
    df.reset_index(drop=True,
                   inplace=True)
    
    # Go through all the probe points and calculate mould index for
    # cols 
    for point in points_for_mould_index:
        
        
        
        M_name = 'M_' + point[0]
        T_data = df.loc[:, 'T_' + point[0]]
        RH_data = df.loc[:, 'RH_' + point[0]]
        MG_speedclass = point[1]
        MG_maxclass = point[2]
        C_mat = point[3]
        
        df.loc[:,M_name] = helper.MI(T_data,
                                     RH_data,
                                     MG_speedclass,
                                     MG_maxclass,
                                     C_mat)
    
    # 
    
    group_names = '_'.join([str(x).replace('_','') for x in cols_to_groupby])
    
    if type(key) == float:
        group_vals = str(key)
    
    else:
        group_vals = '_'.join([str(x) for x in key])
    
    case_name = f'{case_folder}_{group_names}_{group_vals}'
    
    data[case_name] = df






# Go through the other case folders here...












###############

# Here the results data is saved to output folder


fname = os.path.join(output_folder,
                     'results.pickle')

with open(fname, 'wb') as f:
    pickle.dump(data, f)




