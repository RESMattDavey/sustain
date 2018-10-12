import pandas as pd
import datetime as dt
import numpy as np
year = 2018
s = dt.datetime(year,1,1)
e = dt.datetime(year+1,1,1)
heating_efficiency = 0.8
tariff_name_elec = 'Eco7'
tariff_name_heat = 'Gas'

tariffs_df = pd.read_excel(r'C:\Users\mdavey\PycharmProjects\sustain\cfg.xlsx',sheet_name='tariffs')
tariff_elec = tariffs_df[tariff_name_elec][:24].to_frame('unit_cost')
standing_charge_elec = tariffs_df[tariff_name_elec][24]
tariff_heat = tariffs_df[tariff_name_heat][:24].to_frame('unit_cost')
standing_charge_heat = tariffs_df[tariff_name_heat][24]
if tariff_name_heat == tariff_name_elec:
    standing_charge_heat = 0

energy_profile = pd.read_excel(r'C:\Users\mdavey\PycharmProjects\sustain\cfg.xlsx',sheet_name='energy_hour')
day_elec_pc = energy_profile[['weekday_elec','weekend_elec']].iloc[24]
energy_profile = energy_profile.iloc[:24]

def calc_heating_required(df,energy_profile,comfy_temp=20,leakiness = 6/24):
    df['temp_delta'] = comfy_temp-df['temperature']
    df['heating_required_kwh'] = df['temp_delta'] * leakiness
    df['heating_required'] = 0
    for hour in energy_profile.index:
        df.loc[((df.weekday >= 5) & (df.hour == hour)),'heating_required'] = energy_profile['weekend_heat'][hour]
        df.loc[((df.weekday < 5) & (df.hour == hour)), 'heating_required'] = energy_profile['weekday_heat'][hour]
    df['heating_required_kwh'] = df['heating_required_kwh']*df['heating_required']
    df.loc[df['heating_required_kwh'] <= 0,'heating_required_kwh'] = 0
    return df

def calc_elec_required(df,energy_profile,day_elec_pc, mean_annual_kwh=5000):
    df['elec_required_kwh'] = 0
    for hour in energy_profile.index:
        df.loc[((df.weekday >= 5) & (df.hour == hour)),'elec_required_kwh'] = energy_profile['weekend_elec'][hour]*day_elec_pc[1]*mean_annual_kwh/365
        df.loc[((df.weekday < 5) & (df.hour == hour)), 'elec_required_kwh'] = energy_profile['weekday_elec'][hour]*day_elec_pc[0]*mean_annual_kwh/365
    return df

hourly_idx = pd.DatetimeIndex(freq='1H', start=s, end=e)
hr_df = pd.DataFrame(index=hourly_idx)
hr_df['hour'] = hr_df.index.hour
hr_df['weekday'] = hr_df.index.weekday

climate_cols = ['temperature']
climate = pd.read_csv(r'C:\Users\mdavey\PycharmProjects\sustain\climate.csv',index_col=0,parse_dates=[0])
hr_df = hr_df.merge(climate[climate_cols], left_index=True,right_index=True)

hr_df = calc_heating_required(hr_df,energy_profile)
hr_df = calc_elec_required(hr_df,energy_profile,day_elec_pc)

hr_df = hr_df.merge(tariff_heat, left_on='hour', right_index=True, how='left')
hr_df = hr_df.rename(columns={'unit_cost': 'unit_cost_heat'})
hr_df['heat_cost'] = hr_df['heating_required_kwh']*hr_df['unit_cost_heat']/heating_efficiency

hr_df = hr_df.merge(tariff_elec, left_on='hour', right_index=True, how='left')
hr_df = hr_df.rename(columns={'unit_cost': 'unit_cost_elec'})
hr_df['elec_cost'] = hr_df['elec_required_kwh']*hr_df['unit_cost_elec']

daily_df = hr_df[['elec_cost','heat_cost']].resample('1M').sum()

daily_df['elec_cost'] += standing_charge_elec
daily_df['heat_cost'] += standing_charge_heat

monthly_df = daily_df[['elec_cost','heat_cost']].resample('1M').sum()

print(monthly_df['elec_cost'].sum(), monthly_df['heat_cost'].sum())
print('a')