<?php
/*
 *  Copyright (c) 2004 Klaraelvdalens Datakonsult AB
 *
 *    Written by Steffen Hansen <steffen@klaralvdalens-datakonsult.se>
 *
 *  This  program is free  software; you can redistribute  it and/or
 *  modify it  under the terms of the GNU  General Public License as
 *  published by the  Free Software Foundation; either version 2, or
 *  (at your option) any later version.
 *
 *  This program is  distributed in the hope that it will be useful,
 *  but WITHOUT  ANY WARRANTY; without even the  implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
 *  General Public License for more details.
 *
 *  You can view the  GNU General Public License, online, at the GNU
 *  Project's homepage; see <http://www.gnu.org/licenses/gpl.html>.
 */

function shutdown() {
    global $fb, $ldap;

    if (isset($fb) && $fb !== false) {
        $fb->imapDisconnect();
        $fb = false;
    }
    if (isset($ldap) && $ldap !== false) {
        $ldap->close();
        $ldap = false;
    }
    logClose();
}

function serverError($errortext) {
  myLog( $errortext, RM_LOG_ERROR );
  shutdown();

  header('HTTP/1.0 500 Server Error');

  echo '<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML 2.0//EN">
<html><head>
<title>500 Server Error</title>
</head><body>
<h1>Error</h1>
<p>'.htmlentities($_SERVER['REQUEST_URI']) . ':</p>
';

  if (!empty($errortext)) {
    echo "<hr>
<pre>$errortext</pre>
";
  }

  echo '<hr>
' . $_SERVER['SERVER_SIGNATURE'] . '</body></html>';
    exit;
}

function notFound($errortext) {
  myLog( $errortext, RM_LOG_ERROR );
  shutdown();

  header('HTTP/1.0 404 Not Found');

  echo '<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML 2.0//EN">
<html><head>
<title>404 Not Found</title>
</head><body>
<h1>Not Found</h1>
<p>The requested URL ' . htmlentities($_SERVER['REQUEST_URI']) . ' was not found on this server.</p>
';

  if (!empty($errortext)) {
    echo "<hr>
<pre>$errortext</pre>
";
  }

  echo '<hr>
' . $_SERVER['SERVER_SIGNATURE'] . '</body></html>';
    exit;
}

function unauthorized($errortext = '') {
    global $params;
    myLog( $errortext, RM_LOG_ERROR );
    shutdown();

    header('WWW-Authenticate: Basic realm="freebusy-'.$params['email_domain'].'"');
    header('HTTP/1.0 401 Unauthorized');

    echo '<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML 2.0//EN">
<html><head>
<title>401 Unauthorized</title>
</head><body>
<h1>Unauthorized</h1>
<p>You are not authorized to access the requested URL.</p>
';

    if (!empty($errortext)) {
        echo "<hr>
<pre>$errortext</pre>
";
    }

    echo '<hr>
' . $_SERVER['SERVER_SIGNATURE'] . '</body></html>
';

    exit;
}

// What myLog levels we can use
define('RM_LOG_SUPER',         -1);
define('RM_LOG_SILENT',         0);
define('RM_LOG_ERROR',          1);
define('RM_LOG_WARN',           2);
define('RM_LOG_INFO',           3);
define('RM_LOG_DEBUG',          4);

$logLevelPrefixes = array(
    RM_LOG_SUPER            => '',
    RM_LOG_SILENT           => '',
    RM_LOG_ERROR            => 'Error',
    RM_LOG_WARN             => 'Warning',
    RM_LOG_INFO             => '',
    RM_LOG_DEBUG            => 'Debug',
);
// What logging mechanisms are available for use
define('RM_LOG_SYSLOG',      1);
define('RM_LOG_FILE',        2);
define('RM_LOG_STDERR',      3);

$logType = 0;
$logPrefix = '';
$logDestination = NULL;

function logInit($name = '')
{
    global $params, $argv, $logType, $logPrefix, $logDestination;

    if (empty($name)) {
        $name = basename($argv[0]);
    }

    if (!array_key_exists('log', $params) || empty($params['log'])) {
        return;
    }

    $matches = array();
    if (preg_match('/(\w+):(.*)?/', $params['log'], $matches)) {
        switch ($matches[1]) {
        case 'syslog':
            $logType = RM_LOG_SYSLOG;
            $txtopts = preg_split('/[\s,]+/', $matches[2], -1, PREG_SPLIT_NO_EMPTY);
            $options = 0;
            foreach ($txtopts as $txtopt) {
                switch ($txtopt) {
                case 'cons': $options |= LOG_CONS; break;
                case 'ndelay': $options |= LOG_NDELAY; break;
                case 'odelay': $options |= LOG_ODELAY; break;
                case 'perror': $options |= LOG_PERROR; break;
                case 'pid': $options |= LOG_PID; break;
                }
            }
            openlog($name, $options, LOG_USER);
            break;

        case 'file':
            $logType = RM_LOG_FILE;
            $logPrefix = $name;
            $logDestination = fopen($matches[2], 'a');
            break;
	case 'stderr':
            $logType = RM_LOG_STDERR;
            $logPrefix = $name;
            $logDestination = fopen('php://stderr', 'a');
	    break;
        }
    }
}

function logClose()
{
    global $logType, $logDestination;

    switch ($logType) {
    case RM_LOG_SYSLOG:
        closelog();
        break;

    case RM_LOG_FILE:
        fclose($logDestination);
        $logDestination = NULL;
        break;
    }
}
function myLog($text, $priority = RM_LOG_INFO)
{
    global $params, $logLevelPrefixes, $logPrefix, $logType, $logDestination;

    if ($params['log_level'] >= $priority) {
        if (!empty($logLevelPrefixes[$priority])) {
            $text = $logLevelPrefixes[$priority] . ": $text";
        }

        switch ($logType) {
        case RM_LOG_SYSLOG:
            syslog(RM_LOG_INFO, $text);
            break;

        case RM_LOG_FILE:
            fwrite($logDestination, strftime('%B %d %T') . " ${logPrefix}[" . getmypid() . "]: $text\n");
            fflush($logDestination);
            break;
	case RM_LOG_STDERR:
            fwrite($logDestination, strftime('%B %d %T') . " ${logPrefix}[" . getmypid() . "]: $text\n");
            fflush($logDestination);
            break;	    
        }
    }
}

/** Helper function */
function assembleUri($parsed)
{
    if (!is_array($parsed)) return false;

    $uri = empty($parsed['scheme']) ? '' :
        $parsed['scheme'] . ':' . ((strtolower($parsed['scheme']) == 'mailto') ? '' : '//');

    $uri .= empty($parsed['user']) ? '' :
        ($parsed['user']) .
        (empty($parsed['pass']) ? '' : ':'.($parsed['pass']))
        . '@';

    $uri .= empty($parsed['host']) ? '' :
        $parsed['host'];
    $uri .= empty($parsed['port']) ? '' :
        ':' . $parsed['port'];

    $uri .= empty($parsed['path']) ? '' :
        $parsed['path'];
    $uri .= empty($parsed['query']) ? '' :
        '?' . $parsed['query'];
    $uri .= empty($parsed['anchor']) ? '' :
        '#' . $parsed['anchor'];

    return $uri;
}

function removePassword( $url ) {
  $parsed = parse_url($url);
  if( !empty($parsed['pass']) ) $parsed['pass'] = 'XXX';
  return assembleUri($parsed);
}

?>