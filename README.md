# Rove R2-4k Dashcam metadata extractor
This is a Python3 script that can extract the metadata (Date/Time, License Plate, Speed, GPS and Accelerometer) data from the video files that the [Rove R2-4k](https://www.rovedashcam.com/products/rove-r2-4k-car-dashcam) dashcamera.

It has been tested with the current latest [firmware](https://www.rovedashcam.com/pages/update-firmware-rove-r2-4k-dash-cam) of the camera: `ROVE R2-4K 07-07-2020 V3`

## How to use the script
To get information on how to execute the script one can execute the script with no arguments

```
$ python3 program.py 
Please call the script like follows:
	program.py (dash cam file) [other dash cam files]
```

And to actually extract data from the video files one just has to pass the path of the video files that will be processed:

```
$ python3 program.py /path/to/the/sd/card/ROVE\ R2-4K/Novatek/Movie/*
```

The script will then iterate on all files and extract the metadata, and store it on a [SQLite3](https://www.sqlite.org/index.html) database. By executing the program (even without any video file) will create the *dashcam.db* database file.

## SQLite3 database schema
The following is the schema of the SQLite database:

```
$ sqlite3 dashcam.db 
sqlite> .schema
CREATE TABLE IF NOT EXISTS "FilesInfo" (
    "Id"	INTEGER NOT NULL,
    "FileName"	TEXT NOT NULL UNIQUE,
    "ProcessedOn"	REAL NOT NULL, -- Unix Time
    "CompressedDataPoints"	BLOB NOT NULL,
    PRIMARY KEY("Id")
);
CREATE TABLE IF NOT EXISTS "DataPoints" (
    "Time"	INTEGER NOT NULL,
    "LicensePlate"	TEXT,
    "Latitude"	REAL,
    "Longitude"	REAL,
    "Speed"	INTEGER,
    "Accel1"	REAL NOT NULL,
    "Accel2"	REAL NOT NULL,
    "Accel3"	REAL NOT NULL,
    "FilesInfoId"	INTEGER NOT NULL,
FOREIGN KEY("FilesInfoId") REFERENCES "FilesInfo"("Id")
);
```

## Notes on the Database Schema and collected data
The SQLite database only has 2 tables; the following is more details on what each field has/is

* FilesInfo table
  * Id - An unique number for each file that has been processed
  * FileName - The original file name for some file that has been processed
  * ProcessedOn - The Unix Timestamp that this file has been processed on
  * CompressedDataPoints - The original *unscrambled raw data* that has been used to create the information on the **DataPoints** table.

* DataPoints table
  * Time - An Unix timestamp for the time that is stamped on the video stream for this sample
    * See quirks for some details about this
  * LicensePlate - The License Plate that is stamped on the video stream for this sample.
    * *NULL* will be stored if there is no license plate information
  * Latitude - GPS Latitude that is stamped on the video stream for this sample.
    * GPS data only available if stamped on the video
    * This data is stored as Degrees and can be positive or negative ranging from -90 to +90
  * Longitude - GPS Longitude that is stamped on the video stream for this sample.
    * GPS data only available if stamped on the video
    * This data is stored as Degrees and can be positive or negative ranging from -180 to +180
  * Speed - GPS Speed that is stamped on the video stream for this sample.
    * It is only available if the speed is being stamped on the video
    * It will match the camera's settings for either *km/h* or *mph*
    * Speed value is only "stable" if there is a GPS fix. All samples that the GPS fix is not available will set the Speed to NULL
  * Accel1/Accel2/Accel3 - Store Acceleration data from the 3 axis that the camera measures, in *G*
    * Notes on each acceleration will asume that the acceleration that is being mesured is *gravity* only!
    * Accel1 - Acceleration on the SDCard/MiniUSB-connector axis. It is positive when the SDCard is pointing to the floor / MiniUSB is pointing to the ceiling
    * Accel2 - Acceleration on the TV-Out/MIC axis (I'd say it is the "expected" orientation of the camera). It is positive when the MIC is pointing to the floor / TV-Out is poiting to the ceiling
    * Accel3 - Acceleration on the Camera-Lens/Camera-Screen axis. It is positive when the Camera-Screen is pointing to the floor / Camera-Lens is pointing to the ceiling.
  * FilesInfoId - Foreign key that points to which file this DataPoint belongs to

### Some examples for data that is stored on the DataPoints table:
* Latitude/Longitude: [38.897440, -77.036559](https://www.google.com/maps/place/38%C2%B053'50.8%22N+77%C2%B002'11.6%22W/@38.8974442,-77.0387477,17z/data=!3m1!4b1!4m5!3m4!1s0x0:0x0!8m2!3d38.89744!4d-77.036559)
  * This is a point in the front of the U.S.A. White House

# Quirks
These are the quirks that were noticed while writing this program

TODO: Writem them

# Acknowledgments
* I'd like to thank **Sergei's Stuff and Things** blog write-up, which helped me to understand how to parse the MP4 container. The origianal page that was references follows:
  * https://sergei.nz/extracting-gps-data-from-viofo-a119-and-other-novatek-powered-cameras/
