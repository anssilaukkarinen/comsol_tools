# -*- coding: utf-8 -*-
"""
Created on Wed Jun 12 00:08:38 2024

@author: laukkara
"""

import os
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

print('numpy version:', np.__version__)
print('pandas version:', pd.__version__)

root_folder = os.path.join(r'C:\Temp\Rosenlof')

input_folder = os.path.join(root_folder,
                            'DB_climate')

output_folder = os.path.join(root_folder,
                             'DB_climate')

if not os.path.exists(output_folder):
    os.makedirs(output_folder)


############


# file = 'Jokioinen 2011 nykyilmasto 1989-2018.csv'
file = 'Jokioinen 2011 RCP85-2080.csv'

fname = os.path.join(input_folder,
                     file)

data = pd.read_csv(fname,
                   sep=r'\s+')

sigma_SB = 5.67e-8



## 

# 1:3 -> 1/30 OR
# dy/dx
slope_as_quotient = 1.2/2.0


# degrees from horizontal, wall=90
# surface_tilt = 90.0
surface_tilt = np.arctan(slope_as_quotient)*(180.0/np.pi)

print(f'1/slope = {1/slope_as_quotient:.2f}, slope = {surface_tilt:.2f} deg')

F_surf_sky = ( np.cos((np.pi/180.0)*(surface_tilt/2.0)) )**2

F_surf_ground = 1.0 - F_surf_sky



## LW from sky to surface
# LW reflectivity of ground is assumed zero

emissivity_ground = 0.95


LWdn = data.loc[:,'LWdn'].values

T_mean = data.loc[:,'Te'].rolling(window=730, min_periods=1).mean()
LWup = emissivity_ground * sigma_SB * (T_mean + 273.15)**4


LW_incoming = F_surf_sky * LWdn + F_surf_ground * LWup



## Output

tup = (np.arange(start=0, stop=len(LW_incoming)),
       LW_incoming)
X = np.column_stack(tup)

# File

fname = os.path.join(output_folder,
                     f'{file[:-4]} LWincoming_total {surface_tilt:.2f}.csv')

np.savetxt(fname,
           X,
           fmt = ['%d', '%.3f'])


# Plot

fig, ax = plt.subplots()
ax.plot(LW_incoming)
ax.set_title('LW incoming')








