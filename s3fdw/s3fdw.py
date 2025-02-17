import boto3
from botocore.client import Config
from io import TextIOWrapper
import csv
import ssl
from multicorn import ForeignDataWrapper
from multicorn.utils import log_to_postgres, ERROR, WARNING, DEBUG

# Custom TLS domain validation logic for S3 bucket names
_old_match_hostname = ssl.match_hostname

def remove_dot(host):
    """
    >>> remove_dot('a.x.s3-eu-west-1.amazonaws.com')
    'ax.s3-eu-west-1.amazonaws.com'
    >>> remove_dot('a.s3-eu-west-1.amazonaws.com')
    'a.s3-eu-west-1.amazonaws.com'
    >>> remove_dot('s3-eu-west-1.amazonaws.com')
    's3-eu-west-1.amazonaws.com'
    >>> remove_dot('a.x.s3-eu-west-1.example.com')
    'a.x.s3-eu-west-1.example.com'
    """
    if not host.endswith('.amazonaws.com'):
        return host
    parts = host.split('.')
    h = ''.join(parts[:-3])
    if h:
        h += '.'
    return h + '.'.join(parts[-3:])

def _new_match_hostname(cert, hostname):
    return _old_match_hostname(cert, remove_dot(hostname))

# Patch the ssl module to use the custom hostname validation logic
ssl.match_hostname = _new_match_hostname

class S3Fdw(ForeignDataWrapper):
    """
    valid parameters:
        - aws_access_key : AWS access keys
        - aws_secret_key : AWS secret keys
        - hostname : accepted but ignored
        - bucket or bucketname : bucket in S3
        - filename : full path to the csv file, which must be readable
          with S3 credentials
        - delimiter : the delimiter used between fields (default: ",")
        - quotechar or quote : quote separator
        - skip_header or header: if integer, number of lines to skip, if true then 1, else 0
        - endpoint : custom S3-compatible endpoint
    """
    
    def __init__(self, options, columns):
        super(S3Fdw, self).__init__(options, columns)
        
        # Validate required options
        if 'aws_access_key' not in options:
            log_to_postgres("You must set aws_access_key", ERROR)
        if 'aws_secret_key' not in options:
            log_to_postgres("You must set aws_secret_key", ERROR)
        if 'bucket' not in options:
            log_to_postgres("You must set bucket", ERROR)
        if 'filename' not in options:
            log_to_postgres("You must set filename", ERROR)
        
        # Extract the custom endpoint from options
        self.endpoint = options.get('endpoint', None)
        
        # Validate and normalize the endpoint URL
        if self.endpoint:
            if not self.endpoint.startswith(('http://', 'https://')):
                self.endpoint = f"https://{self.endpoint}"  # Default to HTTPS if no scheme is provided
            log_to_postgres(f"Using custom endpoint: {self.endpoint}", DEBUG)
        
        # Initialize S3 client with custom endpoint if provided
        if self.endpoint:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=options.get('aws_access_key'),
                aws_secret_access_key=options.get('aws_secret_key'),
                endpoint_url=self.endpoint,  # Use the custom endpoint
                config=Config(signature_version='s3v4')
            )
        else:
            # Fallback to default AWS S3 endpoint
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=options.get('aws_access_key'),
                aws_secret_access_key=options.get('aws_secret_key')
            )

        # Extract table-specific options
        self.bucket = options.get('bucket')
        self.filename = options.get('filename')
        self.columns = columns

        # CSV parsing options
        self.delimiter = options.get('delimiter', ',')
        self.quotechar = options.get('quotechar', '"')
        self.skip_header = int(options.get('skip_header', 0))

    def execute(self, quals, columns):
        # Fetch the CSV file from S3
        try:
            response = self.s3_client.get_object(Bucket=self.bucket, Key=self.filename)
            stream = response['Body']
            
            # Parse the CSV file
            reader = csv.reader(TextIOWrapper(stream, encoding='utf-8'), delimiter=self.delimiter, quotechar=self.quotechar)
            count = 0
            checked = False
            for line in reader:
                if count >= self.skip_header:
                    if not checked:
                        # On first iteration, check if the lines are of the appropriate length
                        checked = True
                        if len(line) > len(self.columns):
                            log_to_postgres("There are more columns than defined in the table", WARNING)
                        if len(line) < len(self.columns):
                            log_to_postgres("There are less columns than defined in the table", WARNING)
                    
                    # Yield rows with null values for missing columns
                    row = line[:len(self.columns)]
                    nulled_row = [v if v else None for v in row]
                    yield dict(zip(self.columns, nulled_row))
                count += 1
        except Exception as e:
            log_to_postgres(f"Error fetching or parsing S3 file: {e}", ERROR)