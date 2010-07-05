<?php
/**
 * $Horde: horde/services/javascript.php,v 1.37.10.8 2009-01-06 15:26:20 jan Exp $
 *
 * Copyright 2000-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author Chuck Hagenbuch <chuck@horde.org>
 */

@define('HORDE_BASE', dirname(__FILE__) . '/..');
require_once HORDE_BASE . '/lib/core.php';

$registry = &Registry::singleton(HORDE_SESSION_READONLY);

// Figure out if we've been inlined, or called directly.
$send_headers = strstr($_SERVER['PHP_SELF'], 'javascript.php');

$app = Util::getFormData('app', Util::nonInputVar('app'));
$file = Util::getFormData('file', Util::nonInputVar('file'));
if (!empty($app) && !empty($file) && strpos($file, '..') === false) {
    $script_file = $registry->get('templates', $app) . '/javascript/' . $file;
    if (file_exists($script_file)) {
        $registry->pushApp($app, false);
        $script = Util::bufferOutput('require', $script_file);

        if ($send_headers) {
            /* Compress the JS. We need this explicit call since we
             * don't include base.php in this file. */
            Horde::compressOutput();

            header('Cache-Control: no-cache');
            header('Content-Type: text/javascript');
        }

        echo $script;
    }
}
