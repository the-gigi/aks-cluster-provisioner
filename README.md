# Overview

The AKS cluster provisioner provisions [AKS](https://azure.microsoft.com/en-us/services/kubernetes-service/) clusters :-)

It uses the [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/) to configure VNet and subnets before creating the cluster itself. You need to have an Azure account and be a subscription owner. 

All the configuration options are provided through a config file.

In addition, it can also peer Vnets of existing clusters to allow cross-cluster private communication.

This is recommended for exploring and creating throwaway clusters that you experiment with and discard soon after. Use your favorite infrastructure as code to provision "real" clusters.


# Requirements

This is a Python 3 program.

Make sure you have Python 3 installed:

```
$ brew install python
```  

Install `pyenv`:

```
brew install pyenv
```

Install `poetry`:

```
curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/install-poetry.py | python -
```

Set up a virtual environment for the project:

```
pyenv install 3.9.6
pyenv local 3.9.6
poetry install 
```

Install Azure-CLI:

```
brew update && brew install azure-cli
```

Install Azure-CLI dynamic provisioning extension:

Follow the instructions here:
[Install the aks-preview Azure CLI](https://docs.microsoft.com/en-us/azure/aks/configure-azure-cni#install-the-aks-preview-azure-cli)

You also need to run this command to allow enabling CSI drivers:

```
az feature register --namespace "Microsoft.ContainerService" --name "EnableAzureDiskFileCSIDriver"
```

This takes a few minutes. Verify the registration was successful by running:

```
az feature list -o table --query "[?contains(name, 'Microsoft.ContainerService/EnableAzureDiskFileCSIDriver')].{Name:name,State:properties.state}"
```

# Usage

## Provisioning AKS cluster
Copy the `sample_config.py` file into a file called `config.py` and 
modify as necessary.

Then run:

```
poetry run python aks_cluster_provisioner.py
```

The program will create a resource group, VNet, subnets and the cluster itself.

You can also bring your own resource group, VNet and subnets. 

The code is idempotent. If some resource already exists it will just keep going.

Once the cluster is ready, the program will fetch its credentials and update your ~/.kube/config file.

## Peering VNets

If you want to peer the VNets of two existing clusters (just any two Vnets).

Have the resource group and VNet name of each clusters ready and run:

```
poetry python run aks_cluster_provisioner.py --peer <rg1> <vnet1> <rg2> <vnet2>
```

## Clean up

To get rid of your cluster and all the associated resources just delete the resource group you define in `config.py`

```
az group delete -n <resource group>
```
