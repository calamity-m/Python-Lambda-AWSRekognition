from __future__ import print_function

import boto3
from decimal import Decimal
import json
import urllib

print('Loading function')

# Amazon Rekognition client
rekognition = boto3.client('rekognition')
# Confidence checking point
percent = 85
# Amazon SNS client
sns = boto3.client('sns')

# Detect labels in an image
def detect_labels(bucket, key):
    response = rekognition.detect_labels(Image={"S3Object": {"Bucket": bucket, "Name": key}})
    return response

def lambda_entry(event, context):
    # Get the object from the event
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.unquote_plus(event['Records'][0]['s3']['object']['key'].encode('utf8'))
    
    # Attempt to call amazon image recognition
    try:

        # Calls rekognition DetectLabels API to detect labels in S3 object
        response = detect_labels(bucket, key)

        # Start our SNS body reply
        msg = 'Image Labels Found With Confidence > %s points\n\n' %(percent)

        # Concatenate all valid labels
        tally = 0
        for label in response['Labels']:
            if (float(label['Confidence']) > percent):
                msg += '%s\n' % (label['Name'])
                tally += 1
        
        # If none are found, add a slight error message
        if tally == 0:
            msg += "No labels with high enough confidence found\n"
        
        # Get our metadata into a usable format
        metadata = response['ResponseMetadata']
        httpheader = metadata['HTTPHeaders']
        date = httpheader['date']
        
        # Final touches to SNS body
        msg += "\n"
        msg += "Image was uploaded to S3 Bucket at: %s" %(date)

        # Send email with response by publishing to specified SNS
        email = sns.publish(
            TargetArn='arn:aws:sns:us-west-2:974415615896:image-recognition-lambda',
            Message=msg,
            Subject='Label Recognition for Image: %s' %(key),
        )

        # Print response to console.
        print(response)

        return response
    except Exception as e:
        print(e)
        print("Error processing object {} from bucket {}. ".format(key, bucket) +
              "Make sure your object and bucket exist and your bucket is in the same region as this function.")
        raise e