import apache_beam as beam
import pytz
import json
import datetime
import os
from apache_beam.options.pipeline_options import PipelineOptions
from google.cloud import storage
from google.cloud import aiplatform

credentials_file = "tensile-nebula-406509-8fd0cc70c363.json"
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_file

def get_latest_dataset(bucket_name):    

    project_id = "tensile-nebula-406509"

    # Initialize the Google Cloud Storage client
    client = storage.Client(project=project_id)
    print(client)

    # Get the bucket
    bucket = client.get_bucket(bucket_name)
 
    # List all objects in the bucket
    blobs = bucket.list_blobs()
 
    ist = pytz.timezone('Asia/Kolkata')
 
    # Initialize variables to track the latest modified time and object
    latest_modified_time = None
    latest_modified_blob = None

    # Find the latest modified file
    for blob in blobs:
        # Convert last modified time to IST
        last_modified_ist = blob.updated.astimezone(ist)
       
        # Check if this is the latest modified file
        if latest_modified_time is None or last_modified_ist > latest_modified_time:
            latest_modified_time = last_modified_ist
            latest_modified_blob = blob
 
    if latest_modified_blob:
      formatted_time = latest_modified_time.strftime("%Y-%m-%d %I:%M:%S %p")
      return {
          "file_name": latest_modified_blob.name,
          "size": latest_modified_blob.size,
          "last_modified_ist": formatted_time
      }
    else:
      return None


class CombineColumns(beam.DoFn):
    def process(self, element):
        if element['FirstName'] == 'FirstName':
            element['FullName'] = 'FullName'
        else:
            element['FullName'] = element['FirstName'] +' '+ element['LastName']
        element = ','.join(element.values())
        yield element


def run():
    credentials_path = "tensile-nebula-406509-8fd0cc70c363.json"

    latest_file_info = get_latest_dataset("input_buk-1")

    input_csv_path = f"gs://input_buk-1/{latest_file_info['file_name']}"
    output_csv_path = f"gs://output_buk/output/{latest_file_info['file_name']}"

    print(output_csv_path)

    pipeline_options = PipelineOptions(
        flags=[], 
        runner="DataflowRunner",
        project="tensile-nebula-406509",
        region="us-central1",
        job_name="my-dataflow-job-1215",
        temp_location="gs://output_buk/temp_dir",
        # setup_file="./setup.py",
        # service_account_email="your-service-account@your-project.iam.gserviceaccount.com",
        service_account_file=credentials_path
    )

    with beam.Pipeline(options=pipeline_options) as p:
        header = (
            p
            | 'ReadHeader' >> beam.io.ReadFromText(input_csv_path, skip_header_lines=0)
            | 'ExtractHeader' >> beam.Map(lambda x: x.split(','))
            | 'FirstRow' >> beam.combiners.ToList()
            | 'GetFirstRow' >> beam.Map(lambda lst: lst[0])  # Get the single element in the list
           
        )

        lines = p | 'ReadFromText' >> beam.io.ReadFromText(input_csv_path, skip_header_lines=0)

        def parse_csv(row, header):
            return dict(zip(header, row.split(',')))

        data = lines | 'ParseCSV' >> beam.Map(parse_csv, header=beam.pvalue.AsSingleton(header))
        
        combined_data = data | 'CombineColumns' >> beam.ParDo(CombineColumns())
        
        combined_data | 'WriteToText' >> beam.io.WriteToText(output_csv_path, file_name_suffix=".csv")

if __name__ == '__main__':
    run()