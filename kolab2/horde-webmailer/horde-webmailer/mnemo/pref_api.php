<?php
/**
 * $Horde: mnemo/pref_api.php,v 1.1.2.5 2009-01-06 15:24:57 jan Exp $
 *
 * Copyright 2006-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author Chuck Hagenbuch <chuck@horde.org>
 */

@define('HORDE_BASE', dirname(dirname(__FILE__)));
require_once HORDE_BASE . '/lib/core.php';

$registry = &Registry::singleton();

/* Which application. */
$app = Util::getFormData('app');
if (!$app) {
    echo '<ul id="app">';
    foreach ($registry->listApps() as $app) {
        echo '<li>' . htmlspecialchars($app) . '</li>';
    }
    echo '</ul>';
    exit;
}

/* Load $app's base environment, but don't request that the app perform
 * authentication beyond Horde's. */
$authentication = 'none';
$appbase = $registry->get('fileroot', $app);
require_once $appbase . '/lib/base.php';

/* Which preference. */
$pref = Util::getFormData('pref');
if (!$pref) {
    $_prefs = array();
    if (is_callable(array('Horde', 'loadConfiguration'))) {
        $result = Horde::loadConfiguration('prefs.php', array('_prefs'), $app);
        if (is_a($result, 'PEAR_Error')) {
            exit;
        }
        extract($result);
    } elseif (file_exists($appbase . '/config/prefs.php')) {
        require $appbase . '/config/prefs.php';
    }

    echo '<ul id="pref">';
    foreach ($_prefs as $pref => $params) {
        switch ($params['type']) {
        case 'special':
        case 'link':
            break;

        default:
            echo '<li preftype="' . htmlspecialchars($params['type']) . '">' . htmlspecialchars($pref) . '</li>';
        }
    }
    echo '</ul>';
}

/* Which action. */
if (Util::getPost('pref') == $pref) {
    /* POST for saving a pref. */
    $prefs->setValue($pref, Util::getPost('value'));
}

/* GET returns the current value, POST returns the new value. */
header('Content-type: text/plain');
echo $prefs->getValue($pref);
