<?php
/**
 * Generates upgrade scripts for Horde's setup. Currently allows the generation
 * of PHP upgrade scripts for conf.php files either as download or saved to the
 * server's temporary directory.
 *
 * $Horde: horde/admin/setup/scripts.php,v 1.9.10.13 2009-12-07 12:31:33 jan Exp $
 *
 * Copyright 1999-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author Chuck Hagenbuch <chuck@horde.org>
 */

@define('HORDE_BASE', dirname(__FILE__) . '/../..');
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
    $path = Util::realPath($tmp_dir . '/' . $filename);
    if (@unlink($tmp_dir . '/' . $filename)) {
        $notification->push(sprintf(_("Deleted setup upgrade script \"%s\"."), $path), 'horde.success');
    } else {
        $notification->push(sprintf(_("Could not delete setup upgrade script \"%s\"."), Util::realPath($path)), 'horde.error');
    }
    $registry->clearCache();
    $url = Horde::applicationUrl('admin/setup/index.php', true);
    header('Location: ' . $url);
    exit;
}

$data = '';
if ($setup == 'conf' && $type == 'php') {
    /* A bit ugly here, save PHP code into a string for creating the script
     * to be run at the command prompt. */
    $data = '#!/usr/bin/php' . "\n";
    $data .= '<?php' . "\n";
    foreach ($_SESSION['_config'] as $app => $php) {
        $path = $registry->get('fileroot', $app) . '/config';
        /* Add code to save backup. */
        $data .= 'if (file_exists(\'' . $path . '/conf.php\')) {' . "\n";
        $data .= '    if (@copy(\'' . $path . '/conf.php\', \'' . $path . '/conf.bak.php\')) {' . "\n";
        $data .= '        echo \'Successfully saved backup configuration.\' . "\n";' . "\n";
        $data .= '    } else {' . "\n";
        $data .= '        echo \'Could NOT save a backup configuation.\' . "\n";' . "\n";
        $data .= '    }' . "\n";
        $data .= '}' . "\n";

        $data .= 'if ($fp = @fopen(\'' . $path . '/conf.php\', \'w\')) {' . "\n";
        $data .= '    fwrite($fp, \'';
        $data .= String::convertCharset(str_replace(array('\\', '\''),
                                                    array('\\\\', '\\\''),
                                                    $php),
                                        NLS::getCharset(), 'iso-8859-1');
        $data .= '\');' . "\n";
        $data .= '    fclose($fp);' . "\n";
        $data .= '    echo \'' . sprintf('Saved %s configuration.', $app) . '\' . "\n";' . "\n";
        $data .= '} else {' . "\n";
        $data .= '    echo \'' . sprintf('Could NOT save %s configuration.', $app) . '\' . "\n";' . "\n";
        $data .= '    exit;' . "\n";
        $data .= '}' . "\n\n";
    }
}

if ($save != 'tmp') {
    /* Output script to browser for download. */
    $browser->downloadHeaders($filename, 'text/plain', false, strlen($data));
    echo $data;
    exit;
}

$tmp_dir = Horde::getTempDir();
/* Add self-destruct code. */
$data .= 'echo \'Self-destructing...\' . "\n";' . "\n";
$data .= 'if (unlink(__FILE__)) {' . "\n";
$data .= '    echo \'Upgrade script deleted.\' . "\n";' . "\n";
$data .= '} else {' . "\n";
$data .= '    echo \'WARNING!!! REMOVE SCRIPT MANUALLY FROM ' . $tmp_dir . '\' . "\n";' . "\n";
$data .= '}' . "\n";
/* The script should be saved to server's temporary directory. */
$path = Util::realPath($tmp_dir . '/' . $filename);
if ($fp = @fopen($tmp_dir . '/' . $filename, 'w')) {
    fwrite($fp, $data);
    fclose($fp);
    chmod($tmp_dir . '/' . $filename, 0777);
    $notification->push(sprintf(_("Saved setup upgrade script to: \"%s\"."), $path), 'horde.success');
} else {
    $notification->push(sprintf(_("Could not save setup upgrade script to: \"%s\"."), $path), 'horde.error');
}
header('Location: ' . Horde::applicationUrl('admin/setup/index.php', true));
