<?php
/**
 * Horde Application Framework core services file.
 *
 * This file sets up any necessary include path variables and includes
 * the minimum required Horde libraries.
 *
 * $Horde: horde/lib/core.php,v 1.23 2004/04/29 02:40:47 marcus Exp $
 *
 * Copyright 1999-2004 Chuck Hagenbuch <chuck@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 */

/* Turn PHP stuff off that can really screw things up. */
ini_set('magic_quotes_sybase', 0);
ini_set('magic_quotes_runtime', 0);

// If the Horde Framework packages are not installed in PHP's global
// include_path, you must add an ini_set() call here to add their
// location to the include_path.

// Horde core classes.
include_once 'Horde.php';
include_once 'Horde/Registry.php';
include_once 'Horde/String.php';
include_once 'Horde/Notification.php';
include_once 'Horde/Auth.php';
include_once 'Horde/Browser.php';
include_once 'Horde/Perms.php';

// Browser detection object.
if (class_exists('Browser')) {
    $browser = &Browser::singleton();
}
