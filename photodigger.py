#!/usr/bin/env python3

import argparse
import pathlib
from re import I
import exiftool
import logging
import shutil
from datetime import datetime, timedelta
import zlib

logging.basicConfig(level=logging.INFO)

def calculate_crc32(filename):
    with open(filename, 'rb') as f:
        content = f.read()
        crc32_value = zlib.crc32(content)
        return crc32_value & 0xFFFFFFFF  # Mask to get a 32-bit value

raws = [ '.RAF','.CR2','.NRW','.ERF','.RW2','.NEF','.ARW','.RWZ','.EIP','.DNG','.BAY','.DCR','.RAW','.CRW','.3FR','.K25','.KC2','.MEF','.DNG','.CS1','.ORF','.ARI','.SR2','.MOS','.CR3','.GPR','.SRW','.MFW','.SRF','.FFF','.KDC','.MRW','.J6I','.RWL','.X3F','.PEF','.IIQ','.CXI','.NKSC','.MDC', '.DNG' ]
archives = [ '.XMP', '.JPG' ]
videos = [ '.MP4', '.MOV' ]

description = (
    'Command line interface for manage better your raw and your jpg'
)

parser = argparse.ArgumentParser(description=description)
parser.add_argument( '--debug', action='store_true', help='Print debug info')
subparsers = parser.add_subparsers(dest='command')

copy_cmd = subparsers.add_parser('copy', help='Copy to Local')
copy_cmd.add_argument( '--sourcedir', help='Set the dir to read', required=True, type=pathlib.Path)
copy_cmd.add_argument( '--destdir', help='Set the destination dir of files', required=True, type=pathlib.Path)

archive_cmd = subparsers.add_parser('archive', help='archive jpg or raws')
archive_cmd.add_argument( '--sourcedir', help='Set the dir to read', required=True, type=pathlib.Path)
archive_cmd.add_argument( '--destdir', help='Set the destination dir of files', required=True, type=pathlib.Path)
archive_cmd.add_argument('--date-structure', dest="datestructure", action='store_true', help="store file into YY/mm/dd/ structure")

fixexifdata_cmd = subparsers.add_parser('fixexifdate', help="fix the exif date")
fixexifdata_cmd.add_argument( '--sourcedir', help='Set the dir to read', required=True, type=pathlib.Path)
fixexifdata_cmd.add_argument( '--regexpfile', help='Set regexp file', required=True)
fixexifdata_cmd.add_argument('--seconds', help='seconds to fix', required=True, type=int)
fixexifdata_cmd.add_argument('--action', help='add or remove seconds', default="add")


args = parser.parse_args()

if args.command is None:
    parser.print_help()
    exit()

try:
   args.destdir.mkdir(parents=True, exist_ok=True)
except:
    logging.error("Failed to create dir")

if args.command == "copy":
    try:
       args.destdir. mkdir(parents=True, exist_ok=True)
    except:
        logging.error("Failed to create dir")
        raise

    for f in args.sourcedir.rglob('*'):
        file_ext = (f.suffix).upper()
        if file_ext in raws:
            file_identifier = (f.stem).replace("_","")
            with exiftool.ExifToolHelper() as et:
                try:
                    exifs = et.get_metadata(f)
                except:
                    logging.info("Failed to get exif of {}".format(f))
                    continue
                try:
                    createdate=int(exifs[0]['EXIF:DateTimeOriginal'].replace(":","").replace(" ", ""))
                except:
                    logging.error("Create date is missing for {}".format(f))
                    raise

            newfilename = "{}_{}{}".format(createdate, file_identifier, file_ext)
            destination_file = args.destdir / newfilename

            logging.debug("file: {}, ext: {}, createdate: {}, file_identifier: {}".format(f, file_ext, createdate, file_identifier))
            logging.debug("destination file: {}".format(destination_file))

            try:
                shutil.copy(f, destination_file)
                f.rename(f.with_suffix('.copied'))
                logging.info("File {} copied to {}".format(f, destination_file))
            except Exception as e:
                logging.error("Error copying {}: {}".format(f, e))

    for v in args.sourcedir.rglob('*'):
        file_ext = (v.suffix).upper()
        if file_ext in videos:
            try:
                shutil.copy(v, args.destdir )
                v.rename(v.with_suffix('.copied'))
                logging.info("File {} copied to {}".format(v, args.destdir ))
            except Exception as e:
                logging.error("Error copying {}: {}".format(v,e))

if args.command == "archive":
    files = args.sourcedir.rglob('*')
    for f in files:
        file_ext = (f.suffix).upper()
        file_name = f.stem
        if file_ext in archives:
            linked_files = []
            for fi in files:
                if fi.stem == file_name:
                    linked_files.append(fi)
            print(f)
            print(linked_files)
            print("------------")

if args.command == "fixexifdate":
    files = args.sourcedir.rglob("{}".format(args.regexpfile))
    for f in files:
        print("File: {}".format(f))
        file_ext = (f.suffix).upper()
        if file_ext in raws:
            with exiftool.ExifToolHelper() as et:
                try:
                    exifs = et.get_metadata(f)
                except:
                    logging.info("Failed to get exif of {}".format(f))
                    continue

                try:
                    createdate_as_string=exifs[0]['EXIF:DateTimeOriginal']
                    exif_datetime_format = "%Y:%m:%d %H:%M:%S"
                    createdate = datetime.strptime(createdate_as_string, exif_datetime_format)
                except:
                    logging.error("Create date is missing for {}".format(f))
                    raise

                print("Old createdate: {}".format(createdate_as_string))


                try:
                    logging.info("create backup file")
                    backupdir = "backup"
                    new_backupdir = args.sourcedir / backupdir
                    new_backupdir.mkdir(parents=True, exist_ok=True)

                    shutil.copy(f, new_backupdir)
                except Exception as e:
                    logging.error("Error: {}".format(e))
                    raise


                # calculate new date
                try:
                    new_datetime_obj = createdate + timedelta(seconds=args.seconds)
                    new_exif_datetime = new_datetime_obj.strftime(exif_datetime_format)
                    et.set_tags(f, tags={"EXIF:DateTimeOriginal": new_exif_datetime}, params=["-P", "-overwrite_original"])
                    logging.info("EXIF DateTimeOriginal modified successfully.")
                except KeyError:
                    logging.error("EXIF:DateTimeOriginal not found in metadata for {}".format(f))
                    raise
                except:
                    logging.error("Failed to modify EXIF DateTimeOriginal for {}".format(f))
                    raise

                try:
                    file_identifier = calculate_crc32(f)
                    newfilename = f.parent / "{}_{}{}".format(new_exif_datetime.replace(":","").replace(" ", ""),file_identifier, file_ext)

                    f.rename(newfilename)
                    logging.info("File {} copied to {}".format(f, newfilename))
                except Exception as e:
                    logging.error("Error copying {}: {}".format(f, e))
                    raise
