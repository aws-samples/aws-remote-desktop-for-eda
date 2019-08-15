#!/usr/bin/env python
#
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
# the Software, and to permit persons to whom the Software is furnished to do so.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
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