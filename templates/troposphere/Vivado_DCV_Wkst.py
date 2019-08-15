#!/usr/bin/env python

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
import sys
from troposphere import Base64, FindInMap, GetAtt, Join, iam, Tags, Parameter, \
    Output, Ref, Template, Equals, Not, If
from troposphere.cloudformation import WaitCondition, WaitConditionHandle
from troposphere.ec2 import NetworkInterfaceProperty, EIP, SecurityGroup
from troposphere.iam import PolicyType, InstanceProfile
import troposphere.ec2 as ec2

from cfn_flip import flip, to_yaml, to_json
from _include.cfn_mappings import AddAMIMap, AddOSInfoMap


def main():

    t = Template()
    AddAMIMap(t)

    t.set_version("2010-09-09")

    t.set_description(
        "DCV 2017 Remote Desktop with Xilinx Vivado (using AWS FPGA Developer AMI)"
    )

    tags = Tags(Name=Ref("AWS::StackName"))

    # user data
    InstUserData = list()
    InstUserData = [
        '#!/usr/bin/env bash\n',
        '\n',
        'set -x\n',
        '\n',
        '##exit 0\n',  # use this to disable all user-data and bring up files
        '\n',
        'my_wait_handle="', Ref('InstanceWaitHandle'), '"\n',
        'user_name="', Ref('UserName'), '"\n',
        'user_pass="', Ref('UserPass'), '"\n',
        '\n',
    ]

    with open('_include/dcv-install.sh', 'r',) as ud_file:
        user_data_file = ud_file.readlines()

    for l in user_data_file:
        InstUserData.append(l)

    VPCId = t.add_parameter(Parameter(
        'VPCId',
        Type="AWS::EC2::VPC::Id",
        Description="VPC ID for where the remote desktop instance should be launched"
    ))
    t.set_parameter_label(VPCId, "VPC ID")
    t.add_parameter_to_group(VPCId, "Instance Configuration")

    Subnet = t.add_parameter(Parameter(
        'Subnet',
        Type="AWS::EC2::Subnet::Id",
        Description="For the Subnet ID, you should choose one in the "
                    "Availability Zone where you want the instance launched"
    ))
    t.set_parameter_label(Subnet, "Subnet ID")
    t.add_parameter_to_group(Subnet, "Instance Configuration")

    ExistingSecurityGroup = t.add_parameter(Parameter(
        'ExistingSecurityGroup',
        Type="String",
        Default="NO_VALUE",
        Description="OPTIONAL: Needs to be a SG ID, for example sg-abcd1234efgh. "
                    "This is an already existing Security Group ID that is "
                    "in the same VPC, this is an addition to the security groups that "
                    "are automatically created to enable access to the remote desktop,"
                    "leave as NO_VALUE if you choose not to use this"
    ))
    t.set_parameter_label(ExistingSecurityGroup, "OPTIONAL: Existing Security Group (e.g. sg-abcd1234efgh)")
    t.add_parameter_to_group(ExistingSecurityGroup, "Instance Configuration")

    remoteDesktopInstanceType = t.add_parameter(Parameter(
        'remoteDesktopInstanceType',
        Type="String",
        Description="This is the instance type that will be used. As this is a "
                    "2D workstation, we are not supporting GPU instance types.",
        Default="m4.xlarge",
        AllowedValues=[
            "m4.large",
            "m4.xlarge",
            "m4.2xlarge",
            "m4.4xlarge",
            "m4.10xlarge",
            "m5.large",
            "m5.xlarge",
            "m5.2xlarge",
            "m5.4xlarge",
            "m5.12xlarge",
            "m5.24xlarge",
            "z1d.large",
            "z1d.xlarge",
            "z1d.2xlarge",
            "z1d.3xlarge",
            "z1d.6xlarge",
            "z1d.12xlarge",
            "z1d.metal"
        ],
        ConstraintDescription= "Must an EC2 instance type from the list"
    ))
    t.set_parameter_label(remoteDesktopInstanceType, "Remote Desktop Instance Type")
    t.add_parameter_to_group(remoteDesktopInstanceType, "Instance Configuration")

    EC2KeyName = t.add_parameter(Parameter(
        'EC2KeyName',
        Type="AWS::EC2::KeyPair::KeyName",
        Description="Name of an existing EC2 KeyPair to enable SSH access to the instance.",
        ConstraintDescription="REQUIRED: Must be a valid EC2 key pair"
    ))
    t.set_parameter_label(EC2KeyName, "EC2 Key Name")
    t.add_parameter_to_group(EC2KeyName, "Instance Configuration")

    OperatingSystem = t.add_parameter(Parameter(
        'OperatingSystem',
        Type="String",
        Description="Operating System of the AMI",
        Default="centos7",
        AllowedValues=[
            "centos7"
        ],
        ConstraintDescription="Must be: centos7"
    ))
    t.set_parameter_label(OperatingSystem, "Operating System of AMI")
    t.add_parameter_to_group(OperatingSystem, "Instance Configuration")

    StaticPrivateIpAddress = t.add_parameter(Parameter(
        'StaticPrivateIpAddress',
        Type="String",
        Default="NO_VALUE",
        Description="OPTIONAL: If you already have a private VPC address range, you can "
                    "specify the private IP address to use, leave as NO_VALUE if you choose not to use this",
    ))
    t.set_parameter_label(StaticPrivateIpAddress, "OPTIONAL: Static Private IP Address")
    t.add_parameter_to_group(StaticPrivateIpAddress, "Instance Configuration")

    UsePublicIp = t.add_parameter(Parameter(
        'UsePublicIp',
        Type="String",
        Description="Should a public IP address be given to the instance, "
                    "this is overridden by CreateElasticIP=True",
        Default="True",
        ConstraintDescription="True/False",
        AllowedValues=[
            "True",
            "False"
        ]
    ))
    t.set_parameter_label(UsePublicIp, "Assign a public IP Address")
    t.add_parameter_to_group(UsePublicIp, "Instance Configuration")

    CreateElasticIP = t.add_parameter(Parameter(
        'CreateElasticIP',
        Type="String",
        Description="Should an Elastic IP address be created and assigned, "
                    "this allows for persistent IP address assignment",
        Default="True",
        ConstraintDescription="True/False",
        AllowedValues=[
            "True",
            "False"
        ]
    ))
    t.set_parameter_label(CreateElasticIP, "Create an Elastic IP address")
    t.add_parameter_to_group(CreateElasticIP, "Instance Configuration")

    S3BucketName = t.add_parameter(Parameter(
        'S3BucketName',
        Type="String",
        Default="NO_VALUE",
        Description="OPTIONAL: S3 bucket to allow this instance read access (List and Get),"
                    "leave as NO_VALUE if you choose not to use this"
    ))
    t.set_parameter_label(S3BucketName, "OPTIONAL: S3 bucket for read access")
    t.add_parameter_to_group(S3BucketName, "Instance Configuration")

    AccessCidr = t.add_parameter(Parameter(
        'AccessCidr',
        Type="String",
        Description="This is the CIDR block for allowing remote access, for ports 22 and 8443",
        Default="111.222.333.444/32",
        AllowedPattern="(\\d{1,3})\\.(\\d{1,3})\\.(\\d{1,3})\\.(\\d{1,3})/(\\d{1,2})",
        ConstraintDescription="Must be a valid CIDR x.x.x.x/x"
    ))
    t.set_parameter_label(AccessCidr, "CIDR block for remote access (ports 22 and 8443)")
    t.add_parameter_to_group(AccessCidr, "Instance Configuration")

    UserName = t.add_parameter(Parameter(
        'UserName',
        Type="String",
        Description="User name for DCV remote desktop login, default is \"simuser\".",
        Default="simuser",
        MinLength="4",
    ))
    t.set_parameter_label(UserName, "User name for DCV login")
    t.add_parameter_to_group(UserName, "DCV Configuration")

    UserPass = t.add_parameter(Parameter(
        'UserPass',
        Type="String",
        Description="Password for DCV remote desktop login. The default password is Ch4ng3M3!",
        Default="Ch4ng3M3!",
        MinLength="8",
        AllowedPattern="^((?=.*[a-z])(?=.*[A-Z])(?=.*[\\d])|(?=.*[a-z])(?=.*[A-Z])(?=.*[\\W_])|(?=.*[a-z])(?=.*[\\d])(?=.*[\\W_])|(?=.*[A-Z])(?=.*[\\d])(?=.*[\\W_])).+$",
        ConstraintDescription="Password must contain at least one element from three of the following sets: lowercase letters, uppercase letters, base 10 digits, non-alphanumeric characters",
        NoEcho=True
    ))
    t.set_parameter_label(UserPass, "Password for DCV login")
    t.add_parameter_to_group(UserPass, "DCV Configuration")


    # end parameters

    RootRole = t.add_resource(iam.Role(
        "RootRole",
        AssumeRolePolicyDocument={
            "Version": "2012-10-17",
            "Statement": [ {
                "Effect": "Allow",
                "Principal": {
                    "Service": ["ec2.amazonaws.com"],
                 },
                "Action": ["sts:AssumeRole"]
            }]
        }
    ))

    dcvBucketPolicy= t.add_resource(PolicyType(
        "dcvBucketPolicy",
        PolicyName="dcvBucketPolicy",
        Roles=[Ref(RootRole)],
        PolicyDocument={
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": ["s3:GetObject"],
                    "Resource": "arn:aws:s3:::dcv-license.us-east-1/*"
                }
            ],
        },
    )),

    BucketPolicy= t.add_resource(PolicyType(
        "BucketPolicy",
        PolicyName="BucketPolicy",
        Roles=[Ref(RootRole)],
        PolicyDocument={
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": ["s3:GetObject"],
                    "Resource": {"Fn::Join":["", ["arn:aws:s3:::", {"Ref": "S3BucketName"},"/*"]]}
                },
                {
                    "Effect": "Allow",
                    "Action": [ "s3:ListBucket"],
                    "Resource": {"Fn::Join":["", ["arn:aws:s3:::", {"Ref": "S3BucketName"}]]}
                }
            ],
        },
        Condition="Has_Bucket"
    )),

    remoteDesktopSecurityGroup = t.add_resource(SecurityGroup(
        "remoteDesktopSecurityGroup",
        VpcId = Ref(VPCId),
        GroupDescription = "Remote Desktop Secuirty group",
        SecurityGroupIngress=[
            ec2.SecurityGroupRule(
                IpProtocol="tcp",
                FromPort="8443",
                ToPort="8443",
                CidrIp=Ref(AccessCidr),
            ),
        ]
    ))

    SshSecurityGroup = t.add_resource(SecurityGroup(
        "SshSecurityGroup",
        VpcId = Ref(VPCId),
        GroupDescription = "SSH Secuirty group",
        SecurityGroupIngress=[
            ec2.SecurityGroupRule(
                IpProtocol="tcp",
                FromPort="22",
                ToPort="22",
                CidrIp=Ref(AccessCidr),
            ),
        ]
    ))

    RootInstanceProfile = t.add_resource(InstanceProfile(
        "RootInstanceProfile",
        Roles=[Ref(RootRole)]
    ))

    remoteDesktopInstance = t.add_resource(ec2.Instance(
        'remoteDesktopInstance',
        ImageId=FindInMap("AWSRegionAMI", Ref("AWS::Region"), Ref(OperatingSystem)),
        KeyName=Ref(EC2KeyName),
        InstanceType=(Ref(remoteDesktopInstanceType)),
        DisableApiTermination='false',
        NetworkInterfaces=[
            NetworkInterfaceProperty(
                SubnetId=Ref(Subnet),
                GroupSet=If(
                    "not_existing_sg",
                    [Ref(remoteDesktopSecurityGroup), Ref(SshSecurityGroup)],
                    [Ref(remoteDesktopSecurityGroup), Ref(SshSecurityGroup), Ref(ExistingSecurityGroup)]
                ),
                AssociatePublicIpAddress=Ref(UsePublicIp),
                DeviceIndex='0',
                DeleteOnTermination='true',
                PrivateIpAddress=If(
                    "Has_Static_Private_IP",
                    Ref(StaticPrivateIpAddress),
                    Ref("AWS::NoValue"),
                )
            )
        ],
        IamInstanceProfile=(Ref(RootInstanceProfile)),
        UserData=Base64(Join('', InstUserData)),
    ))

    EIPAddress = t.add_resource(EIP(
        'EIPAddress',
        Domain='vpc',
        InstanceId=Ref(remoteDesktopInstance),
        Condition="create_elastic_ip"
    ))

    t.add_condition(
        "not_existing_sg",
        Equals(Ref(ExistingSecurityGroup), "NO_VALUE")
    )

    t.add_condition(
        "Has_Public_Ip",
        Equals(Ref(UsePublicIp), "True")
    )

    t.add_condition(
        "Has_Bucket",
        Not(Equals(Ref(S3BucketName), "NO_VALUE"))
    )

    t.add_condition(
        "create_elastic_ip",
        Equals(Ref(CreateElasticIP), "True")
    )

    t.add_condition(
        "Has_Static_Private_IP",
        Not(Equals(Ref(StaticPrivateIpAddress), "NO_VALUE"))
    )

    waithandle = t.add_resource(WaitConditionHandle('InstanceWaitHandle'))

    instanceWaitCondition = t.add_resource(WaitCondition(
        "instanceWaitCondition",
        Handle=Ref(waithandle),
        Timeout="3600",
        DependsOn="remoteDesktopInstance"
    ))

    t.add_output([
        Output(
            "DCVConnectionLink",
            Description="Connect to the DCV Remote Desktop with this URL",
            Value=Join("", [
                "https://",
                GetAtt("remoteDesktopInstance", 'PublicIp'),
                ":8443"
            ])
        ),
        Output(
            "DCVUserName",
            Description="Login name for DCV session",
            Value=(Ref(UserName))
        ),
        Output(
            "SSHTunnelCommand",
            Description='Command for setting up SSH tunnel to remote desktop, use "localhost:18443" for DCV client',
            Value=Join("", [
                "ssh -i <file.pem> -L 18443:localhost:8443 -l centos ",
                GetAtt("remoteDesktopInstance", 'PublicIp')
            ])
        ),
    ])

    #print(t.to_json(indent=2))
    print(to_yaml(t.to_json(indent=2), clean_up=True))


if __name__ == "__main__":
    sys.exit(main())


