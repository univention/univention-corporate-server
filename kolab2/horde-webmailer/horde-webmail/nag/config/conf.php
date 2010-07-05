<?php
/* CONFIG START. DO NOT CHANGE ANYTHING IN OR AFTER THIS LINE. */
// $Horde: nag/config/conf.xml,v 1.25.10.2 2007/12/20 14:23:06 jan Exp $
$conf['storage']['driver'] = 'kolab';
$conf['menu']['print'] = true;
$conf['menu']['import_export'] = true;
$conf['menu']['apps'] = array();
/* CONFIG END. DO NOT CHANGE ANYTHING IN OR BEFORE THIS LINE. */
if (file_exists(dirname(__FILE__) . '/conf.local.php')) {
  require(dirname(__FILE__) . '/conf.local.php');
}

