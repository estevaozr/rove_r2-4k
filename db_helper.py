import sqlite3

class DbHelper:
	def __init__(self, db_name="dashcam.db"):
		self.conn = sqlite3.connect(db_name)
		self.curs = self.conn.cursor()

		# Force foreign key support
		self.curs.execute("PRAGMA foreign_keys = ON")
		self.conn.commit()

		# Create tables
		self.create_tables()

	def __del__(self):
		# Commit any pending changes and close DB
		self.conn.commit()
		self.conn.close()

	def __execute_sql(self, sql, args=None, commit=True):
		res = None

		if args:
			res = self.curs.execute(sql, args)
		else:
			res = self.curs.execute(sql)

		if commit:
			self.conn.commit()

		return res.fetchall()

	def __execute_many_sql(self, sql, args_list, commit=True):
		if not args_list:
			raise Exception("Need to pass args_list")

		if (not isinstance(args_list, list)) and (not isinstance(args_list[0], tuple)):
			raise Exception("Need to pass an args_list of list of tuples")

		self.curs.executemany(sql, args_list)

		if commit:
			self.conn.commit()

	def create_tables(self):
		## Table definitions

		# --- FilesInfo table creation -----------------------------------------
		files_info_table = \
		"""
		CREATE TABLE IF NOT EXISTS "FilesInfo" (
			"Id"	INTEGER NOT NULL,
			"FileName"	TEXT NOT NULL UNIQUE,
			"ProcessedOn"	REAL NOT NULL, -- Unix Time
			"CompressedDataPoints"	BLOB NOT NULL,
			PRIMARY KEY("Id")
		);
		"""

		data_points_table = \
		"""
		CREATE TABLE IF NOT EXISTS "DataPoints" (
			"Time"	REAL NOT NULL, -- Unix Time
			"LicensePlate"	TEXT,
			"Latitude"	REAL,
			"Longitude"	REAL,
			"Speed"	INTEGER NOT NULL,
			"Accel1"	REAL NOT NULL,
			"Accel2"	REAL NOT NULL,
			"Accel3"	BLOB NOT NULL,
			"FilesInfoId"	INTEGER NOT NULL,
			FOREIGN KEY("FilesInfoId") REFERENCES "FilesInfo"("Id")
		);
		"""

		# ----------------------------------------------------------------------

		# Create all tables, commit only on last call
		self.__execute_sql(files_info_table, commit=False)
		self.__execute_sql(data_points_table, commit=False)
		self.__execute_sql("", commit=True)

	# --- FilesInfo Table Operations -------------------------------------------
	def add_files_info(self, filename, now, compressed_data_points):
		"""
		Adds a FilesInfo entry.
		Returns True if entry was added
		Returns False if the filename already was processed before
		"""

		sql = \
		"""
		INSERT OR FAIL INTO FilesInfo
		VALUES
		(NULL, ?, ?, ?)
		"""

		try:
			self.__execute_sql(sql, (filename, now, compressed_data_points))
		except sqlite3.IntegrityError:
			# Filename is not unique, which we are going to assume that the
			# file was processed before
			return False
		except Exception as e:
			# Some other unexpected exception
			print("exception type: {}".format(type(e)))
			print(str(e))
			return False

		return True

	def get_files_info_by_id(self, fid):
		"""
		Return everything from FilesInfo for a specific Id
		"""

		sql = \
		"""
		SELECT * FROM FilesInfo WHERE Id = ?
		"""

		res = self.__execute_sql(sql, (fid,))

		if len(res) > 0:
			return res[0]

		return None

	def get_files_info_by_filename(self, filename):
		"""
		Return everything from FilesInfo for a filename
		Note: Adding % will allow matching more than one FilesInfo
		"""

		sql = \
		"""
		SELECT * FROM FilesInfo WHERE FileName LIKE ?
		"""

		return self.__execute_sql(sql, (filename,))

	# --- DataPoints Table Operations ------------------------------------------
	def add_data_points(self, points):
		"""
		Store several data points at the same time.
		'poits' is a list of tuples to be added
		"""

		sql = \
		"""
		INSERT INTO DataPoints
		VALUES
		(?, ?, ?, ?, ?, ?, ?, ?, ?)
		"""

		self.__execute_many_sql(sql, points)

