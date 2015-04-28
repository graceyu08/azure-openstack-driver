# Azure Driver for OpenStack

This is the Azure Driver for OpenStack as Hybrid cloud solution.
Using OpenStack Horizon to operate and manage both private and public cloud resources.
This driver is implemented on OpenStack Icehouse version, and has not been tested on
other OpenStack versions.

## What you need to install

- Openstack Icehouse
- Python 2.7
- azure-sdk-for-python (pip install azure)
- Make sure you have valid Azure account

## How to setup

1. `# cd <openstack_installation_dir>/nova/virt`
2. `# git clone https://github.com/graceyu08/azure-openstack-driver.git azure`
3. `# vi /etc/nova/nova.conf`

       [DEFAULT]
       compute_driver=nova.virt.azure.AzureDriver

       [conductor]
       use_local=True

       [azuredriver]
       subscription_id=<your-subscriptionId>
       cert_file=<path-of-certificate-file>

4. Restart compute service.
