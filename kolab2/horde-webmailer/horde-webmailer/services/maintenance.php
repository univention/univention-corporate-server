<?php
/**
 * $Horde: horde/services/maintenance.php,v 1.31.2.7 2009-01-06 15:26:20 jan Exp $
 *
 * Copyright 2001-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author Chuck Hagenbuch <chuck@horde.org>
 * @author Michael Slusarz <slusarz@horde.org>
 */

@define('HORDE_BASE', dirname(__FILE__) . '/..');
require_once HORDE_BASE . '/lib/base.php';
require_once 'Horde/Maintenance.php';
require_once 'Horde/Template.php';

/* Make sure there is a user logged in. */
if (!Auth::getAuth()) {
    Horde::authenticationFailureRedirect();
}

/* If no 'module' parameter passed in, die with an error. */
if (!($module = basename(Util::getFormData('module')))) {
    Horde::fatal(PEAR::raiseError(_("Do not directly access maintenance.php")), __FILE__, __LINE__);
}
$app_name = $registry->get('name', $module);

/* Load the module specific maintenance class now. */
if (!($maint = &Maintenance::factory($module))) {
    Horde::fatal(PEAR::raiseError(_("The Maintenance:: class did not load successfully")), __FILE__, __LINE__);
}

/* Create the Horde_Template item. */
$template = new Horde_Template();
$template->set('javascript', $browser->hasFeature('javascript'), true);

/* Have the maintenance module do all necessary processing. */
list($action, $tasklist) = $maint->runMaintenancePage();

switch ($action) {
case MAINTENANCE_OUTPUT_CONFIRM:
    /* Confirmation-style output. */
    $template->set('confirm', true, true);
    $template->set('agree', false, true);
    $template->set('notice', false, true);

    $notification->push(sprintf(_("%s is ready to perform the maintenance operations checked below. Check the box for any operation(s) you want to perform at this time."), $app_name), 'horde.message');
    $template->set('header', sprintf(_("%s Maintenance Operations - Confirmation"), $app_name));
    break;

case MAINTENANCE_OUTPUT_AGREE:
    /* Agreement-style output. */
    $template->set('confirm', false, true);
    $template->set('agree', true, true);
    $template->set('notice', false, true);

    $notification->push(_("Please read the following text. You MUST agree with the terms to use the system."), 'horde.message');
    $template->set('header', sprintf(_("%s Terms of Agreement"), $app_name));
    break;

case MAINTENANCE_OUTPUT_NOTICE:
    /* Notice-style output. */
    $template->set('confirm', false, true);
    $template->set('agree', false, true);
    $template->set('notice', true, true);

    $template->set('header', sprintf(_("%s - Notice"), $app_name));
    break;
}

/* Make variable array needed for templates. */
$tasks = array();
foreach ($tasklist as $pref) {
    list($descrip, $checked) = $maint->infoMaintenance($pref);
    $tasks[] = array('pref' => $pref, 'descrip' => $descrip, 'checked' => $checked ? ' checked="checked"' : '');
}

$template->setOption('gettext', true);
$template->set('tasks', $tasks);
$template->set('maint_url', htmlspecialchars($maint->getMaintenanceFormURL()));
$template->set('maint_postdata', $maint->getPostData());
$template->set('notify', Util::bufferOutput(array($notification, 'notify'), array('listeners' => 'status')));

$bodyId = 'services_maintenance';
require HORDE_TEMPLATES . '/common-header.inc';
echo $template->fetch(HORDE_TEMPLATES . '/maintenance/maintenance.html');
require HORDE_TEMPLATES . '/common-footer.inc';
