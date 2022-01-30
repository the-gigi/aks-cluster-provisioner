import sys

import functools
import json

import sh
import config


def az(command, format="json"):
    args = command.split() + ["-o", format]
    result = sh.az(args).stdout.decode("utf-8")
    if format == "json":
        result = json.loads(result)
    return result


def is_object(list_cmd: str, name: str) -> bool:
    """Check if an object with a given name exists in the given location

    Note that some objects (e.g. subnets) have a location in which case
    the config's location is used by default. In practice comparing
    the object name only.

    The list command is provided to the az CLI to list all resources
    """
    result = az(list_cmd)
    location = config.location
    for item in result:
        # if item doesn't have a "location" key, use the config.location as default
        if item.get("location", location) == location and item["name"] == name:
            return True

    return False


is_resource_group = functools.partial(is_object, "group list")
is_vnet = functools.partial(is_object, f"network vnet list -g {config.resource_group}")
is_cluster = functools.partial(is_object, f"aks list -g {config.resource_group}")
is_subnet = functools.partial(
    is_object,
    f"""network vnet subnet list 
          -g {config.resource_group}
          --vnet {config.vnet["name"]}""",
)


def create_resource_group():
    """If the resource group doesn't exist yet create it """
    name = config.resource_group
    if is_resource_group(name):
        print(f"Resource group {name} already exists")
        return

    result = az(f"group create -l {config.location} -n {name}")
    print(result)


def create_vnet():
    """Create the VNet with the address prefixes for the nodes and pods subnets"""
    name = config.vnet["name"]
    if is_vnet(name):
        print(f"VNet {name} already exists")
        return

    cmd = f"""network vnet create          
              -n {config.vnet["name"]}     
              -g {config.resource_group}   
              -l {config.location}          
              --address-prefixes {config.vnet["address_prefixes"]}            
    """
    if config.vnet["tags"]:
        cmd += f"--tags {config.vnet['tags']}"
    result = az(cmd)
    print(result)


def create_subnets():
    """Create the nodes and pods subnets"""
    for subnet_type in ("nodes", "pods"):
        name = f"subnet-{config.name}-{subnet_type}"
        if is_subnet(name):
            print(f"Subnet {name} already exists")
            return

        cmd = f"""network vnet subnet create   
                  -n {name}                                
                  -g {config.resource_group}          
                  --vnet-name {config.vnet["name"]}                     
                  --address-prefixes {config.subnets[subnet_type]}           
        """
        result = az(cmd)
        print(result)


def get_subnet_id(name: str):
    vnet_name = config.vnet["name"]
    rg = config.resource_group
    return az(f"network vnet subnet show --vnet-name {vnet_name} -g {rg} -n {name}")[
        "id"
    ]


def create_cluster():
    """Create the cluster using the VNet """
    name = config.cluster["name"]
    if is_cluster(name):
        print(f"Cluster {name} already exists in {config.location}")
        return

    cmd = f"""aks create 
    -n {config.cluster["name"]}
    -g {config.resource_group}
    -l {config.location}   
    --aks-custom-headers {config.cluster["custom_headers"]} 
    --dns-service-ip {config.cluster["dns_service_ip"]}
    --docker-bridge-address {config.cluster["docker_bridge_cidr"]}
    --enable-cluster-autoscaler
    --generate-ssh-keys
    --kubernetes-version {config.cluster["version"]}
    --min-count {config.cluster["min_nodes"]}
    --max-count {config.cluster["max_nodes"]}
    --max-pods {config.cluster["max_pods_per_node"]}
    --network-plugin azure
    --node-count 1    
    --node-vm-size Standard_D2_v4
    --nodepool-name default
    --pod-subnet-id {get_subnet_id("subnet-pods")}
    --service-cidr {config.cluster["service_cidr"]}      
    --vnet-subnet-id {get_subnet_id("subnet-nodes")}    
    --yes          
    """
    result = az(cmd)
    print(result)


def fetch_credentials():
    """ """
    az(
        f"aks get-credentials -g {config.resource_group} -n {config.cluster['name']}",
        format="tsv",
    )


def provision_cluster():
    """ """
    create_resource_group()
    create_vnet()
    create_subnets()
    create_cluster()
    fetch_credentials()


def get_vnet_id(resource_group: str, vnet_name: str) -> str:
    return az(
        f"network vnet show -g {resource_group} -n {vnet_name} --query id", format="tsv"
    )


def peer_vnets(name, resource_group, vnet_name, remote_vnet_id):
    """"""
    az(
        f"""network vnet peering create
           -g {resource_group} 
           -n {name} 
           --vnet-name {vnet_name}
           --remote-vnet {remote_vnet_id}
           --allow-vnet-access"""
    )


def peer_clusters(rg1: str, vnet1: str, rg2: str, vnet2: str):
    """Establish VNet peering between vnet1 and vnet2

    Assume the VNets belong to the same configured resource group
    """
    # Get vnet IDs
    vnet1_id = get_vnet_id(rg1, vnet1)
    vnet2_id = get_vnet_id(rg2, vnet2)

    peer_vnets(f"vnet-peering-{vnet1}-{vnet2}", rg1, vnet1, vnet2_id)
    peer_vnets(f"vnet-peering-{vnet2}-{vnet1}", rg2, vnet2, vnet1_id)


def print_usage():
    usage = """Usage: poetry tun python aks_cluster_provisioner.py <--peer> <rg1> <vnet1> <rg2> <vnet2>
    
    If you run without command-line arguments it will provision a cluster according to
    the config.py file. If you provide the --peer command you must provide also the 
    resource group and vnet name of two AKS clusters.
    """

    usage = "\n".join(line.strip() for line in usage.split("\n"))
    print(usage)


def main(args):
    if len(args) == 0:
        provision_cluster()
        return

    if len(args) != 5 or args[0] != "--peer":
        print_usage()
        return

    peer_clusters(*args[1:])


if __name__ == "__main__":
    main(sys.argv[1:])
