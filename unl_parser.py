# unl_parser.py

import csv, io, sys, argparse, pathlib

# -- args demo ---------------------------------------------------------------
p = argparse.ArgumentParser()
p.add_argument('--givenFile', required=True)
p.add_argument('--outputFile', required=True)
p.add_argument('--d', default='|', help='UNLOAD delimiter (default: |)')
args = p.parse_args()
# ---------------------------------------------------------------------------

column_names = [
    # ... put your header list here ...
]

# open raw, then decode + newline-normalise with TextIOWrapper
with open(args.givenFile, 'rb') as fh_raw, \
     io.TextIOWrapper(fh_raw, encoding='utf-8', newline='') as unl_in, \
     open(args.outputFile, 'w', newline='', encoding='utf-8') as csv_out:

    # reader that understands Informix’s escape rules
    rdr = csv.reader(
        unl_in,
        delimiter=args.d,
        escapechar='\\',
        quoting=csv.QUOTE_NONE  # UNLOAD never double-quotes
    )

    # writer for standard CSV
    wtr = csv.writer(csv_out, delimiter=',', quoting=csv.QUOTE_ALL)
    wtr.writerow(column_names)          # header

    for row in rdr:
        # row is already a list of strings, properly un-escaped
        # If you want to turn empty strings into None, do it here:
        # row = [f if f != '' else None for f in row]
        wtr.writerow(row)