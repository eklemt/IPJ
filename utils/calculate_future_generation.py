import pandas as pd
from utils.addTimePerformance import addTimePerformance
from szenarioDefinition.szenario import *

def calculate_future_generation(case_PV, case_WindOnshore, case_WindOffshore, dataFrame_performance, dataFrame_generation_start_year):
    # Erstellung eines leeren Dictionaries für die Generation
    directoryGeneration = {}

    # Kopieren der DataFrames, um die Originaldaten nicht zu verändern
    df_performance = dataFrame_performance.copy()
    df_generation_start_year = dataFrame_generation_start_year.copy()

    # Pfade zu den CSV-Dateien, je nach Case
    filepath_PV = f'CSV/Installed/{case_PV}_Photovoltaik_projections.csv'
    filepath_Onshore = f'CSV/Installed/{case_WindOnshore}_Wind Onshore_projections.csv'
    filepath_Offshore = f'CSV/Installed/{case_WindOffshore}_Wind Offshore_projections.csv'

    # Einlesen der CSV-Dateien
    df_PV = pd.read_csv(filepath_PV)
    df_Onshore = pd.read_csv(filepath_Onshore)
    df_Offshore = pd.read_csv(filepath_Offshore)

    # Alle Daten ab 2024 sind von Interesse
    df_filtered_PV = df_PV[df_PV['year'] >= 2024].reset_index(drop=True)
    df_filtered_Onshore = df_Onshore[df_Onshore['year'] >= 2024].reset_index(drop=True)
    df_filtered_Offshore = df_Offshore[df_Offshore['year'] >= 2024].reset_index(drop=True)

    # Zusammenführen der Daten
    df_combined = pd.concat([
        df_filtered_PV['year'],
        df_filtered_PV['projected_capacity'],
        df_filtered_Onshore['projected_capacity'],
        df_filtered_Offshore['projected_capacity']
    ], axis=1)
    df_combined.columns = ['Jahr', 'Photovoltaik', 'Wind Onshore', 'Wind Offshore']

    # Umwandlung in ein Dictionary
    directoryInstalled = df_combined.set_index('Jahr').to_dict(orient='index')

    # Schleife für die Jahre 2024 bis 2030
    for year in range(2024, 2031):
        if year + 1 in directoryInstalled:  # Falls ein Folgejahr existiert
            dayly_expansion_rate_PV = (directoryInstalled[year + 1]['Photovoltaik'] - directoryInstalled[year]['Photovoltaik']) / 365
            dayly_expansion_rate_Onshore = (directoryInstalled[year + 1]['Wind Onshore'] - directoryInstalled[year]['Wind Onshore']) / 365
            dayly_expansion_rate_Offshore = (directoryInstalled[year + 1]['Wind Offshore'] - directoryInstalled[year]['Wind Offshore']) / 365
        else:  # Keine Daten für das Folgejahr vorhanden
            dayly_expansion_rate_PV = 0
            dayly_expansion_rate_Onshore = 0
            dayly_expansion_rate_Offshore = 0


        # Erstellung eines DataFrames für die Tageswerte
        PV_generation = []
        Onshore_generation = []
        Offshore_generation = []

        for day in range(365):
            start_index = day * 96
            end_index = (day + 1) * 96

            daily_PV = (directoryInstalled[year]['Photovoltaik'] + day * dayly_expansion_rate_PV) * 0.25
            daily_Onshore = (directoryInstalled[year]['Wind Onshore'] + day * dayly_expansion_rate_Onshore) * 0.25
            daily_Offshore = (directoryInstalled[year]['Wind Offshore'] + day * dayly_expansion_rate_Offshore) * 0.25

            PV_generation.extend(df_performance['Photovoltaik'].iloc[start_index:end_index] * daily_PV)
            Onshore_generation.extend(df_performance['Wind Onshore'].iloc[start_index:end_index] * daily_Onshore)
            Offshore_generation.extend(df_performance['Wind Offshore'].iloc[start_index:end_index] * daily_Offshore)

        # Erstellung eines DataFrames für das Jahr
        combined_generation = pd.DataFrame({
            'Photovoltaik': PV_generation,
            'Wind Onshore': Onshore_generation,
            'Wind Offshore': Offshore_generation,
            'Wasserkraft': df_generation_start_year['Wasserkraft'],
            'Biomasse': df_generation_start_year['Biomasse'],
            'Sonstige Erneuerbare': df_generation_start_year['Sonstige Erneuerbare']
        })

        # Netzverluste einbeziehen
        combined_generation *= netzverluste # aus szenarioDefinition/szenario.py

        addTimePerformance(combined_generation, year)

        # Speichern des Jahres-DataFrames in das Dictionary
        directoryGeneration[year] = combined_generation

    return directoryGeneration