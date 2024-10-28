# -*- coding: utf-8 -*-
"""
Created on Sat Oct 26 15:45:05 2024

@author: laukkara


Read in WUFI .wac file and convert data to be used as input
in COMSOL Multiphysics heat and moisture model.

The code is written only for specific and pre-known columns
in the wac file.

This file is written a little later than other "1_comsol_..." files
in the repository. Earlier files made comsol input files from
certain type csv files. This code makes comsol input files from a
WUFI wac file.


Indoor:
    Temperature
    Relative humidity

Outdoor:
    Temperature
    Relative humidity
    Wind-driven rain
    Long-wave radiation
    Short-wave radiation


"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import pvlib

import helper




# Input files
wac_file_name = 'Jokioinen 2011 RCP85-2080.wac'

fname = os.path.join(r'C:\Users\laukkara\github\comsol_tools',
                     'input',
                     f'{wac_file_name}')


# Output folder

output_folder = os.path.join(r'C:\Temp',
                             'wac_for_comsol')

if not os.path.exists(output_folder):
    os.makedirs(output_folder)



# Read in all rows from wac file

with open(fname, 'r') as f:
    rows_list = f.readlines()


# Make sure it is a wac file
assert 'WUFI®_WAC_02' in rows_list[0]

# It is assumed that second row gives the amount of rows until data
line_offset = int(rows_list[1].split()[0])

header_rows = rows_list[2:2+line_offset]

data_rows = rows_list[2+line_offset:]


# Parse header rows
# It is assumed that data starts from beginning of year, has 1 h frequency
# and there are 8760 rows.

# It is also assumed that there are only specific columns

data = {}

for item in header_rows:
    
    if 'Longitude' in item:
        data['LAT'] = float(item.split()[0])
    
    elif 'Latitude' in item:
        data['LON'] = float(item.split()[0])
    
    elif 'Height' in item:
        data['ALT'] = float(item.split()[0])
    
    elif 'Zone' in item:
        data['timezone'] = float(item.split()[0])
    
    elif 'HREL' in item:
        
        data['column_names'] = item.split()
    

# Read data rows into a pandas DataFrame

data_rows_splitted = []

for item in data_rows:
    data_rows_splitted.append(item.split())



df = pd.DataFrame(data=data_rows_splitted,
                  columns=data['column_names'])

df = df.apply(pd.to_numeric)



### Calculate values for comsol

## Indoor conditions

Ti, vi, phii = helper.calc_indoor_conditions(Te=df.loc[:,'TA'], 
                                             RHe=df.loc[:,'HREL'])

fname = os.path.join(output_folder,
                     f'{wac_file_name[:-4]} Ti.csv')
helper.save_to_file_for_comsol(Ti, fname)



fname = os.path.join(output_folder,
                     f'{wac_file_name[:-4]} phii.csv')
helper.save_to_file_for_comsol(phii, fname)




## Outdoor conditions


# Te

fname = os.path.join(output_folder,
                     f'{wac_file_name[:-4]} Te.csv')

helper.save_to_file_for_comsol(df.loc[:,'TA'], fname)



# RHe

fname = os.path.join(output_folder,
                     f'{wac_file_name[:-4]} RHe.csv')

helper.save_to_file_for_comsol(100 * df.loc[:,'HREL'], fname)



# Wind-driven rain (WDR) to wall surface

surface_azimuth = 180.0
terrain_category='I'
z_building=6.0

I_WS = helper.calc_WDR(ws=df.loc[:,'WS'], 
                       wd=df.loc[:,'WD'], 
                       precip_horizontal=df.loc[:,'RN'], 
                       Te=df.loc[:,'TA'], 
                       terrain_category=terrain_category, 
                       z_building=z_building,
                       Theta_azimuth=surface_azimuth)

fname = os.path.join(output_folder,
                     f'{wac_file_name[:-4]} wdr surfaz{surface_azimuth}' \
                     f' tercat{terrain_category} z{z_building:.1f}.csv')

helper.save_to_file_for_comsol(I_WS, fname)



# Long-wave radiation towards surface

slope_as_quotient = 100000.0 # dy/dx
surface_tilt = np.arctan(slope_as_quotient)*(180/np.pi)
LWdn = df.loc[:,'ILAH']
Te = df.loc[:,'TA']
LW_incoming = helper.calc_LWincoming(slope_as_quotient, LWdn, Te)

fname = os.path.join(output_folder,
                     f'{wac_file_name[:-4]} LWincoming_total {surface_tilt:.2f}.csv')

helper.save_to_file_for_comsol(LW_incoming, fname)



# Solar radiation

time_fin_normal = pd.date_range(start='2011-01-01 00:00:00',
                                  end='2011-12-31 23:00:00',
                                  inclusive='both',
                                  freq='1H')

time_utc = time_fin_normal - pd.Timedelta(value='2h')
time_utc_plusHalfHour = time_utc + pd.Timedelta(value='30min')

if 'Jok' in wac_file_name:
    location = 'Jokioinen'
elif 'Van' in wac_file_name:
    location = 'Vantaa'
elif 'Jyv' in wac_file_name:
    location = 'Jyvaskyla'
elif 'Sod' in wac_file_name:
    location = 'Sodankyla'
else:
    print('Location unknown!', flush=True)

Idif_hor = df.loc[:,'ISD']
Idir_hor = df.loc[:,'ISDH']

xp = Te.index.values
fp = Te.values
x = xp + 0.5
Te_betweens = np.interp(x, xp, fp)

SW_incoming = helper.calc_solar_radiation_to_surface(time_utc_plusHalfHour,
                                                    location,
                                                    surface_tilt,
                                                    surface_azimuth,
                                                    Idif_hor,
                                                    Idir_hor,
                                                    Te_betweens)

fname = os.path.join(output_folder,
                    f'{wac_file_name[:-4]} sunrad surfaz{surface_azimuth} slope{surface_tilt:.2f}.csv')

helper.save_to_file_for_comsol(SW_incoming, fname)






















