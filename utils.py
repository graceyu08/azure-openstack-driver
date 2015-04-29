# Copyright 2015 Grace Yu                                                                                                                                            
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
__author__ = 'graceyu'

import string
import random


from azure import WindowsAzureMissingResourceError
from nova.openstack.common import log as logging


LOG = logging.getLogger(__name__)


def generate_random_name(length, prefix=None,
                         chars=string.ascii_lowercase+string.digits):
    string =  ''.join(random.choice(chars) for _ in range(length))
    if prefix:
        string = '-'.join((prefix, string))

    return string


def resource_not_found_handler(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except WindowsAzureMissingResourceError:
            LOG.warning("******Cannot find Azure Resources********************")
            return None

    return inner
