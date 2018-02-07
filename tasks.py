from invoke import task
import boto3
from os import environ as env
from time import sleep, time
import pdb

env['EC2_INI_PATH'] = './ec2/ec2.ini'
env['ANSIBLE_HOST_KEY_CHECKING'] = 'False'
env['ANSIBLE_VAULT_PASSWORD_FILE'] = env['HOME'] + '/.vault_pass_myproject.txt'


@task
def provision(ctx, inventory='YOU_MUST_PICK_ONE', playbook='provision',
              limit='YOU_MUST_PICK_ONE'):
    cmd = 'ansible-playbook ' \
        '-i inventories/{inventory} ' \
        'playbooks/{playbook}.yml ' \
        '--limit {limit}'.format(
            inventory=inventory, playbook=playbook, limit=limit)
    ctx.run(cmd)


@task
def createami(ctx, env='production'):
    ec2r = boto3.resource('ec2')
    ec2c = boto3.client('ec2')
    asc = boto3.client('autoscaling')
    instance = None

    try:
        print('Finding security group...')
        sg = ec2c.describe_security_groups(
            Filters=[{
                'Name': 'group-name',
                'Values': ['myproject-{env}-app'.format(env=env)]}
            ]
        )['SecurityGroups'][0]['GroupId']

        print('Finding vpc...')
        vpc = ec2c.describe_vpcs(
            Filters=[{
                'Name': 'tag:Name',
                'Values': ['myproject-{env}'.format(env=env)]}]

        )['Vpcs'][0]['VpcId']

        print('Finding subnet...')
        subnet = ec2c.describe_subnets(
            Filters=[{
                'Name': 'vpc-id',
                'Values': [vpc]}]

        )['Subnets'][0]['SubnetId']

        print('Launching instance...')
        instances = ec2r.create_instances(
            BlockDeviceMappings=[
                {
                    'DeviceName': '/dev/sda1',
                    'Ebs': {
                        'VolumeSize': 25,
                        'VolumeType': 'gp2',
                        'DeleteOnTermination': True
                    }
                }
            ],
            ImageId='ami-46c1b650',
            InstanceType='m4.large',
            MaxCount=1,
            MinCount=1,
            Monitoring={'Enabled': True},
            EbsOptimized=True,
            InstanceInitiatedShutdownBehavior='terminate',
            NetworkInterfaces=[
                {
                    'DeviceIndex': 0,
                    'AssociatePublicIpAddress': True,
                    'SubnetId': subnet,
                    'Groups': [sg]
                }
            ],
            TagSpecifications=[
                {
                    'ResourceType': 'instance',
                    'Tags': [
                        {
                            'Key': 'Name',
                            'Value': 'myproject-{env}-app'.format(env=env)
                        },
                        {
                            'Key': 'env',
                            'Value': env
                        },
                        {
                            'Key': 'product',
                            'Value': 'myproject'
                        },
                        {
                            'Key': 'role',
                            'Value': 'app'
                        },
                        {
                            'Key': 'createami',
                            'Value': env
                        },

                    ]
                }
            ],
            KeyName='myproject-production'
        )

        instance = instances[0]

        print('Waiting for instance to launch...')
        instance.wait_until_running()

        print('Waiting for instance to have IP address...')
        while(not instance.public_dns_name):
            sleep(2)
            instance.load()

        print('Waiting for instance to boot...')
        sleep(60)

        print('Provisioning...')
        cmd = 'ansible-playbook ' \
            '-i inventories/{env} ' \
            '--limit {env}-createami ' \
            'playbooks/provision.yml'.format(env=env)
        ctx.run(cmd)

        print('Creating AMI...')
        rev = int(time())
        name = 'myproject-{env}-app-{rev}'.format(env=env, rev=rev)
        resp = ec2c.create_image(Name=name, Description=name,
                                 InstanceId=instance.instance_id)
        image_id = resp['ImageId']

        print('Waiting for AMI...')
        waiter = ec2c.get_waiter('image_available')
        waiter.wait(ImageIds=[image_id], WaiterConfig={
            'Delay': 10,
            'MaxAttempts': 180
        })

        print('Creating launch configuration...')
        asc.create_launch_configuration(
            LaunchConfigurationName=name,
            ImageId=image_id,
            KeyName='myproject-production',
            SecurityGroups=['sg-XXXXXXXX'],
            InstanceType='m4.large',
            InstanceMonitoring={'Enabled': True},
            IamInstanceProfile='myproject-{env}-app'.format(env=env),
            EbsOptimized=True,
            AssociatePublicIpAddress=True,
            BlockDeviceMappings=[{
                    'DeviceName': '/dev/sda1',
                    'Ebs': {
                        'VolumeSize': 25,
                        'VolumeType': 'gp2',
                        'DeleteOnTermination': True
                    }
            }]
        )
    finally:
        print('Terminating instance...')
        if instance:
            ec2c.terminate_instances(InstanceIds=[instance.instance_id])
