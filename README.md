# unl_to_csv

`unl_to_csv` is a summer project for converting Informix `.unl` unload files into standard `.csv` files. The work began as a local parser experiment and progressed into an AWS-oriented pipeline for moving unload data through S3, Lambda, and multipart CSV output.

This repository reflects work done while developing a UNL-to-CSV pipeline based on experience with the Skechers Database Engineering/AI Team.

## What This Project Does

- Reads Informix UNLOAD-style `.unl` files.
- Uses the pipe character (`|`) as the default UNL delimiter.
- Handles escaped delimiters with Python's `csv.reader`.
- Opens UNL input in binary mode before decoding text.
- Uses `latin-1` decoding with `surrogateescape` to preserve difficult source bytes.
- Writes standards-friendly CSV output with comma delimiters and quoted fields.
- Adds AWS Lambda and S3 examples for a scalable conversion workflow.
- Explores multipart upload flushing for large CSV outputs.

## Project Files

| File | Purpose |
| --- | --- |
| `unl_parser.py` | Local command-line parser prototype for converting a `.unl` file into `.csv`. |
| `scaleableConverter.py` | AWS Lambda-style converter that downloads a UNL file and column list from S3, writes a CSV to `/tmp`, and uploads the result back to S3. |
| `scaleableConventerBatchFlushStreaming.py` | Multipart upload prototype for flushing CSV output to S3 in parts instead of keeping one full output file in local storage. |
| `exampleInput.json` | Example Lambda event payload showing bucket, input key, output key, delimiter, and encoding settings. |
| `LICENSE` | MIT license for this repository. |

## Current Pipeline Shape

The current work can be understood in three stages:

1. Local conversion research in `unl_parser.py`
   - Accepts input and output file paths.
   - Reads the UNL file as raw bytes.
   - Decodes through `TextIOWrapper`.
   - Uses `csv.reader` with `delimiter="|"`, `escapechar="\\"`, and `quoting=csv.QUOTE_NONE`.
   - Writes CSV output with quoted comma-separated fields.

2. AWS Lambda conversion in `scaleableConverter.py`
   - Receives bucket and object keys from an event payload.
   - Downloads the UNL file and a column-name file from S3.
   - Converts the UNL file to CSV in Lambda's `/tmp` storage.
   - Uploads the finished CSV back to S3.
   - Returns status, row count, and output S3 URI.

3. Large-output streaming direction in `scaleableConventerBatchFlushStreaming.py`
   - Demonstrates using `create_multipart_upload`.
   - Buffers CSV rows in memory.
   - Flushes parts once the buffer reaches the configured part size.
   - Completes the multipart upload after the final flush.

## Example Local Usage

`unl_parser.py` expects a source `.unl` file, an output `.csv` path, and optionally a delimiter:

```bash
python unl_parser.py --givenFile test.unl --outputFile output.csv --d "|"
```

Before using it with real data, fill in `column_names` inside `unl_parser.py` so the output CSV has the expected header row.

## Example Lambda Event

`exampleInput.json` shows the expected event shape for the AWS-oriented converter:

```json
{
  "bucket": "my-raw-data",
  "unl_key": "unloads/2025-07/inv.unl",
  "columns_key": "schema/inv_columns.txt",
  "output_key": "csv/2025-07/inv.csv",
  "delimiter": "|",
  "encoding": "latin-1"
}
```

The `columns_key` file should contain one column name per line. Those names are written as the first row of the output CSV.

## Design Notes

- Informix UNL files are not standard CSV files, so the parser uses `quoting=csv.QUOTE_NONE` and an explicit escape character.
- Binary input plus `TextIOWrapper` gives better control over encoding and newline behavior than opening the file directly in text mode.
- `latin-1` decoding is useful for legacy data because every byte can be mapped to a character.
- `surrogateescape` keeps problematic bytes round-trippable instead of failing the conversion.
- The Lambda version currently writes the converted CSV to `/tmp`; the multipart streaming prototype points toward handling larger data sets without depending on one full local output file.

## Attribution

The first parser iteration was based on Maury Quijada's original UNL parser:

[mauryquijada/unl_parser](https://github.com/mauryquijada/unl_parser)

Credit to Maury Quijada for the initial UNL parsing approach that this project adapted and extended.

## License

This project is licensed under the MIT License. See `LICENSE` for details.
