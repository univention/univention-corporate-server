<?php
/**
 * $Horde: kronolith/imple.php,v 1.1.2.3 2008/04/25 03:50:58 chuck Exp $
 *
 * Copyright 2005-2008 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author Michael Slusarz <slusarz@horde.org>
 */

function impleLogout() 
{
    Auth::clearAuth();
    @session_destroy();
}

@define('AUTH_HANDLER', true);
@define('HORDE_BASE', dirname(__FILE__) . '/..');
require_once HORDE_BASE . '/lib/base.php';

// We want to always generate UTF-8 iCalendar data.
NLS::setCharset('UTF-8');

$auth = &Auth::singleton('kolab');

if (isset($conf['ics']['default_user'])
    && isset($conf['ics']['default_pass'])) {
    $user = $conf['ics']['default_user'];
    $pass = $conf['ics']['default_pass'];
    $_SESSION = array();
    $auth->authenticate($user,
                        array('password' =>
                              $pass));
    register_shutdown_function('impleLogout');
}   

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
    header('Content-Type: text/x-json');
    require_once KRONOLITH_BASE . '/lib/JSON.php';
    echo Kronolith_Serialize_JSON::encode(String::convertCharset($result, NLS::getCharset(), 'utf-8'));
    break;

case 'plain':
    header('Content-Type: text/plain');
    echo $result;
    break;

case 'html':
    header('Content-Type: text/html');
    echo $result;
    break;

default:
    echo $result;
}