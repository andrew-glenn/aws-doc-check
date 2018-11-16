#!/usr/bin/env python3

import argparse
import os

import boto3

S3_BUCKET = os.environ['S3_BUCKET'] if 'S3_BUCKET' in os.environ else ''
S3_PATH = os.environ['S3_PATH'] if 'S3_PATH' in os.environ else ''


def lambda_handler(event: dict, context):
    """Entry point when executed as a Lambda function.

    :param event: Standard event object provided by Lambda.
    :param context: Standard Lambda context provided by Lambda.
    :return:
    """

    scan_for_delete_markers(S3_BUCKET, S3_PATH)


def main():
    """Entry point when executed directly as a script from a terminal.

    :return:
    """

    arg_parser = argparse.ArgumentParser(
        description='Simple utility to scan for delete markers and delete them'
    )
    arg_parser.add_argument(
        '-b', '--bucket', default=S3_BUCKET, help='S3 bucket to scan',
        metavar='BUCKET')
    arg_parser.add_argument(
        '-p', '--prefix', default=S3_PATH,
        help='Path in the S3 bucket where docs are located', metavar='PATH')
    arg_parser.add_argument(
        '-r', '--restore', action='store_true',
        help='S3 delete the delete marker where it\'s the latest version')

    args = arg_parser.parse_args()

    scan_for_delete_markers(args.bucket, args.prefix, args.restore)


def scan_for_delete_markers(s3_bucket: str, s3_prefix: str,
                            restore_objects: bool=False):
    """Iterate through a specified bucket and path checking for deleted docs.

    Optionally, restores deleted objects by deleting the delete marker when
    it's the latest version. This requires that versioning be enabled on the S3
    bucket.

    :param s3_bucket: S3 bucket where docs are stored.
    :param s3_prefix: Location of docs inside the S3 bucket. Should not have a
        slash at the beginning, but should end with one.
    :param restore_objects: Controls whether objects whose latest version is a
        delete marker will have that marker deleted.
    """

    s3_client = boto3.client('s3')
    key_marker = ''

    while True:
        object_versions = s3_client.list_object_versions(
            Bucket=s3_bucket, KeyMarker = key_marker, Prefix=s3_prefix)

        if 'DeleteMarkers' in object_versions:
            for s3_object in object_versions['DeleteMarkers']:
                if s3_object['IsLatest']:
                    print('Doc at {key} has been deleted'.format(
                        key=s3_object['Key']))
                if restore_objects:
                    print('Restoring doc located at {key}'.format(
                          key=s3_object['Key']))
                    s3_client.delete_object(
                        Bucket=s3_bucket, Key=s3_object['Key'],
                        VersionId=s3_object['VersionId'])

        key_marker = object_versions['KeyMarker']
        if not key_marker:
            break


if __name__ == '__main__':
    main()