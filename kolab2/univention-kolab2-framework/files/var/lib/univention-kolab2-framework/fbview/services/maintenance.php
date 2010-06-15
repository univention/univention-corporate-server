<?php
/**
 * $Horde: horde/services/maintenance.php,v 1.28 2004/04/07 14:43:45 chuck Exp $
 *
 * Copyright 2001-2004 Michael Slusarz <slusarz@bigworm.colorado.edu>
 * Copyright 2001-2004 Charles J. Hagenbuch <chuck@horde.org>
 * Copyright 2001-2004 Jon Parise <jon@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL).  If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 */

include_once '../lib/base.php';
include_once 'Horde/Maintenance.php';

/* Make sure there is a user logged in. */
if (!Auth::getAuth()) {
    $url = Horde::url($registry->getParam('webroot', 'horde') . '/login.php', true);
    $url = Util::addParameter($url, 'url', Horde::selfUrl());
    header('Location: ' . $url);
    exit;
}

/* If no 'module' parameter passed in, return error. */
if (!($module = basename(Util::getFormData('module', '')))) {
    Horde::fatal(PEAR::raiseError(_("Do not directly access maintenance.php")), __FILE__, __LINE__);
}

/* Load the module specific maintenance class now. */
if (!($maint = &Maintenance::factory($module))) {
    Horde::fatal(PEAR::raiseError(_("The Maintenance:: class did not load successfully")), __FILE__, __LINE__);
}

/* Have the maintenance module do all necessary processing. */
list($action, $tasks) = $maint->runMaintenancePage();

/* Print top elements of confirmation page. */
require HORDE_TEMPLATES . '/common-header.inc';
require HORDE_TEMPLATES . '/maintenance/maintenance_top.inc';

if ($action == MAINTENANCE_OUTPUT_CONFIRM) {
    /* Confirmation-style output */
    require HORDE_TEMPLATES . '/maintenance/confirm_top.inc';
    if ($browser->hasFeature('javascript')) {
        include HORDE_TEMPLATES . '/maintenance/javascript.inc';
    }
    /* $pref, $descrip, & $checked need to be set for the templates. */
    foreach ($tasks as $pref) {
        list($descrip, $checked) = $maint->infoMaintenance($pref);
        include HORDE_TEMPLATES . '/maintenance/confirm_middle.inc';
    }
    require HORDE_TEMPLATES . '/maintenance/confirm_bottom.inc';
} elseif ($action == MAINTENANCE_OUTPUT_AGREE) {
    /* Agreement-style output */
    require HORDE_TEMPLATES . '/maintenance/agreement_top.inc';
    /* $pref & $descrip need to be set for the templates. */
    foreach ($tasks as $pref) {
        list($descrip, $checked) = $maint->infoMaintenance($pref);
        include HORDE_TEMPLATES . '/maintenance/agreement_middle.inc';
    }
    require HORDE_TEMPLATES . '/maintenance/agreement_bottom.inc';
} elseif ($action == MAINTENANCE_OUTPUT_NOTICE) {
    /* Notice-style output */
    require HORDE_TEMPLATES . '/maintenance/notice_top.inc';
    /* $pref & $descrip need to be set for the templates. */
    foreach ($tasks as $pref) {
        list($descrip, $checked) = $maint->infoMaintenance($pref);
        include HORDE_TEMPLATES . '/maintenance/notice_middle.inc';
    }
    require HORDE_TEMPLATES . '/maintenance/notice_bottom.inc';
}

/* Print bottom elements of maintenance page. */
require HORDE_TEMPLATES . '/maintenance/maintenance_bottom.inc';
require HORDE_TEMPLATES . '/common-footer.inc';
