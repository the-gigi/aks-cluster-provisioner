name = "test"
location = "westus3"  # run `az account list-locations` to see all locations
environment = "development"  # development, staging or production
suffix = "001"
resource_group = f"rg-{name}-{environment}-{location}-{suffix}"

subnets = dict(
    nodes="10.64.16.0/21",
    pods="10.49.0.0/16",
)

vnet = dict(
    name=f"vnet-{name}-{environment}-{location}-{suffix}",
    address_prefixes=f"{subnets['nodes']} {subnets['pods']}",
    tags="",
)

cluster = dict(
    name=f"aks-{name}-{environment}-{location}-{suffix}",
    service_cidr="172.16.0.0/16",
    dns_service_ip="172.16.0.10",
    docker_bridge_cidr="172.17.0.1/16",  # the default, just make it explicit
    min_nodes=1,
    max_nodes=3,
    max_pods_per_node="250",
    version="1.20.9",
    custom_headers="EnableAzureDiskFileCSIDriver=true",
)
