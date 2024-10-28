# -*- coding: utf-8 -*-
"""

@author: laukkara



decomposition - vaakapinnalta mitatun GHI:n jakaminen suoraan ja diffuusiin
closure equation: GHI = DNI * cos(zenith_angle) + DHI
GHI (Iglob) - pyranometer, horizontal surface (Rdif + Rdir)
DNI (Ibeam) - pyrheliometer + sun tracker
DHI (Idif) - pyranometers + shading device, horizontal surface

transposition - convert solar radiation from horizontal surface to other surface
Itot = Ibeam*cos(incidence_angle) + Idif*Rdif + albedo*Iglob*Rground_refl

In WUFI wac files the radiation values are given for the next hour.

ISDH = Direct horizontal radiation
ISD = Diffuse radiation, horizontal surface


"""
import numpy as np
import pandas as pd

import pvlib




def calc_vsat(T_, arg1='ice'):
    # [T_] = degC
    
    R_w = 461.5
    
    pvsat = 610.5 * np.exp((17.269*T_)/(237.3+T_))
    
    if arg1 == 'ice':
        
        idxs_subzero = (T_ < 0.0)
        
        pvsat[idxs_subzero] \
            = 610.5*np.exp((21.875*T_[idxs_subzero])/(265.5+T_[idxs_subzero]))
    
    vsat = 1000.0 * pvsat / (R_w*(273.15+T_))
    
    return(vsat)

     


def calc_indoor_conditions(Te, RHe):
    # [Te] = degC
    # [RHe] = 1 (0...1)
    
    # Outdoor conditions
    ve = RHe * calc_vsat(Te)
    
    Te_24hmean = Te.rolling(24, center=True, min_periods=1).mean()
    ve_24hmean = ve.rolling(24, center=True, min_periods=1).mean()
    
    # Indoor temperature
    Te_low = 10.0
    Te_high = 20.0
    Ti_low = 21.0
    Ti_high = 21.0

    xp = (Te_low, Te_high)
    fp = (Ti_low, Ti_high)

    Ti_24hmean = np.interp(Te_24hmean, xp, fp)
    
    # Indoor air vapor concentration
    Te_low = 5.0
    Te_high = 15.0
    dv_low = 5.0
    dv_high = 2.0
    
    xp = (Te_low, Te_high)
    fp = (dv_low, dv_high)
    
    dv_24hmean = np.interp(Te_24hmean, xp, fp)
    
    vi_24hmean = ve_24hmean + dv_24hmean
    
    # Indoor relative humidity
    vsat_Ti = calc_vsat(Ti_24hmean)
    phii_24hmean = vi_24hmean / vsat_Ti
    phii_24hmean = np.minimum(phii_24hmean, 0.8)
    
    # Return values
    return(Ti_24hmean, vi_24hmean, phii_24hmean)


    


def save_to_file_for_comsol(x, fname):
    
    if type(x) == np.ndarray:
        tup = (np.arange(start=0, stop=len(x)),
               x)
    
    elif type(x) == pd.core.series.Series:
        tup = (np.arange(start=0, stop=len(x)),
               x.values)
    
    else:
        print('Uncertain of variable type', flush=True)
        tup = (np.arange(start=0, stop=len(x)),
               x)
        
        
    X = np.column_stack(tup)
    
    np.savetxt(fname, X, fmt = ['%d','%.5f'])
    
    return(X)



def calc_LWincoming(slope_as_quotient, LWdn, Te):
    
    # slope_as_quotient = dy/dx from horizontal level
    # degrees from horizontal, wall=90
    # surface_tilt = 90.0
    
    # [LWdn] = W/m2
    # [T_e] = degC
    
    # View factors
    surface_tilt = np.arctan(slope_as_quotient)*(180.0/np.pi)

    print(f'1/slope = {1/slope_as_quotient:.2f}, slope = {surface_tilt:.2f} deg')

    F_surf_sky = ( np.cos((np.pi/180.0)*(surface_tilt/2.0)) )**2

    F_surf_ground = 1.0 - F_surf_sky
    
    
    # long-wave radiation from ground
    # LW reflectivity of ground is assumed zero
    emissivity_ground = 0.95
    sigma_SB = 5.67e-8
    
    T_ground = Te.rolling(window=730, min_periods=1).mean()
    
    LWup = emissivity_ground * sigma_SB * (T_ground + 273.15)**4
    
    # Total incoming long-wave radiation towards a surface

    LW_incoming = F_surf_sky * LWdn \
                + F_surf_ground * LWup
                
    return(LW_incoming)


    



def calc_WDR(ws, wd, precip_horizontal, Te, 
             terrain_category,
             z_building, Theta_azimuth):
    # [ws] = m/s
    # [wd] = deg, degrees clockwise from north
    # [precip_horizontal] = mm/h
    # terrain_category = {'0','I','II','III', 'IV'}
    # [z_building] = m
    # [Theta_azimuth] = deg, surface azimuth
    
    
    C_T = 1.0
    O = 1.0
    W = 0.5
    a_r = 0.7
    
    z_0_II_1991 = 0.05


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
    
    
    
    I_S = (2.0/9.0) * ws * ( precip_horizontal**(8.0/9.0) ) \
            * np.maximum( np.cos( (np.pi/180.0)*(wd-Theta_azimuth) ) , 0.0)
    
    k_r_1991 = 0.19 * (z_0_1991/z_0_II_1991)**0.07
    
    C_R_1991 = k_r_1991 * np.log(np.max((z_building, z_min_1991))/z_0_1991)
    
    C_R_15927 = K_R_15927 * np.log(np.max((z_building, z_min_15927))/z_0_15927)
    
    
    # C_R_1991 or C_R_15927 ?
    # z_min is bigger in SFS-EN ISO 15927-3, which leads to
    # higher wind velocity and wind-driven rain amounts
    # when calculated for buildings for which z_building < z_min
    C_R = C_R_15927    
    
    I_WS = I_S * C_R * C_T * O * W * a_r
    
    
    # Include only wind-driven rain when outdoor air temperature is above 0 degC
    idxs_subzero = Te < 0.0
    I_WS[idxs_subzero] = 0.0
    
    
    return(I_WS)






def calc_solar_radiation_to_surface(time,
                                    location,
                                    surface_tilt,
                                    surface_azimuth,
                                    Idif_hor,
                                    Idir_hor,
                                    Te):
    
    
    if type(location) is str:
        if 'Van' in location:
            # Vantaa Helsinki-Vantaan lentoasema, 100968
            latitude = 60.33
            longitude = 24.97
            altitude = 47.0
    
        elif 'Jok' in location:
            # Jokioinen Ilmala, 101104
            latitude = 60.81
            longitude = 23.5
            altitude = 104.0
            
        elif 'Jyv' in location:
            # Jyväskylä lentoasema
            latitude = 62.4
            longitude = 25.67
            altitude = 139.0
    
        elif 'Sod' in location:
            # Sodankylä Tähtelä
            latitude = 67.37
            longitude = 26.63
            altitude = 179.0
    
        else:
            print('Unknown location!')
    
    else:
        
        latitude = location['latitude']
        longitude = location['longitude']
        altitude = location['altitude']
    
    
    
    solar_position = pvlib.solarposition.get_solarposition(time, 
                                                      latitude, 
                                                      longitude, 
                                                      altitude=altitude, 
                                                      method='nrel_numpy', 
                                                      temperature=Te)
    
    solar_zenith = solar_position.loc[:,'zenith'].values

    solar_azimuth = solar_position.loc[:,'azimuth'].values
    
    # Transposition
    ghi = Idif_hor + Idir_hor
    dhi = Idif_hor
    
    dni = pvlib.irradiance.dni(ghi=ghi, 
                               dhi=dhi, 
                               zenith=solar_zenith, 
                               clearsky_dni=None, 
                               clearsky_tolerance=1.1, 
                               zenith_threshold_for_zero_dni=88.0, 
                               zenith_threshold_for_clearsky_limit=80.0)

    
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

    
    # In comsol interpolation for each time point is used,
    # so radiation is interpolated to even hours for which 
    # the time stamps are.
    
    
    xp = total_irrad.index.values
    fp = total_irrad['poa_global'].values
    x = np.arange(-0.5,8760-0.5,1.0)
    
    poa_global_evenHours = np.interp(x, xp, fp)
    
    # print(total_irrad['poa_global'].sum()/1000)
    # print(poa_global_evenHours.sum()/1000)
    
    return(poa_global_evenHours)
    



def MI(dataT, dataRH, MGspeedclass, MGmaxclass, Cmat):
    
    """
    # Example 1, just to get started    
    import numpy as np
    import matplotlib.pyplot as plt
    % matplotlib inline

    tmax = 120*168
    t = np.arange(0, tmax/168+0.01, 1/168)
    T = 22 * np.ones(len(t))
    RH = 90 * np.ones(len(t))
    Mspeedclass = 's'
    Mmaxclass = 's'
    Cmat = 0.25

    Mvals = tutpy.MI(T, RH, Mspeedclass, Mmaxclass, Cmat)

    plt.plot(t, Mvals)
    plt.xlim([0, 120])
    plt.ylim([0, 6])
    plt.grid()
    """
    # import numpy as np

    # This was previously, one class can be given as argument
    # MGspeedclass = oneclass;
    # MGmaxclass = oneclass;

    # Array for mold index values is created to avoid resizing
    M = np.zeros(dataT.size)

    # Time from the beginning of the recession
    TFR = 0


    # Determining the factors for k2
    # These are constant throughout the calculation
    # They are used to calculate the Mmax
    if MGmaxclass == 'vs':
        A = 1
        B = 7
        C = 2
    elif MGmaxclass == 's':
        A = 0.3
        B = 6
        C = 1
    elif MGmaxclass == 'mr':
        A = 0
        B = 5
        C = 1.5
    elif MGmaxclass == 'r':
        A = 0
        B = 3
        C = 1

    # RHmin is determined, it is also in the calculation of Mmax
    if MGspeedclass == 'vs':
        RHmin = 80
    elif MGspeedclass == 's':
        RHmin = 80
    elif MGspeedclass == 'mr':
        RHmin = 85
    elif MGspeedclass == 'r':
        RHmin = 85

    # Next the actual calculation
    for k in range(dataT.size - 1):

        # First the limit value for RH
        if dataT[k] < 0.0:
            RHcrit=100
        else:
            RHcrit = np.max([-0.00267*dataT[k]**3 + 0.16*dataT[k]**2 \
                -3.13*dataT[k]+100, RHmin])

        # Then mould growth/decline speed calculation
        if dataT[k]>0.0 and dataT[k]<50.0 and dataRH[k]>=RHcrit:
            # Mould grows

            dummy1 = (RHcrit-dataRH[k])/(RHcrit-100.0)
            Mmax = np.max([A + B*dummy1 - C*dummy1**2, 0.0])

            if M[k] < 1.0:
                if MGspeedclass == 'vs':
                    k1 = 1
                elif MGspeedclass == 's':
                    k1 = 0.578
                elif MGspeedclass == 'mr':
                    k1 = 0.072
                else:
                    k1 = 0.033
                    
            else:
                if MGspeedclass == 'vs':
                    k1 = 2
                elif MGspeedclass == 's':
                    k1 = 0.386
                elif MGspeedclass == 'mr':
                    k1 = 0.097
                else:
                    k1 = 0.014

            # Time from the beginning of the recession
            TFR = 0
            k2 = np.max([1.0-np.exp(2.3*(M[k]-Mmax)), 0.0])
            
            # log() calculates natural logarithm
            # Two parameters from the old model are removed (+0.14*W-0.33*SQ)
            dummy2 = -0.68*np.log(dataT[k]) \
                -13.9*np.log(dataRH[k]) + 66.02
            dMdt = (1.0/(7*np.exp(dummy2))) \
                * k1 * k2 * (1.0/24.0)

        else:
            # Mould doesn't grow
                                                     
            # Time from the beginning of recession
            TFR = TFR + 1
            
            if TFR <= 6:
                dMdt0 = -0.032*(1/24)
            elif TFR >6 and TFR <=24:
                dMdt0 = 0
            else:
                dMdt0 = -0.016*(1/24)

            # The dMdt is sometimes written as (dM0/dt)mat
            # Time step is one hour
            dMdt = Cmat * dMdt0*1

        # Calculation of the new mould index value
        # New mould index value, one hour time step
        M[k+1] = np.max([M[k]+dMdt*1, 0])
    return(M)



def MI_RHcrit(T):
    # [T] = degC
    # RHCrit always for very sensitive
    
    RHcrit = np.maximum(-0.00267*T**3 + 0.16*T**2 - 3.13*T + 100, 80.0)
    
    RHcrit[T < 0.0] = 100.0
    RHcrit[T > 50.0] = 100.0
    
    return(RHcrit)

    