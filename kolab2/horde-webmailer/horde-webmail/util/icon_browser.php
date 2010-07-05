<?php
/**
 * $Horde: horde/util/icon_browser.php,v 1.4.2.8 2009-01-06 15:28:05 jan Exp $
 *
 * Copyright 2004-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author Chuck Hagenbuch <chuck@horde.org>
 */

@define('AUTH_HANDLER', true);
@define('HORDE_BASE', dirname(__FILE__) . '/..');
require_once HORDE_BASE . '/lib/core.php';

$registry = &Registry::singleton();
$apps = $registry->listApps(array('notoolbar', 'active', 'admin', 'inactive', 'hidden'), true);
ksort($apps);

if (($app = basename(Util::getFormData('app'))) && isset($apps[$app])) {
    // Provide a non-white background for eyeballing transparency.
    echo '<html><body bgcolor="#aaaaaa">';

    $themeDir = $registry->get('themesfs', $app);
    if (!is_dir($themeDir)) {
        exit(sprintf(_("Themes directory \"%s\" not found."), $themeDir));
    }

    // Base graphics for now, feel free to add theme support.
    $basedir = $dir = $themeDir . DIRECTORY_SEPARATOR . 'graphics';
    if (!is_dir($dir)) {
        exit(sprintf(_("Base graphics directory \"%s\" not found."), $dir));
    }

    if (($subdir = basename(Util::getFormData('subdir')))) {
        $dir .= DIRECTORY_SEPARATOR . $subdir;
        if (!is_dir($dir)) {
            exit(sprintf(_("Subdirectory \"%s\" not found."), $dir));
        }
    }

    // Breadcrumbs.
    echo Horde::link('icon_browser.php') . _("Application List") . '</a><br />';
    if (!empty($subdir)) {
        echo Horde::link('icon_browser.php?app=' . $app) . $registry->get('name', $app) . '</a><br />';
    }
    echo '<br />';

    // Show icons for app.
    echo '<h2>' . sprintf(_("Icons for %s"), $registry->get('name', $app)) . (!empty($subdir) ? '/' . $subdir : '') . '</h2>';


    // List subdirectories.
    $subdirs = glob($dir . DIRECTORY_SEPARATOR . '*', GLOB_ONLYDIR);
    if ($subdirs && count($subdirs)) {
        foreach ($subdirs as $subdir) {
            if (basename($subdir) == 'CVS') {
                continue;
            }
            echo Horde::link(Util::addParameter('icon_browser.php', array('subdir' => basename($subdir),
                                                                          'app' => $app))) . basename($subdir) . '</a><br />';
        }
        echo '<br />';
    }

    $images = glob($dir . DIRECTORY_SEPARATOR . '*.png');
    if ($images && count($images)) {
        foreach ($images as $png) {
            echo Horde::img(str_replace($basedir . DIRECTORY_SEPARATOR, '', $png), $png, array('hspace' => 10, 'vspace' => 10), $registry->getImageDir($app));
        }
    } else {
        echo _("No icons found.");
    }

    echo '</body></html>';
} else {
    // List apps.
    foreach ($apps as $app) {
        echo Horde::link(Util::addParameter('icon_browser.php', 'app', $app)) . $registry->get('name', $app) . '</a><br />';
    }
}
