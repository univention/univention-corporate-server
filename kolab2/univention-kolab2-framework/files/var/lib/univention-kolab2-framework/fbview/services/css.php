<?php
/**
 * $Horde: horde/services/css.php,v 1.45 2004/02/14 04:02:20 chuck Exp $
 *
 * Copyright 2000-2004 Charles J. Hagenbuch <chuck@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 */

@define('HORDE_BASE', dirname(__FILE__) . '/..');
require_once HORDE_BASE . '/lib/core.php';

$registry = &Registry::singleton(HORDE_SESSION_NONE);

// Figure out if we've been inlined, or called directly.
$send_headers = strstr($_SERVER['PHP_SELF'], 'css.php');

// Set initial $mtime of this script.
$mtime = getlastmod();

if (@file_exists(HORDE_BASE . '/config/conf.php')) {
    require HORDE_BASE . '/config/conf.php';
} else {
    $conf['css']['cached'] = false;
}

$theme = Util::getFormData('theme');
if (Util::getFormData('inherit') !== 'no') {
    if (@file_exists(HORDE_BASE . '/config/html.php')) {
        $file = HORDE_BASE . '/config/html.php';
    } else {
        $file = HORDE_BASE . '/config/html.php.dist';
    }
    if ($conf['css']['cached']) {
        $hmtime = filemtime($file);
        if ($hmtime > $mtime) {
            $mtime = $hmtime;
        }
    }
    require $file;
    if (!empty($theme) && @file_exists(HORDE_BASE . '/config/themes/html-' . $theme . '.php')) {
        $file = HORDE_BASE . '/config/themes/html-' . $theme . '.php';
        if ($conf['css']['cached']) {
            $hmtime = filemtime($file);
            if ($hmtime > $mtime) {
                $mtime = $hmtime;
            }
        }
        require $file;
    }
}

$apps = Util::getFormData('app');
if (!empty($apps)) {
    if (!is_array($apps)) {
        $apps = array($apps);
    }
    foreach ($apps as $app) {
        $conf_file = $registry->applicationFilePath('%application%/config/conf.php', $app);
        if (@file_exists($conf_file)) {
            require $conf_file;
        }

        $file = '';
        if (@file_exists($registry->applicationFilePath('%application%/config/html.php', $app))) {
            $file = $registry->applicationFilePath('%application%/config/html.php', $app);
        } elseif (@file_exists($registry->applicationFilePath('%application%/config/html.php.dist', $app))) {
            $file = $registry->applicationFilePath('%application%/config/html.php.dist', $app);
        }
        if (!empty($file)) {
            if ($conf['css']['cached']) {
                $amtime = filemtime($file);
                if ($amtime > $mtime) {
                    $mtime = $amtime;
                }
            }
            require $file;
        }
        if (!empty($theme) && @file_exists($registry->applicationFilePath('%application%/config/themes/html-' . $theme . '.php', $app))) {
            $file = $registry->applicationFilePath('%application%/config/themes/html-' . $theme . '.php', $app);
            if ($conf['css']['cached']) {
                $amtime = filemtime($file);
                if ($amtime > $mtime) {
                    $mtime = $amtime;
                }
            }
            require $file;
        }
    }
}

if ($send_headers) {
    /* Compress the CSS. We need this explicit call since we don't call
     * base.php in this file. */
    Horde::compressOutput();

    if ($conf['css']['cached']) {
        $mod_gmt = gmdate('D, d M Y H:i:s', $mtime) . ' GMT';
        header('Last-Modified: ' . $mod_gmt);
        header('Cache-Control: public, max-age=86400');
    } else {
        header('Expires: -1');
        header('Pragma: no-cache');
        header('Cache-Control: no-store, no-cache, must-revalidate, post-check=0, pre-check=0');
    }
    header('Content-Type: text/css; charset=iso-8859-1');
}

if (is_array($css)) {
    foreach ($css as $class => $params) {
        echo "$class {\n";
        if (is_array($params)) {
            foreach ($params as $key => $val) {
                if (is_array($val)) {
                    echo "$key {\n";
                    foreach ($val as $skey => $sval) {
                        echo "    $skey: $sval;\n";
                    }
                    echo "}\n";
                } else {
                    echo "    $key: $val;\n";
                }
            }
        }
        echo "}\n";
    }
}
