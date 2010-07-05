<?php
/**
 * $Horde: dimp/config/menu.php.dist,v 1.4.2.1 2008-03-10 20:19:35 slusarz Exp $
 *
 * This file lets you extend DIMP's menu with your own items.
 *
 * To add a new menu item, simply add a new entry to the $site_menu array.
 * Valid attributes for a new menu item are:
 *
 *  'action' - The javascript code for the menu item.
 *  'text'   - The text to accompany the menu item.
 *  'icon'   - The filename of an icon to use for the menu item.
 *
 * You can also add a "separator" (a spacer) between menu items. To add a
 * separator, simply add a new string to the $site_menu array set to the text
 * 'separator'.
 */

/* Example: */
// $site_menu = array(
//     'today' => array(
//         'action' => 'DimpBase.go("app:kronolith", "' . Horde::url($GLOBALS['registry']->get('webroot', 'kronolith') . '/day.php', true) . '")',
//         'text' => 'Today',
//         'icon' => $GLOBALS['registry']->getImageDir('kronolith') . '/dayview.png'),
//     'separator1' => 'separator',
//     'hello' => array(
//         'action' => 'alert("Hello World!")',
//         'text' => 'Say Hi!',
//         'icon' => $GLOBALS['registry']->getImageDir('horde') . '/horde.png'),
// );

// Load configuration files in .d directory
$directory = dirname(__FILE__) . '/menu.d';
if (file_exists($directory) && is_dir($directory)) {
    $sub_files = glob("$directory/*.php");
    if ($sub_files) {
        foreach ($sub_files as $sub_file) {
            require_once $sub_file;
        }
    }
 }
