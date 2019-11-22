#!/usr/bin/env python3
# -*- coding:utf-8 -*-

""" S3ConnectionCreator Service Software Inc. 2018
lambda_handler is the lambda function used to send 
get/post presigned URLs to client
"""

import boto3
import json

def lambda_handler(event, context):
    s3 = boto3.client('s3')
    companyName = event['queryStringParameters']['companyName']
    resultsKey = event['queryStringParameters']['resultsKey']


    configBucket = 'integrationconfigs'
    newestKey = max([
        obj['Key'] 
        for obj in 
        s3.list_objects(Bucket=configBucket, Prefix=companyName)['Contents']
    ])
    url = s3.generate_presigned_url(
        ClientMethod='get_object',
        ExpiresIn=300,
        Params={
            'Bucket' : configBucket,
            'Key' : newestKey
        }
    )

    resultsBucket = 'integrationresults'
    post = s3.generate_presigned_post(
        Bucket=resultsBucket,
        Key = resultsKey,
        ExpiresIn=300
    )

    return {
        'statusCode': 200,
        'body': json.dumps({
            "companyName": companyName,
            "scriptUrl": url,
            "postUrl": post,
        })
    }
