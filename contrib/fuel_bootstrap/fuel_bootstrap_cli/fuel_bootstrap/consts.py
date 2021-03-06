# -*- coding: utf-8 -*-

#    Copyright 2015 Mirantis, Inc.
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


# These consts shouldn't be configured

# There is a possibility to specify custom config file with the key --config
CONFIG_FILE = "/etc/fuel-bootstrap-cli/fuel_bootstrap_cli.yaml"
METADATA_FILE = "metadata.yaml"
COMPRESSED_CONTAINER_FORMAT = "tar.gz"
UNCOMPRESSED_CONTAINER_FORMAT = "directory"
ROOTFS = {'name': 'rootfs',
          'mask': 'rootfs',
          'compress_format': 'xz',
          'uri': 'http://127.0.0.1:8080/bootstraps/{uuid}/root.squashfs',
          'format': 'ext4',
          'container': 'raw'}
BOOTSTRAP_MODULES = [
    {'name': 'kernel',
     'mask': 'kernel',
     'uri': 'http://127.0.0.1:8080/bootstraps/{uuid}/vmlinuz'},
    {'name': 'initrd',
     'mask': 'initrd',
     'compress_format': 'xz',
     'uri': 'http://127.0.0.1:8080/bootstraps/{uuid}/initrd.img'},
    ROOTFS
]

IMAGE_DATA = {'/': ROOTFS}

# FIXME(azvyagintsev) bug: https://bugs.launchpad.net/fuel/+bug/1525882
# Nailgun\astute should support API call to change their bootstrap profile
# While its not implemented, we need astute.yaml file to perform
# bootstrap_image._activate_dockerized process
ASTUTE_CONFIG_FILE = "/etc/fuel/astute.yaml"
# FIXME(azvyagintsev) bug: https://bugs.launchpad.net/fuel/+bug/1525857
DISTROS = {'ubuntu': {'cobbler_profile': 'ubuntu_bootstrap',
                      'astute_flavor': 'ubuntu'}}
COBBLER_MANIFEST = '/etc/puppet/modules/fuel/examples/cobbler.pp'
ASTUTE_MANIFEST = '/etc/puppet/modules/fuel/examples/astute.pp'
