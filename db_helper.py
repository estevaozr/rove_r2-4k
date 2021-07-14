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

		# ----------------------------------------------------------------------

		# Create all tables, commit only on last call
		self.__execute_sql(files_info_table, commit=False)
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

