<?php
/* CONFIG START. DO NOT CHANGE ANYTHING IN OR AFTER THIS LINE. */
// $Horde: kronolith/config/conf.xml,v 1.14.10.5 2007/12/20 14:12:23 jan Exp $
$conf['calendar']['driver'] = 'kolab';
$conf['storage']['driver'] = 'kolab';
$conf['storage']['default_domain'] = '';
$conf['storage']['freebusy']['protocol'] = 'https';
$conf['storage']['freebusy']['port'] = 443;
$conf['metadata']['keywords'] = false;
$conf['autoshare']['shareperms'] = 'none';
$conf['holidays']['enable'] = true;
$conf['menu']['print'] = true;
$conf['menu']['import_export'] = true;
$conf['menu']['apps'] = array();
$conf['authenticated_freebusy'] = true;
/* CONFIG END. DO NOT CHANGE ANYTHING IN OR BEFORE THIS LINE. */
if (file_exists(dirname(__FILE__) . '/kolab.php')) {
  require_once(dirname(__FILE__) . '/kolab.php');
}
