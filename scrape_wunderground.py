import datetime as dt
import weather_underground_parser as wp


# Change these or put them in a loop
year=2016
month=1
day=7

start_datetime = dt.datetime(year,month,day)
end_datetime = dt.datetime(year,month,day)


# Gatwick
loc = "airport/EGKK"

# Heathrow
loc = "airport/EGLL"

hp = wp.weather_underground_parser(start_datetime,end_datetime, loc)

print(hp.relative_humidity)
