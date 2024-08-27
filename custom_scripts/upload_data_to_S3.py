#Python code to list all files in an S3 bucket, it would take in the credentials of the bucket
import boto3
import os

#Upload a folder containing multiple files to S3 with a prefix in the bucket
def upload_folder_to_S3(bucket_name, folder_path):
    s3 = boto3.client('s3')
    for file in os.listdir(folder_path):
        s3_dest_path = os.path.join('input/dataset_A', file)
        s3.upload_file(os.path.join(folder_path, file), bucket_name, s3_dest_path)
        print(f"Uploaded to {s3_dest_path}")
    print("Files uploaded successfully")

def display_files_in_S3_bucket(bucket_name):
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(bucket_name)
    print(bucket)
    for obj in bucket.objects.all():
        print(obj.key)
    print("Total files in the bucket: ", len(list(bucket.objects.all())))

def main():
    bucket_name = 'imerit-iupui'
    folder_path = '/media/mathe102/TASI-ESC-BKCP/1FPS_fixed_error_folders_zips'
    # upload_folder_to_S3(bucket_name, folder_path) #Uncomment it to upload
    display_files_in_S3_bucket(bucket_name)

main()