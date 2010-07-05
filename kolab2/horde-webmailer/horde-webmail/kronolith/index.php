<?php
/**
 * $Horde: kronolith/index.php,v 1.28.10.3 2009-01-06 15:24:43 jan Exp $
 *
 * Copyright 1999-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * not receive such a file, see also http://www.fsf.org/copyleft/gpl.html.
 */

@define('KRONOLITH_BASE', dirname(__FILE__));
$kronolith_configured = (is_readable(KRONOLITH_BASE . '/config/conf.php') &&
                         is_readable(KRONOLITH_BASE . '/config/prefs.php'));

if (!$kronolith_configured) {
    require KRONOLITH_BASE . '/../lib/Test.php';
    Horde_Test::configFilesMissing('Kronolith', KRONOLITH_BASE,
        array('conf.php', 'prefs.php'));
}

require_once KRONOLITH_BASE . '/lib/base.php';
require KRONOLITH_BASE . '/' . $prefs->getValue('defaultview') . '.php';
