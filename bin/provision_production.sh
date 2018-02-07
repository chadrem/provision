#!/bin/sh

ansible-playbook -i inventories/production playbooks/provision.yml --limit production
