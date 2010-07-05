<?php
/**
 * Horde Application Framework core services file.
 *
 * This file sets up any necessary include path variables and includes
 * the minimum required Horde libraries.
 *
 * $Horde: horde/lib/core.php,v 1.26.6.17 2009-02-18 16:23:50 chuck Exp $
 *
 * Copyright 1999-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 */

/* Turn PHP stuff off that can really screw things up. */
ini_set('magic_quotes_sybase', 0);
ini_set('magic_quotes_runtime', 0);
ini_set('zend.ze1_compatibility_mode', 0);
ini_set('allow_url_include', 0);

/* Unset all variables populated through register_globals. */
if (ini_get('register_globals')) {
    foreach (array($_GET, $_POST, $_COOKIE, $_ENV, $_SERVER) as $var) {
        foreach (array_keys($var) as $key) {
            unset($$key);
        }
    }
}

/* If the Horde Framework packages are not installed in PHP's global
 * include_path, you must add an ini_set() call here to add their location to
 * the include_path. */
ini_set('include_path', dirname(__FILE__) . PATH_SEPARATOR . ini_get('include_path'));

/* PEAR base class. */
include_once 'PEAR.php';

/* Horde core classes. */
include_once 'Horde.php';
include_once 'Horde/Registry.php';
include_once 'Horde/String.php';
include_once 'Horde/NLS.php';
include_once 'Horde/Notification.php';
include_once 'Horde/Auth.php';
include_once 'Horde/Browser.php';
include_once 'Horde/Perms.php';

/* Browser detection object. */
if (class_exists('Browser')) {
    $browser = &Browser::singleton();
}
