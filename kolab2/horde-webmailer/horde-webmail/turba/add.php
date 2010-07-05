<?php
/**
 * The Turba script to add a new entry into an address book.
 *
 * $Horde: turba/add.php,v 1.54.4.15 2009-01-06 15:27:38 jan Exp $
 *
 * Copyright 2000-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file LICENSE for license information (ASL).  If you did
 * did not receive this file, see http://www.horde.org/licenses/asl.php.
 *
 * @author Chuck Hagenbuch <chuck@horde.org>
 */

@define('TURBA_BASE', dirname(__FILE__));
require_once TURBA_BASE . '/lib/base.php';
require_once TURBA_BASE . '/lib/Forms/AddContact.php';
require_once 'Horde/Form/Renderer.php';
require_once 'Horde/Variables.php';

/* Setup some variables. */
$contact = null;
$vars = Variables::getDefaultVariables();
if (count($addSources) == 1) {
    $vars->set('source', key($addSources));
}
$source = $vars->get('source');
$url = $vars->get('url');

/* Exit with an error message if there are no sources to add to. */
if (!$addSources) {
    $notification->push(_("There are no writeable address books. None of the available address books are configured to allow you to add new entries to them. If you believe this is an error, please contact your system administrator."), 'horde.error');
    $url = $url ? Horde::url($url, true) : Horde::applicationUrl('index.php', true);
    header('Location: ' . $url);
    exit;
}

/* A source has been selected, connect and set up the fields. */
if ($source) {
    $driver = &Turba_Driver::singleton($source);
    if (is_a($driver, 'PEAR_Error')) {
        $notification->push(sprintf(_("Failed to access the address book: %s"), $driver->getMessage()), 'horde.error');
    } else {
        /* Check permissions. */
        $max_contacts = Turba::getExtendedPermission($driver, 'max_contacts');
        if ($max_contacts !== true &&
            $max_contacts <= $driver->count()) {
            $message = @htmlspecialchars(sprintf(_("You are not allowed to create more than %d contacts in \"%s\"."), $max_contacts, $cfgSources[$source]['title']), ENT_COMPAT, NLS::getCharset());
            if (!empty($conf['hooks']['permsdenied'])) {
                $message = Horde::callHook('_perms_hook_denied', array('turba:max_contacts'), 'horde', $message);
            }
            $notification->push($message, 'horde.error', array('content.raw'));
            $url = $url ? Horde::url($url, true) : Horde::applicationUrl('index.php', true);
            header('Location: ' . $url);
            exit;
        }

        $contact = new Turba_Object($driver);
    }
}

/* Set up the form. */
$form = new Turba_AddContactForm($vars, $contact);

/* Validate the form. */
if ($form->validate()) {
    $form->execute();
}

$title = _("New Contact");
require TURBA_TEMPLATES . '/common-header.inc';
require TURBA_TEMPLATES . '/menu.inc';
$form->renderActive(new Horde_Form_Renderer(), $vars, 'add.php', 'post');
require $registry->get('templates', 'horde') . '/common-footer.inc';
