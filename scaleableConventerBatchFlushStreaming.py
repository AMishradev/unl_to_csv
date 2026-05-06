import boto3, csv, io

s3 = boto3.client("s3")
mp = s3.create_multipart_upload(Bucket=bucket, Key=out_key, ContentType="text/csv")
upload_id = mp["UploadId"]
parts = []
part_number = 1

buf = io.BytesIO()
text = io.TextIOWrapper(buf, encoding="utf-8", newline="")
wtr = csv.writer(text, delimiter=",", quoting=csv.QUOTE_ALL)

# header
wtr.writerow(column_names)

PART_SIZE = 5 * 1024 * 1024  # 5 MB

def flush_part():
    nonlocal part_number, parts
    text.flush()         # push text into buf
    size = buf.tell()
    if size == 0: 
        return
    buf.seek(0)
    resp = s3.upload_part(
        Bucket=bucket, Key=out_key,
        PartNumber=part_number, UploadId=upload_id,
        Body=buf.read(size)
    )
    parts.append({"ETag": resp["ETag"], "PartNumber": part_number})
    part_number += 1
    buf.seek(0); buf.truncate(0)

# stream rows from your UNL reader
for row in rdr:
    wtr.writerow(row)
    text.flush()
    if buf.tell() >= PART_SIZE:
        flush_part()

# flush final (possibly <5MB) part and complete
flush_part()
s3.complete_multipart_upload(
    Bucket=bucket, Key=out_key, UploadId=upload_id,
    MultipartUpload={"Parts": parts}
)