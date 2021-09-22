# zabbix-manager

1. Create yaml from template zabbix.yaml.example
2. Create .env from .env.example
3. Install requirements.txt or build docker
```
pip install -r requirements.txt

docker build -t zabbix-manager
```
4. Run for create groups:
```
python app.py --config zabbix.yaml.example --create_hosts_groups
or for docker
docker run --rm -t zabbix-manager python3 app.py --config zabbix.yaml.example --create_hosts_groups
```
5. Run for create hosts:
```
python app.py --config zabbix.yaml.example --create_host
or for docker
docker run --rm -t zabbix-manager python3 app.py --config zabbix.yaml.example --create_host
```