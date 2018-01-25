#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
import datetime
from datetime import timedelta

class weather_underground_parser:

    # default location is Heathrow
    def __init__(self, start_datetime, end_datetime, loc_string = "airport/EGLL"):

        self.location_string = loc_string

        self.temperature = [];
        self.pressure = [];
        self.relative_humidity = [];
        self.datetime = [];
        self.epochtime = [];
        self.precipitation = [];
        self.humidity = [];

        self.html_table = [];
        self.year = 2017
        self.month = 1
        self.day = 1

        # Loop over each in the datetime range and extract the relevant weather data
        day_count = (end_datetime - start_datetime).days + 1
        # Main loop
        for single_date in [d for d in (start_datetime + timedelta(n) for n in range(day_count)) if d <= end_datetime]:

                # For this date, download the data and parse the pressure and datetimes
                self.parse_weather_underground(single_date)

                # Extract the weather data and datetimes
                self.extract_pressure(self.html_table);
                self.extract_datetimes(self.html_table);
                self.extract_relative_humidity(self.html_table)
                self.extract_temperatures(self.html_table)

    def parse_weather_underground(self, date_time):

        # e.g. "https://www.wunderground.com/history/airport/EGLL/2017/1/23/DailyHistory.html?req_city=Twickenham&req_state=GLA&req_statename=United%20Kingdom&reqdb.zip=00000&reqdb.magic=57&reqdb.wmo=03772"
        # Convert the datetime object into a readable url
        base_url = "https://www.wunderground.com/history/" + self.location_string + "/"

        # Get the year, month, day
        self.year = date_time.year
        self.month = date_time.month
        self.day = date_time.day

        base_url += str(self.year) + "/" + str(self.month) + "/" + str(self.day) + "/DailyHistory.html?req_city=Twickenham&req_state=GLA&req_statename=United%20Kingdom&reqdb.zip=00000&reqdb.magic=57&reqdb.wmo=03772"
        response = requests.get(base_url)
        soup = BeautifulSoup(response.text, 'lxml')

        # Get the right hourly table
        table = self.parse_html_table(soup.find_all("table")[4])
        self.html_table = table


    def extract_temperatures(self,table):
        temperatures = []

        # Loop over each line in the table
        for p in table.as_matrix():

            # This is the temperature value as a string
            new_temperature_value = p[1].split()[0]
            try:
                temperatures.append(float(new_temperature_value))
            except:
                temperatures.append(float('nan'))

        self.temperature.extend(temperatures)

    def extract_relative_humidity(self,table):
        rel_humid = []

        # Loop over each line in the table
        for p in table.as_matrix():

            # This is the rh value as a string in %
            new_rh_value = p[4].split()[0]

            # It has the % at the end so remove this
            try:
                rel_humid.append(float(new_rh_value[:-1]))
            except:
                rel_humid.append(float('nan'))

        self.relative_humidity.extend(rel_humid)

    # Returns an interpolated pressure for the given datetime
    def get_pressure(self,interp_datetime):
        # Convert the given datetime to epoch time
        this_epoch_time = (interp_datetime - datetime.datetime(1970,1,1)).total_seconds()

        # Interpolate
        return np.interp(this_epoch_time,np.asarray(self.epochtime),np.asarray(self.pressure))





    def extract_pressure(self,table):
        pressure_data = []

        # Loop over each line in the table
        for p in table.as_matrix():

            # This is the pressure value as a string
            new_pressure_value = p[5].split()[0]

            try:
                if(new_pressure_value.isdigit()):
                    pressure_data.append(float(new_pressure_value))
                else:
                    pressure_data.append(float('nan'))
            except:
                pressure_data.append(float('nan'))

        # Save the pressure data into the class variable
        self.pressure.extend(pressure_data)


    def extract_datetimes(self,table):

        time_data = [];
        epoch_times = []
        for p in table.as_matrix():
            # Get the hour and whether its am or pm
            new_hour_value = p[0].split()[0]
            new_am_pm_value = p[0].split()[1]

            # Create a string for the date
            date_string = "%d-%02d-%02d %s %s" % (self.year, self.month, self.day, new_hour_value, new_am_pm_value)

            format = '%Y-%m-%d %I:%M %p'
            table_datetime = datetime.datetime.strptime(date_string,format)
            time_data.append(table_datetime)
            epoch_times.append((table_datetime - datetime.datetime(1970,1,1)).total_seconds())

        self.datetime.extend(time_data)
        self.epochtime.extend(epoch_times)

    def parse_html_table(self, table):
        n_columns = 0
        n_rows=0
        column_names = []

        # Find number of rows and columns
        # we also find the column titles if we can
        for row in table.find_all('tr'):

            # Determine the number of rows in the table
            td_tags = row.find_all('td')
            if len(td_tags) > 0:
                n_rows+=1
                if n_columns == 0:
                    # Set the number of columns for our table
                    n_columns = len(td_tags)

            # Handle column names if we find them
            th_tags = row.find_all('th')
            if len(th_tags) > 0 and len(column_names) == 0:
                for th in th_tags:
                    column_names.append(th.get_text())

        # Safeguard on Column Titles
        if len(column_names) > 0 and len(column_names) != n_columns:
            #raise Exception("Column titles do not match the number of columns")
            return 0

        columns = column_names if len(column_names) > 0 else range(0,n_columns)
        df = pd.DataFrame(columns = columns,
        index= range(0,n_rows))
        row_marker = 0
        for row in table.find_all('tr'):
            column_marker = 0
            columns = row.find_all('td')
            for column in columns:
                df.iat[row_marker,column_marker] = column.get_text()
                column_marker += 1
            if len(columns) > 0:
                row_marker += 1

        # Convert to float if possible
        for col in df:
            try:
                df[col] = df[col].astype(float)
            except ValueError:
                pass

        return df
