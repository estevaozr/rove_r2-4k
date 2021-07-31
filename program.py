#!/bin/env python3

import os
import sys
import mmap
import time
import struct

from db_helper import DbHelper
from data_point import DataPoint

def get_atom_info(data):
	try:
		atom_size, atom_type = struct.unpack(">I4s", data)
	except struct.error:
		return -1, "(Unpack Error)"
	except Exception as e:
		print("Error!")
		print(data)
		print(str(e))

	try:
		a_t = atom_type.decode()
	except UnicodeDecodeError:
		a_t = "UNKNOWN"
	except Exception as e:
		print("Error2!")
		print(atom_type)
		print(str(e))
		a_t = "UNKNOWN2"

	return int(atom_size), a_t

def get_gps_atom_info(data):
	atom_pos, atom_len = struct.unpack(">II", data)
	return int(atom_pos), int(atom_len)

def process_gps_atom(atom_pos, fh):
	# Seek the file to this Chunk position
	fh.seek(atom_pos, 0)

	atom_size, atom_type = get_atom_info(fh.read(8))

	if atom_type != "free":
		print("\t\tWill not parse atom at {}, since its type is not \"free\" (actual: {})".format(atom_pos, atom_type))
		return None

	offset = atom_pos + 8
	fh.seek(offset, 0)

	## Process GPS information!
	# Check if the chunk has the expected "GPS " text
	magic = fh.read(4).decode()
	offset += 4
	fh.seek(offset)

	if magic != "GPS ":
		print("\t\tWill not parse atom at {}, since its data does not start with \"GPS \" (actual: {})".format(atom_pos, magic))
		return None

	# Read data size
	data_size, = struct.unpack("<I", fh.read(4))
	offset += 4
	fh.seek(offset)

	print("\t\tData size: {}".format(data_size))

	# Read actual data
	data = fh.read(data_size)

	# XOR with 'AA'
	data_dec = bytearray()

	for b in data:
		data_dec.append(b ^ 170) # 0xAA = 170

	# Now we have plaintext data with the GPS and Accelerometer data
	dp = DataPoint(data_dec)

	return dp

def parse_moov_atom(fh, offset):
	print("--> moov atom found! (offset: {})".format(offset))

	gps_data_found = False
	gps_data = list()

	# Reread the moov atom information
	fh.seek(offset, 0)
	atom_size, atom_type = get_atom_info(fh.read(8))

	# Process the atoms inside the moov atom
	sub_offset = offset + 8

	while sub_offset < (offset + atom_size):
		sub_atom_size, sub_atom_type = get_atom_info(fh.read(8))

		if sub_atom_type == "gps ":
			gps_data_found = True
			print("--> GPS chunk descriptor atom found! (offset: {})".format(sub_offset))
			print("\tGPS chunk atom size: {}".format(sub_atom_size))

			gps_offset = 16 + sub_offset # Skipping some headers...?
			fh.seek(gps_offset, 0)

			while gps_offset < (sub_offset + sub_atom_size):
				gps_atom_pos, gps_atom_size = get_gps_atom_info(fh.read(8))
				print("\tGPS atom pos: {} - GPS atom size: {}".format(gps_atom_pos, gps_atom_size))

				gps_atom_data = process_gps_atom(gps_atom_pos, fh)
				if gps_atom_data:
					gps_data.append(gps_atom_data)

				# Continue processing GPS atom
				gps_offset += 8
				fh.seek(gps_offset, 0)

		# Continue processing subatom
		sub_offset += sub_atom_size
		fh.seek(sub_offset, 0)

	# Return data that was found
	return gps_data_found, gps_data

def try_finding_moov_atom(fh):
	print("----> Will try searching the \"moov\" atom through the file...")

	offset = 0
	fh.seek(offset, 0)

	m = mmap.mmap(fh.fileno(), 0, prot=mmap.PROT_READ)

	moov_candidates = list()

	while offset >= 0:
		offset = m.find("moov".encode(), offset)

		if offset > 0:
			if offset > 0:
				print("----> found a \"moov\" string in offset {} on the file. Will try parsing it...".format(offset))
				moov_candidates.append(offset - 4)
				offset += 4
			else:
				print("----> could not find any other \"moov\" string on the file")

	return moov_candidates

def parse_mov(fh):
	# Returns if file is a MOV+GPS, and GPS data objects if found
	is_valid = False
	gps_data = None

	offset = 0

	while True:
		# Get atom information
		atom_size, atom_type = get_atom_info(fh.read(8))

		if atom_size < 8 and atom_size >= 0:
			print("--> Atom size is too small for a correctly formed file! (atom: \"{}\" - size: {})".format(atom_type, atom_size))
			candidates = try_finding_moov_atom(fh)

			if len(candidates) == 0:
				break

			# We will try searching GPS data in each of these moov candidates
			for cand in candidates:
				print("----> Trying moov candidate on offset {}...".format(cand))

				is_valid, gps_data = parse_moov_atom(fh, cand)

				if is_valid and len(gps_data) > 0:
					print("----> Found something. Will assume that this is the correct moov atom")
					return is_valid, gps_data

			# We could not find the correct moov atom. Abort
			return False, None

		if atom_size < 0:
			print("--> End of File")
			break

		# Check if Atom is moov
		if atom_type == "moov":
			is_valid, gps_data = parse_moov_atom(fh, offset)
			break

		# Continue processing file
		offset += atom_size
		fh.seek(offset, 0)

	return is_valid, gps_data

def process_file(arg):
	filename = os.path.basename(arg)

	files_info = db.get_files_info_by_filename(filename)

	if files_info and len(files_info) > 0:
		print("--> File \"{}\" already exists on the DB, will not process it again".format(filename))
		print()
		return

	print("--> Processing \"{}\" file...".format(os.path.basename(filename)))

	with open(arg, "rb") as fh:
		is_valid, gps_data = parse_mov(fh)

	print("is_valid: {}".format(is_valid))

	if is_valid:
		print("gps data len: {}".format(len(gps_data)))

		# Try to store file info
		if db.add_files_info(filename, time.time(), DataPoint.compress_data_points(gps_data)):
			print("--> Saved information for file \"{}\"".format(filename))

			# Get FilesInfo.Id to store data for this file
			fid = db.get_files_info_by_filename(filename)[0][0]

			# Prepare data_point_list
			db_data_points = list()
			for dp in gps_data:
				db_data_points.append(dp.get_db_tuple(fid))

			# Store data points
			db.add_data_points(db_data_points)

		else:
			print("--> File \"{}\" already was saved before, didn't update it".format(filename))

	print()

if __name__ == "__main__":
	global db
	db = DbHelper()

	if len(sys.argv) < 2:
		print("Please call the script like follows:")
		print("\t{} (dash cam file) [other dash cam files]".format(sys.argv[0]))
		sys.exit(-1)

	for arg in sys.argv[1:]:
		process_file(arg)

