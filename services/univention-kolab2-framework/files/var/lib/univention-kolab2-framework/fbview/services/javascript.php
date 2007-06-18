<?php
/**
 * $Horde: horde/services/javascript.php,v 1.34 2004/03/03 08:38:18 jan Exp $
 *
 * Copyright 2000-2004 Charles J. Hagenbuch <chuck@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 */

@define('HORDE_BASE', dirname(__FILE__) . '/..');
require_once HORDE_BASE . '/lib/core.php';

$registry = &Registry::singleton(HORDE_SESSION_READONLY);

// Figure out if we've been inlined, or called directly.
$send_headers = strstr($_SERVER['PHP_SELF'], 'javascript.php');

$app = Util::getFormData('app');
$file = Util::getFormData('file');
if (!empty($app) && !empty($file) && strpos($file, '..') === false) {
    $script_file = $registry->getParam('templates', $app) . '/javascript/' . $file;
    if (@file_exists($script_file)) {
        $registry->pushApp($app);
        $script = Util::bufferOutput('require', $script_file);

        if ($send_headers) {
            /* Compress the JS. We need this explicit call since we
             * don't include base.php in this file. */
            Horde::compressOutput();

            $mod_gmt = gmdate('D, d M Y H:i:s', filemtime($script_file)) . ' GMT';
            header('Last-Modified: ' . $mod_gmt);
            header('Cache-Control: public, max-age=86400');
            header('Content-Type: text/javascript');
        }

        echo $script;
    }
}
