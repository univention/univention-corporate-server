<?php
/**
 * $Horde: horde/services/prefs.php,v 1.19.2.17 2009-01-06 15:26:20 jan Exp $
 *
 * Copyright 1999-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author Chuck Hagenbuch <chuck@horde.org>
 * @author Jan Schneider <jan@horde.org>
 */

@define('HORDE_BASE', dirname(__FILE__) . '/..');
require_once HORDE_BASE . '/lib/core.php';
require_once 'Horde/Prefs/UI.php';

$registry = &Registry::singleton();

/* Figure out which application we're setting preferences for. */
$app = Util::getFormData('app', Prefs_UI::getDefaultApp());
$appbase = realpath($registry->get('fileroot', $app));

/* See if we have a preferences group set. */
$group = Util::getFormData('group');

/* See if only a page body was requested. */
$chunk = Util::nonInputVar('chunk');

/* Load $app's base environment, but don't request that the app perform
 * authentication beyond Horde's. */
$authentication = 'none';
require_once $appbase . '/lib/base.php';

/* Set title. */
$title = sprintf(_("Options for %s"), $registry->get('name'));

/* Load identity here - Identity object may be needed in app's prefs.php. */
if ($group == 'identities') {
    require_once 'Horde/Identity.php';
    $identity = &Identity::singleton($app == 'horde' ? null : array($app, $app));
}

/* Load $app's preferences, if any. */
$prefGroups = array();
$result = Horde::loadConfiguration('prefs.php', array('prefGroups', '_prefs'), $app);
if (!is_a($result, 'PEAR_Error')) {
    extract($result);
}

/* See if this group has a custom URL. */
if ($group && !empty($prefGroups[$group]['url'])) {
    $pref_url = $prefGroups[$group]['url'];
    $filename = realpath($appbase . '/' . $pref_url);
    if (file_exists($filename) &&
        (strpos($filename, $appbase) === 0)) {
        require $filename;
        return;
    }
    Horde::fatal('Incorrect url value (' . $pref_url . ') for preferences group ' . $group . ' for app ' . $app, __FILE__, __LINE__);
}

/* Load custom preference handlers for $app, if present. */
if (file_exists($appbase . '/lib/prefs.php')) {
    require_once $appbase . '/lib/prefs.php';
}

/* If there's only one prefGroup, just show it. */
if (empty($group) && count($prefGroups) == 1) {
    $group = array_keys($prefGroups);
    $group = array_pop($group);
}

if ($group == 'identities') {
    if ($app != 'horde') {
        $result = Horde::loadConfiguration('prefs.php', array('prefGroups', '_prefs'), 'horde');
        if (!is_a($result, 'PEAR_Error')) {
            require_once 'Horde/Array.php';
            $prefGroups['identities']['members'] = array_keys(array_flip(array_merge(
                $result['prefGroups']['identities']['members'],
                $prefGroups['identities']['members'])));
            $_prefs = Horde_Array::array_merge_recursive_overwrite($result['_prefs'], $_prefs);
        }
    }

    switch (Util::getFormData('actionID')) {
    case 'update_prefs':
        $from_addresses = $identity->getAll('from_addr');
        $current_from = $identity->getValue('from_addr');
        if ($prefs->isLocked('default_identity')) {
            $default = $identity->getDefault();
        } else {
            $default = Util::getPost('default_identity');
            $id = Util::getPost('identity');
            if ($id == -1) {
                $id = $identity->add();
            } elseif ($id == -2) {
                $prefGroups['identities']['members'] = array('default_identity');
            }
            $identity->setDefault($id);
        }

        if (!Prefs_UI::handleForm($group, $identity)) {
            break;
        }

        $new_from = $identity->getValue('from_addr');
        if (!empty($conf['user']['verify_from_addr']) &&
            $current_from != $new_from &&
            !in_array($new_from, $from_addresses)) {
            $result = $identity->verifyIdentity($id, empty($current_from) ? $new_from : $current_from);
            if (is_a($result, 'PEAR_Error')) {
                $notification->push(_("The new from address can't be verified, try again later: ") . $result->getMessage(), 'horde.error');
                Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
            } elseif (is_a($result, 'Notification_Event')) {
                $notification->push($result, 'horde.message');
            }
            break;
        }

        $identity->setDefault($default);
        $identity->save();
        unset($prefGroups);
        $result = Horde::loadConfiguration('prefs.php', array('prefGroups', '_prefs'), $app);
        if (!is_a($result, 'PEAR_Error')) {
            extract($result);
        }
        break;

    case 'delete_identity':
        $id = (int)Util::getFormData('id');
        $deleted_identity = $identity->delete($id);
        unset($_prefs['default_identity']['enum'][$id]);
        $notification->push(sprintf(_("The identity \"%s\" has been deleted."), $deleted_identity[0]['id']), 'horde.success');
        break;

    case 'change_default_identity':
        $default_identity = $identity->setDefault(Util::getFormData('id'));
        $identity->save();
        $notification->push(_("Your default identity has been changed."),
                            'horde.success');
        break;
    }
} elseif (Prefs_UI::handleForm($group, $prefs)) {
    $result = Horde::loadConfiguration('prefs.php', array('prefGroups', '_prefs'), $app);
    if (!is_a($result, 'PEAR_Error')) {
        extract($result);
    }
    if (count($prefGroups) == 1 && empty($group)) {
        $group = array_keys($prefGroups);
        $group = array_pop($group);
    }
}

/* Show the UI. */
Prefs_UI::generateUI($group, $chunk);

if (!$chunk) {
    require $registry->get('templates', 'horde') . '/common-footer.inc';
}
