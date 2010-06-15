<?php
/**
 * $Horde: horde/lib/prefs.php,v 1.9 2004/05/27 17:50:29 chuck Exp $
 *
 * Copyright 1999-2004 Charles J. Hagenbuch <chuck@horde.org>
 * Copyright 1999-2004 Jon Parise <jon@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL).  If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 */

function handle_showsummaryselect($updated)
{
    global $prefs;

    $show_summaries = Util::getFormData('show_summaries');
    if (!is_null($show_summaries)) {
        $prefs->setValue('show_summaries', $show_summaries);
        $updated = true;
    }

    return $updated;
}

function handle_themeselect($updated)
{
    global $prefs;

    $theme = Util::getFormData('theme');
    if (!is_null($theme)) {
        $prefs->setValue('theme', $theme);
        $updated = true;
    }

    return $updated;
}

function handle_categorymanagement($updated)
{
    require_once 'Horde/Prefs/CategoryManager.php';
    $cManager = &new Prefs_CategoryManager();

    /* Always save colors. */
    $colors = $cManager->colors();
    foreach (array_keys($colors) as $category) {
        if ($color = Util::getFormData('color_' . base64_encode($category))) {
            $colors[$category] = $color;
        }
    }
    $cManager->setColors($colors);

    $action = Util::getFormData('cAction');
    $category = Util::getFormData('category');

    switch ($action) {
    case 'add':
        $cManager->add($category);
        break;

    case 'remove':
        $cManager->remove($category);
        break;

    default:
        /* Save button. */
        $updated = true;
    }

    return $updated;
}

/* Assign variables for select lists. */
if (!$prefs->isLocked('timezone')) {
    $timezone_options = &$tz;
}
if (!$prefs->isLocked('initial_application')) {
    global $perms;

    $initial_application_options = array();
    $apps = $registry->listApps(array('active'));
    foreach ($apps as $a) {
        if (($perms->exists($a) && ($perms->hasPermission($a, Auth::getAuth(), PERMS_READ) || Auth::isAdmin())) ||
            !$perms->exists($a)) {
            $initial_application_options[$a] = $registry->getParam('name', $a);
        }
    }
}
if (!$prefs->isLocked('theme')) {
    $theme_options = array();
    $dh = @opendir($appbase . '/config/themes');
    if (!$dh) {
        $notification->push("Theme directory can't be opened", 'horde.error');
    } else {
        while (($file = readdir($dh)) !== false) {
            if (substr($file, 0, 5) != 'html-' && substr($file, -4) == '.php') {
                $theme_name = null;
                @include $appbase . '/config/themes/' . $file;
                if (!empty($theme_name)) {
                    $theme_options[substr($file, 0, -4)] = $theme_name;
                }
            }
        }
    }
    asort($theme_options);
    $theme_options = array_merge(
        array('' => sprintf(_("%s Standard"), $GLOBALS['registry']->getParam('name'))),
        $theme_options
    );
}
