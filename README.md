# compose2aci
Converting Game Docker Compose files to Azure Container Instances, and instructions to deploy to Azure.

## intro
A lot of folks have $150/month azure dev credits so I made this repo for people to easily deploy their own game servers. Unfortunately, Azure lost direct Docker Compose deployment - but I created this script to easily convert Docker Compose yaml files (easily found for most online hostable games) into Azure Container Instance Yaml Files and instructions below to easily deploy each server attached to Fileshare storage.

## Setup
### Pre-Reqs:
1. [Install Azure CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli)
2. [Install Python]()

### Instructions
1. pip install -r requirements.txt
3. Create a fileshare storage in Azure with the following command:
```bash
g=<resouce_group>
l=<location>
s=<storage_account_name>
az group create --name $g --location $l
az storage account create -n $s -g $g --sku Premium_LRS --kind FileStorage
```
4. get storage account access key:
```bash
az storage account keys list --account-name $s
sp=<key>
```
5. Copy env_template.yaml into env.yaml and fill out all fields:
```yaml
# game server name + password
server_name: <your_server_name>
server_password: <your_server_password>
location: <your_location>
resource_group: <your_resource_group>
# storage account name + pass
storage_account_name: <your_storage_account_name>
storage_account_key: <your_storage_account_key>
# dockerhub username + pass (to get around anonymous azure rate limiting from dockerhub)
dockerhub_username: <your_dockerhub_username>
dockerhub_password: <your_dockerhub_password>

```
6. Per each game, convert each game docker compose yaml into ACI yaml, create fileshare for that game and deploy it
```bash
game=<game>
python3 compose2aci.py --game $game
az storage share create --name $game --quota 100 --account-name $s --account-key $sp
az container create --resource-group $g --file games/$game/aci.yaml
```

7. Check ACI FQDN (should be setup automatically to be {server_name}-{game}.{location}.azurecontainer.io) and connect!
```bash
az container show --resource-group $g --name $game --query ipAddress.fqdn
```

# Containers

each subdir here should contain a docker compose file for deploying a docker container to your ACI

## TESTED
1. valheim: https://github.com/lloesche/valheim-server-docker/blob/main/docker-compose.yaml
2. satisfactory - DOESN'T WORK  FOR ACI DUE TO TCP/UDP ON THE SAME PORTS, VM GUIDE HERE: https://www.reddit.com/r/SatisfactoryGame/comments/13dlggp/host_a_dedicated_server_on_azure_the_easy_way/
3. minecraft: https://www.docker.com/blog/deploying-a-minecraft-docker-server-to-the-cloud/
4. enshrouded: https://github.com/mornedhels/enshrouded-server - Should work but be wary of high resource requests and default quota limits may need to be upgraded

## UNTESTED
1. palworld: https://github.com/thijsvanloef/palworld-server-docker/blob/main/docker-compose.yml

## Adding new containers
I welcome you to please add new docker compose containers!

Some instructions:
* put them under games/<game_name>/compose.yaml
* make sure that cpu+memory (in numeric format) are requested - i normally have to adjust.
* test the conversion script and try to deploy - there may be some small issues to resolve in either compose file or even the adaption script.

## Future
* Potentially use Terraform so we can create templates for all cloud provider instead of just Azure
* Be on the lookout for a discord bot docker that you can deploy and have your friends start/stop your hosted game servers.