<?php
/**
 * $Horde: mimp/index.php,v 1.14.2.4 2009-01-06 15:24:53 jan Exp $
 *
 * Copyright 1999-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author Chuck Hagenbuch <chuck@horde.org>
 */

@define('MIMP_BASE', dirname(__FILE__));
$mimp_configured = (is_readable(MIMP_BASE . '/config/conf.php') &&
                    is_readable(MIMP_BASE . '/config/prefs.php'));

if (!$mimp_configured) {
    /* MIMP isn't configured. */
    require MIMP_BASE . '/templates/index/notconfigured.inc';
    exit;
}

require MIMP_BASE . '/mailbox.php';
