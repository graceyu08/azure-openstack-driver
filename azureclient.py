
import utils

#from nova.openstack.common import log as logging

from azure.servicemanagement import CaptureRoleAsVMImage
from azure.servicemanagement import LinuxConfigurationSet
from azure.servicemanagement import OSVirtualHardDisk
from azure.servicemanagement import ServiceManagementService

# Storage
CONTAINER = 'os-image'
WINDOWS_BLOB_URL = 'blob.core.windows.net'

# Linux
LINUX_USER = 'azureuser'
LINUX_PASS = 'mypassword'

# SSH Keys
#LOG = logging.getLogger(__name__)


class AzureServicesManager:
    # Storage
    container = 'vhds'
    windows_blob_url = 'blob.core.windows.net'

    # Linux
    linux_user = 'azureuser'
    linux_pass = 'Test123#'
    location = 'West US'
    # SSH Keys

    def __init__(self, subscription_id, cert_file):
        self.subscription_id = subscription_id
        self.cert_file = cert_file
        self.sms = ServiceManagementService(self.subscription_id, self.cert_file)

    @property
    def sms(self):
         return self.sms

    def list_locations(self):
        locations = self.sms.list_locations()
        for location in locations:
            print location

    def list_images(self):
        return self.sms.list_os_images()

    def delete_hosted_service(self, service_name):
        res = self.sms.check_hosted_service_name_availability(service_name)
        if not res.result:
            return

        self.sms.delete_hosted_service(service_name)

    def create_hosted_service(self, os_user, service_name=None, random=False):
        if not service_name:
            service_name = self.generate_cloud_service_name(os_user, random)

        available = False

        while not available:
            res = self.sms.check_hosted_service_name_availability(service_name)
            if not res.result:
                service_name = self.generate_cloud_service_name(os_user,
                                                                random)
            else:
                available = True

        self.sms.create_hosted_service(service_name=service_name,
                                       label=service_name,
                                       location='West US')

        return service_name

    def create_vm(self, service_name, vm_name, image_name, flavor):
        #image = self._get_azure_image(image_name)
        image_name='5112500ae3b842c8b9c604889f8753c3__OpenLogic-CentOS-65-20150128'
        media_link = self._get_media_link(vm_name)
        # Linux VM configuration
        hostname = '-'.join((vm_name, 'host'))
        linux_config = LinuxConfigurationSet(hostname,
                                             self.linux_user,
                                             self.linux_pass,
                                             True)

        # Hard disk for the OS
        os_hd = OSVirtualHardDisk(image_name, media_link)

        #role_size = self._get_role_size(flavor)
        role_size = 'Small'

        # Create vm
        result = self.sms.create_virtual_machine_deployment(
            service_name=service_name,  deployment_name=vm_name,
            deployment_slot='production', label=vm_name,
            role_name=vm_name, system_config=linux_config,
            os_virtual_hard_disk=os_hd,
            role_size=role_size
        )
        request_id = result.request_id
        #self.sms.wait_for_operation_status(request_id, timeout=3000)

        return {
            'request_id': request_id,
            'media_link': media_link
        }

    def delete_vm(self, service_name, vm_name):
        resp = self.sms.delete_deployment(service_name, vm_name, True)
        self.sms.wait_for_operation_status(resp.request_id)
        result = self.sms.delete_hosted_service(service_name)
        return result

    def generate_cloud_service_name(self, os_user=None, random=False):
        if random:
            return utils.generate_random_name(10)

        return '-'.join((os_user, utils.generate_random_name(6)))

    def get_vm_info(self, service_name, vm_name):
        vm_info = {}
        deploy_info = self.sms.get_deployment_by_name(service_name, vm_name)
        if deploy_info and deploy_info.role_instance_list:
            vm_info = deploy_info.role_instance_list[0].__dict__

        return vm_info

    def list_vms(self):
        vm_list = []
        services = self.sms.list_hosted_services()
        for service in services:
            deploys = service.deployments
            if deploys and deploys.role_instance_list:
                vm_name = deploys.role_instance_list[0].instance_name
                vm_list.append(vm_name)

        return vm_list

    def power_on(self, service_name, vm_name):
        resp = self.sms.start_role(service_name, vm_name, vm_name)
        return resp.request_id

    def power_off(self, service_name, vm_name):
        resp = self.sms.shutdown_role(service_name, vm_name, vm_name)
        return resp.request_id

    def soft_reboot(self, service_name, vm_name):
        resp = self.sms.restart_role(service_name, vm_name, vm_name)
        return resp.request_id

    def hard_reboot(self, service_name, vm_name):
        resp = self.sms.reboot_role_instance(service_name, vm_name, vm_name)
        return resp.request_id

    def attach_volume(self, service_name, vm_name, size, lun):
        disk_name = utils.generate_random_name(5, vm_name)
        media_link = self._get_media_link(vm_name, disk_name)

        self.sms.add_data_disk(service_name,
                               vm_name,
                               vm_name,
                               lun,
                               host_caching='ReadWrite',
                               media_link=media_link,
                               disk_name=disk_name,
                               logical_disk_size_in_gb=size)

    def detach_volume(self, service_name, vm_name, lun):
        self.sms.delete_data_disk(service_name, vm_name, vm_name, lun, True)

    def get_available_lun(self, service_name, vm_name):
        try:
            role = self.sms.get_role(service_name, vm_name, vm_name)
        except Exception:
            return 0

        disks = role.data_virtual_hard_disks
        luns = [disk.lun for disk in disks].sort()

        for i in range(1, 16):
            if i not in luns:
                return i

        return None

    def snapshot(self, service_name, vm_name, image_id):
        image_desc = 'Snapshot for image %s' % vm_name
        image = CaptureRoleAsVMImage('Specialized', image_id, image_id,
                                     image_desc, 'english')
        resp = self.sms.capture_vm_image(service_name, vm_name, vm_name, image)

        self.sms.wait_for_operation_status(resp.request_id)

    def _get_media_link(self, vm_name, filename=None, storage_account=None):
        """ The MediaLink should be constructed as:
        https://<storageAccount>.<blobLink>/<blobContainer>/<filename>.vhd
        """
        if not storage_account:
            storage_account = self._get_or_create_storage_account()

        container = self.container
        filename = vm_name if filename is None else filename
        blob = vm_name + '-' + filename + '.vhd'
        media_link = "http://%s.%s/%s/%s" % (storage_account,
                                             self.windows_blob_url,
                                             container, blob)

        return media_link

    def _get_or_create_storage_account(self):
        account_list = self.sms.list_storage_accounts()

        if account_list:
            return account_list[-1].service_name

        storage_account = utils.generate_random_name(10)
        description = "Storage account %s description" % storage_account
        label = storage_account + 'label'
        self.sms.create_storage_account(storage_account,
                                        description,
                                        label,
                                        location=self.location)

        return storage_account

    def _get_role_size(self, flavor):
        pass

    def _get_azure_image(self, image_name):
        pass

    def _wait_for_operation(self, request_id, timeout=3000,
                            failure_callback=None,
                            failure_callback_kwargs=None):
        try:
            self.sms.wait_for_operation_status(request_id, timeout=timeout)
        except Exception as ex:
            if failure_callback and failure_callback_kwargs:
                failure_callback(**failure_callback_kwargs)

            raise ex
