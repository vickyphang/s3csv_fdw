# S3 CSV Foreign Data Wrapper for PostgreSQL

This foreign data wrapper (FDW) allows you to perform `SELECT *` queries on CSV files stored on Amazon S3 or S3-compatible storage. It is designed to replace `s3_fdw`, which is not supported on PostgreSQL version 9.2+.

> **Note**: This FDW now supports **S3-compatible storage** (e.g., MinIO, Ceph, etc.) by allowing you to specify a custom endpoint.


## Installation

### Step 1: Install Multicorn


```bash
#!/bin/sh
VERSION='3.0'
ARCHIVE="v${VERSION}.tar.gz"

wget -N "https://github.com/pgsql-io/multicorn2/archive/refs/tags/${ARCHIVE}"
tar -xvf "${ARCHIVE}"
rm -f "${ARCHIVE}"
cd "multicorn2-${VERSION}"

make && sudo make install
```

### Step 2: Clone and Install S3CsvFdw

The following commands will clone the repository and install it (the last command might require `sudo`):

```bash
git clone git@github.com:vickyphang/s3csv_fdw.git
cd s3csv_fdw
python setup.py install
```

### Step 3: Activate Multicorn in PostgreSQL

After installing Multicorn, activate the extension in your PostgreSQL database:

```sql
CREATE EXTENSION multicorn;
```


## Create Foreign Data Wrapper

To create the foreign data wrapper, run the following SQL command:

```sql
CREATE SERVER multicorn_csv FOREIGN DATA WRAPPER multicorn
OPTIONS (
    wrapper 's3csvfdw.s3csvfdw.S3CsvFdw'
);
```


## Create Foreign Table

You can create a foreign table to query your CSV file stored in S3 or S3-compatible storage. Replace the example fields with your own information.

#### Example:

```sql
CREATE FOREIGN TABLE test (
    remote_field1  character varying,
    remote_field2  integer
) SERVER multicorn_csv OPTIONS (
    bucket   'BUCKET',
    filename 'FILENAME'
);
```


## Add User Credentials

Store your AWS credentials (or S3-compatible storage credentials) in a PostgreSQL user mapping.

#### Example:

```sql
CREATE USER MAPPING FOR my_pg_user
SERVER multicorn_csv
OPTIONS (
    aws_access_key_id  'XXXXXXXXXXXXXXX',
    aws_secret_access_key  'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX',
    endpoint 's3.example.com'  -- Optional: Custom S3-compatible endpoint
);
```


## Perform Queries

Once the foreign table is created, you can query it like any other PostgreSQL table. For now, only read queries are supported.

### Example:

```sql
SELECT * FROM test;
```


## New Features

### Support for S3-Compatible Endpoints

You can now use this FDW with **S3-compatible storage** (e.g., MinIO, Ceph, etc.) by specifying a custom endpoint in the `OPTIONS` clause:

```sql
endpoint 's3.example.com'
```

If the endpoint does not start with `http://` or `https://`, the FDW will automatically prepend `https://`.


## Credits

- **Christian Toivola** ([dev360](https://github.com/dev360)) wrote the original code and submitted it as a Multicorn request [here](https://github.com/Kozea/Multicorn/pull/49).
- This repository packages the code for easier use.

---

## Notes

- Ensure your AWS credentials or S3-compatible storage credentials have the necessary permissions to access the bucket and file.
- The FDW reads the entire CSV file into memory, so it may not be suitable for very large files.
