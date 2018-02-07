# Ansible Example Project

This is an example project for provisioning cloud servers using Ansible and the following applications:

* CentOS 7
* Amazon (AWS) EC2
* nginx
* Ruby on Rails
* Capistrano
* PostgreSQL (Amazon RDS)
* PgBouncer
* Redis

This example project is meant to be highly customized.
Do not attempt to use it without customization.
The target audience for this project is someone with detailed knowledge of Linux, devops, AWS, Python, Bash, etc.
The goal of this project is to demonstrate reproducible and automated server builds.

## Features

* Reproducible and automated server builds.
* Python Invoke script for creating AMIs and launch configurations.

## Setup

* Install [Ansible](https://www.ansible.com)and any of its dependencies (such as Python) using the official documentation.
* Install [Python](https://www.python.org) and [Invoke](http://www.pyinvoke.org).
* Setup your default ansible-vault password file: ````echo myproject > "$HOME/.vault_pass_myproject.txt"````
* Source the required environment variables: ````. shell_vars.env````
* Customize the project to your requirements.

## Customization

* This example project is called ````myproject```` throughout the code and configuration files. You will need to manually edit all of the files to change the name.
* Sensitive information is stored in ````inventories/production/inventory```` and encrypted with ansible-vault. You will need to customize it to your environment.

## Ansible Vault

Some file(s) that contain sensitive information are encrypted using ````ansible-vault````.
The default password is ````myproject````.

To find all of your encrypted files you can run:

````grep -R '$ANSIBLE_VAULT' .````

Example on how to change a password:

````ansible-vault rekey inventories/production/inventory````

## Copyright

Copyright (c) 2018 Chad Remesch. See LICENSE.txt for
further details.
