<?php
/**
 * $Horde: dimp/dimple.php,v 1.16.2.3 2009-01-06 15:22:36 jan Exp $
 *
 * Copyright 2005-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 */

// As of right now, Dimples don't need read/write session access.
$session_control = 'readonly';
$session_timeout = 'none';

@define('AUTH_HANDLER', true);
@define('DIMP_BASE', dirname(__FILE__));
require_once DIMP_BASE . '/lib/base.php';
require_once DIMP_BASE . '/lib/Dimple.php';

$path_info = Util::getPathInfo();
if (empty($path_info)) {
    IMP::sendHTTPResponse(new stdClass(), 'json');
}

if ($path_info[0] == '/') {
    $path_info = substr($path_info, 1);
}
$path = explode('/', $path_info);
$dimpleName = array_shift($path);

if (!($dimple = Dimple::factory($dimpleName))) {
    IMP::sendHTTPResponse(new stdClass(), 'json');
}

$args = array();
foreach ($path as $pair) {
    if (strpos($pair, '=') === false) {
        $args[$pair] = true;
    } else {
        list($name, $val) = explode('=', $pair);
        $args[$name] = $val;
    }
}

$result = $dimple->handle($args);

if (!empty($_SERVER['Content-Type'])) {
    $ct = $_SERVER['Content-Type'];
} else {
    $ct = is_string($result) ? 'plain' : 'json';
}

IMP::sendHTTPResponse($result, $ct);
