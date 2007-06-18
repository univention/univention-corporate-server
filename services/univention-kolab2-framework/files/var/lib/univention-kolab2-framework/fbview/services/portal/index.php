<?php
/**
 * $Horde: horde/services/portal/index.php,v 1.33 2004/05/29 16:06:27 jan Exp $
 *
 * Copyright 2003-2004 Mike Cochrane <mike@graftonhall.co.nz>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 */

@define('HORDE_BASE', dirname(__FILE__) . '/../..');
require_once HORDE_BASE . '/lib/base.php';
require_once 'Horde/Block.php';
require_once 'Horde/Identity.php';
require_once 'Horde/Menu.php';
require_once 'Horde/Help.php';

if (!Auth::isAuthenticated()) {
    Horde::authenticationFailureRedirect();
}

// Get full name for title
$identity = &Identity::singleton();
$fullname = $identity->getValue('fullname');
if (empty($fullname)) {
    $fullname = Auth::getAuth();
}

// Get refresh interval.
if ($prefs->getValue('summary_refresh_time')) {
    $refresh_time = $prefs->getValue('summary_refresh_time');
    $refresh_url = Horde::applicationUrl('services/portal/');
}

// Load layout from preferences.
$layout_pref = @unserialize($prefs->getValue('portal_layout'));
if (!is_array($layout_pref)) {
    $layout_pref = array();
}

// Store the apps we need to load stylesheets for.
$cssApps = array();
foreach ($layout_pref as $row) {
    foreach ($row as $item) {
        if (is_array($item) && !in_array($item['app'], $cssApps)) {
            $cssApps[] = $item['app'];
        }
    }
}

$title = _("My Portal");
$cssApp = 'app[]=' . implode(ini_get('arg_separator.output') . 'app[]=', $cssApps);
require HORDE_TEMPLATES . '/common-header.inc';
require HORDE_TEMPLATES . '/portal/menu.inc';
Help::javascript();
$notification->notify(array('listeners' => 'status'));
require HORDE_TEMPLATES . '/portal/header.inc';

$covered = array();
foreach ($layout_pref as $row_num => $row) {
    $width = floor(100 / count($row));
    echo "<tr>\n";
    foreach ($row as $col_num => $item) {
        if (isset($covered[$row_num]) && isset($covered[$row_num][$col_num])) {
            continue;
        }
        if (is_array($item)) {
            $block = $registry->callByPackage($item['app'], 'block', $item['params']);
            if (is_a($block, 'Horde_Block')) {
                $rowspan = $item['height'];
                $colspan = $item['width'];
                $header  = $block->getTitle();
                $content = $block->getContent();
                require HORDE_TEMPLATES . '/portal/block.inc';
                for ($i = 0; $i < $item['height']; $i++) {
                    if (!isset($covered[$row_num + $i])) {
                        $covered[$row_num + $i] = array();
                    }
                    for ($j = 0; $j < $item['width']; $j++) {
                        $covered[$row_num + $i][$col_num + $j] = true;
                    }
                }
            } else {
                require HORDE_TEMPLATES . '/portal/empty.inc';
            }
        } else {
            require HORDE_TEMPLATES . '/portal/empty.inc';
        }
    }
    echo "</tr>\n";
}

require HORDE_TEMPLATES . '/portal/footer.inc';
require HORDE_TEMPLATES . '/common-footer.inc';
