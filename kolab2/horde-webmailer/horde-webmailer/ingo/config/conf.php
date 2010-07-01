<?php
/* CONFIG START. DO NOT CHANGE ANYTHING IN OR AFTER THIS LINE. */
// $Horde: ingo/config/conf.xml,v 1.13.12.1 2007/12/20 14:05:46 jan Exp $
$conf['menu']['apps'] = array();
$conf['storage']['driver'] = 'prefs';
$conf['storage']['maxblacklist'] = 0;
$conf['storage']['maxwhitelist'] = 0;
$conf['rules']['userheader'] = true;
$conf['rules']['usefolderapi'] = true;
$conf['spam']['header'] = 'X-Spam-Level';
$conf['spam']['char'] = '*';
$conf['spam']['compare'] = 'string';
$conf['hooks']['vacation_addresses'] = false;
$conf['hooks']['vacation_only'] = true;
/* CONFIG END. DO NOT CHANGE ANYTHING IN OR BEFORE THIS LINE. */
if (file_exists(dirname(__FILE__) . '/conf.local.php')) {
  require(dirname(__FILE__) . '/conf.local.php');
}

