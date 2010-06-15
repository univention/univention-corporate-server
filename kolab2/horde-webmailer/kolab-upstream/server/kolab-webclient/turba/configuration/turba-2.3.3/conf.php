<?php
/* CONFIG START. DO NOT CHANGE ANYTHING IN OR AFTER THIS LINE. */
// $Horde: turba/config/conf.xml,v 1.6.2.6 2008/06/25 15:52:54 jan Exp $
$conf['menu']['import_export'] = true;
$conf['menu']['apps'] = array();
$conf['client']['addressbook'] = 'INBOX%2FClients';
$conf['shares']['source'] = 'kolab';
$conf['comments']['allow'] = true;
$conf['documents']['type'] = 'horde';
/* CONFIG END. DO NOT CHANGE ANYTHING IN OR BEFORE THIS LINE. */
if (file_exists(dirname(__FILE__) . '/conf.local.php')) {
  require(dirname(__FILE__) . '/conf.local.php');
}

