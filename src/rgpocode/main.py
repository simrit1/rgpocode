import os
from os.path import expanduser
import csv
import sys
from sys import platform
import sqlite3
import zipfile
import subprocess

conn = None
BASE_URL = 'http://download.geonames.org/export/'
FILE_ONE = 'allCountries'
FILE_TWO = "countryInfo.txt"
LOCATION = ''

if sys.version_info[0] == 3:
	import urllib.request
elif sys.version_info[0] < 3:
	import urllib
	
def connectdatabase():
	global conn
	global LOCATION
	try:
		conn = sqlite3.connect(os.path.join(LOCATION, 'gpo.db'))
	except sqlite3.Error as e:
		status='Error in postalcode: '+str(e)

def creategpotable():
	try:
		sql ="""CREATE TABLE gpotable(
        gpo_countrycode TEXT NOT NULL,
        gpo_postalcode TEXT NOT NULL,
        gpo_placename TEXT NOT NULL,
        gpo_admin1 TEXT,
        gpo_admin2 TEXT,
        gpo_admin3 TEXT,
        gpo_latitude REAL NOT NULL,
        gpo_longitude REAL NOT NULL
        )"""
		cursor = conn.cursor()
		cursor.execute(sql)
		conn.commit()
		status = 'table created'
	except sqlite3.Error as e:
		if not 'table already exists' in str(e):
			status='Error occured in creating table gpotable: '+ str(e)
			print(status)
	return(status)


def cleanup():
	global LOCATION
	global FILE_ONE
	if conn is not None:
		conn.close()

	if os.path.exists(os.path.join(LOCATION, FILE_ONE+'.zip')):
		os.remove(os.path.join(LOCATION, FILE_ONE+'.zip'))

	if os.path.exists(os.path.join(LOCATION, FILE_ONE+'.txt')):
		os.remove(os.path.join(LOCATION, FILE_ONE+'.txt'))

	if os.path.exists(os.path.join(LOCATION, 'gponamesdata.csv')):
		os.remove(os.path.join(LOCATION, 'gponamesdata.csv'))

	if os.path.exists(os.path.join(LOCATION, 'readme.txt')):
		os.remove(os.path.join(LOCATION, 'readme.txt'))

	
def downloadfile(filename, savetofile):
	global BASE_URL
	global LOCATION
	savetofile = os.path.join(LOCATION, savetofile)
	if sys.version_info[0] == 3:
		try:
			urllib.request.urlretrieve(BASE_URL + filename, savetofile)
			status = filename + ' download complete ...'
		except Exception as e:
			status='Error downloading file: ' + filename + ' ' + str(e)
	elif sys.version_info[0] < 3:
		try:
			urllib.urlretrieve(BASE_URL + filename, savetofile)
			status = filename + ' download complete ...'
		except Exception as e:
			status='Error downloading file: ' + filename + ' ' + str(e)
	return(status)

def do_check():
	global conn
	global LOCATION
	global FILE_ONE
	downloadflag = 0
	if sys.version_info[0] < 3 and sys.version_info[1] < 5:
		status = 'Python version should be greater than 2.5'
		return(status)

	if platform == "win32":
		if not os.path.exists(os.path.join(LOCATION, 'sqlite3.exe')):
			status='sqlite3.exe not found.'
			return(status)
		connectdatabase()
	else:
		if not os.path.exists(os.path.join(LOCATION, 'sqlite3')):
			status='sqlite3 not found.'
			return(status)
		connectdatabase()

	
	sql="""SELECT
	NAME
	FROM
	SQLITE_MASTER
	WHERE
	TYPE = 'table'
	AND
	NAME = 'gpotable';
	"""
	try:    
		cursor = conn.execute(sql)
		row = cursor.fetchone()
		if row is None:
			creategpotable()
			downloadflag = 1
		else:
			status = 'Start reverse postalcode - gpotable and file already exist ...'
	except sqlite3.Error as e:
	  	status = 'Error in reverse postalcode: ' + str(e)
	  	return(status)


	if downloadflag == 1:
		status = downloadfile('zip/'+FILE_ONE+'.zip', FILE_ONE+'.zip')
		if 'Error downloading file: ' in status:
			return(status)
		with zipfile.ZipFile(os.path.join(LOCATION, FILE_ONE+'.zip'), 'r') as z:
			z.extractall(LOCATION)

		f=open(os.path.join(LOCATION, 'gponamesdata.csv'), 'w', encoding='UTF-8')

		with open(os.path.join(LOCATION, FILE_ONE + '.txt'), 'r', encoding="utf8") as source:
			reader = csv.reader(source, delimiter='\t')
			for r in reader:
				f.write((r[0]+ '|' + r[1] + '|' + r[2] + '|' + r[3] + '|' + r[5] + '|' + r[7]+ '|' + r[9] + '|' + r[10] + '\n'))
			f.close()

		#Enclosing location of geonamesdata.csv file in quotes allows for spaces in file path
		NL = '"' + LOCATION  + '/' + "gponamesdata.csv" + '"'
		
		subprocess.call([
		os.path.join(LOCATION, "sqlite3"), 
		os.path.join(LOCATION, "gpo.db"), 
		"-separator", "|" ,
		".import "+ NL + " gpotable"
		])

	status = 'Start reverse postalcode'
	return(status)

def user_cwd(LOCATIONDICT):
	global LOCATION
	try:
		LOCATION = os.path.dirname(LOCATIONDICT['__file__'])
	except KeyError:
		#LOCATION is set to home path when start_rgpocode is run from interactive shell
		LOCATION = expanduser("~") 
	
	if platform == "win32":
		LOCATION = LOCATION + '\\'
		LOCATION = LOCATION.replace('\\', '\\\\')

	if len(LOCATION) == 0:			
		LOCATION = os.getcwd()		#LOCATION is set to cwd when rgpocode.py is main
	return(LOCATION)

def country_code():
	global LOCATION
	country_code_dictionary={}

	if not os.path.exists(os.path.join(LOCATION, 'countries.tsv')):
		status = downloadfile(FILE_TWO, 'countries.tsv')
		if 'Error downloading file: ' in status:
			return(status)
	try:
		with open(os.path.join(LOCATION, 'countries.tsv'), 'r', encoding="utf8") as source:
			reader = csv.reader(source, delimiter='\t')
			for row in reader:
				code = row[0]
				if not '#' in code:
					name = row[4]
					country_code_dictionary[code] = name
	except FileNotFoundError:
		status = 'File not found countries.tsv'
		return(status)
	return(country_code_dictionary)

def filter_rgpocode(codelist):
	LOCATIONDICT = sys._getframe(1).f_globals
	LOCATION = user_cwd(LOCATIONDICT)
	country_code_dictionary = country_code()

	if country_code_dictionary == 'File not found countries.tsv':
		status = 'File not found countries.tsv'
		return(status)

	connectdatabase()
	dictionary_keys = country_code_dictionary.keys()

	for key in range(len(codelist)):
		if codelist[key] not in dictionary_keys:
			status = 'Invalid country code: ' + str(codelist[key])
			return(status)

	code="'"
	delim = "',"
	for i in range(len(codelist)):
		code = code + "'" + str(codelist[i]) + delim
	
	code = code[1:-1]

	sql="""DELETE
	FROM gpotable
	WHERE gpo_countrycode NOT IN (""" + code +");"
	
	try: 
		cursor = conn.execute(sql)
		conn.commit()
		conn.execute("vacuum")	#This is to reduce file size of geo.db from ~600MB
		status = 'Database filtered: '
	except sqlite3.Error as e:
		status = 'Error in filter_rgpocode delete ' + str(e)
		
	if status == 'Database filtered: ':
		sql="SELECT changes();"
		try: 
			cursor = conn.execute(sql)
			count = cursor.fetchone()
			status = status + 'Deleted ' + str(count[0]) + ' rows.'
		except sqlite3.Error as e:
		  	status = 'Error in filter_rgpocode changes() ' + str(e)
		
	cleanup()
	return(status)


def get_location(userinput):
	global conn
	locationlist=[]
	gpolocation = []
		
	sql = """SELECT
	rowid,
	gpo_countrycode,
	gpo_placename,
	gpo_admin1,
	gpo_admin2,
	gpo_admin3
	FROM gpotable 
	WHERE gpo_postalcode = '""" + str(userinput) + "';"

	try: 
		cursor = conn.execute(sql)
		rows = cursor.fetchall()
	except sqlite3.Error as e:
	  	status = 'Error in reverse postalcode: ' + str(e)
	  	return(status)
	
	for row in rows:
		gpolocation.append(dict(place_name=row[2],
								admin1=row[3],
								admin2=row[4],
								admin3=row[5],
								country_code=row[1]
	            				)
							)
	return(gpolocation)
	

def start_rgpocode(userinput):
	LOCATIONDICT = sys._getframe(1).f_globals
	LOCATION = user_cwd(LOCATIONDICT)

	if platform == "win32":
		LOCATION = LOCATION + '\\'
		LOCATION = LOCATION.replace('\\', '\\\\')
	
	status=do_check()
		
	if 'Start reverse postalcode' in status:
		if 'Error in reverse postalcode: ' in status:
			return(status)
		else:
			locationlist=get_location(userinput)
			
			cleanup()
			return(locationlist)
	else:
		cleanup()
		return(status)
	

if __name__ == '__main__':
	location = start_rgpocode('N5V')
	print(location)
