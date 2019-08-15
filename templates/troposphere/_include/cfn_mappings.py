#!/usr/bin/env python
#
# Copyright 2018 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You may not use this file
# except in compliance with the License. A copy of the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is distributed on an "AS IS"
# BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under the License.
#

# Includes ap-east-1 (hkg) region

def AddAMIMap(t):

    t.add_mapping('AWSRegionAMI', {
        "ap-northeast-1": {
            "centos7": "ami-01c6b51fe8525af71"
        },
        "ap-northeast-2": {
            "centos7": "ami-0de44a841014b9e10"
        },
        "ap-south-1": {
            "centos7": "ami-0fbad96708b2cb7eb"
        },
        "ap-southeast-1": {
            "centos7": "ami-047586fe27dd4dca5"
        },
        "ap-southeast-2": {
            "centos7": "ami-06dc438e221a40328"
        },
        "ca-central-1": {
            "centos7": "ami-0e34c6f9c75696d8e"
        },
        "eu-central-1": {
            "centos7": "ami-0ac82e537f386ca99"
        },
        "eu-north-1": {
            "centos7": "ami-d35fd6ad"
        },
        "eu-west-1": {
            "centos7": "ami-0157c1e780f144955"
        },
        "eu-west-2": {
            "centos7": "ami-0e6580b0663210a44"
        },
        "eu-west-3": {
            "centos7": "ami-009002993433a3c75"
        },
        "sa-east-1": {
            "centos7": "ami-00bd76ca9b4be8367"
        },
        "us-east-1": {
            "centos7": "ami-0e560af290c745f5b"
        },
        "us-east-2": {
            "centos7": "ami-04207b688d79a3b2c"
        },
        "us-west-1": {
            "centos7": "ami-0f53c9faf89b4c688"
        },
        "us-west-2": {
            "centos7": "ami-02b792770bf83b668"
        },
        "ap-east-1": {
            "centos7": "ami-f44f3785"
        }
    })

def AddOSInfoMap(t):

    t.add_mapping('OSInfo', {
        "LoginID": {
            "centos7": "centos",
        }
    })