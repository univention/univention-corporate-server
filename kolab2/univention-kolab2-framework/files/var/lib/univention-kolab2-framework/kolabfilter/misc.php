<?php
/*
 *  Copyright (c) 2004 Klaraelvdalens Datakonsult AB
 *
 *    Writen by Steffen Hansen <steffen@klaralvdalens-datakonsult.se>
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
        }
    }
}

function init()
{
    global $params;

    define_syslog_variables();

    logInit();

    //myLog('Starting up in ' . ($params['group'] ? 'group' : 'resource') . ' mode', RM_LOG_SUPER);

    $url_fopen = ini_get('allow_url_fopen');
    if (!$url_fopen) {
        myLog('\'allow_url_fopen\' is disabled in php.ini, enabling...', RM_LOG_WARN);
        ini_set('allow_url_fopen', '1');
    }

    // This is used as the default domain for unqualified adresses
    global $_SERVER;
    if (!array_key_exists('SERVER_NAME', $_SERVER)) {
        $_SERVER['SERVER_NAME'] = $params['email_domain'];
    }

    if (!array_key_exists('REMOTE_ADDR', $_SERVER)) {
        $_SERVER['REMOTE_ADDR'] = $params['server'];
    }

    if (!array_key_exists('REMOTE_HOST', $_SERVER)) {
        $_SERVER['REMOTE_HOST'] = $params['server'];
    }
}

/* Since getopt() in php can't parse the options the way
 * postfix gives them to us, we write our own option
 * handling:
 *
 * Inputs:
 *  $opts:  array('a','b','c'), a list of wanted options
 *  $args:  the argv list
 * Output:
 *  array of options and values. For example, the input
 *  "-a foo -b bar baz" would result in 
 *  array( 'a' => 'foo', 'b' => array('bar','baz') )
 */
function parse_args( $opts, $args )
{
  $ret = array();
  for( $i = 0; $i < count($args); ++$i ) {
    $arg = $args[$i];
    if( $arg[0] == '-' ) {
      if( in_array( $arg[1], $opts ) ) {
	$val = array();
	$i++;
	while( $i < count($args) && $args[$i][0] != '-' ) {
	  $val[] = $args[$i];
	  $i++;
	}
	$i--;
	if( is_array( $ret[$arg[1]] ) ) $ret[$arg[1]] = array_merge($ret[$arg[1]] ,$val);
	else if( count($val) == 1 ) $ret[$arg[1]] = $val[0];
	else $ret[$arg[1]] = $val;
      }
    }
  }
  return $ret;
}

?>