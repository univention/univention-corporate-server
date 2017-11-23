import subprocess
from samba.auth import system_session
from samba.samdb import SamDB
from samba.param import LoadParm
import ldb
import time
import socket
import re
import contextlib
import sqlite3

from univention.testing.utils import package_installed
import univention.config_registry as config_registry

CONNECTOR_WAIT_INTERVAL = 12
CONNECTOR_WAIT_SLEEP = 5
CONNECTOR_WAIT_TIME = CONNECTOR_WAIT_SLEEP * CONNECTOR_WAIT_INTERVAL


@contextlib.contextmanager
def password_policy(complexity=False, minimum_password_age=0):
    if not package_installed('univention-samba4'):
        print 'skipping samba password policy adjustment'
        yield
        return
    complexity = 'on' if complexity else 'off'
    minimum_password_age = str(minimum_password_age)
    min_pwd_age = int(subprocess.check_output('samba-tool domain passwordsettings show | grep "Minimum password age" | sed s/[^0-9]*/""/', shell=True).strip())
    pwd_complexity = subprocess.check_output('samba-tool domain passwordsettings show | grep complexity | sed "s/Password complexity: //"', shell=True).strip()
    if complexity != pwd_complexity or minimum_password_age != min_pwd_age:
        subprocess.call(['samba-tool', 'domain', 'passwordsettings', 'set', '--min-pwd-age', str(minimum_password_age), '--complexity', complexity])
    yield
    if complexity != pwd_complexity or minimum_password_age != min_pwd_age:
        subprocess.call(['samba-tool', 'domain', 'passwordsettings', 'set', '--min-pwd-age', min_pwd_age, '--complexity', pwd_complexity])


def wait_for_drs_replication(ldap_filter, attrs=None, base=None, scope=ldb.SCOPE_SUBTREE, lp=None, timeout=360, delta_t=1, verbose=True):
    if not package_installed('univention-samba4'):
        if verbose:
            print 'wait_for_drs_replication(): skip, univention-samba4 not installed.'
        return
    if not lp:
        lp = LoadParm()
        lp.load('/etc/samba/smb.conf')
    if not attrs:
        attrs = ['dn']
    elif not isinstance(attrs, list):
        attrs = [attrs]

    samdb = SamDB("tdb://%s" % lp.private_path("sam.ldb"), session_info=system_session(lp), lp=lp)
    controls = ["domain_scope:0"]
    base = samdb.domain_dn()
    if not base or base == 'None':
        if verbose:
            print 'wait_for_drs_replication(): skip, no samba domain found'
        return

    if verbose:
        print "Waiting for DRS replication, filter: '%s'" % (ldap_filter, ),
    t = t0 = time.time()
    while t < t0 + timeout:
        try:
            res = samdb.search(base=base, scope=scope, expression=ldap_filter, attrs=attrs, controls=controls)
            if res:
                if verbose:
                    print "\nDRS replication took %d seconds" % (t - t0, )
                return res
        except ldb.LdbError as (_num, msg):
            print "Error during samdb.search: %s" % (msg, )

        print '.',
        time.sleep(delta_t)
        t = time.time()


def get_available_s4connector_dc():
    cmd = ("/usr/bin/univention-ldapsearch", "-LLL", "(univentionService=S4 Connector)", "uid")
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    stdout, _stderr = p.communicate()
    if not stdout:
        print "WARNING: Automatic S4 Connector host detection failed"
        return
    matches = re.compile('^uid: (.*)\$$', re.M).findall(stdout)
    if len(matches) == 1:
        return matches[0]
    elif len(matches) == 0:
        print "WARNING: Automatic S4 Connector host detection failed"
        return

    # check if this is UCS@school
    cmd = ("/usr/bin/univention-ldapsearch", "-LLL", "(univentionService=UCS@school)", "dn")
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    stdout, _stderr = p.communicate()
    if not stdout:
        print "ERROR: Automatic S4 Connector host detection failed: Found %s S4 Connector services" % len(matches)
        return
    # Look for replicating DCs
    dcs_replicating_with_this_one = []
    for s4c in matches:
        cmd = ("/usr/bin/samba-tool", "drs", "showrepl", s4c)
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, _stderr = p.communicate()
        if p.returncode != 0:
            continue
        dcs_replicating_with_this_one.append(s4c)
    if len(dcs_replicating_with_this_one) == 1:
        return dcs_replicating_with_this_one[0]
    else:
        print "ERROR: Automatic S4 Connector host detection failed: Replicating with %s S4 Connector services" % len(dcs_replicating_with_this_one)
        return


def force_drs_replication(source_dc=None, destination_dc=None, partition_dn=None, direction="in"):
    if not package_installed('univention-samba4'):
        print 'force_drs_replication(): skip, univention-samba4 not installed.'
        return
    if not source_dc:
        source_dc = get_available_s4connector_dc()
        if not source_dc:
            return 1

    if not destination_dc:
        destination_dc = socket.gethostname()

    if destination_dc == source_dc:
        return

    if not partition_dn:
        lp = LoadParm()
        lp.load('/etc/samba/smb.conf')
        samdb = SamDB("tdb://%s" % lp.private_path("sam.ldb"), session_info=system_session(lp), lp=lp)
        partition_dn = str(samdb.domain_dn())
        print "USING partition_dn:", partition_dn

    if direction == "in":
        cmd = ("/usr/bin/samba-tool", "drs", "replicate", destination_dc, source_dc, partition_dn)
    else:
        cmd = ("/usr/bin/samba-tool", "drs", "replicate", source_dc, destination_dc, partition_dn)
    return subprocess.call(cmd)


def _ldap_replication_complete():
    return subprocess.call('/usr/lib/nagios/plugins/check_univention_replication') == 0


def wait_for_s4connector():
    ucr = config_registry.ConfigRegistry()
    ucr.load()

    if not package_installed('univention-s4-connector'):
        print 'wait_for_s4connector(): skip, univention-s4-connector not installed.'
        return
    if ucr.is_false('connector/s4/autostart'):
        print 'wait_for_s4connector(): skip, connector/s4/autostart is set to false.'
        return
    conn = sqlite3.connect('/etc/univention/connector/s4internal.sqlite')
    c = conn.cursor()

    static_count = 0

    highestCommittedUSN = -1
    lastUSN = -1
    while static_count < CONNECTOR_WAIT_INTERVAL:
        time.sleep(CONNECTOR_WAIT_SLEEP)

        if not _ldap_replication_complete():
            continue

        previous_highestCommittedUSN = highestCommittedUSN

        highestCommittedUSN = -1
        ldbsearch = subprocess.Popen("ldbsearch -H /var/lib/samba/private/sam.ldb -s base -b '' highestCommittedUSN", shell=True, stdout=subprocess.PIPE)
        ldbresult = ldbsearch.communicate()
        for line in ldbresult[0].split('\n'):
            line = line.strip()
            if line.startswith('highestCommittedUSN: '):
                highestCommittedUSN = line.replace('highestCommittedUSN: ', '')
                break

        print highestCommittedUSN

        previous_lastUSN = lastUSN
        try:
            c.execute('select value from S4 where key=="lastUSN"')
        except sqlite3.OperationalError as e:
            static_count = 0
            print 'Reset counter: sqlite3.OperationalError: %s' % e
            print 'Counter: %d' % static_count
            continue

        conn.commit()
        lastUSN = c.fetchone()[0]

        if not (lastUSN == highestCommittedUSN and lastUSN == previous_lastUSN and highestCommittedUSN == previous_highestCommittedUSN):
            static_count = 0
            print 'Reset counter'
        else:
            static_count = static_count + 1
        print 'Counter: %d' % static_count

    conn.close()
    return 0
