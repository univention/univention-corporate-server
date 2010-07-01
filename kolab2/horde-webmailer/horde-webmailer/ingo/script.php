<?php
/**
 * $Horde: ingo/script.php,v 1.33.6.7 2009-01-06 15:24:34 jan Exp $
 *
 * Copyright 2002-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file LICENSE for license information (ASL).  If you
 * did not receive this file, see http://www.horde.org/licenses/asl.php.
 *
 * @author Mike Cochrane <mike@graftonhall.co.nz>
 */

@define('INGO_BASE',  dirname(__FILE__));
require_once INGO_BASE . '/lib/base.php';

/* Redirect if script updating is not available. */
if (!$_SESSION['ingo']['script_generate']) {
    header('Location: ' . Horde::applicationUrl('filters.php', true));
    exit;
}

$script = '';

/* Get the Ingo_Script:: backend. */
$scriptor = Ingo::loadIngoScript();
if ($scriptor) {
    /* Generate the script. */
    $script = $scriptor->generate();
}

/* Activate/deactivate script if requested.
   activateScript() does its own $notification->push() on error. */
$actionID = Util::getFormData('actionID');
switch ($actionID) {
case 'action_activate':
    if (!empty($script)) {
        Ingo::activateScript($script);
    }
    break;

case 'action_deactivate':
    Ingo::activateScript('', true);
    break;

case 'show_active':
    $script = Ingo::getScript();
    if (is_a($script, 'PEAR_Error')) {
        $notification->push($script, 'horde.error');
        $script = '';
    }
    break;
}

$title = _("Filter Script Display");
require INGO_TEMPLATES . '/common-header.inc';
require INGO_TEMPLATES . '/menu.inc';
require INGO_TEMPLATES . '/script/header.inc';
if (!empty($script)) {
    require INGO_TEMPLATES . '/script/activate.inc';
}
require INGO_TEMPLATES . '/script/script.inc';
if (!empty($script)) {
    $lines = preg_split('(\r\n|\n|\r)', $script);
    $i = 0;
    foreach ($lines as $line) {
        printf("%3d: %s\n", ++$i, htmlspecialchars($line));
    }
} else {
    echo '[' . _("No script generated.") . ']';
}

require INGO_TEMPLATES . '/script/footer.inc';
require $registry->get('templates', 'horde') . '/common-footer.inc';
