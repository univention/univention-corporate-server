<?php

@%@BCWARNING=#@%@

$conf['menu']['apps'] = array();
$conf['storage']['driver'] = 'prefs';
$conf['storage']['maxblacklist'] = 0;
$conf['storage']['maxwhitelist'] = 0;
$conf['rules']['userheader'] = true;
$conf['rules']['usefolderapi'] = true;
$conf['spam']['enabled'] = true;
$conf['spam']['header'] = 'X-Spam-Level';
$conf['spam']['char'] = '*';
$conf['spam']['compare'] = 'string';
$conf['hooks']['vacation_addresses'] = false;
$conf['hooks']['vacation_only'] = true;

