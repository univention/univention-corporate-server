#!/usr/share/ucs-test/runner python3
## desc: Create and install a simple docker app and check ports exclusive
## tags: [docker]
## exposure: dangerous
## packages:
##   - docker.io

#from textwrap import dedent

from univention.testing.utils import is_port_open, restart_firewall

from dockertest import Appcenter, tiny_app


if __name__ == '__main__':
    with Appcenter() as appcenter:
        app = tiny_app()
        ports = ['21', '23']
        packages = ['telnetd', 'proftpd']

        # check ports are unused
        for port in ports:
            assert not is_port_open(port)

        try:
            # check ports exclusive
            app.set_ini_parameter(
                # DockerScriptInit='/usr/sbin/proftpd -n',
                # DockerScriptInit='/bin/sh',
                DockerImage='instantlinux/proftpd',
                PortsExclusive=','.join(ports),
                DefaultPackages=','.join(packages),
                DockerInjectEnvFile='main',
                # DockerScriptSetup='/usr/sbin/%s-setup' % app.app_name
            )
            #app.add_script(env='\nPASV_ADDRESS=localhost\n')
            app.add_script(env='\nPASV_ADDRESS=0.0.0.0\n')
            #app.add_script(setup=dedent('''\
            #    #!/bin/bash
            #    set -x -e
            #    apt update
            #    apt install --assume-yes telnetd proftpd-basic
            #    proftpd
            #    '''))
            app.add_to_local_appcenter()
            appcenter.update()
            app.install()

            # check ports are open
            for port in ports:
                assert is_port_open(port)

            # restart firewall and check again
            restart_firewall()

            # check ports are open
            for port in ports:
                assert is_port_open(port)
        finally:
            app.uninstall()
            app.remove()

        # check ports are unused
        for port in ports:
            assert not is_port_open(port)
