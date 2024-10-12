# -*- coding: utf-8 -*-
"""
Created on Tue Jun 11 10:06:03 2024
Anssi Laukkarinen

Read in hourly radiation data for horizontal surface and calculate
radiation to vertical surfaces.

The calculations are done using the pvlib python package.



decomposition - vaakapinnalta mitatun GHI:n jakaminen suoraan ja diffuusiin
closure equation: GHI = DNI * cos(zenith_angle) + DHI
GHI (Iglob) - pyranometer, horizontal surface (Rdif + Rdir)
DNI (Ibeam) - pyrheliometer + sun tracker
DHI (Idif) - pyranometers + shading device, horizontal surface

transposition - vaakapinnalta mitatun säteilyn muuntaminen muulle pinnalle
It = Ibeam*cos(incidence_angle) + Idif*Rdif + albedo*Iglob*Rground_refl

RAMI-aineistoissa säteilysuureet ovat edeltävän tunnin keskiarvoja

"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import pvlib

print('pandas version:', pd.__version__)
print('pvlib version:', pvlib.__version__)


root_folder = os.path.join(r'C:\Temp\Rosenlof')

input_folder = os.path.join(root_folder,
                            'DB_climate')

output_folder = os.path.join(root_folder,
                             'DB_climate')

if not os.path.exists(output_folder):
    os.makedirs(output_folder)



########



# file = 'Jokioinen 2011 nykyilmasto 1989-2018.csv'
file = 'Jokioinen 2011 RCP85-2080.csv'

fname = os.path.join(input_folder,
                     file)

data = pd.read_csv(fname,
                   sep=r'\s+')


## Solar position
# the times in csv files are finnish normal time (winter time)
# all year around
my_dict = {'year': data.loc[:,'YEAR'].values,
           'month': data.loc[:, 'MON'].values,
           'day': data.loc[:,'DAY'].values,
           'hour': data.loc[:,'HOUR'].values}
my_datetime_fin_normal = pd.to_datetime(arg=my_dict)
my_datetime_utc = my_datetime_fin_normal - pd.Timedelta(value='2h')
my_datetime_utc_minusHalfHour = my_datetime_utc - pd.Timedelta(value='30min')

time = my_datetime_utc_minusHalfHour

if 'Van' in fname:
    # Vantaa Helsinki-Vantaan lentoasema, 100968
    latitude = 60.33
    longitude = 24.97
    altitude = 47.0

elif 'Jok' in fname:
    # Jokioinen Ilmala, 101104
    latitude = 60.81
    longitude = 23.5
    altitude = 104.0
    
elif 'Jyv' in fname:
    # Jyväskylä lentoasema
    latitude = 62.4
    longitude = 25.67
    altitude = 139.0

elif 'Sod' in fname:
    # Sodankylä Tähtelä
    latitude = 67.37
    longitude = 26.63
    altitude = 179.0

else:
    print('Unknown location!')



temperature = data.loc[:,'Te'].values

solar_position = pvlib.solarposition.get_solarposition(time, 
                                                  latitude, 
                                                  longitude, 
                                                  altitude=altitude, 
                                                  method='nrel_numpy', 
                                                  temperature=temperature)


## Transposition

dni = data.loc[:,'Ibeam'].values # W/m2
ghi = data.loc[:,'Iglob'].values # W/m2
dhi = data.loc[:,'Idif'].values # W/m2

solar_zenith = solar_position.loc[:,'zenith'].values

solar_azimuth = solar_position.loc[:,'azimuth'].values


# for surface_azimuth in np.arange(start=0.0, stop=360.0, step=180.0):
for surface_azimuth in np.arange(start=0.0, stop=360.0, stop=90.0):
    #surface_azimuth = 180.0 # degrees from north
    
    
    
    slope_as_quotient = 1.2/2.0
    
    # degrees from horizontal, wall=90
    # surface_tilt = 90.0 
    surface_tilt = np.arctan(slope_as_quotient)*(180.0/np.pi)
    
    
    
    total_irrad = pvlib.irradiance.get_total_irradiance(surface_tilt, 
                                                surface_azimuth, 
                                                solar_zenith, 
                                                solar_azimuth, 
                                                dni, 
                                                ghi, 
                                                dhi, 
                                                dni_extra=None, 
                                                airmass=None, 
                                                albedo=0.25, 
                                                surface_type=None, 
                                                model='isotropic', 
                                                model_perez='allsitescomposite1990')
    
    
    # Interpolation to next half hour
    
    poa_global_even_hours = np.zeros(shape=total_irrad['poa_global'].shape)
    
    starts = total_irrad['poa_global'][0:-1]
    ends = total_irrad['poa_global'][1:]
    
    betweens = starts + 0.5*(ends - starts)
    
    poa_global_even_hours[:-1] = betweens
    
    
    
    ## Output
    fname = os.path.join(output_folder,
                         f'{file[:-4]} sunrad surfaz{surface_azimuth} slope{surface_tilt:.2f}.csv')
    
    tup = (np.arange(start=0, stop=len(poa_global_even_hours)),
           poa_global_even_hours)
    X = np.column_stack(tup)
    
    np.savetxt(fname,
               X,
               fmt = ['%d', '%.3f'])


# plot
fig, ax = plt.subplots()
ax.plot(total_irrad['poa_global'][4500:4600])
ax.plot(poa_global_even_hours[4500:4600])




