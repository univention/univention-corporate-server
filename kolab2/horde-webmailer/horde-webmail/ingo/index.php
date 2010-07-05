<?php
/**
 * $Horde: ingo/index.php,v 1.14.10.7 2009-01-06 15:24:34 jan Exp $
 *
 * Copyright 2002-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file LICENSE for license information (ASL).  If you
 * did not receive this file, see http://www.horde.org/licenses/asl.php.
 *
 * @author Mike Cochrane <mike@graftonhall.co.nz>
 */

@define('INGO_BASE', dirname(__FILE__));
$ingo_configured = (is_readable(INGO_BASE . '/config/conf.php') &&
                    is_readable(INGO_BASE . '/config/prefs.php') &&
                    is_readable(INGO_BASE . '/config/backends.php') &&
                    is_readable(INGO_BASE . '/config/fields.php'));

if (!$ingo_configured) {
    require INGO_BASE . '/../lib/Test.php';
    Horde_Test::configFilesMissing('Ingo', INGO_BASE,
        array('conf.php', 'prefs.php', 'backends.php'),
        array('fields.php' => 'This file defines types of credentials that a backend might request.'));
}

require INGO_BASE . '/filters.php';
