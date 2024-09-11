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


Update 11.9.2024
The comsol output is changed in such a way, that only single case is run
at a time. Because of this, there is no parametric sweep/batch sweep
being used. The grouping is removed from the code below.

"""



import os
import pickle
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import helper



## The folders can be changed as needed

root_folder = r'S:\91202_Rakfys_yhteiset\Tiiliverhous\2_Laskenta\narvi stuff'

case_folder = 'esimerkki'

file_name_to_read = 'vuoden tulokset.txt'




############

data = {}

fname = os.path.join(root_folder,
                     case_folder,
                     file_name_to_read)

# version 1
# column_names = ['n_vent',
#                 'time',
#                 'T_wood_e_up',
#                 'RH_wood_e_up',
#                 'T_wb_i_up',
#                 'RH_wb_i_up',
#                 'T_ins_i_up',
#                 'RH_ins_i_up']

# version 2
column_names = ['time',
                'T_wood_e_up',
                'RH_wood_e_up',
                'T_wb_i_up',
                'RH_wb_i_up',
                'T_ins_i_up',
                'RH_ins_i_up',
                'T_wood_m_up',
                'RH_wood_m_up',
                'T_wood_i_up',
                'RH_wood_i_up']



points_for_mould_index = [['wood_e_up', 'vs', 'vs', 0.5],
                          ['wb_i_up', 'mr', 'mr', 0.1],
                          ['ins_i_up', 'mr', 'mr', 0.1],
                          ['wood_m_up', 'vs', 'vs', 0.5],
                          ['wood_i_up', 'vs', 'vs', 0.5]]


print('Reading file...')

df_all = pd.read_csv(fname,
                 sep=r'\s+',
                 skiprows=5,
                 header=None,
                 names=column_names,
                 dtype=np.float64)


df = df_all.iloc[-8760:, :].copy()
df.reset_index(drop=True,
               inplace=True)


print('Calculate mould index...')

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



case_name = case_folder.replace(' ','_')

data[case_name] = df






###############

# Here the results data is saved to output folder

print('Export to pickle file...')

file_name_to_write = f'{file_name_to_read.replace(".txt","")}_results.pickle'


fname = os.path.join(root_folder,
                     case_folder,
                     file_name_to_write)

with open(fname, 'wb') as f:
    pickle.dump(data, f)


print('END')


