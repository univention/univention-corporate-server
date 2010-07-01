<?php
/**
 * $Horde: imp/imple.php,v 2.7.2.3 2009-01-06 15:24:01 jan Exp $
 *
 * Copyright 2005-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author Michael Slusarz <slusarz@horde.org>
 */

@define('IMP_BASE', dirname(__FILE__));
$authentication = 'horde';
require_once IMP_BASE . '/lib/base.php';
require_once IMP_BASE . '/lib/Imple.php';

if (!($path = Util::getFormData('imple'))) {
    exit;
}
if ($path[0] == '/') {
    $path = substr($path, 1);
}
$path = explode('/', $path);
$impleName = array_shift($path);

if (!($imple = Imple::factory($impleName))) {
    exit;
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

$result = $imple->handle($args);

if (!empty($_SERVER['Content-Type'])) {
    $ct = $_SERVER['Content-Type'];
} else {
    $ct = is_string($result) ? 'plain' : 'json';
}

IMP::sendHTTPResponse($result, $ct);
