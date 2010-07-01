<?php
/**
 * $Horde: kronolith/imple.php,v 1.1.2.5 2009-10-15 10:07:50 jan Exp $
 *
 * Copyright 2005-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author Michael Slusarz <slusarz@horde.org>
 */

@define('KRONOLITH_BASE', dirname(__FILE__));
require_once KRONOLITH_BASE . '/lib/base.php';
require_once KRONOLITH_BASE . '/lib/Imple.php';

$path = Util::getFormData('imple');
if (!$path) {
    exit;
}
if ($path[0] == '/') {
    $path = substr($path, 1);
}
$path = explode('/', $path);
$impleName = array_shift($path);

$imple = Imple::factory($impleName);
if (!$imple) {
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

switch ($ct) {
case 'json':
    header('Content-Type: text/x-json; charset=' . NLS::getCharset());
    require_once KRONOLITH_BASE . '/lib/JSON.php';
    echo Kronolith_Serialize_JSON::encode(String::convertCharset($result, NLS::getCharset(), 'utf-8'));
    break;

case 'plain':
    header('Content-Type: text/plain; charset=' . NLS::getCharset());
    echo $result;
    break;

case 'html':
    header('Content-Type: text/html; charset=' . NLS::getCharset());
    echo $result;
    break;

default:
    echo $result;
}
