import gzip
import time
import struct
import datetime

class DataPoint:
	def __init__(self, data = None):
		# Fields
		self.date_str = None
		self.time_str = None
		self.unix_time = None

		self.license_plate = None

		self.latitude_str = None
		self.longitude_str = None

		self.latitude = None
		self.longitude = None

		self.speed_str = None
		self.speed = None

		self.accel1_str = None
		self.accel2_str = None
		self.accel3_str = None
		self.accel1 = None
		self.accel2 = None
		self.accel3 = None

		self.__raw_data = data

		# Pare data to setup fields
		self.parse_data()

	def parse_data(self):
		# Do some basic validation of the data
		if len(self.__raw_data) != 261:
			# The data format might not be what we expect... bail out
			return

		## Parse data as we understand it now
		# Date
		self.date_str = self.__raw_data[10:18].decode()

		# Time (Expect it to be in 24 hour format)
		self.time_str = self.__raw_data[18:24].decode()

		# Time as unix time (using system's timezone)
		self.unix_time = time.mktime(datetime.datetime.strptime(self.__raw_data[10:24].decode(), "%Y%m%d%H%M%S").timetuple())

		## License Plate
		self.license_plate = self.__raw_data[25:34].decode().strip()
		if not self.license_plate:
			self.license_plate = None

		## Latitude
		self.latitude_str = self.__raw_data[40:49].decode()

		lat = float(self.latitude_str[-6:]) / 10000
		lat /= 60

		lat += float(self.latitude_str[1:3])

		if self.latitude_str[0] == 'N':
			self.latitude = +lat
		elif self.latitude_str[0] == 'S':
			self.latitude = -lat
		else:
			self.latitude = None

		## Longitude
		self.longitude_str = self.__raw_data[49:59].decode()

		lon = float(self.longitude_str[-6:]) / 10000
		lon /= 60

		lon += float(self.longitude_str[1:4])

		if self.longitude_str[0] == 'E':
			self.longitude = +lon
		elif self.longitude_str[0] == 'W':
			self.longitude = -lon
		else:
			self.longitude = None

		## Speed
		self.speed_str = self.__raw_data[59:67].decode()
		self.speed = int(self.speed_str)

		## Acelerometers
		self.accel1_str = self.__raw_data[175:179].decode()
		self.accel1 = float(self.accel1_str) / 10
		self.accel2_str = self.__raw_data[179:183].decode()
		self.accel2 = float(self.accel2_str) / 10
		self.accel3_str = self.__raw_data[183:187].decode()
		self.accel3 = float(self.accel3_str) / 10

	def __str__(self):
		return str(self.__dict__)

