# -*- coding: utf-8 -*-
"""
Created on Thu Sep  3 15:09:27 2026

@author: Anssi Laukkarinen

Read in location latitude, longitude and elevation and output
solar position angles with hourly resolution

Solar position: azimuth and elevation (or zenith) angle of the sun
azimuth angle
zenith angle
elevation angle
surface azimuth, surface slope
solar azimuth, solar azimuth
angle of incidence: angle between surface normal and solar beam

Transposition: calculate solar radiation to any surface, from data from
                horizontal and beam radiation data
slope = tilt angle: 0 deg (horizontal), 90 deg (vertical), >90 deg (facing towards ground)



"""

#TODO: implementoi aurinkokulmien laskenta ja käyttö comsoliin


import os
import numpy as np
import pandas as pd
import pvlib
import matplotlib.pyplot as plt

print('pandas version:', pd.__version__)
print('pvlib version:', pvlib.__version__)

pd.set_option('display.float_format', lambda x: f'{x:.3f}')


## Read in hourly data to pandas DataFrame

# Read in data

file_in = os.path.join('C:\Temp\SFS-EN 15026 Simuloinnit',
                       r'Koko Suomi homeen kasvun mitoitusvuodet\csv',
                       'Jokioinen 2011 nykyilmasto 1989-2018.csv')

# Define another file name and path here is needed
dummy_str = file_in.split("\\")[-1][:-4]
file_out = f'{dummy_str}_solarposition.csv'

df = pd.read_csv(file_in,
                 sep='\s+')


# Location parameters

location_str = 'Jok'

T_e_yearly_average = 6.0

if location_str == 'Van':
    # Vantaa Helsinki-Vantaan lentoasema, 100968
    latitude_deg = 60.33
    longitude_deg = 24.97
    altitude = 47.0
    timezone_as_decimal_hours = 2.0

elif location_str == 'Jok':
    # Jokioinen Ilmala, 101104
    latitude_deg = 60.81
    longitude_deg = 23.5
    altitude = 104.0
    timezone_as_decimal_hours = 2.0
    
    fname = os.path.join(r'C:\Temp\SFS-EN 15026 Simuloinnit',
                         r'Koko Suomi homeen kasvun mitoitusvuodet',
                         'csv',
                         'Jokioinen 2011 nykyilmasto 1989-2018.csv')
    
    df_climate = pd.read_csv(fname,
                             sep='\s+')
    Te = df_climate.loc[:,'Te']
    T_e_yearly_average = np.mean(Te)
    Idif = df_climate.loc[:,'Idif']
    Idir = df_climate.loc[:,'Idir']
    
    
elif location_str == 'Jyv':
    # Jyväskylä lentoasema
    latitude_deg = 62.4
    longitude_deg = 25.67
    altitude = 139.0
    timezone_as_decimal_hours = 2.0

elif location_str == 'Sod':
    # Sodankylä Tähtelä
    latitude_deg = 67.37
    longitude_deg = 26.63
    altitude = 179.0
    timezone_as_decimal_hours = 2.0

elif location_str == 'TAU_testbuildings':
    # Tampere University Building Physics research group test buildings
    latitude_deg = 61.45
    longitude_deg = 23.86
    altitude = 131.0
    timezone_as_decimal_hours = 2.0

else:
    print('Unknown location!')

# currently only positive timezone hours
if timezone_as_decimal_hours >= 0:
    pos_or_neg = '+'
else:
    pos_or_neg = '-'
hours = int(timezone_as_decimal_hours)
minutes = round((timezone_as_decimal_hours - hours)*60)
tz_str = f'UTC{pos_or_neg}{hours:02d}:{minutes:02d}'


print(f'latitude: {latitude_deg} deg, {latitude_deg*(np.pi/180)} rad')
print(f'longitude: {longitude_deg} deg, {longitude_deg*(np.pi/180)} rad')
print(f'altitude: {altitude} m')
print(f'timezone as decimal hours, east is positive: {timezone_as_decimal_hours} h')
print(f'timezone as string: {tz_str}')



# The first data line of a WUFI .wac file is for the first hour of the year,
# i.e. 1 January 00:00 - 1 January 01:00.
# no daylight savings time in any of the datasets (this or the one below)
# -> average values for the previous hour

# timestamps in RASMI
# instantaneous values (T, RH, ws, wd) or 
# average values of previous hour (radiation, precipitation)

# timestamps in RAMI
# -> as in RASMI data

timestamp_values = pd.date_range(start='2011-01-01 00:00',
                                 end='2011-12-31 23:00',
                                 freq='1h',
                                 tz=tz_str) - pd.Timedelta('30min')





## Calculate hourly solar position for the location described above

def calc_solpos_pvlib(timestamp_values,
                      latitude_deg, longitude_deg, altitude,
                      T_e_yearly_average):

    df_solpos = pvlib.solarposition.get_solarposition(time=timestamp_values,
                                                    latitude=latitude_deg,
                                                    longitude=longitude_deg,
                                                    altitude=altitude,
                                                    temperature=T_e_yearly_average,
                                                    method='nrel_numpy')
    
    df_solpos.index.name = 't_fin_standardtime'
    
    print(df_solpos.columns)
    
    return(df_solpos)



df_solpos = calc_solpos_pvlib(timestamp_values,
                      latitude_deg, longitude_deg, altitude,
                      T_e_yearly_average)


df_solpos.index += pd.Timedelta('30min')

print('Solar position calculated with pvlib')


## Check that all is ok and export, all angle in degrees

# apparent_zenith (degrees)
# -> angle between sun and zenith, refraction-corrected
# zenith (degrees)

# apparent_elevation (degrees); elevation = 90 - zenith
# elevation (degrees) 

# azimuth (degrees), pvlib calculates azimuth from north; east=90, south=180

# equation_of_time (minutes)


# -> use apparent_zenith and azimuth, both are in degrees

df_solpos.loc[:,['apparent_zenith','azimuth']].round(2).to_csv(file_out)







## Calculat solar position manually
# t_hour is in local standard hours, no daylight savings
t_hour = np.arange(0, 8760) - 0.5

# January 1 = 1; February 1 = 32
# This is defined here that 00:00 = 0
n_day = (t_hour + 24)/24


Gamma_rad = (2*np.pi) * (n_day - 1) / 365
Gamma_deg = Gamma_rad * (180.0/np.pi)


ET = 2.2918*(0.0075 \
             + 0.1868 * np.cos(Gamma_rad) \
             - 3.2077 * np.sin(Gamma_rad) \
             - 1.4615 * np.cos(2*Gamma_rad) \
             - 4.089 * np.sin(2*Gamma_rad))

LST = t_hour % 24 # local standard time
LON_deg = longitude_deg
TZ_hours = timezone_as_decimal_hours
LSM_deg = 15.0 * TZ_hours # longitude of local standard meridian

AST = LST + ET/60.0 + (LON_deg-LSM_deg)/15 # apparent solar time

delta_declination_rad = (23.45*np.pi/180.0)*np.sin( (2*np.pi) * ((n_day+284)/365) )
delta_declination_deg = delta_declination_rad * (180.0/np.pi)

hour_angle_rad = (15*(np.pi/180.0)) * (AST - 12)
hour_angle_deg = hour_angle_rad * (180.0/np.pi)

latitude_rad = latitude_deg*(np.pi/180.0)

beta_rad = np.asin(np.cos(latitude_rad)*np.cos(delta_declination_rad)*np.cos(hour_angle_rad) \
                   + np.sin(latitude_rad)*np.sin(delta_declination_rad))
beta_deg = beta_rad * (180.0/np.pi)


s = np.sin(hour_angle_rad) \
    * np.cos(delta_declination_rad) \
    / np.cos(beta_rad)

c = (np.cos(hour_angle_rad) \
     *np.cos(delta_declination_rad) \
     *np.sin(latitude_rad) \
     -np.sin(delta_declination_rad) \
     *np.cos(latitude_rad) 
    )/np.cos(beta_rad)

# np.asin() returns angle in range [-pi/2, pi/2] = [-90, 90]
phi_rad_eq1 = np.asin(s)

# np.acos() returns angle in range [0, pi] = [0, 180]
phi_rad_eq2 = np.acos(c)

# Get the correct quandrant, angle is in range [-pi, pi] = [-180, 180]
# This is the correct angle range
# np.asin() and np.acos() do not directly return angles that would cover
# the full value range of the azimuth angle
phi_rad_eq3_fromsouth = np.arctan2(s,c)

# Addition to match pvlib: add pi to angles to have the range at [0, 2*pi]
phi_rad_eq3_fromnorth = phi_rad_eq3_fromsouth + np.pi

phi_deg_eq1 = phi_rad_eq1*(180/np.pi)
phi_deg_eq2 = phi_rad_eq2*(180/np.pi)
phi_deg_eq3_fromnorth = phi_rad_eq3_fromnorth*(180/np.pi)
phi_deg_eq3_fromsouth = phi_rad_eq3_fromsouth*(180/np.pi)


fig, ax = plt.subplots(figsize=(5,3))
ax.plot(beta_deg[180*24:185*24], label='eq. from ASHRAE')
ax.plot(df_solpos.loc[:,'apparent_elevation'].iloc[180*24:185*24].values,
        label='pvlib')
ax.grid()
ax.set_xlabel('hours from midnight')
ax.set_ylabel('elevation angle')
ax.legend()

fig, ax = plt.subplots(figsize=(5,3))
ax.plot(phi_deg_eq3_fromnorth[180*24:185*24], label='eq. from ASHRAE')
ax.plot(df_solpos.loc[:,'azimuth'].iloc[180*24:185*24].values,
        label='pvlib')
ax.grid()
ax.set_xlabel('hours from midnight')
ax.set_ylabel('azimuth angle, 12:00 at south')


fig, ax = plt.subplots(figsize=(5,3))
ax.plot(beta_deg - df_solpos.loc[:,'apparent_elevation'].values)
ax.set_xlabel('Hours from the beginning of year')
ax.set_ylabel('beta_pvlib - beta_ashrae, deg')

fig, ax = plt.subplots(figsize=(5,3))
ax.plot(phi_deg_eq3_fromnorth - df_solpos.loc[:,'azimuth'].values)
ax.set_xlabel('Hours from the beginning of year')
ax.set_ylabel('phi_pvlib - phi_ashrae, deg')
ax.set_ylim(-5,5)





"""
## Example in ASHRAE Fundamentals, Ch. 14
# The correct angle is: phi = 56.69; both asin and acos produce this below.
# Note! The range of values that np.asin() and np.acos() return do not cover
# the full azimuth angle range. Better to use np.arctan2().

import numpy as np

hour_angle_rad = 18.97 * np.pi/180
delta_declination_rad = 20.44*np.pi/180
beta_rad = 68.62 * np.pi/180
latitude_rad = 33.64 * np.pi/180

s = np.sin(hour_angle_rad) \
    * np.cos(delta_declination_rad) \
    / np.cos(beta_rad)
print(s)


c = (np.cos(hour_angle_rad) \
     *np.cos(delta_declination_rad) \
     *np.sin(latitude_rad) \
     -np.sin(delta_declination_rad) \
     *np.cos(latitude_rad) 
    )/np.cos(beta_rad)
print(c)

phi_asin = np.asin(s)
print(phi_asin*180/np.pi)

phi_acos = np.acos(c)
print(phi_acos*180/np.pi)

phi_atan2 = np.arctan2(s, c)
print(phi_atan2*180/np.pi)

"""


## Calculate angle of incidence

# pvlib, angle of incidence aoi

surface_slope_deg = 90.0 # also called tilt
surface_azimuth_fromnorth_deg = 90.0
solar_zenith_deg = df_solpos.loc[:,'apparent_zenith']
solar_azimuth_deg = df_solpos.loc[:,'azimuth']

Sigma_deg = surface_slope_deg
Sigma_rad = Sigma_deg*(np.pi/180)

dummy_aoi = pvlib.irradiance.aoi(surface_tilt=surface_slope_deg, 
                                     surface_azimuth=surface_azimuth_fromnorth_deg, 
                                     solar_zenith=solar_zenith_deg, 
                                     solar_azimuth=solar_azimuth_deg)

# for horizontal surface, the aoi is the same as zenith angle (=90-beta)
# plt.plot(dummy_aoi.iloc[180*24:185*24].values);plt.plot(90-beta_deg[180*24:185*24])


# ASHRAE Fundamentals
phi_rad = phi_rad_eq3_fromsouth
psi_rad = (surface_azimuth_fromnorth_deg - 1*180.0) * (np.pi/180.0)

gamma_rad = phi_rad - psi_rad
gamma_deg = gamma_rad * (180/np.pi)

cos_theta = np.cos(beta_rad)*np.cos(gamma_rad)*np.sin(Sigma_rad) \
            + np.sin(beta_rad)*np.cos(Sigma_rad)

# for vertical surfaces (Sigma=90deg) -> cos_theta = cos(beta)*cos(gamma)
# for horizontal surfaces (Sigma=0deg) -> theta = 90 - beta

# theta is the angle of incidence aoi
theta_rad = np.acos(cos_theta)
theta_deg = theta_rad * (180/np.pi)

fig, ax = plt.subplots(figsize=(5,3))
ax.plot(dummy_aoi.iloc[180*24:185*24].values, label='pvlib')
ax.plot(theta_deg[180*24:185*24], label='ASHRAE')
ax.grid(True)
ax.legend()
ax.set_ylabel('angle of incidence, degrees')




### Irradiance to specific surface

# Extraterrestrial irradiance
I_solarconst = 1361.1 # W/m2
I_extraterrestrial = I_solarconst * (1.0 + 0.033 * np.cos(2*np.pi*(n_day-3)/365))
fig, ax = plt.subplots(figsize=(5,3))
ax.plot(I_extraterrestrial)
ax.grid()

# sum_i(F_i_j) = 1
# F_surf_ground + F_surf_sky = 1
# F_surf_sky = 1 - F_surf_ground

# WUFI Help:
# WUFI inclination: horizontal surface 0 deg, vertical surface 90 deg
# Solar radiation that is reflected from ground and hits the surface
# Unobstructed vertical_wall: F_ground_surf = 0.5
# Unobstructed general case: F_ground_surf = sin2(inclination angle/2)

# In ASHRAE the view factor equations are a bit different
# Trigonometric identities (https://en.wikipedia.org/wiki/List_of_trigonometric_identities):
# sin**2(angle) = (1 - cos(2*angle)) / 2
# sin**2(inclination/2) = (1 - cos(angle)) / 2
# F_surf_sky = 1 - (1 - cos(angle)) / 2
#            = 1*2/2 - (1 - cos(angle))/2
#            = 1*2/2 - 1/2 + cos(angle)/2
#            = 1/2 + cos(angle)/2
#            = (1 + cos(angle)) / 2

F_ground_surf = (1 - np.cos(Sigma_rad)) / 2.0
F_sky_surf = (1 + np.cos(Sigma_rad)) / 2.0


# Direct radiation
idxs_betasmall = (beta_rad < 5*(np.pi/180))


I_dir_hor = df_climate.loc[:,'Idir']
I_dif_hor = df_climate.loc[:,'Idif']

# Allocate all direct radiation values with small elevation angle to diffuse radiation
I_dif_hor[idxs_betasmall] = I_dif_hor[idxs_betasmall] + I_dir_hor[idxs_betasmall]
I_dir_hor[idxs_betasmall] = 0.0

# I_dir_hor = I_beam * sin(beta)
# I_beam = I_dir_hor / sin(beta)
I_beam = I_dir_hor / np.sin(beta_rad)
I_dir_surf = I_beam * np.maximum(0.0, np.cos(theta_rad))


# Diffuse radiation
# Hay and Davies (1980) as according to ASHRAE Fundamentals 2025
AI = I_beam / I_extraterrestrial

R_b = np.cos(theta_rad) / np.sin(np.maximum(5*(np.pi/180), beta_rad))
idxs_betanegative = (beta_rad < 0.0)
idxs_thetalargerthannormal = (theta_rad > 90*(np.pi/180))
R_b[idxs_betanegative] = 0.0
R_b[idxs_thetalargerthannormal] = 0.0
dif_multiplier = AI*R_b + (1.0-AI)*F_sky_surf
I_dif_surf = I_dif_hor * dif_multiplier


# Reflected radiation
rho_albedo = 0.2
I_refl_surf = (I_dir_hor + I_dif_hor) * rho_albedo * F_ground_surf


# Incoming solar radiation to the surface in surface normal direction
I_tot_surf = I_dir_surf + I_dif_surf + I_refl_surf








