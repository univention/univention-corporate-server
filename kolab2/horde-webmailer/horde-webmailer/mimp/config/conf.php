<?php
/* CONFIG START. DO NOT CHANGE ANYTHING IN OR AFTER THIS LINE. */
// $Horde: mimp/config/conf.xml,v 1.11.2.2 2008/04/23 05:07:06 slusarz Exp $
$conf['mailbox']['max_from_chars'] = 10;
$conf['mailbox']['max_subj_chars'] = 20;
/* CONFIG END. DO NOT CHANGE ANYTHING IN OR BEFORE THIS LINE. */
if (file_exists(dirname(__FILE__) . '/conf.local.php')) {
  require(dirname(__FILE__) . '/conf.local.php');
}

