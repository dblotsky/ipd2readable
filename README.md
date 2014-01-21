ipd2readable
============

A set of Python tools to make BlackBerry's very monolithic IPD backups more easily machine-readable. The IPD file format description can be found in [this document][ipd] in page 19.

# shatter.py

Translates an IPD file into a JSON file. The JSON file contains a list of named lists of records (the databases from the IPD file). The records are just numbered dictionaries mapping record field numbers to record field values.

Usage:

    shatter.py Databases.ipd > Databases.json

[ipd]: http://us.blackberry.com/devjournals/resources/journals/jan_2006/BlackBerryDeveloperJournal-0301.pdf
