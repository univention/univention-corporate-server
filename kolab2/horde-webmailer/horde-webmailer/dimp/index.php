<?php
/**
 * $Horde: dimp/index.php,v 1.59.2.13 2009-01-06 15:22:36 jan Exp $
 *
 * Copyright 2005-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author Jan Schneider <jan@horde.org>
 */

@define('DIMP_BASE', dirname(__FILE__));
$dimp_configured = (is_readable(DIMP_BASE . '/config/conf.php') &&
                    is_readable(DIMP_BASE . '/config/portal.php') &&
                    is_readable(DIMP_BASE . '/config/prefs.php'));

if (!$dimp_configured) {
    require DIMP_BASE . '/../lib/Test.php';
    Horde_Test::configFilesMissing('DIMP', DIMP_BASE,
                                   array('conf.php', 'prefs.php'),
                                   array('portal.php' => 'This file controls the blocks that appear in DIMP\'s portal'));
}

$load_imp = true;
require_once DIMP_BASE . '/lib/base.php';

$scripts = array(
    array('DimpBase.js', 'dimp', true),
    array('ContextSensitive.js', 'dimp', true),
    array('ViewPort.js', 'dimp', true),
    array('dragdrop.js', 'dimp', true),
    array('dhtmlHistory.js', 'horde', true),
    array('redbox.js', 'horde', true),
    array('mailbox.js', 'dimp'),
    array('DimpSlider.js', 'dimp', true),
    array('unblockImages.js', 'imp', true)
);

/* Get site specific menu items. */
$js_code = $site_menu = array();
if (is_readable(DIMP_BASE . '/config/menu.php')) {
    include DIMP_BASE . '/config/menu.php';
}

/* Add the site specific javascript now. */
if (!empty($site_menu)) {
    foreach ($site_menu as $key => $menu_item) {
        if ($menu_item == 'separator') {
            continue;
        }
        $js_code[] = 'DimpCore.clickObserveHandler({ d: $(\'menu' . $key . '\'), f: function() { ' . $menu_item['action'] . ' } })';
        $js_code[] = 'DimpCore.clickObserveHandler({ d: $(\'tab' . $key . '\'), f: function() { ' . $menu_item['action'] . ' } })';
    }
}

IMP::addInlineScript($js_code, true);
DIMP::header('', $scripts);

/* Get application folders list. */
$application_folders = array();
foreach (DIMP::menuList() as $app) {
    if ($registry->get('status', $app) != 'inactive' &&
        $registry->hasPermission($app, PERMS_SHOW)) {
        $application_folders[] = array(
            'name' => htmlspecialchars($registry->get('name', $app)),
            'icon' => $registry->get('icon', $app),
            'app' => rawurlencode($app)
        );
    }
}

echo "<body>\n";
require DIMP_TEMPLATES . '/index/index.inc';
DIMP::outputJS();
$notification->notify(array('listeners' => array('javascript')));
echo "</body>\n</html>";
