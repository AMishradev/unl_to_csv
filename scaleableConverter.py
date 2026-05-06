# file: unl_to_csv_lambda.py
import boto3, csv, io, logging, os, tempfile

s3 = boto3.client("s3")
LOG = logging.getLogger()
LOG.setLevel(logging.INFO)               # CloudWatch picks this up

def lambda_handler(event, context):
    # ── 1. Gather “arguments” ────────────────────────────────────────────────
    bucket       = event["bucket"]
    unl_key      = event["unl_key"]
    columns_key  = event["columns_key"]
    out_key      = event.get("output_key",
                             unl_key.rsplit(".", 1)[0] + ".csv")
    delim        = event.get("delimiter", "|")
    enc          = event.get("encoding", "latin-1")  # cope with 0xA0 etc.

    LOG.info("Converting s3://%s/%s → %s", bucket, unl_key, out_key)

    # ── 2. Download both helper files to /tmp/  ─────────────────────────────
    # /tmp is the Lambda ephemeral storage (default 512 MB, up to 10 GB) :contentReference[oaicite:0]{index=0}
    tmp_unl      = tempfile.mktemp(suffix=".unl", dir="/tmp")
    tmp_columns  = tempfile.mktemp(suffix=".txt", dir="/tmp")
    tmp_csv      = tempfile.mktemp(suffix=".csv", dir="/tmp")

    s3.download_file(bucket, unl_key,     tmp_unl)
    s3.download_file(bucket, columns_key, tmp_columns)

    # ── 3. Read column names  ───────────────────────────────────────────────
    with open(tmp_columns, encoding="utf-8") as f:
        column_names = [ln.strip() for ln in f if ln.strip()]

    # ── 4. Convert UNL → CSV  ───────────────────────────────────────────────
    row_count = 0
    with open(tmp_unl, "rb") as fh_raw, \
         io.TextIOWrapper(fh_raw,
                          encoding=enc,
                          errors="surrogateescape",
                          newline="") as unl_in, \
         open(tmp_csv, "w", newline="", encoding="utf-8") as csv_out:

        rdr = csv.reader(unl_in,
                         delimiter=delim,
                         escapechar="\\",
                         quoting=csv.QUOTE_NONE)
        wtr = csv.writer(csv_out,
                         delimiter=",",
                         quoting=csv.QUOTE_ALL)

        wtr.writerow(column_names)
        for row in rdr:
            wtr.writerow(row)
            row_count += 1

    LOG.info("Wrote %s rows", row_count)

    # ── 5. Upload result back to S3  ────────────────────────────────────────
    s3.upload_file(tmp_csv, bucket, out_key)

    return {
        "status":   "ok",
        "rows":     row_count,
        "csv_uri":  f"s3://{bucket}/{out_key}"
    }