<?php
/**
 * Generates upgrade scripts for Horde's setup. Currently allows the generation
 * of PHP upgrade scripts for conf.php files either as download or saved to the
 * server's temporary directory.
 *
 * $Horde: horde/admin/setup/scripts.php,v 1.5 2004/02/04 13:43:48 mdjukic Exp $
 *
 * Copyright 1999-2004 Charles J. Hagenbuch <chuck@horde.org>
 * Copyright 1999-2004 Jon Parise <jon@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL).  If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 */

define('HORDE_BASE', dirname(__FILE__) . '/../..');
require_once HORDE_BASE . '/lib/base.php';

if (!Auth::isAdmin()) {
    Horde::fatal('Forbidden.', __FILE__, __LINE__);
}

/* Get form data. */
$setup = Util::getFormData('setup');
$type = Util::getFormData('type');
$save = Util::getFormData('save');
$clean = Util::getFormData('clean');

$filename = 'horde_setup_upgrade.php';

/* Check if this is only a request to clean up. */
if ($clean == 'tmp') {
    $tmp_dir = Horde::getTempDir();
    if (unlink($tmp_dir . '/' . $filename)) {
        $notification->push(sprintf(_("Deleted setup upgrade script '%s'."), $tmp_dir . '/' . $filename), 'horde.success');
    } else {
        $notification->push(sprintf(_("Could not delete setup upgrade script '%s'."), $tmp_dir . '/' . $filename), 'horde.error');
    }
    $url = Horde::applicationUrl('admin/setup/index.php', true);
    header('Location: ' . $url);
    exit;
}

$data = '';
if ($setup == 'conf' && $type == 'php') {
    /* A bit ugly here, save PHP code into a string for creating the script
     * to be run at the command prompt. */
    $data = '#!/usr/local/bin/php' . "\n";
    $data .= '<?php' . "\n";
    foreach ($_SESSION['_config'] as $app => $php) {
        $path = $registry->getParam('fileroot', $app) . '/config';
        $data .= 'if ($fp = @fopen(\'' . $path . '/conf.php\', \'w\')) {' . "\n";
        $data .= '    fwrite($fp, \'';
        $data .= String::convertCharset(addslashes($php), NLS::getCharset(), 'iso-8859-1');
        $data .= '\');' . "\n";
        $data .= '    fclose($fp);' . "\n";
        $data .= '    echo \'' . sprintf(_("Saved %s configuration."), $app) . '\' . "\n";' . "\n";
        $data .= '} else {' . "\n";
        $data .= '    echo \'' . sprintf(_("Could not save %s configuration."), $app) . '\' . "\n";' . "\n";
        $data .= '}' . "\n\n";
    }
}

if ($save == 'tmp') {
    $tmp_dir = Horde::getTempDir();
    /* Add self-destruct code. */
    $data .= 'echo \'Self-destructing...\' . "\n";' . "\n";
    $data .= 'if (unlink(__FILE__)) {' . "\n";
    $data .= '    echo \'' . _("Upgrade script deleted.") . '\' . "\n";' . "\n";
    $data .= '} else {' . "\n";
    $data .= '    echo \'' . sprintf(_("WARNING!!! REMOVE SCRIPT MANUALLY FROM %s."), $tmp_dir) . '\' . "\n";' . "\n";
    $data .= '}' . "\n";
    /* The script should be saved to server's temporary directory. */
    if ($fp = @fopen($tmp_dir . '/' . $filename, 'w')) {;
        fwrite($fp, $data);
        fclose($fp);
        chmod($tmp_dir . '/' . $filename, 0777);
        $notification->push(sprintf(_("Saved setup upgrade script to: '%s'."), $tmp_dir . '/' . $filename), 'horde.success');
    } else {
        $notification->push(sprintf(_("Could not save setup upgrade script to: '%s'."), $tmp_dir . '/' . $filename), 'horde.error');
    }
    $url = Horde::applicationUrl('admin/setup/index.php', true);
    header('Location: ' . $url);
    exit;
} else {
    /* Output script to browser for download. */
    $browser->downloadHeaders($filename, 'text/plain', false, strlen($data));
    echo $data;
}
