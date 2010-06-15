<?php
/**
 * $Horde: kronolith/attendeesview.php,v 1.1 2004/05/25 08:34:21 stuart Exp $
 *
 * Copyright 2004 Code Fusion  <http://www.codefusion.co.za/>
 *                Stuart Binge <s.binge@codefusion.co.za>
 *
 * See the enclosed file COPYING for license information (GPL).  If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 */

@define('KRONOLITH_BASE', dirname(__FILE__));
require_once KRONOLITH_BASE . '/lib/base.php';

$allow_dismiss = false;
$form_handler = Horde::applicationUrl('attendeesview.php');
require KRONOLITH_BASE . '/attendeeshandler.php';
$title = _('Free/Busy');

Horde::addScriptFile('tooltip.js', 'horde');
//Horde::addScriptFile('open_savedattlist_win.js');
require KRONOLITH_TEMPLATES . '/common-header.inc';

if ($browser->hasFeature('javascript')) {
    Horde::addScriptFile('open_savedattlist_win.js');
    $savedattlist_url = 'javascript:open_savedattlist_win();';
} else {
    $savedattlist_url = Horde::applicationUrl('savedattlist.php');
}

$print_view = (Util::getFormData('print') == 'true');
if ($print_view) {
    require_once $registry->getParam('templates', 'horde') . '/javascript/print.js';
} else {
    $print_link = Util::addParameter('attendeesview.php', 'print', 'true');
    $print_link = Horde::url($print_link);
    if ($browser->hasFeature('javascript')) {
        require_once $registry->getParam('templates', 'horde') . '/javascript/open_print_win.js';
    }

    Kronolith::menu();
}

require KRONOLITH_BASE . '/attendeescommon.php';
