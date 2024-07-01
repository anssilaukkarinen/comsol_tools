# -*- coding: utf-8 -*-
"""
Created on Fri Jun 28 15:56:23 2024

@author: laukkara
"""

import os
import pickle
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import helper



# Input and output folders can be changed as needed

input_folder = r'S:\91202_Rakfys_yhteiset\Tiiliverhous\2_Laskenta\results_data'
output_folder = os.path.join(r'S:\91202_Rakfys_yhteiset\Tiiliverhous\2_Laskenta\results_data',
                            'figures')

# input_folder = r'C:\Temp\tiiliverhous\results_data'
# output_folder = r'C:\Temp\tiiliverhous\results_data\figures'




####################

fname = os.path.join(input_folder,
                     'results.pickle')

with open(fname, 'rb') as f:
    data = pickle.load(f)


if not os.path.exists(output_folder):
    os.makedirs(output_folder)


figseiz = (5.5, 3.5)

# This can be e.g. 100 during preliminatyr calculations
# and 300 during final figures
dpi_val = 100 



######################


## Time series

indicators_list = []

for key in data.keys():
    
    cols_to_plot = [x for x in data[key].columns if 'T_' in x or 'RH_' in x or 'M_' in x]
    
    
    
    for col in cols_to_plot:
    
        # plot
        
        fig, ax = plt.subplots(figsize=figseiz)
        
        data[key].loc[:,col].plot(ax=ax,
                                  grid=True,
                                  lw=0.5)
        ax.set_xlabel('Tuntia vuoden alusta')
        ax.set_ylabel(col)
        ax.set_title(key)
        
        fname = os.path.join(output_folder,
                             f'{key}_{col}.png')
        fig.savefig(fname, dpi=dpi_val, bbox_inches='tight')
        plt.close(fig)
        
        
        # Indicators
        
        if 'M_' in col:
            Mmax = data[key].loc[:,col].max()
            
            indicators_list.append([key, col, 'Mmax', Mmax])
        
        if 'RH_' in col:
            
            RH_over_95 = (data[key].loc[:,col] > 95.0).sum()
            
            indicators_list.append([key, col, 'RH_over_95', RH_over_95])


# Save indicators to file

df_indicators = pd.DataFrame(data=indicators_list, 
                                  columns=['key','col','indicator','value'])
df_indicators.index.name = 'index'

fname = os.path.join(output_folder,
                     'indicators.csv')
df_indicators.to_csv(fname)


            


        
        
    
    
    
    
    