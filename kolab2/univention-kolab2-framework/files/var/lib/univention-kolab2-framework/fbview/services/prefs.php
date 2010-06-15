<?php
/**
 * $Horde: horde/services/prefs.php,v 1.12 2004/05/08 21:54:48 jan Exp $
 *
 * Copyright 1999-2004 Charles J. Hagenbuch <chuck@horde.org>
 * Copyright 1999-2004 Jon Parise <jon@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 */

@define('HORDE_BASE', dirname(__FILE__) . '/..');
require_once dirname(__FILE__) . '/../lib/core.php';
require_once 'Horde/Prefs/UI.php';

$registry = &Registry::singleton();

/* Figure out which application we're setting preferences for. */
$app = Util::getFormData('app', Prefs_UI::getDefaultApp());
$appbase = $registry->getParam('fileroot', $app);

/* See if we have a preferences group set. */
$group = Util::getFormData('group');

/* Load $app's base environment. */
require_once $appbase . '/lib/base.php';

if ($group == 'identities') {
    require_once 'Horde/Identity.php';
    $identity = &Identity::singleton($app == 'horde' ? null : array($app, $app));
    if ($app != 'horde') {
        require HORDE_BASE . '/config/prefs.php';
        $horde_members = $prefGroups['identities']['members'];
    }
}

/* Load $app's preferences, if any. */
if (file_exists($appbase . '/config/prefs.php')) {
    require $appbase . '/config/prefs.php';
}

/* Load custom preference handlers for $app, if present. */
if (file_exists($appbase . '/lib/prefs.php')) {
    require_once $appbase . '/lib/prefs.php';
}

if ($group == 'identities') {
    if (isset($horde_members)) {
        $prefGroups['identities']['members'] = array_merge($horde_members, $prefGroups['identities']['members']);
    }
    switch (Util::getFormData('actionID')) {
    case 'update_prefs':
        $default = Util::getFormData('default_identity');
        $id = Util::getFormData('identity');
        if ($id == -1) {
            $id = $identity->add();
        } elseif ($id == -2) {
            $prefGroups['identities']['members'] = array('default_identity');
        }
        $identity->setDefault($id);
        if (Prefs_UI::handleForm($group, $identity)) {
            $identity->setDefault($default);
            $result = $identity->verify();
            if (is_a($result, 'PEAR_Error')) {
                $notification->push($result, 'horde.error');
            } else {
                $identity->save();
            }
        } else {
            $identity->setDefault($default);
            $identity->save();
        }
        unset($prefGroups);
        require $appbase . '/config/prefs.php';
        break;
    case 'delete_identity':
        $deleted_identity = $identity->delete(Util::getFormData('id'));
        $notification->push(sprintf(_("The identity \"%s\" has been deleted."), $deleted_identity[0]['id']), 'horde.success');
        break;
    }
} elseif (Prefs_UI::handleForm($group, $prefs)) {
    require $appbase . '/config/prefs.php';
}

/* Show the UI. */
Prefs_UI::generateUI($group);

require $registry->getParam('templates', 'horde') . '/common-footer.inc';
