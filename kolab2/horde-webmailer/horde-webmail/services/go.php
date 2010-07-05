<?php
/**
 * A script to redirect to a given URL, used for example in IMP to hide any
 * referrer data being passed to the remote server and potentially exposing
 * any session IDs.
 *
 * Copyright 2003-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * $Horde: horde/services/go.php,v 1.6.2.21 2009-01-06 15:26:20 jan Exp $
 *
 * @author Marko Djukic <marko@oblo.com>
 */

$session_control = 'none';
@define('AUTH_HANDLER', true);
require_once dirname(__FILE__) . '/../lib/base.php';

if (empty($_GET['url'])) {
    exit;
}

$url = trim($_GET['url']);
if (preg_match('/;\s*url\s*=/i', $url)) {
    // IE will process the last ;URL= string, not the first, allowing
    // protocols that shouldn't be let through.
    exit;
}

// Check the HMAC
if (!Horde::verifySignedQueryString($_SERVER['QUERY_STRING'])) {
    exit;
}

if (get_magic_quotes_gpc()) {
    $parsed_url = @parse_url(stripslashes($url));
} else {
    $parsed_url = @parse_url($url);
}

if (empty($parsed_url) || empty($parsed_url['host'])) {
    exit;
}
if (empty($parsed_url['path'])) {
    $parsed_url['path'] = false;
}

// Do a little due diligence on the target URL. If it's on the same server
// that we're already on, display an intermediate page asking people if
// they're sure they want to click through.
if (!strncmp(PHP_SAPI, 'cgi', 3)) {
    // When using CGI PHP, SCRIPT_NAME may contain the path to the PHP binary
    // instead of the script being run; use PHP_SELF instead.
    $myurl = $_SERVER['PHP_SELF'];
} else {
    $myurl = isset($_SERVER['SCRIPT_NAME']) ?
        $_SERVER['SCRIPT_NAME'] :
        $_SERVER['PHP_SELF'];
}
// 16 is the length of "/services/go.php".
$webroot = substr($myurl, 0, -16);

// Build a list of hosts considered dangerous (local hosts, the user's
// host, etc).
$dangerous_hosts = array('localhost', 'localhost.localdomain', '127.0.0.1');
if (!empty($_SERVER['SERVER_NAME'])) {
    $dangerous_hosts[] = $_SERVER['SERVER_NAME'];
}
if (!empty($_SERVER['HTTP_HOST'])) {
    $dangerous_hosts[] = $_SERVER['HTTP_HOST'];
}

// List of allowed services.
$allowed_uris = array($webroot . '/services/confirm.php');

// Check against our lists.
if ((empty($webroot) || strpos($parsed_url['path'], $webroot) === 0) &&
    !empty($parsed_url['query']) &&
    !in_array($parsed_url['path'], $allowed_uris) &&
    in_array($parsed_url['host'], $dangerous_hosts)) {
?>
<html>
<head>
<title>Potentially Dangerous URL</title>
</head>
<body>
 <h1>Potentially Dangerous URL</h1>

 <p>
  A referring site, an email you were reading, or some other
  potentially untrusted source has attempted to send you to <?php echo
  htmlspecialchars($url) ?>. This may be an attempt to
  delete data or change settings without your knowledge. If
  you have any concerns about this URL, please contact your
  System Administrator. If you are confident that it is safe,
  you may follow the link by clicking below.
 </p>

 <p>
  <a href="<?php echo htmlspecialchars($url) ?>"><?php echo htmlspecialchars($url) ?></a>
 </p>

</body>
</html>
<?php
    exit;
}

header('Refresh: 0; URL=' . $url);
