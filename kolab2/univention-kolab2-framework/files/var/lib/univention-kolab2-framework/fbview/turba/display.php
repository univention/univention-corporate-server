<?php
/**
 * $Horde: turba/display.php,v 1.46 2004/04/07 14:43:52 chuck Exp $
 *
 * Copyright 2000-2004 Charles J. Hagenbuch <chuck@horde.org>
 *
 * See the enclosed file COPYING for license information (GPL). If you did not
 * receive this file, see http://www.fsf.org/copyleft/gpl.html.
 */

define('TURBA_BASE', dirname(__FILE__));
require_once TURBA_BASE . '/lib/base.php';
require_once 'Horde/Form.php';
require_once 'Horde/Links.php';
require_once TURBA_BASE . '/lib/Renderer.php';
require_once TURBA_BASE . '/lib/Source.php';
require_once TURBA_BASE . '/lib/ObjectView.php';
require_once 'Horde/Variables.php';

$links = &Horde_Links::singleton($registry->getApp());
$renderer = &new Turba_Renderer();
$vars = &Variables::getDefaultVariables();

$source = $vars->get('source');
if (!isset($cfgSources[$source])) {
    $notification->push(_("The contact you requested does not exist."));
    header('Location: ' . Horde::applicationUrl($prefs->getValue('initial_page'), true));
    exit;
}

$driver = &Turba_Source::singleton($source, $cfgSources[$source]);

/* Get the form object. */
$form = &Horde_Form::singleton('', $vars);
$form->setButtons(_("Save"), true);
$form->addHidden('', 'url', 'text', false);
$form->addHidden('', 'source', 'text', true);
$form->addHidden('', 'key', 'text', false);

/* Set the contact from the key requested. */
$key = $vars->get('key');
$object = $driver->getObject($key);
if (is_a($object, 'PEAR_Error')) {
    $notification->push($object->getMessage(), 'horde.error');
    header('Location: ' . Horde::applicationUrl($prefs->getValue('initial_page'), true));
    exit;
}

/* Check permissions on this contact. */
$readonly = false;
if (!Turba::checkPermissions($object, 'object', PERMS_READ)) {
    $notification->push(_("You do not have permission to view this contact."), 'horde.error');
    header('Location: ' . Horde::applicationUrl($prefs->getValue('initial_page'), true));
    exit;
}

$renderer->setObject($object);
$view = &new Turba_ObjectView($object);

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
        $view->set('created', true);
        $vars['__created'] = strftime($prefs->getValue('date_format'), $entry['ts']) . ' ' . date($prefs->getValue('twentyFour') ? 'G:i' : 'g:i a', $entry['ts']);
        break;

    case 'modify':
        $view->set('modified', true);
        $vars['__modified'] = strftime($prefs->getValue('date_format'), $entry['ts']) . ' ' . date($prefs->getValue('twentyFour') ? 'G:i' : 'g:i a', $entry['ts']);
        break;
    }
}

$view->setupForm($form);

$vars = &new Variables(array('object' => $vars));
if ($title = $vars->get('object[name]')) {
    $form->setTitle($title);
}

require TURBA_TEMPLATES . '/common-header.inc';
Turba::menu();
$form->renderInactive($renderer, $vars);
if ($links->listLinkTypes()) {
    $links->viewLinks(array('source' => $source,
                            'id' => $key));
}
require $registry->getParam('templates', 'horde') . '/common-footer.inc';
