<?php
/**
 * $Horde: turba/addressbooks/create.php,v 1.1.2.3 2009-01-06 15:27:40 jan Exp $
 *
 * Copyright 2001-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file LICENSE for license information (ASL). If you
 * did not receive this file, see http://www.horde.org/licenses/asl.php.
 */

@define('TURBA_BASE', dirname(dirname(__FILE__)));
require_once TURBA_BASE . '/lib/base.php';
require_once TURBA_BASE . '/lib/Forms/CreateAddressBook.php';

// Exit if this isn't an authenticated user, or if there's no source
// configured for shares.
if (!Auth::getAuth() || empty($_SESSION['turba']['has_share'])) {
    require TURBA_BASE . '/'
        . ($browse_source_count ? basename($prefs->getValue('initial_page')) : 'search.php');
    exit;
}

$vars = Variables::getDefaultVariables();
$form = new Turba_CreateAddressBookForm($vars);

// Execute if the form is valid.
if ($form->validate($vars)) {
    $result = $form->execute();
    if (is_a($result, 'PEAR_Error')) {
        $notification->push($result, 'horde.error');
    } else {
        $notification->push(sprintf(_("The address book \"%s\" has been created."), $vars->get('name')), 'horde.success');
    }

    header('Location: ' . Horde::applicationUrl('addressbooks/', true));
    exit;
}

$title = $form->getTitle();
require TURBA_TEMPLATES . '/common-header.inc';
require TURBA_TEMPLATES . '/menu.inc';
echo $form->renderActive($form->getRenderer(), $vars, 'create.php', 'post');
require $registry->get('templates', 'horde') . '/common-footer.inc';
