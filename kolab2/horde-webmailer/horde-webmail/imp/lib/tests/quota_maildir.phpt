--TEST--
IMP_Quota_maildir test.
--FILE--
<?php

$_SESSION['imp']['user'] = null;
require_once dirname(__FILE__) . '/../Quota.php';
$quota = IMP_Quota::factory('maildir',
                            array('path' => dirname(__FILE__) . '/fixtures'));
var_export($quota->getQuota());

?>
--EXPECT--
array (
  'usage' => 550839239,
  'limit' => 1000000000,
)
