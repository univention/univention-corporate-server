<?php
/**
 * $Horde: turba/contact.php,v 1.8.2.7 2009-01-06 15:27:38 jan Exp $
 *
 * Copyright 2000-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file LICENSE for license information (ASL).  If you
 * did not receive this file, see http://www.horde.org/licenses/asl.php.
 *
 * @author Chuck Hagenbuch <chuck@horde.org>
 */

@define('TURBA_BASE', dirname(__FILE__));
require_once TURBA_BASE . '/lib/base.php';
require_once 'Horde/Form.php';
require_once 'Horde/Form/Renderer.php';
require_once 'Horde/Variables.php';
require_once 'Horde/UI/Tabs.php';

$vars = Variables::getDefaultVariables();
$source = $vars->get('source');
if (!isset($GLOBALS['cfgSources'][$source])) {
    $notification->push(_("The contact you requested does not exist."));
    header('Location: ' . Horde::applicationUrl($prefs->getValue('initial_page'), true));
    exit;
}

/* Set the contact from the key requested. */
$driver = &Turba_Driver::singleton($source);
if (is_a($driver, 'PEAR_Error')) {
    $notification->push($driver->getMessage(), 'horde.error');
    header('Location: ' . Horde::applicationUrl($prefs->getValue('initial_page'), true));
    exit;
}

$contact = null;
$uid = $vars->get('uid');
if (!empty($uid)) {
    $search = $driver->search(array('__uid' => $uid));
    if (!is_a($search, 'PEAR_Error') && $search->count()) {
        $contact = $search->next();
        $vars->set('key', $contact->getValue('__key'));
    }
}
if (!$contact || is_a($contact, 'PEAR_Error')) {
    $contact = $driver->getObject($vars->get('key'));
    if (is_a($contact, 'PEAR_Error')) {
        $notification->push($contact->getMessage(), 'horde.error');
        header('Location: ' . Horde::applicationUrl($prefs->getValue('initial_page'), true));
        exit;
    }
}

// Mark this contact as the user's own?
if ($vars->get('action') == 'mark_own') {
    $prefs->setValue('own_contact', $source . ';' . $contact->getValue('__key'));
    $notification->push(_("This contact has been marked as your own."), 'horde.success');
}

// Are we printing?
$print_view = (bool)Util::getFormData('print');

// Get view.
$viewName = Util::getFormData('view', 'Contact');
switch ($viewName) {
case 'Contact':
    require_once TURBA_BASE . '/lib/Views/Contact.php';
    $view = new Turba_View_Contact($contact, $print_view);
    if (!$vars->get('url')) {
        $vars->set('url', $contact->url(null, true));
    }
    break;

case 'EditContact':
    require_once TURBA_BASE . '/lib/Views/EditContact.php';
    $view = new Turba_View_EditContact($contact);
    break;

case 'DeleteContact':
    require_once TURBA_BASE . '/lib/Views/DeleteContact.php';
    $view = new Turba_View_DeleteContact($contact);
    break;
}

// Get tabs.
$url = $contact->url();
$tabs = new Horde_UI_Tabs('view', $vars);
$tabs->addTab(_("_View"), $url,
              array('tabname' => 'Contact', 'id' => 'tabContact', 'onclick' => 'return ShowTab(\'Contact\');'));
if ($contact->hasPermission(PERMS_EDIT)) {
    $tabs->addTab(_("_Edit"), $url,
                  array('tabname' => 'EditContact', 'id' => 'tabEditContact', 'onclick' => 'return ShowTab(\'EditContact\');'));
}
if ($contact->hasPermission(PERMS_DELETE)) {
    $tabs->addTab(_("De_lete"), $url,
                  array('tabname' => 'DeleteContact', 'id' => 'tabDeleteContact', 'onclick' => 'return ShowTab(\'DeleteContact\');'));
}

@list($own_source, $own_id) = explode(';', $prefs->getValue('own_contact'));
if ($own_source == $source && $own_id == $contact->getValue('__key')) {
    $own_icon = ' ' . Horde::img('user.png', _("Your own contact"),
                                 array('title' => _("Your own contact")),
                                 $registry->getImageDir('horde'));
    $own_link = '';
} else {
    $own_icon = '';
    $own_link = '<span class="smallheader rightFloat">'
        . Horde::link(Util::addParameter($url, array('action' => 'mark_own')))
        . _("Mark this as your own contact") . '</a></span>';
}

$title = $view->getTitle();
Horde::addScriptFile('prototype.js', 'turba', true);
Horde::addScriptFile('contact_tabs.js', 'turba', true);
require TURBA_TEMPLATES . '/common-header.inc';
if ($print_view) {
    require_once $registry->get('templates', 'horde') . '/javascript/print.js';
} else {
    require TURBA_TEMPLATES . '/menu.inc';
}
echo '<div id="page">';
if (!$print_view) {
    echo $tabs->render($viewName);
}

if ($contact->hasValue('name')) {
    $name = $contact->getValue('name');
} elseif (isset($contact->driver->alternativeName) &&
          $contact->hasValue($contact->driver->alternativeName)) {
    $name = $contact->getValue($contact->driver->alternativeName);
}
echo '<h1 class="header">' . $own_link
    . ($name
       ? htmlspecialchars($name)
       : '<em>' . _("Blank name") . '</em>')
    . $own_icon . '</h1>';
$view->html();
echo '</div>';
require $registry->get('templates', 'horde') . '/common-footer.inc';
