#!@@@php_bin@@@
<?php
/**
 * Deletes the Kolab webclient data of deleted users.
 *
 * PHP version 5
 *
 * Copyright 2010 Klarälvdalens Datakonsult AB
 *
 * @category Kolab
 * @package  Kolab
 * @author   Gunnar Wrobel <wrobel@pardus.de>
 * @license  http://www.fsf.org/copyleft/lgpl.html LGPL
 * @link     http://www.kolab.org
 */

require_once 'Horde/Kolab/Config.php';
require_once 'Horde/Kolab/Config/Exception.php';

$uid = $_SERVER['argv'][1];
$config = new Horde_Kolab_Config('@@@prefix@@@/etc/kolab');
if (file_exists($config['webclient_data_root'] . '/storage/' . $uid . '.prefs')) {
    unlink($config['webclient_data_root'] . '/storage/' . $uid . '.prefs');
    if ($config['log_level'] >= 3) {
        syslog(LOG_INFO, "L: Deleted web client user preferences for user $uid.");
    }
}

