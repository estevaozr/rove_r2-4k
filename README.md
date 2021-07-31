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
These are the quirks that were noticed while writing this script.

## DataPoints Time and GPS clock desync
The camera sincronizes its time with the GPS system. If the camera spends time without receiving GPS data (like over a weekend) its clock will diverge from the GPS system time.

Because of this when the dashcam gets a GPS fix and update its clock the time being stamped in the video and on the metadata will change to match the GPS time. This means that the DataPoints.Time **can** shift forwards and/or backwards depending on how much the camera's clock drifted.

## MP4 Atom structure inconsistency when using 32GB+ cards with exFAT
It was noticed that when using an SDCard formatted with *exFAT* some of the MP4 container *atoms* would have inconsistent sizes of 1 byte.

Files that are affected by this issue will cause the script to print a message like `--> Atom size is too small for a correctly formed file!`. This will cause the script to have to search on all of the file for the *moov* atom instead of traversing the MP4 atom structure, which will take longer and cause more IO on the SD card.

That said it will find all *moov* strings on the file and try to parse it to find the metadata location, so it will be able to get it but it will take longer and use more CPU to be able to do so.

Since the [SDCard Association](https://www.sdcard.org/developers/sd-standard-overview/capacity-sd-sdhc-sdxc-sduc/) recommends that any card with more than 32GB to be formatted with exFAT this is expected to happen with any card that is larger than 32GB.

The Rove R2-4k camera correctly formats 32GB+ cards as *exFAT* as recommended, but to avoid this issue one can use external tools to format the card in *FAT32* which [can support cards up to 2TB](https://en.wikipedia.org/wiki/File_Allocation_Table#Maximal_sizes). One just have to re-create the folder structure and files that the camera normally creates when it formats the card natively in order to make it not try to re-format the card after that.

Final note: The creator of the repository is using a 64GB Samsung card formated with FAT32, recording video files at the 4k@24fps and 3 minutes duration with no issues as of now. The *atom size* issue is not happening with this setup.

# Acknowledgments
* I'd like to thank **Sergei's Stuff and Things** blog write-up, which helped me to understand how to parse the MP4 container. The origianal page that was references follows:
  * https://sergei.nz/extracting-gps-data-from-viofo-a119-and-other-novatek-powered-cameras/
