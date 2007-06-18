<?php
/*
 * $Horde: turba/miniwindow.php,v 1.7 2004/04/07 14:43:52 chuck Exp $
 *
 * Copyright 2002-2004 Charles J. Hagenbuch <chuck@horde.org>
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 */

define('TURBA_BASE', dirname(__FILE__));
require_once TURBA_BASE . '/lib/base.php';

if (Util::getFormData('menu')) {
    require_once 'Horde/Menu.php';
    require TURBA_TEMPLATES . '/common-header.inc';
    require TURBA_TEMPLATES . '/miniwindow/menu.inc';

    /* Include the JavaScript for the help system (if enabled). */
    if ($conf['user']['online_help'] && $browser->hasFeature('javascript')) {
        Help::javascript();
    }

    require $registry->getParam('templates', 'horde') . '/common-footer.inc';
} else {
    require TURBA_TEMPLATES . '/miniwindow/frames.inc';
}
