# -*- coding: utf-8 -*-
"""
Created on Tue Jun 11 21:38:38 2024
Anssi Laukkarinen

Read in hourly wind and precipitation data and calculate the 
wind driven rain load to vertical surfaces.

The calculation is done according to SFS-EN ISO 15927-3.


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
                             'wind-driven rain')

if not os.path.exists(output_folder):
    os.makedirs(output_folder)


############


file = 'Jokioinen 2011 nykyilmasto 1989-2018.csv'
fname = os.path.join(input_folder,
                     file)

data = pd.read_csv(fname,
                   sep='\s+')




##


terrain_category = 'I' # 



if terrain_category == '0':
    # Avomeri tai merelle avoin rannikko
    z_0_1991 = 0.003
    z_min_1991 = 1.0
    
    K_R_15927 = 0.17
    z_0_15927 = 0.01
    z_min_15927 = 2.0
    
    
elif terrain_category == 'I':
    # Järvet tai tasanko, jolla on enintään vähäistä
    # kasvillisuutta eikä tuuliesteitä
    z_0_1991 = 0.01
    z_min_1991 = 1.0
    
    K_R_15927 = 0.17
    z_0_15927 = 0.01
    z_min_15927 = 2.0
    
elif terrain_category == 'II':
    # Alue, jolla on matalaa heinää tai siihen verrattavaa
    # kasvillisuutta ja erillisiä esteitä (puita, rakennuksia),
    # joiden etäisyys toisistaan on vähintään 20 kertaa
    # esteen korkeus
    z_0_1991 = 0.05
    z_min_1991 = 2.0
    
    K_R_15927 = 0.19
    z_0_15927 = 0.05
    z_min_15927 = 4.0
    
elif terrain_category == 'III':
    # Alueet, joilla on säännöllinen kasvipeite tai rakennuksia
    # tai erillisiä tuuliesteitä, joiden keskinäinen etäisyys on
    # enintään 20 kertaa esteen korkeus (kuten kylät, esikaupunkialueet,
    # pysyvä metsä)
    z_0_1991 = 0.3
    z_min_1991 = 5.0
    
    K_R_15927 = 0.22
    z_0_15927 = 0.3
    z_min_15927 = 8.0
    
elif terrain_category == 'IV':
    # Alueet, joiden pinta-alasta vähintään 15 % on rakennusten peitossa
    # ja niiden keskimääräinen korkeus ylittää 15 m
    z_0_1991 = 1.0
    z_min_1991 = 10.0
    
    K_R_15927 = 0.24
    z_0_15927 = 1.0
    z_min_15927 = 16.0
    
else:
    print('Unknown terrain category!')



##


ws = data.loc[:,'ws'].values # m/s
wd = data.loc[:,'wd'].values # deg from north
precip = data.loc[:,'precip'].values # mm/h






## 

for Theta_wall in np.arange(start=0.0, stop=360.0, step=90.0):
    # Wall direction, degree
    # This is the same than surface_azimuth in solar radiation calculations
    #Theta_wall = 180.0
    
    # Building total height, m
    z_building = 6.0
    
    
    
    I_S = (2.0/9.0) * ws * ( precip**(8.0/9.0) ) \
            * np.maximum( np.cos( (np.pi/180.0)*(wd-Theta_wall) ) , 0.0)
    
    
    
    z_0_II_1991 = 0.05
    k_r_1991 = 0.19 * (z_0_1991/z_0_II_1991)**0.07
    
    C_R_1991 = k_r_1991 * np.log(np.max((z_building, z_min_1991))/z_0_1991)
    
    C_R_15927 = K_R_15927 * np.log(np.max((z_building, z_min_15927))/z_0_15927)
    
    
    # C_R_1991 or C_R_15927
    # z_min is bigger in SFS-EN ISO 15927-3, which leads to
    # higher wind velocity and wind-driven rain amounts
    # when calculated for buildings for which z_building < z_min
    C_R = C_R_15927 
    
    C_T = 1.0
    
    O = 1.0
    
    W = 0.5
    
    I_WS = I_S * C_R * C_T * O * W
    
    
    print('I_WS all Te:', I_WS.sum())
    
    # Include only wind-driven rain when outdoor air temperature is above 0 degC
    
    idxs_subzero = data.loc[:,'Te'] < 0.0
    I_WS[idxs_subzero] = 0.0
    
    print('I_WS positive Te:', I_WS.sum())
    
    
    ## Output
    
    # File
    
    fname = os.path.join(output_folder,
                         f'wdr {file[:-4]} surfaz{Theta_wall}' \
                         f' tercat{terrain_category} z{z_building}.csv')
    
    np.savetxt(fname,
               I_WS,
               fmt = '%.3f')
    



# Plot

fig, ax = plt.subplots()
ax.plot(I_WS)






