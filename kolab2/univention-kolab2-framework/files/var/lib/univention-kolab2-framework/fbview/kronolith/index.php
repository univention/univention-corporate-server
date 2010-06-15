<?php
/**
 * $Horde: kronolith/index.php,v 1.27 2004/04/07 14:43:28 chuck Exp $
 *
 * Kronolith: Copyright 1999, 2000 Charles J. Hagenbuch <chuck@horde.org>
 *
 * See the enclosed file COPYING for license information (GPL). If you did
 * not receive such a file, see also http://www.fsf.org/copyleft/gpl.html.
 */

@define('KRONOLITH_BASE', dirname(__FILE__));
$kronolith_configured = (@is_readable(KRONOLITH_BASE . '/config/conf.php') &&
                         @is_readable(KRONOLITH_BASE . '/config/prefs.php') &&
                         @is_readable(KRONOLITH_BASE . '/config/html.php'));

if (!$kronolith_configured) {
    require KRONOLITH_BASE . '/../lib/Test.php';
    Horde_Test::configFilesMissing('Kronolith', KRONOLITH_BASE,
        array('conf.php', 'html.php', 'prefs.php'));
}

require_once KRONOLITH_BASE . '/lib/base.php';
require KRONOLITH_BASE . '/' . $prefs->getValue('defaultview') . '.php';
