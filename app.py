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
parser.add_argument('--create_hosts_groups', dest='create_hosts_groups', help='for work with zabbix hosts group', action="store_true")
parser.add_argument('--create_host', dest='create_host', help='for work with zabbix host', action="store_true")
parser.add_argument('--update_host_macros', dest='update_host_macros', help='for update macros for host', action="store_true")
parser.add_argument('--create_user', dest='create_user', help='for work with zabbix user', action="store_true")
parser.add_argument('--create_web', dest='create_web', help='for work with zabbix web scenario', action="store_true")
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

            templates_list = []
            for template in host['templateid']:
                templates_list.append({'templateid': getTemplateId(template)})

            groups_list = []
            for group in host['groupid']:
                groups_list.append({'groupid': getGroupId(group)})

            host_create = zapi.host.create(
                groups = groups_list,
                interfaces = [{
                    'type': 1,
                    'main': 1,
                    'useip': 1 if host['use_ip'] else 0,
                    'ip': host['ip'],
                    'dns': host['host'],
                    'port': host['port']
                }],
                templates = templates_list,
                host=host['host']
            )

            hostids = host_create['hostids'][0]

            if host['macros']:
                for macro in host['macros']:
                    macros_create = zapi.usermacro.create(
                        hostid = hostids,
                        macro = '{$'+macro+'}',
                        value = host['macros'][macro]
                    )
        else:
            logging.info(f'Host {host} is existed, skip')

def hostUpdateMacros():
    for host in data['hosts']:
        if host['macros']:
            macros_list = []
            for macro in host['macros']:
                macros_list.append(
                    {
                        'macro': '{$'+macro+'}',
                        'value': host['macros'][macro]
                    }
                )

            macros_update = zapi.host.update(
                hostid = getHostId(host['host']),
                macros = macros_list
            )
            logging.info(f'Macros for {host["host"]} update')
        else:
            logging.info(f'Host {host["host"]} without macros')

def getHostId(name):
    for host in zapi.host.get():
        if host['name'] == name:
            return host['hostid']

def getGroupId(name):
    for group in zapi.hostgroup.get():
        if group['name'] == name:
            return group['groupid']

def getTemplateId(name):
    for template in zapi.template.get():
        if template['name'] == name:
            return template['templateid']

def getUserGroupId(name):
    for group in zapi.usergroup.get():
        if group['name'] == name:
            return group['usrgrpid']

def userCreate():
    for user in data['users']:
        for ex_user in zapi.user.get():
            if ex_user['username'] == user['name']:
                create_user = False
                break
            else:
                create_user = True

        if create_user:
            logging.info(f'User {user} is not existed, creating...')

            groups_list = []
            for group in user['usergroups']:
                groups_list.append({'usrgrpid': getUserGroupId(group)})

            user_create = zapi.user.create(
                alias = user['name'],
                passwd = user['password'],
                usrgrps = groups_list,
                user_medias = [],
                roleid = user['role_id']
            )
        else:
            logging.info(f'User {user} is existed, skip')

def webCreate():
    for web in data['web']:
        for ex_host in zapi.host.get():
            if ex_host['host'] == web['hostname']:
                create_host = False
                break
            else:
                create_host = True

        if create_host:
            logging.info(f'Web host {web["hostname"]} is not existed, creating...')
            host_create = zapi.host.create(
                groups = [{'groupid': getGroupId(web['group'])}],
                interfaces = [],
                templates = [],
                host=web['hostname']
            )

            hostids = host_create['hostids'][0]

            step_list = []
            for step in web['steps']:
                step_dict = {
                    'name': step['name'],
                    'url': step['url'],
                    'status_codes': str(step['status_codes']),
                    'no': step['number']
                }
                step_list.append(step_dict)

            web_create = zapi.httptest.create(
                name = web['name'],
                hostid = hostids,
                steps = step_list
            )
            logging.info(f'{web["hostname"]}: created web check')

            trigger_create = zapi.trigger.create(
                description = f'web check {web["hostname"]}',
                expression = f"last(/{web['hostname']}/{web['trigger']['type']}[{web['name']}],#{web['trigger']['count']})<>0",
                priority = web['trigger']['priority']
            )
            logging.info(f'{web["hostname"]}: created trigger for web check')
        else:
            logging.info(f'Web host {web["hostname"]} is existed, skip')

if args.zabbix_config:
    with open(args.zabbix_config[0]) as f:
        data = yaml.load(f, Loader=SafeLoader)

    if args.create_hosts_groups:
        logging.info(f'Proccess for creating host group was started')
        hostGroupCreate()
    
    if args.create_host:
        logging.info(f'Proccess for creating host was started')
        hostCreate()

    if args.update_host_macros:
        logging.info(f'Proccess for updating macros was started')
        hostUpdateMacros()

    if args.create_user:
        logging.info(f'Proccess for creating user was started')
        userCreate()
    
    if args.create_web:
        logging.info(f'Proccess for creating web scenario was started')
        webCreate()