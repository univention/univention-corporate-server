DNS in UCS
==========

Depending on UCRV `dns/backend` BIND9 runs on different ports and uses different configuration files:
* `ldap`: Backednd LDAP reads from OpenLDAP, cached by Proxy frontend. Configured by UDL module [bind.py](bind.py).
* `samba4`:  Samba4 only; zones are directly read from Samba4.

|         | LDAP                                                          | Proxy                                                             | Samba4                                                              |
| ------- | ------------------------------------------------------------- | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| Service | [univention-bind-ldap.service](conffiles/etc/systemd/system)  | bind9.service                                                     | bind9.service                                                       |
| DNS     | 7777                                                          | 53                                                                | 53                                                                  |
| rndc    | 5555                                                          | 953                                                               | 953                                                                 |
| Conf    | [/etc/bind/named.conf](conffiles/etc/bind/named.conf)         | [/etc/bind/named.conf.proxy](conffiles/etc/bind/named.conf.proxy) | [/etc/bind/named.conf.samba4](conffiles/etc/bind/named.conf.samba4) |
| Zones   | /etc/bind/univention.conf                                     | /etc/bind/univention.conf.proxy                                   | -                                                                   |
| Local   | /etc/bind/local.conf                                          | /etc/bind/local.conf.proxy                                        | /etc/bind/local.conf.samba4                                         |


