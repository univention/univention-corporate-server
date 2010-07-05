<?php

$site_menu = array(
    'folders' => array(
        'action' => 'DimpCore.DMenu.close(); DimpBase.go("app:horde", "' . Horde::url($GLOBALS['registry']->get('webroot', 'imp') . '/folders.php', true) . '")',
        'text' => _('Folder Subscription'),
        'icon' => $GLOBALS['registry']->getImageDir('horde') . '/prefs.png'),
);
