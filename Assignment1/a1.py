import json
import matplotlib.pyplot as plt
import pandas as pd
import sys
import os
import numpy as np
import math
import re

studentid = os.path.basename(sys.modules[__name__].__file__)


def log(question, output_df, other):
    print("--------------- {}----------------".format(question))

    if other is not None:
        print(question, other)
    if output_df is not None:
        df = output_df.head(5).copy(True)
        for c in df.columns:
            df[c] = df[c].apply(lambda a: a[:20] if isinstance(a, str) else a)

        df.columns = [a[:10] + "..." for a in df.columns]
        print(df.to_string())


def compare(a, b):
    if a > b:
        return "IN"
    elif a < b:
        return "OUT"
    else:
        return "SAME"


def question_1(city_pairs):
    """
    :return: df1
            Data Type: Dataframe
            Please read the assignment specs to know how to create the output dataframe
    """

    #################################################
    df1 = pd.read_csv(city_pairs)
    df1['passenger_in_out'] = df1.apply(lambda x: compare(x.Passengers_In, x.Passengers_Out), axis = 1)
    df1.rename(columns={'Freight_In_(tonnes)':'fin', 'Freight_Out_(tonnes)':'fout', 'Mail_In_(tonnes)':'mailin', 'Mail_Out_(tonnes)':'mout'}, inplace=True)
    df1['freight_in_out'] = df1.apply(lambda y: compare(y.fin, y.fout), axis = 1)
    df1['mail_in_out'] = df1.apply(lambda z: compare(z.mailin, z.mout), axis = 1)
    df1.rename(columns={'fin':'Freight_In_(tonnes)', 'fout':'Freight_Out_(tonnes)', 'mailin':'Mail_In_(tonnes)', 'mout':'Mail_Out_(tonnes)'}, inplace=True)
    #################################################

    log("QUESTION 1", output_df=df1[["AustralianPort", "ForeignPort", "passenger_in_out", "freight_in_out", "mail_in_out"]], other=df1.shape)
    return df1


def question_2(df1):
    """
    :param df1: the dataframe created in question 1
    :return: dataframe df2
            Please read the assignment specs to know how to create the output dataframe
    """

    #################################################
    a = sorted(list(set(df1['AustralianPort'].tolist())))
    data = {'AustralianPort': a}
    df2 = pd.DataFrame(data)
    result1 = []
    result2 = []
    result3 = []
    result4 = []
    result5 = []
    result6 = []
    for i in a:
        result1.append(((df1['AustralianPort'] == i) & (df1['passenger_in_out'] == 'IN')).sum())
        result2.append(((df1['AustralianPort'] == i) & (df1['passenger_in_out'] == 'OUT')).sum())
        result3.append(((df1['AustralianPort'] == i) & (df1['freight_in_out'] == 'IN')).sum())
        result4.append(((df1['AustralianPort'] == i) & (df1['freight_in_out'] == 'OUT')).sum())
        result5.append(((df1['AustralianPort'] == i) & (df1['mail_in_out'] == 'IN')).sum())
        result6.append(((df1['AustralianPort'] == i) & (df1['mail_in_out'] == 'OUT')).sum())
    df2['PassengerInCount'] = result1
    df2['PassengerOutCount'] = result2
    df2['FreightInCount'] = result3
    df2['FreightOutCount'] = result4
    df2['MailInCount'] = result5
    df2['MailOutCount'] = result6
    df2.sort_values(by='PassengerInCount', inplace=True, ascending=False, ignore_index=True)
    #################################################

    log("QUESTION 2", output_df=df2, other=df2.shape)
    return df2


def question_3(df1):
    """
    :param df1: the dataframe created in question 1
    :return: df3
            Data Type: Dataframe
            Please read the assignment specs to know how to create the output dataframe
    """
    #################################################
    a = sorted(list(set(df1['Country'].tolist())))
    data = {'Country': a}
    df3 = pd.DataFrame(data)
    r1 = df1.groupby('Country')['Passengers_In'].agg(['sum']).reset_index()
    result1 = list(r1['sum']/453)
    df3['Passengers_in_average'] = result1
    r2 = df1.groupby('Country')['Passengers_Out'].agg(['sum']).reset_index()
    result2 = list(r2['sum']/453)
    df3['Passengers_out_average'] = result2
    df3['Passengers_out_average'] = df3['Passengers_out_average'].map(lambda x: f'{x:,.2f}')
    df3['Passengers_out_average'] = df3['Passengers_out_average'].str.replace(',', '')
    r3 = df1.groupby('Country')['Freight_In_(tonnes)'].agg(['sum']).reset_index()
    result3 = list(r3['sum']/453)
    df3['Freight_in_average'] = result3
    df3['Freight_in_average'] = df3['Freight_in_average'].map(lambda x: f'{x:,.2f}')
    df3['Freight_in_average'] = df3['Freight_in_average'].str.replace(',', '')
    r4 = df1.groupby('Country')['Freight_Out_(tonnes)'].agg(['sum']).reset_index()
    result4 = list(r4['sum'] / 453)
    df3['Freight_out_average'] = result4
    df3['Freight_out_average'] = df3['Freight_out_average'].map(lambda x: f'{x:,.2f}')
    df3['Freight_out_average'] = df3['Freight_out_average'].str.replace(',', '')
    r5 = df1.groupby('Country')['Mail_In_(tonnes)'].agg(['sum']).reset_index()
    result5 = list(r5['sum'] / 453)
    df3['Mail_in_average'] = result5
    df3['Mail_in_average'] = df3['Mail_in_average'].map(lambda x: f'{x:,.2f}')
    df3['Mail_in_average'] = df3['Mail_in_average'].str.replace(',', '')
    r6 = df1.groupby('Country')['Mail_Out_(tonnes)'].agg(['sum']).reset_index()
    result6 = list(r6['sum'] / 453)
    df3['Mail_out_average'] = result6
    df3['Mail_out_average'] = df3['Mail_out_average'].map(lambda x: f'{x:,.2f}')
    df3['Mail_out_average'] = df3['Mail_out_average'].str.replace(',', '')
    df3.sort_values(by=['Passengers_in_average'], inplace=True, ascending=True, ignore_index=True)
    df3['Passengers_in_average'] = df3['Passengers_in_average'].map(lambda x:f'{x:,.2f}')
    df3['Passengers_in_average'] = df3['Passengers_in_average'].str.replace(',', '')
    #################################################

    log("QUESTION 3", output_df=df3, other=df3.shape)
    return df3


def question_4(df1):
    """
    :param df1: the dataframe created in question 1
    :return: df4
            Data Type: Dataframe
            Please read the assignment specs to know how to create the output dataframe
    """

    #################################################
    new_df = df1[['AustralianPort', 'Country', 'ForeignPort', 'Month', 'Passengers_Out']].copy()
    new_df = new_df[new_df['Passengers_Out'] > 0].drop_duplicates(['AustralianPort', 'Country', 'Month', 'ForeignPort'])
    df4 = new_df.groupby(['Country'])['ForeignPort'].nunique().sort_values(ascending=False)
    df4 = df4.sort_values(ascending=False).groupby(df4.values).apply(
        lambda x: x.sort_values())
    df4 = df4.reset_index(name='Unique_ForeignPort_Count')[['Country', 'Unique_ForeignPort_Count']]
    df4 = df4.sort_values('Unique_ForeignPort_Count', ascending=False, ignore_index=True)
    df4 = df4.head(5)
    #################################################

    log("QUESTION 4", output_df=df4, other=df4.shape)
    return df4


def question_5(seats):
    """
    :param seats : the path to dataset
    :return: df5
            Data Type: dataframe
            Please read the assignment specs to know how to create the  output dataframe
    """
    #################################################
    df5 = pd.read_csv(seats)
    df5['Source_City'] = df5.apply(lambda x: x.International_City if x.In_Out == 'I' else x.Australian_City, axis=1)
    df5['Destination_City'] = df5.apply(lambda y: y.Australian_City if y.In_Out == 'I' else y.International_City, axis=1)
    #################################################

    log("QUESTION 5", output_df=df5, other=df5.shape)
    return df5


def question_6(df5):
    """
    :param df5: the dataframe created in question 5
    :return: df6
    """

    #################################################
    """
    The new data frame first lists all of their routes according to different airlines, 
    using 'Australian_City 'and' International_City 'gives the' route 'column. Then use 'Max_Seats'
    column calculates the total number of seats and the average number of seats on the route. 
    These two columns can be used to simply determine whether the transportation capacity of the 
    route is saturated. Then calculate the number of competitors by counting the same routes in the 
    departure city and destination city, that is, how many airlines are operating this route, so as 
    to judge the risk of opening the same route.
    """

    df6 = df5.groupby(['Airline', 'Australian_City', 'International_City']).agg(
        Total_Seats=('Max_Seats', 'sum'),
        Avg_Seats=('Max_Seats', 'mean'),
    ).reset_index()
    df6['Route'] = df6['Australian_City'] + ' - ' + df6['International_City'].fillna('')
    competition_data = df6.groupby(['Australian_City', 'International_City']).agg(
        Competition=('Airline', 'count')
    ).reset_index()
    df6 = df6.merge(competition_data, on=['Australian_City', 'International_City'], how='left')
    df6['Avg_Seats'] = df6['Avg_Seats'].round(2)
    df6 = df6[['Airline', 'Route', 'Total_Seats', 'Avg_Seats', 'Competition']]
    #################################################

    log("QUESTION 6", output_df=df6, other=df6.shape)
    return df6


def question_7(seats, city_pairs):
    """
    :param seats: the path to dataset
    :param city_pairs : the path to dataset
    :return: nothing, but saves the figure on the disk
    """

    #################################################
    """
    This code draws a line according to each "Port_Region", visualizes "Passengers_In" 
    and "Passengers_Out" as functions of "Year", and the result is seat utilization. 
    For each area, I created a separate graph and combined them into a single graph. 
    Draw a line at 100% utilization to help compare the size. This visualization will help 
    us understand the trend of seat utilization around the world.
    """
    seats = pd.read_csv(seats, dtype={'Year': str})
    city_pairs = pd.read_csv(city_pairs, dtype={'Year': str})

    merged_data = pd.merge(city_pairs, seats, on=['Month', 'Year', 'Month_num'])
    grouped_data = merged_data[['Port_Region', 'Year', 'Passengers_In', 'Passengers_Out', 'Max_Seats']].groupby(
        ['Port_Region', 'Year']).sum().reset_index()
    fig, axes = plt.subplots(nrows=2, ncols=5, figsize=(30, 8))
    regions = grouped_data['Port_Region'].unique()

    for i, ax in enumerate(axes.flatten()):
        region_data = grouped_data[grouped_data['Port_Region'] == regions[i]]
        ax.plot(region_data['Year'], region_data['Passengers_In'] / region_data['Max_Seats'], label='Passengers_In')
        ax.plot(region_data['Year'], region_data['Passengers_Out'] / region_data['Max_Seats'], label='Passengers_Out')
        ax.plot(region_data['Year'], region_data['Max_Seats'] / region_data['Max_Seats'], label='Max_Seats')
        ax.set_title(regions[i])
        ax.set_xlabel('Year')
        ax.set_ylabel('Seat Utilization')
        ax.legend()
        ax.set_xticks(region_data['Year'][::2])
        ax.set_xticklabels(region_data['Year'][::2])

    plt.tight_layout()
    #################################################

    plt.savefig("{}-Q7.png".format(studentid))


if __name__ == "__main__":
    df1 = question_1("city_pairs.csv")
    df2 = question_2(df1.copy(True))
    df3 = question_3(df1.copy(True))
    df4 = question_4(df1.copy(True))
    df5 = question_5("seats.csv")
    df6 = question_6(df5.copy(True))
    question_7("seats.csv", "city_pairs.csv")