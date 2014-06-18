#!/usr/bin/python2.7
import univention.config_registry
from univention.config_registry import ConfigRegistry

def main():
    ucr = ConfigRegistry()
    configRegistry = univention.config_registry.ConfigRegistry()
    print ucr['repository/online']in('1','yes','true','enable','enabled')
    print configRegistry.get('repository/online') not in ('0', 'no', 'false', 'disable', 'disabled', )
    return self.get(key).lower() in ('no', 'false', '0', 'disable', 'disabled', 'off')

if __name__ == '__main__':
    main()
