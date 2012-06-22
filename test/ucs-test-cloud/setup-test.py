#!/usr/bin/python
# vim:set expandtab shiftwidth=4 tabstop=4:
# pylint: disable-msg=C0103
'''Create ucs-test instance in Amazon EC2.'''
import sys
import os
import logging
import boto
from boto.ec2 import regions
from time import time, sleep
import paramiko
import string  # pylint: disable-msg=W0402
from random import choice
from select import select
from socket import error as socket_error
from ConfigParser import ConfigParser, Error as ConfigError
from pipes import quote as escape_shell

INI = '~/ucs-test.ini'
INSTANCES = 1

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger('ec2')
logger.setLevel(logging.DEBUG)

# Read secrets
logger.debug('Reading %s...', INI)
cfg = ConfigParser()
cfg.read(os.path.expanduser(INI))
aws_access_key_id = cfg.get('aws', 'access_key')
aws_secret_access_key = cfg.get('aws', 'secret_key')
ec2_region = cfg.get('ec2', 'region')
ec2_security_group = cfg.get('ec2', 'security_group')
ec2_keypair = cfg.get('ec2', 'keypair')
ec2_instance_type = cfg.get('ec2', 'instance_type')
ec2_ami = cfg.get('ec2', 'ami')
if cfg.has_option('ec2', 'reuse'):
    ec2_reuse = cfg.get('ec2', 'reuse')
else:
    ec2_reuse = None
s3_repo = cfg.get('s3', 'repo')
timeout = int(cfg.get('ec2', 'timeout'))
aws_cfg = {
        'aws_access_key_id': aws_access_key_id,
        'aws_secret_access_key': aws_secret_access_key,
        }

private_key = os.path.expanduser('~/.ssh/%s.pem' % (ec2_keypair,))
env_vars = ('JOB_NAME', 'BUILD_NUMBER')
user_data = '\n'.join(['%s=%s' % (v, os.getenv(v, '')) for v in env_vars])
try:
    ressources = cfg.get('test', 'ressources')
except ConfigError:
    ressources = os.getenv('ressources', os.path.expanduser('~'))

# Create instance
logger.debug('Connecting %s...', ec2_region)
for region in regions(**aws_cfg):
    if region.name == ec2_region:
        aws_cfg['region'] = region
        break
else:
    logger.error("Region %s not found.", ec2_region)
    sys.exit(1)

ec2 = boto.connect_ec2(**aws_cfg)
ami = ec2.get_image(ec2_ami)
logger.info('AMI-Id: %s', ami.id)
if ec2_reuse:
    logger.info('Reusing previous instance %s', ec2_reuse)
    reservation = ec2.get_all_instances(instance_ids=[ec2_reuse])[0]
else:
    logger.info('Creating new reservation')
    reservation = ami.run(min_count=INSTANCES,
            max_count=INSTANCES,
            key_name=ec2_keypair,
            user_data=user_data,
            security_groups=[ec2_security_group],
            instance_type=ec2_instance_type,
            #placement=
            instance_initiated_shutdown_behavior='terminate',  # 'save'
            )
logger.info('Reservation-Id: %s', reservation.id)
instance = reservation.instances[0]  # FIXME: Handle multiple instances
# The instance might not yet exist. Updates to it can generate an
# "InvalidInstanceID.NotFound" error. Delay adding tags until later.
logger.info('Instance-Id: %s', instance.id)

start = now = time()
while now - start < timeout:
    if instance.state == 'running':
        break
    if instance.state == 'pending':
        logger.debug('Pending %d...', timeout - now + start)
    sleep(10)
    try:
        instance.update()
    except boto.exception.EC2ResponseError, ex:
        for error in ex.errors:
            logger.debug('Error code: %r', error.error_code)
            if error.error_code == 'InvalidInstanceID.NotFound':
                break
        else:
            logger.exception('Unexcpected error waiting for instance: %s', ex)
            raise
    now = time()
else:
    logger.error('Timeout waiting for instance')
    sys.exit(1)

instance.add_tag('Name', 'ucs-test-%s' % (instance.id,))
instance.add_tag('class', 'ucs-test')
for var in env_vars:
    instance.add_tag(var.lower(), os.getenv(var, ''))

logger.info('Public DNS: %s', instance.public_dns_name)
logger.info('Public IP: %s', instance.ip_address)
logger.info('Private DNS: %s', instance.private_dns_name)
logger.info('Private IP: %s', instance.private_ip_address)

# Calculate instance data
fqdn = instance.public_dns_name
hostname, domainname = fqdn.split('.', 1)
ip_tuple = hostname.split('-')[1:5]
hostname = 'ip%s' % (''.join(['%02x' % (int(_),) for _ in ip_tuple]))
windom = domainname.split('.', 1)[0].upper()

# Create password for instance
chars = string.letters + string.digits
password = ''.join(choice(chars) for _ in xrange(12))
logger.info('Password: %s', password)

# Open SSH connection
logger.debug('Connecting %s...', instance.public_dns_name)
client = paramiko.SSHClient()
client.load_system_host_keys()
client.set_missing_host_key_policy(paramiko.WarningPolicy())
allowed_failures = 3
start = now = time()
while now - start < timeout and allowed_failures > 0:
    try:
        client.connect(instance.public_dns_name,
                port=22,
                username='root',
                key_filename=private_key)
        break
    except socket_error, e:
        logger.debug('Pending %d...', timeout - now + start)
        sleep(10)
        now = time()
    except paramiko.AuthenticationException, e:
        logger.debug('Authentication failed %d...', timeout - now + start)
        allowed_failures -= 1
        sleep(10)
        now = time()
else:
    logger.error('Timeout waiting to connect')
    sys.exit(2)

# Get required network configuration for profile from instance
logger.debug('Querying network configuration...')
cmd = "univention-config-registry search --brief --non-empty " + \
    "'^interfaces/eth0/|^dns/forwarder|^gateway|^nameserver'"
f_stdin, f_stdout, f_stderr = client.exec_command(cmd)
f_stdin.close()
netconf = f_stdout.read()
f_stdout.close()
f_stderr.close()

# Create profile
logger.debug('Creating profile...')
sftp = client.open_sftp()
profile = sftp.file('/var/cache/univention-system-setup/profile', 'w')
try:
    print >> profile, "timezone='Europe/Berlin'"
    print >> profile, "locale_default='de_DE.UTF-8:UTF-8'"
    print >> profile, "locales='de_DE.UTF-8:UTF-8'"
    print >> profile, "language='de'"
    print >> profile, "keymap='de-latin1'"
    print >> profile, ''
    print >> profile, "call_master_joinscripts='true'"
    print >> profile, "system_role='domaincontroller_master'"
    print >> profile, 'domainname="%s"' % (domainname,)
    print >> profile, 'hostname="%s"' % (hostname,)
    print >> profile, 'ldap/base="dc=%s"' % (domainname.replace('.', ',dc='),)
    print >> profile, 'fqdn="%s.%s"' % (hostname, domainname)
    print >> profile, 'windows/domain="%s"' % (windom,)
    print >> profile, 'root_password="%s"' % (password,)
    print >> profile, ''
    print >> profile, "#update_system_after_installation='true'"
    print >> profile, "#cdrom_device=''"
    print >> profile, "disks='/dev/xvda'"
    print >> profile, "boot_partition='/dev/xdva1'"
    print >> profile, "bootloader_record='/dev/xvda'"
    print >> profile, ''
    print >> profile, 'packages=""'
    print >> profile, '#components="univention-s4-connector"'
    print >> profile, '#packages_install="univention-s4-connector"'
    print >> profile, 'packages_remove=""'
    print >> profile, ''
    for l in netconf.splitlines():
        key, value = l.split(': ', 1)
        if '/fallback/' in key:
            continue
        print >> profile, '%s="%s"' % (key, value)
finally:
    profile.close()

def ssh_exec(command, idle_timeout=10*60):
    '''Execute command using ssh and output stdout, stderr.'''
    transport = client.get_transport()
    session = transport.open_session()
    try:
        session.exec_command(command)
        while idle_timeout > 0:
            r_list, _w_list, _e_list = select([session], [], [], 10)
            if r_list:
                if session.recv_ready():
                    data = session.recv(4096)
                    sys.stdout.write(data)
                    continue
                elif session.recv_stderr_ready():
                    data = session.recv_stderr(4096)
                    sys.stderr.write(data)
                    continue
                else:
                    pass  # EOF
            else:
                idle_timeout -= 10
            if session.exit_status_ready():
                break
        if session.exit_status != 0:
            logger.error('*** Failed %d: %s', session.exit_status, command)
    finally:
        session.close()
    return session.exit_status

# Setup instance
logger.debug('Running setup...')
cmd = '/usr/lib/univention-system-setup/scripts/setup-join.sh'
rv = ssh_exec(cmd)

# Configure instance
logger.debug('Configuring UCR...')
try:
    config = cfg.items('ucr')
except ConfigError:
    pass
else:
    if config:
        cmd = 'univention-config-registry set ' + ' '.join(
                ('%s=%s' % (escape_shell(key), escape_shell(value)) for
                    key, value in config))
        rc = ssh_exec(cmd)

# Update instance
logger.debug('Running update...')
cmd = 'univention-upgrade net --ignoressh --ignoreterm --noninteractive' + \
        ' </dev/null'
rv = ssh_exec(cmd, idle_timeout=30*60)  # FIXME: larger timeout for Bug #27665

# Setup ucs-test repository
logger.debug('Configuring repositories...')
apt_list = sftp.file('/etc/apt/sources.list.d/30_ucs-test.list', 'w')
try:
    print >> apt_list, 'deb %s repo/' % (s3_repo,)
finally:
    apt_list.close()
cmd = 'univention-config-registry set repository/online/unmaintained=yes ' + \
        'update/secure_apt=no'
rv = ssh_exec(cmd)
cmd = 'apt-get update </dev/null'
rv = ssh_exec(cmd)
assert rv == 0

# Remove old kernels
logger.debug('Pruning old kernels...')
cmd = """aptitude remove '
    ?installed
    ?name(linux-image-*)
    !?name(linux-image-'$(uname -r)')
    !?reverse-Depends(
        ?name(univention-kernel-image-*)
        ?version(TARGET)
    )'""".replace('\n', ' ')
rv = ssh_exec(cmd)

# Install ucs-test
logger.debug('Installing ucs-test...')
cmd = 'apt-get install -y --force-yes ucs-test rungetty </dev/null'
rv = ssh_exec(cmd)
assert rv == 0

fn = os.path.join(ressources, 'smtp-send.py')
attributes = sftp.put(fn, 'smtp-send.py')
sftp.chmod('smtp-send.py', 0700)

fn = os.path.join(ressources, 'run-ucs-test.sh')
attributes = sftp.put(fn, 'run-ucs-test.sh')
sftp.chmod('run-ucs-test.sh', 0700)

# Only transfer [mail] and [test] sections; strip credentials!
for section in cfg.sections():
    if section not in ('mail', 'test'):
        cfg.remove_section(section)
ini_file = sftp.file('ucs-test.ini', 'w')
try:
    cfg.write(ini_file)
finally:
    ini_file.close()
sftp.chmod('ucs-test.ini', 0600)

# Remove temporary APT configuration again
cmd = 'rm -f /etc/apt/sources.list.d/*.list ; ' + \
        'univention-config-registry set repository/online/unmaintained=no ' + \
        'update/secure_apt=yes'
rv = ssh_exec(cmd)


# Setup ucs-test to run on reboot
logger.debug('Configuring ucs-test...')
cmd = 'echo "a8:2:once:/sbin/rungetty tty8 -u root -g root -d 10 ' + \
        'bash /root/run-ucs-test.sh" >>/etc/inittab'
rv = ssh_exec(cmd)
assert rv == 0
logger.debug('Scheduling reboot...')
cmd = '/sbin/shutdown -r 1'
rv = ssh_exec(cmd)

logger.info('Done.')
sftp.close()
client.close()
