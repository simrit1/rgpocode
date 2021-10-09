# rgpocode
#### Offline reverse geocoder with postal codes

rgpocode accepts a postal code and returns a list containing the name of:

*	A place
*	First administrative unit
*	Second administrative unit
*    Third administrative unit
*	ISO country code

Credits: rgpocode uses data sourced from https://www.geonames.org/ and is used under a CC 4.0 license [(link to Creative Commons 4.0)](https://creativecommons.org/licenses/by/4.0/)

##	Install

     pip install r-gpocode
     
     >>> location = start_rgpocode(560001)
     
     >>> print(location)
     
     [... {'place_name': 'Mahatma Gandhi Road', 'admin1': 'Karnataka', 'admin2': 'Bengaluru', 'admin3': 'Bangalore North', 'country_code': 'IN'}, ...]

## Requirements

*	sqlite3
*	python version >= 2.5

##	First run

The first time rgpocode is run, it attempts to download the *allCountries.zip* file from geonames.org which is ~120MB. After the download completes, the required data is copied to a local sqlite3 database. After the database is created, the downloaded files are deleted. Subsequent calls to *start_rgpocode()* reference the data in the database. The files are created in the same folder as the script in which *start_rgpocode()* is imported. When *start_rgpocode()* is called from the interactive shell the files are downloaded and created in the home path.

##	Options

If you need to reverse geocode for locations only in specific countries, you can reduce the size of the database *(gpo.db)* by calling *filter_rgpocode(stringList)*.

     >>> from rgpocode import filter_rgpocode
     
     >>> codelist = ['US']
     
     >>> status = filter_rgpocode(codelist)
     
     >>> print(status)
     
     Database filtered: Deleted 1506801 rows.

To retrieve ISO country codes:

     >>> from rgpocode import country_code
     
     >>> codes = country_code()
     
     >>> print(codes)
     
     {'AD': 'Andorra', 'AE': 'United Arab Emirates', ... , 'CS': 'Serbia and Montenegro', 'AN': 'Netherlands Antilles'}

Other projects: [Reverse geocoding (latitude / longitude)](https://pypi.org/project/r-geocode/)
