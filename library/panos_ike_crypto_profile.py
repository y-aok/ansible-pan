#!/usr/bin/env python

from __future__ import absolute_import, division, print_function
__metaclass__ = type

#  Copyright 2017 Palo Alto Networks, Inc
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: panos_ike_crypto_profile
short_description: Configures IKE Crypto profile on the firewall with subset of settings
description:
    - Use the IKE Crypto Profiles page to specify protocols and algorithms for identification, authentication, and
    - encryption (IKEv1 or IKEv2, Phase 1).
author: "Ivan Bojer (@ivanbojer)"
version_added: "2.8"
requirements:
    - pan-python can be obtained from PyPI U(https://pypi.python.org/pypi/pan-python)
    - pandevice can be obtained from PyPI U(https://pypi.python.org/pypi/pandevice)
notes:
    - Checkmode is not supported.
    - Panorama is NOT supported.
options:
    ip_address:
        description:
            - IP address (or hostname) of PAN-OS device being configured.
        required: true
    username:
        description:
            - Username credentials to use for auth unless I(api_key) is set.
        default: "admin"
    password:
        description:
            - Password credentials to use for auth unless I(api_key) is set.
        required: true
    api_key:
        description:
            - API key that can be used instead of I(username)/I(password) credentials.
    state:
        description:
            - Create or remove IKE profile.
        choices: ['present', 'absent']
        default: 'present'
    commit:
        description:
            - Commit configuration if changed.
        default: true
    name:
        description:
            - Name for the profile.
        required: true
    dh_group:
        description:
            - Specify the priority for Diffie-Hellman (DH) groups.
        default: group2
        choices: ['group1', 'group2', 'group5', 'group14', 'group19', 'group20']
        aliases: dhgroup
    authentication:
        description:
            - Authentication hashes used for IKE phase 1 proposal.
        choices: ['md5', 'sha1', 'sha256', 'sha384', 'sha512']
        default: sha1
    encryption:
        description:
            - Encryption algorithms used for IKE phase 1 proposal.
        choices: ['des', '3des', 'aes-128-cbc', 'aes-192-cbc', 'aes-256-cbc']
        default: ['aes-256-cbc', '3des']
    lifetime_seconds:
        description:
            - IKE phase 1 key lifetime in seconds.
        aliases: lifetime_sec
    lifetime_minutes:
        description:
            - IKE phase 1 key lifetime in minutes.
    lifetime_hours:
        description:
            - IKE phase 1 key lifetime in hours.  If no key lifetime is
              specified, default to 8 hours.
    lifetime_days:
        description:
            - IKE phase 1 key lifetime in days.
'''

EXAMPLES = '''
- name: Add IKE crypto config to the firewall
    panos_ike_crypto_profile:
      ip_address: '{{ ip_address }}'
      username: '{{ username }}'
      password: '{{ password }}'
      state: 'present'
      name: 'vpn-0cc61dd8c06f95cfd-0'
      dh_group: ['group2']
      authentication: ['sha1']
      encryption: ['aes-128-cbc']
      lifetime_seconds: '28800'
'''

RETURN = '''
# Default return values
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import get_exception

try:
    from pandevice import base
    from pandevice.errors import PanDeviceError
    from pandevice import network

    HAS_LIB = True
except ImportError:
    HAS_LIB = False


# def get_devicegroup(device, devicegroup):
#     dg_list = device.refresh_devices()
#     for group in dg_list:
#         if isinstance(group, pandevice.panorama.DeviceGroup):
#             if group.name == devicegroup:
#                 return group
#     return False


def main():
    argument_spec = dict(
        ip_address=dict(required=True),
        password=dict(no_log=True),
        username=dict(default='admin'),
        api_key=dict(no_log=True),
        state=dict(default='present', choices=['present', 'absent']),
        name=dict(required=True),
        dh_group=dict(
            type='list',
            default=['group2'],
            choices=[
                'group1', 'group2', 'group5', 'group14', 'group19', 'group20'
            ],
            aliases=['dhgroup']
        ),
        authentication=dict(
            type='list',
            choices=[
                'md5', 'sha1', 'sha256', 'sha384', 'sha512'
            ],
            default=['sha1']
        ),
        encryption=dict(
            type='list',
            choices=[
                'des', '3des', 'aes-128-cbc', 'aes-192-cbc', 'aes-256-cbc'
            ],
            default=['aes-256-cbc', '3des']
        ),
        lifetime_seconds=dict(type='int', aliases=['lifetime_sec']),
        lifetime_minutes=dict(type='int'),
        lifetime_hours=dict(type='int'),
        lifetime_days=dict(type='int'),
        commit=dict(type='bool', default=True)
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=False,
        required_one_of=[
            ['api_key', 'password'],
        ],
        mutually_exclusive=[
            [
                'lifetime_seconds',
                'lifetime_minutes',
                'lifetime_hours',
                'lifetime_days'
            ]
        ]
    )
    if not HAS_LIB:
        module.fail_json(msg='Missing required libraries.')

    ip_address = module.params['ip_address']
    password = module.params['password']
    username = module.params['username']
    api_key = module.params['api_key']
    state = module.params['state']
    name = module.params['name']
    dh_group = module.params['dh_group']
    authentication = module.params['authentication']
    encryption = module.params['encryption']
    lifetime_seconds = module.params['lifetime_seconds']
    lifetime_minutes = module.params['lifetime_minutes']
    lifetime_hours = module.params['lifetime_hours']
    lifetime_days = module.params['lifetime_days']
    commit = module.params['commit']

    # Reflect GUI behavior.  Default is 8 hour key lifetime if nothing else is
    # specified.
    if not any([
        lifetime_seconds, lifetime_minutes, lifetime_hours, lifetime_days
    ]):
        lifetime_hours = 8

    ike_crypto_prof = network.IkeCryptoProfile(
        name=name,
        dh_group=dh_group,
        authentication=authentication,
        encryption=encryption,
        lifetime_seconds=lifetime_seconds,
        lifetime_minutes=lifetime_minutes,
        lifetime_hours=lifetime_hours,
        lifetime_days=lifetime_days
    )

    # Create the device with the appropriate pandevice type
    device = base.PanDevice.create_from_device(ip_address, username, password, api_key=api_key)

    changed = False
    try:
        # fetch all crypto profiles
        profiles = network.IkeCryptoProfile.refreshall(device)
        if state == "present":
            device.add(ike_crypto_prof)
            for p in profiles:
                if p.name == ike_crypto_prof.name:
                    if not ike_crypto_prof.equal(p):
                        ike_crypto_prof.apply()
                        changed = True
                    break
            else:
                ike_crypto_prof.create()
                changed = True
        elif state == "absent":
            ike_crypto_prof = device.find(name, network.IkeCryptoProfile)
            if ike_crypto_prof:
                ike_crypto_prof.delete()
                changed = True
        else:
            module.fail_json(msg='[%s] state is not implemented yet' % state)
    except PanDeviceError:
        exc = get_exception()
        module.fail_json(msg=exc.message)

    if commit and changed:
        device.commit(sync=True)

    module.exit_json(msg='IKE Crypto profile config successful.', changed=changed)


if __name__ == '__main__':
    main()
