#!/usr/bin/env python3

import cgi
import cgitb
import boto3
import os

# Enable debugging
cgitb.enable()

# Set AWS credentials as environment variables
os.environ['AWS_ACCESS_KEY_ID'] = ''
os.environ['AWS_SECRET_ACCESS_KEY'] = ''

def create_bucket(bucket_name):
    try:
        s3 = boto3.client('s3', region_name='ap-south-1')
        s3.create_bucket(
            Bucket=bucket_name,
            ACL='private',
            CreateBucketConfiguration={
                'LocationConstraint': 'ap-south-1'
            }
        )
        return "Bucket created successfully!"
    except Exception as e:
        return f"Error creating bucket: {str(e)}"

def list_buckets():
    try:
        s3 = boto3.client('s3', region_name='ap-south-1')
        buckets = s3.list_buckets()
        return [bucket['Name'] for bucket in buckets['Buckets']]
    except Exception as e:
        return []

def list_files(bucket_name):
    try:
        s3 = boto3.client('s3', region_name='ap-south-1')
        response = s3.list_objects_v2(Bucket=bucket_name)
        files = [content['Key'] for content in response.get('Contents', [])]
        return files
    except Exception as e:
        return []

def generate_presigned_url(bucket_name, object_name):
    try:
        s3 = boto3.client('s3', region_name='ap-south-1')
        url = s3.generate_presigned_url('get_object',
                                        Params={'Bucket': bucket_name, 'Key': object_name},
                                        ExpiresIn=3600)
        return url
    except Exception as e:
        return None

def upload_file(bucket_name, fileitem):
    try:
        s3 = boto3.client('s3', region_name='ap-south-1')
        s3.upload_fileobj(fileitem.file, bucket_name, fileitem.filename)
        return "File uploaded successfully!"
    except Exception as e:
        return f"Error uploading file: {str(e)}"

def main():
    print("Content-Type: text/html")
    print()

    form = cgi.FieldStorage()
    action = form.getvalue("action")
    buckets = list_buckets()
    result = ""
    files = []
    download_links = {}

    if action == "create_bucket":
        bucket_name = form.getvalue("bucket_name")
        if bucket_name:
            result = create_bucket(bucket_name)
    elif action == "upload_file":
        bucket_name = form.getvalue("bucket_name")
        fileitem = form['file']
        if bucket_name and fileitem.filename:
            result = upload_file(bucket_name, fileitem)
    elif action == "list_files":
        bucket_name = form.getvalue("bucket_name")
        if bucket_name:
            files = list_files(bucket_name)
            result = f"Files in bucket '{bucket_name}':"
            for file in files:
                download_links[file] = generate_presigned_url(bucket_name, file)

    print("""
    <html>
    <head>
        <title>Manage S3 Buckets</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background-color: #f0f0f0;
                margin: 0;
                padding: 20px;
            }
            h2 {
                color: #333;
                margin-bottom: 20px;
            }
            form {
                background-color: #fff;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                margin-bottom: 20px;
            }
            label {
                font-weight: bold;
            }
            input[type=text],
            input[type=file],
            select {
                width: 100%;
                padding: 10px;
                margin-bottom: 10px;
                border: 1px solid #ccc;
                border-radius: 4px;
                box-sizing: border-box;
            }
            input[type=submit] {
                background-color: #007bff;
                color: #fff;
                border: none;
                padding: 12px 20px;
                cursor: pointer;
                border-radius: 4px;
                font-size: 16px;
            }
            input[type=submit]:hover {
                background-color: #0056b3;
            }
            .result {
                background-color: #e7f3fe;
                border-left: 6px solid #2196F3;
                margin-bottom: 20px;
                padding: 10px;
            }
            .files-list {
                background-color: #fff;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            }
            .files-list ul {
                list-style-type: none;
                padding: 0;
            }
            .files-list li {
                padding: 8px;
                border-bottom: 1px solid #ccc;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            .files-list a {
                text-decoration: none;
                color: #007bff;
                font-weight: bold;
            }
            .files-list a:hover {
                text-decoration: underline;
            }
        </style>
    </head>
    <body>
        <h2>Create S3 Bucket</h2>
        <form action="/cgi-bin/menu/awsfiles/s3bucket.py" method="post">
            <input type="hidden" name="action" value="create_bucket">
            <label for="bucket_name">Bucket Name:</label>
            <input type="text" id="bucket_name" name="bucket_name" required>
            <input type="submit" value="Create Bucket">
        </form>

        <h2>Upload File to S3 Bucket</h2>
        <form action="/cgi-bin/menu/awsfiles/s3bucket.py" method="post" enctype="multipart/form-data">
            <input type="hidden" name="action" value="upload_file">
            <label for="bucket_name">Select Bucket:</label>
            <select id="bucket_name" name="bucket_name" required>
    """)

    for bucket in buckets:
        print(f'<option value="{bucket}">{bucket}</option>')

    print("""
            </select>
            <label for="file">Choose File:</label>
            <input type="file" id="file" name="file" required>
            <input type="submit" value="Upload File">
        </form>

        <h2>List Files in S3 Bucket</h2>
        <form action="/cgi-bin/menu/awsfiles/s3bucket.py" method="post">
            <input type="hidden" name="action" value="list_files">
            <label for="bucket_name">Select Bucket:</label>
            <select id="bucket_name" name="bucket_name" required>
    """)

    for bucket in buckets:
        print(f'<option value="{bucket}">{bucket}</option>')

    print("""
            </select>
            <input type="submit" value="List Files">
        </form>
    """)

    if result:
        print(f'<div class="result"><p>{result}</p></div>')

    if files:
        print('<div class="files-list"><ul>')
        for file in files:
            download_url = download_links[file]
            print(f'<li>{file} <a href="{download_url}" target="_blank">Download</a></li>')
        print('</ul></div>')

    print("""
    </body>
    </html>
    """)

if __name__ == "__main__":
    main()
