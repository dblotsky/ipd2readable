#!/usr/bin/python

"""
Splits an IPD binary archive file into a more manageable JSON list of databases and records.
"""

import re
import json
import sys
import os
import argparse

HEADER = "Inter@ctive Pager Backup/Restore File"

class NoMoreBytes(Exception):
    def __str__(self):
        return "no more bytes"

# decorator to wrap TypeErrors into NoMoreBytes errors
# used on byte-reading functions to avoid too many 'if's
def safe_reader(f):
    def wrapped(*args,  **kwargs):
        try:
            return f(*args, **kwargs)
        except TypeError as e:
            raise NoMoreBytes()
    return wrapped

@safe_reader
def read_short_le(f):
    return ord(f.read(1)) + (ord(f.read(1)) << 8)

@safe_reader
def read_short(f):
    return (ord(f.read(1)) << 8) + ord(f.read(1)) << 0

@safe_reader
def read_int_le(f):
    return ord(f.read(1)) + (ord(f.read(1)) << 8) + (ord(f.read(1)) << 16) + (ord(f.read(1)) << 24)

@safe_reader
def read_int(f):
    return (ord(f.read(1)) << 24) + (ord(f.read(1)) << 16) + (ord(f.read(1)) << 8) + ord(f.read(1))

@safe_reader
def read_byte(f):
    return ord(f.read(1))

class Database(object):

    def __init__(self, name):
        self.name    = name.rstrip("\x00")
        self.records = []

    def as_dict(self):
        return {
            "name":    self.name,
            "records": [record.as_dict() for record in self.records]
        }

    def __cmp__(self, other):
        return cmp(self.name, other.name)

    def __str__(self):
        return "<Database {name!r} with {n} records>".format(name=self.name, n=len(self.records))

class Record(object):

    def __init__(self, handle, uid):
        self.handle = handle
        self.uid    = uid
        self.fields = {}

    def as_dict(self):
        self_dict = {"uid": self.uid}
        self_dict.update(self.fields)
        return self_dict

    def __str__(self):
        return "<Record {uid} {f}>".format(uid=self.uid, f=self.fields)

def error(m):
    sys.stderr.write(str(m) + "\n")
    exit(1)

def main():

    # build command-line argument parser
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "in_file",
        help = "input IPD file"
    )

    # parse the args
    args = parser.parse_args()

    # check that input file exists
    if not os.path.exists(args.in_file):
        error("input file does not exist")

    databases = []

    # read the file
    with open(args.in_file, "rb") as f:

        # mandatory file header
        header = f.read(len(HEADER))
        assert header == HEADER, "Missing IPD file header"

        # mandatory byte (carriage return)
        assert f.read(1) == "\x0A", "Missing mandatory carriage return"

        # get version and number of databases
        version = ord(f.read(1))
        num_databases = read_short(f)

        # mandatory byte (null)
        assert f.read(1) == "\x00", "Missing mandatory null byte"

        # read names and create databases
        for i in range(num_databases):

            name_length = read_short_le(f)
            name        = f.read(name_length)

            db = Database(name)
            databases.append(db)

        # catch for the NoMoreBytes exception
        try:

            # read until reading fails
            while True:

                # read the record header
                record_db_id      = read_short_le(f)
                record_length     = read_int_le(f)
                record_db_version = read_byte(f)
                record_handle     = read_short_le(f)
                record_unique_id  = read_int(f)

                # add the record to the db
                record = Record(record_handle, record_unique_id)
                db     = databases[record_db_id]
                db.records.append(record)

                # read the rest of the record
                already_read = 7
                while already_read < record_length:

                    # read field
                    field_length = read_short_le(f)
                    field_type   = read_byte(f)
                    field_data   = f.read(field_length)

                    # set field on record
                    # NOTE: the fields may still be ugly binary, so we wrap them in repr()
                    record.fields[field_type] = repr(field_data)

                    already_read += field_length + 3

        except NoMoreBytes as e:
            pass

    print json.dumps([database.as_dict() for database in databases])

if __name__ == '__main__':
    main()
