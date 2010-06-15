<?php
/**
 * $Horde: turba/vcard.php,v 1.7 2004/05/10 13:41:05 jan Exp $
 *
 * Copyright 2000-2004 Charles J. Hagenbuch <chuck@horde.org>
 *
 * See the enclosed file COPYING for license information (GPL). If you did not
 * receive this file, see http://www.fsf.org/copyleft/gpl.html.
 */

define('TURBA_BASE', dirname(__FILE__));
require_once TURBA_BASE . '/lib/base.php';
require_once 'Horde/Form.php';
require_once 'Horde/Data.php';
require_once TURBA_BASE . '/lib/Renderer.php';
require_once TURBA_BASE . '/lib/Source.php';
require_once 'Horde/Variables.php';

$vars = &Variables::getDefaultVariables();

$source = $vars->get('source');
if (!isset($cfgSources[$source])) {
    $notification->push(_("The contact you requested does not exist."), 'horde.error');
    header('Location: ' . Horde::applicationUrl($prefs->getValue('initial_page'), true));
    exit;
}

$driver = &Turba_Source::singleton($source, $cfgSources[$source]);

/* Set the contact from the key requested. */
$key = $vars->get('key');
$object = $driver->getObject($key);
if (is_a($object, 'PEAR_Error')) {
    $notification->push($object->getMessage(), 'horde.error');
    header('Location: ' . Horde::applicationUrl($prefs->getValue('initial_page'), true));
    exit;
}

/* Check permissions on this contact. */
if (!Turba::checkPermissions($object, 'object', PERMS_READ)) {
    $notification->push(_("You do not have permission to view this object."), 'horde.error');
    header('Location: ' . Horde::applicationUrl($prefs->getValue('initial_page'), true));
    exit;
}

$vars = array();
/* Get the values through the AbstractObject class. */
foreach ($object->source->getCriteria() as $info_key => $info_val) {
    $vars[$info_key] = $object->getValue($info_key);
}

/* Get the contact's history. */
$history = &Horde_History::singleton();
$log = $history->getHistory($driver->getGUID($key));
foreach ($log->getData() as $entry) {
    switch ($entry['action']) {
    case 'add':
        $vars['__created'] = strftime($prefs->getValue('date_format'), $entry['ts']) . ' ' . date($prefs->getValue('twentyFour') ? 'G:i' : 'g:i a', $entry['ts']);
        break;

    case 'modify':
        $vars['__modified'] = strftime($prefs->getValue('date_format'), $entry['ts']) . ' ' . date($prefs->getValue('twentyFour') ? 'G:i' : 'g:i a', $entry['ts']);
        break;
    }
}

$vcard = &Horde_Data::singleton('vcard');
$vcard->exportFile(_("contact.vcf"), $vcard->fromHash($vars), NLS::getCharset());
