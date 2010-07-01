<?php
/**
 * $Horde: nag/index.php,v 1.16.10.7 2009-01-06 15:25:04 jan Exp $
 *
 * Copyright 2001-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 */

define('NAG_BASE', dirname(__FILE__));
$nag_configured = (is_readable(NAG_BASE . '/config/conf.php') &&
                   is_readable(NAG_BASE . '/config/prefs.php'));

if (!$nag_configured) {
    require NAG_BASE . '/../lib/Test.php';
    Horde_Test::configFilesMissing('Nag', NAG_BASE,
        array('conf.php', 'prefs.php'));
}

require NAG_BASE . '/list.php';
