from pyzabbix import ZabbixAPI
import os
import yaml
from yaml.loader import SafeLoader
import argparse
from dotenv import load_dotenv
import logging
import sys
logging.basicConfig(stream=sys.stdout, level=logging.INFO)

load_dotenv()
zabbix_host = os.getenv('zabbix_host')
zabbix_pass = os.getenv('zabbix_pass')
zabbix_user = os.getenv('zabbix_user')


zapi = ZabbixAPI(zabbix_host)
zapi.login(zabbix_user, zabbix_pass)

parser = argparse.ArgumentParser(description='Process zabbix manage')
parser.add_argument('--config', dest='zabbix_config', help='path to zabbix yaml config', nargs=1, metavar=("FILE"))
parser.add_argument('--create_update_hosts_groups', dest='create_update_hosts_groups', help='for work with zabbix hosts group', action="store_true")
parser.add_argument('--create_update_host', dest='create_update_host', help='for work with zabbix host', action="store_true")
args = parser.parse_args()

def hostGroupCreate():
    for group in data['host_group']:
        for ex_group in zapi.hostgroup.get():
            if ex_group['name'] == group['name']:
                create_group = False
                break
            else:
                create_group = True

        if create_group:
            logging.info(f'Group {group} is not existed, creating...')
            host_group_create = zapi.hostgroup.create(group)
            logging.info(f'Host Group was created, group id: {host_group_create}')
        else:
            logging.info(f'Group {group} is existed, skip')

def hostCreate():
    for host in data['hosts']:
        for ex_host in zapi.host.get():
            if ex_host['host'] == host['host']:
                create_host = False
                break
            else:
                create_host = True
        
        if create_host:
            logging.info(f'Host {host} is not existed, creating...')
            host_create = zapi.host.create(
                groups = {
                    'groupid': getGroupId(host['groupid'])
                },
                interfaces = {
                    'type': 1,
                    'main': 1,
                    'useip': 1 if host['use_ip'] else 0,
                    'ip': host['ip'],
                    'dns': host['host'],
                    'port': host['port']
                },
                templates = {
                    'templateid': getTemplateId(host['templateid'])
                },
                host=host['host']
            )
        else:
            logging.info(f'Host {host} is existed, skip')

def getGroupId(name):
    for group in zapi.hostgroup.get():
        if group['name'] == name:
            return group['groupid']

def getTemplateId(name):
    for template in zapi.template.get():
        if template['name'] == name:
            return template['templateid']
    

if args.zabbix_config:
    with open(args.zabbix_config[0]) as f:
        data = yaml.load(f, Loader=SafeLoader)

    if args.create_update_hosts_groups:
        logging.info(f'Proccess for creating host group was started')
        hostGroupCreate()
    
    if args.create_update_host:
        logging.info(f'Proccess for creating host was started')
        hostCreate()