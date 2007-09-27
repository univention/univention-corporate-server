<?php
$conf['menu']['apps'] = array();
$conf['backend']['backend_list'] = 'hidden';
$conf['user']['change'] = true;
$conf['user']['refused'] = array('root', 'bin', 'daemon', 'adm', 'lp', 'shutdown', 'halt', 'uucp', 'ftp', 'anonymous', 'nobody', 'httpd', 'operator', 'guest', 'diginext', 'bind', 'cyrus', 'courier', 'games', 'kmem', 'mailnull', 'man', 'mysql', 'news', 'postfix', 'sshd', 'tty', 'www');
$conf['password']['strengthtests'] = true;
$conf['hooks']['full_name'] = true;
$conf['hooks']['default_username'] = false;
$conf['hooks']['username'] = true;
$conf['hooks']['userdn'] = false;

