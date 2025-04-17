# -*- coding: utf-8 -*-
"""
Created on Tue Jun 11 10:06:03 2024
Anssi Laukkarinen

Read in hourly radiation data for horizontal surface and calculate
radiation to vertical surfaces.

The calculations are done using the pvlib python package.

The input data is assumed to contain the following columns:
- YEAR
- MON, month, January = 1
- DAY, first of month = 1
- HOUR, 0-23
- MIN, minutes of the hour, 0-59
- DHI, diffuse horizontal solar radiation, W/m2
- DNI, direct normal radiation (beam radiation), W/m2
- GHI, global horizontal radiation, W/m2
- LWdn, atmoshpheric downward longwave radiation, W/m2
- LWup, ground upward longwave radiation, W/m2
- <empty column, thanks to Excel>

sep=';'


decomposition - vaakapinnalta mitatun GHI:n jakaminen suoraan ja diffuusiin
closure equation: GHI = DNI * cos(zenith_angle) + DHI
GHI (Iglob) - pyranometer, horizontal surface (Rdif + Rdir)
DNI (Ibeam) - pyrheliometer + sun tracker
DHI (Idif) - pyranometers + shading device, horizontal surface

transposition - vaakapinnalta mitatun säteilyn muuntaminen muulle pinnalle
It = Ibeam*cos(incidence_angle) + Idif*Rdif + albedo*Iglob*Rground_refl


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
                            'koerakennus_sateily')

output_folder = os.path.join(root_folder,
                             'koerakennus_sateily')

if not os.path.exists(output_folder):
    os.makedirs(output_folder)



########

# Read in data

file = 'Jokioinen2022_FMI_radiation.txt'

fname = os.path.join(input_folder,
                     file)

data = pd.read_csv(fname,
                   sep=r'\s+')


# There can be missing values, 
# but fixed in such a way that only individual missing values per time
# Convert to pandas dataFrame to numeric
data = data.apply(pd.to_numeric, errors='coerce')

# Interpolate NaN values
data.interpolate(method='linear',
                 limit=3,
                 inplace=True)

print('Number of NaN values per column:', flush=True)
print(data.isna().sum())


# Set negative solar radiation values to zero

for col in ['DHI', 'DNI', 'GHI']:
    
    data.loc[:,col] = np.maximum(data.loc[:,col], 0.0)


# Convert time columns into a single datetime column
# It is assumed that the datetime columns describe the local wall clock time
time_dict = {'year': data.loc[:,'YEAR'].values,
             'month': data.loc[:, 'MON'].values,
             'day': data.loc[:,'DAY'].values,
             'hour': data.loc[:,'HOUR'].values,
             'minute': data.loc[:,'MIN'].values}
datetime_wall_clock_time_tz_naive = pd.to_datetime(arg=time_dict)

# In https://www.ilmatieteenlaitos.fi/havaintojen-lataus,
# the wall clock time shows a jump from 02:00 to 04:00 when moving from
# non-DST to DST in the spring.
# However in autumn, when moving back from DST to non-DST, there is no
# duplicate time stamps in local wall clock time format. In this situation
# the solar radiation data was copied from UTC time representation and 
# added as duplicate 03:00 row to input file. The duplicate time stamp
# is handled by the 'ambiguous' parameter in pandas.Series.dt.tz_localize().

datetime_wall_clock_time_tz_aware \
    = datetime_wall_clock_time_tz_naive.dt.tz_localize(tz='Europe/Helsinki',
                                                       ambiguous='infer')


# The radiation values represent the mean of the previous hour

datetime_wall_clock_time_tz_aware_minusHalfHour \
    = datetime_wall_clock_time_tz_aware - pd.Timedelta(value='30min')




## Solar position
# 'time' is pandas DateTimeIndex and localized or UTC is assumed

time = datetime_wall_clock_time_tz_aware_minusHalfHour

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



if 'Te' in data.columns:
    temperature = data.loc[:,'Te'].values
else:
    temperature = 5.0

solar_position = pvlib.solarposition.get_solarposition(time, 
                                                  latitude, 
                                                  longitude, 
                                                  altitude=altitude, 
                                                  method='nrel_numpy', 
                                                  temperature=temperature)


## Transposition

dni = data.loc[:,'DNI'].values # W/m2
ghi = data.loc[:,'GHI'].values # W/m2
dhi = data.loc[:,'DHI'].values # W/m2

solar_zenith = solar_position.loc[:,'zenith'].values

solar_azimuth = solar_position.loc[:,'azimuth'].values


for surface_azimuth in np.arange(start=0.0, stop=360.0, step=90.0):
    #surface_azimuth = 180.0 # degrees from north
    
    
    # slope_as_quotient = 1.2/2.0
    slope_as_quotient = 1.0/40.0
    
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




