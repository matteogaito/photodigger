#!/usr/bin/env python3

import argparse
import pathlib
from re import I
import exiftool
import logging
import shutil

logging.basicConfig(level=logging.INFO)

raws = [ '.RAF','.CR2','.NRW','.ERF','.RW2','.NEF','.ARW','.RWZ','.EIP','.DNG','.BAY','.DCR','.RAW','.CRW','.3FR','.K25','.KC2','.MEF','.DNG','.CS1','.ORF','.ARI','.SR2','.MOS','.CR3','.GPR','.SRW','.MFW','.SRF','.FFF','.KDC','.MRW','.J6I','.RWL','.X3F','.PEF','.IIQ','.CXI','.NKSC','.MDC', '.DNG' ]
archives = [ '.XMP', '.JPG' ]

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

args = parser.parse_args()

print(args)

try:
   args.destdir. mkdir(parents=True, exist_ok=True)
except:
    logging.error("Failed to create dir")
    raise

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
                exifs = et.get_metadata(f)
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
