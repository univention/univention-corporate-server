#!/usr/local/bin/php
<?php
/**
 * This is a command line interface for the VFS package.
 *
 * @package VFS
 *
 * `vfs.php help' shows some usage instructions.
 */

require_once 'PEAR.php';
require_once 'Console/Getopt.php';
require_once 'DB.php';
require_once 'VFS.php';
ini_set('track_errors', true);

/* Get command line options. */
$argv = Console_Getopt::readPHPArgv();
if (is_a($argv, 'PEAR_Error')) {
    usage($argv->getMessage());
}
array_shift($argv);
$options = Console_Getopt::getopt2($argv, '', array());
if (is_a($options, 'PEAR_Error')) {
    usage($options->getMessage());
}

/* Show help? */
if (!count($options[1]) || in_array('help', $options[1])) {
    usage();
}

/* Get and execute the command. */
$command = array_shift($options[1]);
switch ($command) {
case 'ls':
    if (!count($options[1])) {
        usage($command);
    }
    $params = Console_Getopt::getopt2($options[1], 'alR');
    if (is_a($params, 'PEAR_Error')) {
        usage($params->getMessage());
    }
    $path = array_shift($params[1]);
    ls($path, mergeOptions($params[0]), $params[1]);
}

/**
 * Lists the contents of the specified directory.
 *
 * @param string $url     The URL of the VFS backend
 * @param array $argv     Additional options
 * @param string $filter  Additional parameters
 */
function ls($url, $argv, $filter)
{
    $params = url2params($url);
    $recursive = in_array('R', $argv);

    $vfs = &vfs($params);
    $list = $vfs->listFolder($params['path'], 
                             count($filter) ? $filter[0] : null,
                             in_array('a', $argv));
    if (is_a($list, 'PEAR_Error')) {
        usage($list);
    }
    $list = array_keys($list);
    $max = array_map(create_function('$a', 'return strlen($a);'), $list);
    $max = array_reduce($max, create_function('$a, $b', 'return max($a, $b);'));
    $max += 2;

    $line = '';
    $dirs = array();
    if ($recursive) {
        echo $params['path'] . ":\n";
    }
    foreach ($list as $entry) {
        if ($vfs->isFolder($params['path'], $entry)) {
            $dirs[] = $entry;
        }
        $entry = sprintf('%-' . $max . 's', $entry);
        if (strlen($line . $entry) > 80 && !empty($line)) {
            echo $line . "\n";
            $line = '';
        }
        $line .= $entry;
    }
    if (!empty($line)) {
        echo $line . "\n";
    }

    if ($recursive && count($dirs)) {
        foreach ($dirs as $dir) {
            echo "\n";
            ls($url . '/' . $dir, $argv, $filter);
        }
    }
}

/**
 * Shows some error and usage information.
 *
 * @param object PEAR_Error $error  If specified its error messages will be
 *                                  displayed.
 */
function usage($error = null)
{
    if (is_a($error, 'PEAR_Error')) {
        echo $error->getMessage() . "\n";
        echo $error->getUserinfo() . "\n\n";
    }

    echo <<<USAGE
Usage: vfs.php [options] command [command-options] <parameters>

USAGE;

    exit;
}

/**
 * Returns a VFS instance.
 *
 * @param array $params  A complete parameter set including the driver name
 *                       for the requested VFS instance.
 *
 * @return object VFS  An instance of the requested VFS backend.
 */
function &vfs($params)
{
    return VFS::factory($params['driver'], $params);
}

/**
 * Merges a set of options as returned by Console_Getopt::getopt2() into a
 * single array.
 *
 * @param array $options  A two dimensional array with the options.
 *
 * @return array  A flat array with the options.
 */
function mergeOptions($options)
{
    $result = array();
    foreach ($options as $param) {
        $result = array_merge($result, $param);
    }
    return $result;
}

/**
 * Parses a URL into a set of parameters that can be used to instantiate a
 * VFS object.
 *
 * @todo Document the possible URL formats.
 *
 * @param string $url  A URL with all necessary information for a VFS driver.
 *
 * @return array  A hash with the parsed information.
 */
function url2params($url)
{
    $params = array();
    $params['path'] = '';
    $dsn = @DB::parseDSN($url);
    if ($dsn['phptype'] == 'ftp' || $dsn['phptype'] == 'file') {
        $url = @parse_url($url);
        if (!is_array($url)) {
            usage(PEAR::raiseError($php_errormsg));
        }
        $params['driver'] = $url['scheme'];
        if (isset($url['host'])) {
            $params['hostspec'] = $url['host'];
        }
        if (isset($url['port'])) {
            $params['port'] = $url['port'];
        }
        if (isset($url['user'])) {
            $params['username'] = $url['user'];
        }
        if (isset($url['pass'])) {
            $params['password'] = $url['pass'];
        }
        if (isset($url['path'])) {
            $params['path'] = $url['path'];
        }
        if (isset($url['query'])) {
            $queries = explode('&', $url['query']);
            foreach ($queries as $query) {
                $pair = explode('=', $query);
                $params[$pair[0]] = isset($pair[1]) ? $pair[1] : true;
            }
        }
    } else {
        if (!isset($dsn['driver'])) {
            usage(PEAR::raiseError('If using one of the SQL drivers (sql, sql_file, musql), you have to specify the driver as parameter of the URL.'));
        }
        $params = array_merge($params, $dsn);
    }
    return $params;
}
