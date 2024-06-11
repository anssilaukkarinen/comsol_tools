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

root_folder = os.path.join(r'S:\91202_Rakfys_yhteiset\Tiiliverhous\2_Laskenta')

input_folder = os.path.join(root_folder,
                            'DB_climate')

output_folder = os.path.join(root_folder,
                             'DB_climate',
                             'long-wave radiation')

if not os.path.exists(output_folder):
    os.makedirs(output_folder)


############


file = 'Jokioinen 2011 nykyilmasto 1989-2018.csv'
fname = os.path.join(input_folder,
                     file)

data = pd.read_csv(fname,
                   sep='\s+')

sigma_SB = 5.67e-8



## 

surface_tilt = 90.0 # degrees from horizontal

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

# File

fname = os.path.join(output_folder,
                     f'LWincoming {file[:-4]}.csv')

np.savetxt(fname,
           LW_incoming,
           fmt = '%.3f')


# Plot

fig, ax = plt.subplots()
ax.plot(LW_incoming)









