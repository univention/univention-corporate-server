<?php
/* CONFIG START. DO NOT CHANGE ANYTHING IN OR AFTER THIS LINE. */
// $Horde: dimp/config/conf.xml,v 1.30.2.6 2008/08/08 17:00:47 slusarz Exp $
$conf['hooks']['mailboxarray'] = false;
$conf['hooks']['previewview'] = false;
$conf['hooks']['messageview'] = false;
$conf['hooks']['addressformatting'] = false;
$conf['hooks']['msglist_format'] = false;
$conf['css_files'] = array();
$conf['js']['debug'] = false;
$conf['viewport']['buffer_pages'] = 5;
$conf['viewport']['limit_factor'] = 35;
$conf['viewport']['viewport_wait'] = 12;
$conf['viewport']['background_inbox'] = true;
$conf['search']['search_all'] = false;
$conf['menu']['apps'] = array('turba', 'ingo', 'kronolith', 'nag', 'mnemo');
/* CONFIG END. DO NOT CHANGE ANYTHING IN OR BEFORE THIS LINE. */
if (file_exists(dirname(__FILE__) . '/conf.local.php')) {
  require(dirname(__FILE__) . '/conf.local.php');
}

