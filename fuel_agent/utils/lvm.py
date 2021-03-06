# Copyright 2014 Mirantis, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from oslo_log import log as logging

from fuel_agent import errors
from fuel_agent.utils import utils

LOG = logging.getLogger(__name__)


def pvdisplay():
    # unit m means MiB (power of 2)
    output = utils.execute(
        'pvdisplay',
        '-C',
        '--noheading',
        '--units', 'm',
        '--options', 'pv_name,vg_name,pv_size,dev_size,pv_uuid',
        '--separator', ';',
        check_exit_code=[0])[0]
    return pvdisplay_parse(output)


def pvdisplay_parse(output):
    pvs = []
    for line in output.split('\n'):
        line = line.strip()
        if not line:
            continue
        pv_params = line.split(';')
        pvs.append({
            'name': pv_params[0],
            'vg': pv_params[1] or None,
            'psize': utils.parse_unit(pv_params[2], 'm'),
            'devsize': utils.parse_unit(pv_params[3], 'm'),
            'uuid': pv_params[4]
        })
    LOG.debug('Found physical volumes: {0}'.format(pvs))
    return pvs


def pvcreate(pvname, metadatasize=64, metadatacopies=2):
    # check if pv already exists
    if get_first_by_key_value(pvdisplay(), 'name', pvname, False):
        raise errors.PVAlreadyExistsError(
            'Error while creating pv: pv %s already exists' % pvname)
    utils.execute('pvcreate',
                  '--metadatacopies', str(metadatacopies),
                  '--metadatasize', str(metadatasize) + 'm',
                  pvname, check_exit_code=[0])


def pvremove(pvname):
    pv = get_first_by_key_value(pvdisplay(), 'name', pvname)

    # check if pv exists
    if not pv:
        raise errors.PVNotFoundError(
            'Error while removing pv: pv %s not found' % pvname)
    # check if pv is attached to some vg
    if pv['vg'] is not None:
        raise errors.PVBelongsToVGError('Error while removing pv: '
                                        'pv belongs to vg %s' % pv['vg'])
    utils.execute('pvremove', '-ff', '-y', pvname, check_exit_code=[0])


def vgdisplay():
    output = utils.execute(
        'vgdisplay',
        '-C',
        '--noheading',
        '--units', 'm',
        '--options', 'vg_name,vg_uuid,vg_size,vg_free',
        '--separator', ';',
        check_exit_code=[0])[0]
    return vgdisplay_parse(output)


def vgdisplay_parse(output):
    vgs = []
    for line in output.split('\n'):
        line = line.strip()
        if not line:
            continue
        vg_params = line.split(';')
        vgs.append({
            'name': vg_params[0],
            'uuid': vg_params[1],
            'size': utils.parse_unit(vg_params[2], 'm'),
            'free': utils.parse_unit(vg_params[3], 'm', ceil=False)
        })
    LOG.debug('Found volume groups: {0}'.format(vgs))
    return vgs


def _vg_attach_validate(pvnames):
    pvs = pvdisplay()
    # check if all necessary pv exist
    if not set(pvnames).issubset(set([pv['name'] for pv in pvs])):
        raise errors.PVNotFoundError(
            'Error while creating vg: at least one of pv is not found')
    # check if all necessary pv are not already attached to some vg
    if not set(pvnames).issubset(
            set([pv['name'] for pv in pvs if pv['vg'] is None])):
        raise errors.PVBelongsToVGError(
            'Error while creating vg: at least one of pvs is '
            'already attached to some vg')


def vgcreate(vgname, pvname, *args):
    # check if vg already exists
    if get_first_by_key_value(vgdisplay(), 'name', vgname, False):
        raise errors.VGAlreadyExistsError(
            'Error while creating vg: vg %s already exists' % vgname)
    pvnames = [pvname] + list(args)
    _vg_attach_validate(pvnames)
    utils.execute('vgcreate', vgname, *pvnames, check_exit_code=[0])


def vgextend(vgname, pvname, *args):
    # check if vg exists
    if not get_first_by_key_value(vgdisplay(), 'name', vgname, False):
        raise errors.VGNotFoundError(
            'Error while extending vg: vg %s not found' % vgname)
    pvnames = [pvname] + list(args)
    _vg_attach_validate(pvnames)
    utils.execute('vgextend', vgname, *pvnames, check_exit_code=[0])


def vgreduce(vgname, pvname, *args):
    # check if vg exists
    if not get_first_by_key_value(vgdisplay(), 'name', vgname, False):
        raise errors.VGNotFoundError(
            'Error while reducing vg: vg %s not found' % vgname)
    pvnames = [pvname] + list(args)
    # check if all necessary pv are attached to vg
    if not set(pvnames).issubset(
            set([pv['name'] for pv in pvdisplay() if pv['vg'] == vgname])):
        raise errors.PVNotFoundError(
            'Error while reducing vg: at least one of pv is '
            'not attached to vg')
    utils.execute('vgreduce', '-f', vgname, *pvnames, check_exit_code=[0])


def vgremove(vgname):
    # check if vg exists
    if not get_first_by_key_value(vgdisplay(), 'name', vgname, False):
        raise errors.VGNotFoundError(
            'Error while removing vg: vg %s not found' % vgname)
    utils.execute('vgremove', '-f', vgname, check_exit_code=[0])


def lvdisplay():
    output = utils.execute(
        'lvdisplay',
        '-C',
        '--noheading',
        '--units', 'm',
        # NOTE(agordeev): lv_path had been removed from options
        # since versions of lvdisplay prior 2.02.68 don't have it.
        '--options', 'lv_name,lv_size,vg_name,lv_uuid',
        '--separator', ';',
        check_exit_code=[0])[0]
    return lvdisplay_parse(output)


def lvdisplay_parse(output):
    lvs = []
    for line in output.split('\n'):
        line = line.strip()
        if not line:
            continue
        lv_params = line.split(';')
        lvs.append({
            'name': lv_params[0],
            'size': utils.parse_unit(lv_params[1], 'm'),
            'vg': lv_params[2],
            'uuid': lv_params[3],
            # NOTE(agordeev): simulate lv_path with '/dev/$vg_name/$lv_name'
            'path': '/dev/%s/%s' % (lv_params[2], lv_params[0])
        })
    LOG.debug('Found logical volumes: {0}'.format(lvs))
    return lvs


def lvcreate(vgname, lvname, size):
    vg = get_first_by_key_value(vgdisplay(), 'name', vgname)

    # check if vg exists
    if not vg:
        raise errors.VGNotFoundError(
            'Error while creating vg: vg %s not found' % vgname)
    # check if enough space is available
    if vg['free'] < size:
        raise errors.NotEnoughSpaceError(
            'Error while creating lv: vg %s has only %s m of free space, '
            'but at least %s m is needed' % (vgname, vg['free'], size))
    # check if lv already exists
    if next(
        (x for x in lvdisplay() if x['name'] == lvname and x['vg'] == vgname),
        False
    ):
        raise errors.LVAlreadyExistsError(
            'Error while creating lv: lv %s already exists' % lvname)
    # NOTE(agordeev): by default, lvcreate is configured to wipe signature
    # on allocated volume. '--yes' should be passed to avoid waiting for
    # user's confirmation:
    # "WARNING: <signature> signature detected on <device>. Wipe it? [y/n]"
    # FIXME: the version of lvm2 shipped with Ubuntu 14.04 does not support
    # --yes option. fuel-agent should properly decomission the storage
    # (Ubuntu installer does that just fine).
    stdout, stderr = utils.execute('lvcreate', '--help')
    force_opt = '--yes' if '--yes' in stdout else ''
    cmd = 'lvcreate {force_opt} -L {size}m -n {lvname} {vgname}'.format(
        size=size, lvname=lvname, vgname=vgname, force_opt=force_opt)
    utils.execute(*cmd.split(), check_exit_code=[0])


def lvremove(lvpath):
    # check if lv exists
    if not get_first_by_key_value(lvdisplay(), 'path', lvpath):
        raise errors.LVNotFoundError(
            'Error while removing lv: lv %s not found' % lvpath)
    utils.execute('lvremove', '-f', lvpath, check_exit_code=[0])


def lvremove_all():
    for lv in lvdisplay():
        lvremove(lv['path'])


def vgremove_all():
    for vg in vgdisplay():
        vgremove(vg['name'])


def pvremove_all():
    for pv in pvdisplay():
        pvremove(pv['name'])


def get_first_by_key_value(collection, key, value, default=None):
    return next((x for x in collection if x[key] == value), default)
