<?php
/**
 * $Horde: turba/index.php,v 1.27 2004/04/07 14:43:52 chuck Exp $
 *
 * Copyright 2000-2004 Charles J. Hagenbuch <chuck@horde.org>
 *
 * See the enclosed file COPYING for license information (GPL).  If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 */

@define('TURBA_BASE', dirname(__FILE__));
$turba_configured = (@is_readable(TURBA_BASE . '/config/conf.php') &&
                     @is_readable(TURBA_BASE . '/config/attributes.php') &&
                     @is_readable(TURBA_BASE . '/config/html.php') &&
                     @is_readable(TURBA_BASE . '/config/prefs.php') &&
                     @is_readable(TURBA_BASE . '/config/sources.php'));

if (!$turba_configured) {
    require TURBA_BASE . '/../lib/Test.php';
    Horde_Test::configFilesMissing('Turba', TURBA_BASE,
        array('conf.php', 'html.php', 'prefs.php', 'sources.php'),
        array('attributes.php' => 'This file defines the Turba global attribute names and types - names, email addresses, etc.'));
}

require_once TURBA_BASE . '/lib/base.php';
require TURBA_BASE . '/' . $prefs->getValue('initial_page');
