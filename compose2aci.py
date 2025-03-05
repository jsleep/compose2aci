import argparse
import yaml
import os
import sys

def adapt_ports(ports):
    aci_ports = []
    for port in ports:
        # parse out protocol first
        if '/' in port:
            protocol = port.split('/')[1]
        else:
            protocol = 'udp' # seems to be the default - maybe should always set in compose.yaml

        # then initial port (could be 0/1 should always map X:X)
        port = port.split(':')[0]
        
        if '-' in port:
            start_port = int(port.split('-')[0])
            end_port = int(port.split('-')[1])

        else:
            start_port = int(port)
            end_port = start_port
        
        for i in range(start_port, end_port+1):
            aci_ports.append({
                'port': i,
                'protocol': protocol
            })

    return aci_ports

def adapt_env(env):
    res = []
    for key in env:
        res.append({
            'name': key,
            'value': env[key]
        })
    return res

def adapt_resource(resources):
    res = {}

    for key in resources:
        resource = resources[key]
        azure_resource = {}

        for resource_key in resource:
            if resource_key == 'memory':
                azure_resource['memoryInGB'] = resource['memory']
            elif resource_key == 'cpus':
                azure_resource['cpu'] = resource['cpus']
            # skipping gpus
        
        res[key] = azure_resource
        
    
    return res


def adapt_for_aci(compose_dir, args, azure_env):
    env = {}
    # from compose yaml
    env['game_name'] = args.game
    game_service = compose_dir['services'][args.game]
    env['image'] = game_service['image']
    env['ports'] = adapt_ports(game_service['ports'])
    env['game_env'] = adapt_env(game_service['environment'])
    env['resources'] = adapt_resource(game_service['deploy']['resources'])
    # generally only needs one mount path to file share
    volume = game_service['volumes'][0]
    env['mount_path'] = volume.split(':')[1] if ':' in volume else volume

    # needed for valheim
    azure_env['world_name'] = azure_env['server_name']

    # in case game_env needs replacement
    yaml_replace(env['game_env'], azure_env)

    # merge env and azure_env
    env.update(azure_env)

    return env

def yaml_replace(yaml, env):
    if isinstance(yaml, dict):
        for key in yaml:
            yaml[key] = yaml_replace(yaml[key], env)
    elif isinstance(yaml, list):
        for i in range(len(yaml)):
            yaml[i] = yaml_replace(yaml[i], env)
    elif isinstance(yaml, str):
        for key in env:
            if key in yaml:
                if isinstance(env[key], str):
                    # replace value in string
                    yaml = yaml.replace(f'${{{key}}}', env[key])
                else:
                    # overwrite string with environment variable of new datatype
                    yaml = env[key]
                    break
    return yaml

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--game', help='game name', required=True)
    args = parser.parse_args()

    game_path = os.path.join('games',args.game)
    game_compose_path = os.path.join('games',args.game,'compose.yaml')

    if not os.path.exists(game_compose_path):
        print(f'Game games/{args.game}/compose.yaml does not exist')
        sys.exit(1)
    
    if not os.path.exists('env.yaml'):
        print(f'Set your env.yaml file (copy env_template.yaml) with your Azure values')
        sys.exit(1)

    # load compose and env.json to get values
    with open(game_compose_path, 'r') as f:
        compose_dir = yaml.safe_load(f)
    with open('env.yaml', 'r') as f:
        azure_env = yaml.safe_load(f)
    
    env = adapt_for_aci(compose_dir, args, azure_env)
    
    # load aci yaml template
    with open('aci_template.yaml', 'r') as f:
        aci = yaml.safe_load(f)
    
    aci = yaml_replace(aci, env)

    with open(os.path.join(game_path,'aci.yaml'), 'w') as f:
        yaml.safe_dump(aci, f)

main()