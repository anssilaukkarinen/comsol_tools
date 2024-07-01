# -*- coding: utf-8 -*-
"""
Created on Tue Jun 25 01:54:59 2024

@author: laukkara
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import helper

print('numpy', np.__version__)
print('pandas', pd.__version__)


root_folder = os.path.join(r'S:\91202_Rakfys_yhteiset\Tiiliverhous\2_Laskenta')

input_folder = os.path.join(root_folder,
                            'DB_climate')

output_folder = os.path.join(root_folder,
                             'DB_climate')

if not os.path.exists(output_folder):
    os.makedirs(output_folder)


############


file = 'Jokioinen 2011 nykyilmasto 1989-2018.csv'
fname = os.path.join(input_folder,
                     file)

data = pd.read_csv(fname,
                   sep=r'\s+')


Te = data.loc[:,'Te']
ve = data.loc[:,'ve']




# Read in and export the same file with header line commented out

with open(fname, 'r') as f:
    climate_file_as_list = f.readlines()



fname = os.path.join(output_folder,
                     file[:-4] + ' headerAsComment.csv')
with open(fname, 'w') as f:
    # Note: Each line already has \n at the end
    
    for line in climate_file_as_list:
        
        if 'index' in line or 'RH' in line:
            
            line_to_write = '% ' + line
            f.write(line_to_write)
            
        
        else:
            f.write(line)


    



## Ti

# constant 21

Ti = 21.0 * np.ones(Te.shape)
tup = ( np.arange(start=0, stop=len(Ti)),
       Ti)
X = np.column_stack(tup)

fname = os.path.join(output_folder,
                     f'{file[:-4]} Ti const21.csv')
np.savetxt(fname, X, fmt = ['%d','%.1f'])


# varying 21...25

Te_low = 10.0
Te_high = 20.0
Ti_low = 21.0
Ti_high = 25.0

Te_24hmean = Te.rolling(24, center=True, min_periods=1).mean()
ve_24hmean = ve.rolling(24, center=True, min_periods=1).mean()

xp = (Te_low, Te_high)
fp = (Ti_low, Ti_high)

Ti_24hmean = np.interp(Te_24hmean, xp, fp)

tup = ( np.arange(start=0, stop=len(Ti_24hmean)),
       Ti_24hmean)
X = np.column_stack(tup)

fname = os.path.join(output_folder,
                     f'{file[:-4]} Ti var2125.csv')
np.savetxt(fname, X, fmt = ['%d','%.1f'])




## vi

# RIL 107

Te_low = 5.0
Te_high = 15.0
dv_low = 5.0
dv_high = 2.0

xp = (Te_low, Te_high)
fp = (dv_low, dv_high)
dv_24hmean = np.interp(Te_24hmean, xp, fp)

vi_RIL107 = ve_24hmean + dv_24hmean


# 

vsat_const21 = helper.calc_vsat(Ti)

phi_i_RIL107_const21 = vi_RIL107 / vsat_const21

phi_i_RIL107_const21 = np.minimum(phi_i_RIL107_const21, 0.8)

tup = ( np.arange(start=0, stop=len(Ti_24hmean)),
       phi_i_RIL107_const21)
X = np.column_stack(tup)

fname = os.path.join(output_folder,
                     f'{file[:-4]} phi_i_RIL107_const21.csv')
np.savetxt(fname, X, fmt = ['%d','%.3f'])



# 

vsat_Ti2125 = helper.calc_vsat(Ti_24hmean)

phi_i_RIL107_Ti2125 = vi_RIL107 / vsat_Ti2125

phi_i_RIL107_Ti2125 = np.minimum(phi_i_RIL107_Ti2125, 0.8)

tup = ( np.arange(start=0, stop=len(Ti_24hmean)),
       phi_i_RIL107_Ti2125)
X = np.column_stack(tup)

fname = os.path.join(output_folder,
                     f'{file[:-4]} phi_i_RIL107_var2125.csv')
np.savetxt(fname, X, fmt = ['%d','%.3f'])


























