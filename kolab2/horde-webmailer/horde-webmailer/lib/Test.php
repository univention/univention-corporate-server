<?php

/**
 * Define HORDE_BASE, if it is not already set, and include the main
 * Horde library, since we require it for this package to function.
 */
if (!defined('HORDE_BASE')) {
    define('HORDE_BASE', dirname(__FILE__) . '/..');
}
require_once HORDE_BASE . '/lib/core.php';

/**
 * Set the path to the templates needed for testing output.
 */
define('TEST_TEMPLATES', HORDE_BASE . '/templates/test/');

/* If gettext is not loaded, define a dummy _() function so that
 * including any file with gettext strings won't cause a fatal error,
 * causing test.php to return a blank page. */
if (!function_exists('_')) {
    function _($s) { return $s; }
}

/**
 * The Horde_Test:: class provides functions used in the test scripts
 * used in the various applications (test.php).
 *
 * $Horde: horde/lib/Test.php,v 1.31.4.26 2009-01-06 15:24:51 jan Exp $
 *
 * Copyright 1999-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @author  Jon Parise <jon@horde.org>
 * @author  Brent J. Nordquist <bjn@horde.org>
 * @author  Michael Slusarz <slusarz@horde.org>
 * @since   Horde 3.0
 * @package Horde_Test
 */
class Horde_Test {

    /**
     * Array that holds the list of Horde applications.
     * (Loaded from config/registry.php)
     *
     * @var array
     */
    var $applications = array();

    /**
     * Cached results of getApplications().
     *
     * @var array
     */
    var $_appoutput = array();

    /**
     * The PHP version of the system.
     *
     * @var array
     */
    var $_phpver;

    /**
     * Supported versions of PHP.
     *
     * @var array
     */
    var $_supported = array(
        '4.3', '4.4', '5.0', '5.1', '5.2'
    );

    /**
     * Constructor.
     */
    function Horde_Test()
    {
        if (file_exists(HORDE_BASE . '/config/registry.php')) {
            include HORDE_BASE . '/config/registry.php';
            ksort($this->applications);
        }

        /* Store the PHP version information. */
        $this->_phpver = $this->splitPHPVersion(PHP_VERSION);

        /* We want to be as verbose as possible here. */
        error_reporting(E_ALL);

        /* Set character encoding. */
        header('Content-type: text/html; charset=utf-8');
        header('Vary: Accept-Language');
    }

    /**
     * Parse PHP version.
     *
     * @param string $version  A PHP-style version string (X.X.X).
     *
     * @param array  The parsed string.
     *               Keys: 'major', 'minor', 'subminor', 'class'
     */
    function splitPHPVersion($version)
    {
        /* First pick off major version, and lower-case the rest. */
        if ((strlen($version) >= 3) && ($version[1] == '.')) {
            $phpver['major'] = substr($version, 0, 3);
            $version = substr(strtolower($version), 3);
        } else {
            $phpver['major'] = $version;
            $phpver['class'] = 'unknown';
            return $phpver;
        }

        if ($version[0] == '.') {
            $version = substr($version, 1);
        }

        /* Next, determine if this is 4.0b or 4.0rc; if so, there is no
           minor, the rest is the subminor, and class is set to beta. */
        $s = strspn($version, '0123456789');
        if ($s == 0) {
            $phpver['subminor'] = $version;
            $phpver['class'] = 'beta';
            return $phpver;
        }

        /* Otherwise, this is non-beta;  the numeric part is the minor,
           the rest is either a classification (dev, cvs) or a subminor
           version (rc<x>, pl<x>). */
        $phpver['minor'] = substr($version, 0, $s);
        if ((strlen($version) > $s) &&
            (($version[$s] == '.') || ($version[$s] == '-'))) {
            $s++;
        }
        $phpver['subminor'] = substr($version, $s);
        if (($phpver['subminor'] == 'cvs') ||
            ($phpver['subminor'] == 'dev') ||
            (substr($phpver['subminor'], 0, 2) == 'rc')) {
            unset($phpver['subminor']);
            $phpver['class'] = 'dev';
        } else {
            if (!$phpver['subminor']) {
                unset($phpver['subminor']);
            }
            $phpver['class'] = 'release';
        }

        return $phpver;
    }

    /**
     * Check the list of PHP modules.
     *
     * @param array $modlist  The module list.
     * <pre>
     * KEY:   module name
     * VALUE: Either the description or an array with the following entries:
     *        'descrip'  --  Module Description
     *        'error'    --  Error Message
     *        'fatal'    --  Is missing module fatal?
     *        'phpver'   --  The PHP version above which to do the test
     * </pre>
     *
     * @return string  The HTML output.
     */
    function phpModuleCheck($modlist)
    {
        $output = '';
        $output_array = array();

        foreach ($modlist as $key => $val) {
            $error_msg = $mod_test = $status_out = $fatal = null;
            $test_function = null;
            $entry = array();

            if (is_array($val)) {
                $descrip = $val['descrip'];
                $fatal = !empty($val['fatal']);
                if (isset($val['phpver']) &&
                    (version_compare(PHP_VERSION, $val['phpver']) == -1)) {
                    $mod_test = true;
                    $status_out = 'N/A';
                }
                if (isset($val['error'])) {
                    $error_msg = $val['error'];
                }
                if (isset($val['function'])) {
                    $test_function = $val['function'];
                }
            } else {
                $descrip = $val;
            }

            if (is_null($status_out)) {
                if (!is_null($test_function)) {
                    $mod_test = call_user_func($test_function);
                } else {
                    $mod_test = extension_loaded($key);
                }

                $status_out = $this->_status($mod_test, $fatal);
            }

            $entry[] = $descrip;
            $entry[] = $status_out;

            if (!is_null($error_msg) && !$mod_test) {
                $entry[] = $error_msg;
                if (!$fatal) {
                    $entry[] = 1;
                }
            }

            $output .= $this->_outputLine($entry);

            if ($fatal && !$mod_test) {
                echo $output;
                exit;
            }
        }

        return $output;
    }

    /**
     * Checks the list of PHP settings.
     *
     * @param array $modlist  The settings list.
     * <code>
     * KEY:   setting name
     * VALUE: An array with the following entries:
     *        'error'    --  Error Message
     *        'setting'  --  Either a boolean (whether setting should be on or
     *                       off) or 'value', which will simply output the
     *                       value of the setting.
     * </code>
     *
     * @return string  The HTML output.
     */
    function phpSettingCheck($settings_list)
    {
        $output = '';

        foreach ($settings_list as $key => $val) {
            $entry = array();
            if (is_bool($val['setting'])) {
                $result = (ini_get($key) == $val['setting']);
                $entry[] = $key . ' ' . (($val['setting'] === true) ? 'enabled' : 'disabled');
                $entry[] = $this->_status($result);
                if (!$result) {
                    $entry[] = $val['error'];
                }
            } elseif ($val['setting'] == 'value') {
                $entry[] = $key . ' value';
                $entry[] = ini_get($key);
                if (!empty($val['error'])) {
                    $entry[] = $val['error'];
                    $entry[] = 1;
                }
            }
            $output .= $this->_outputLine($entry);
        }

        return $output;
    }

    /**
     * Check the list of PEAR modules.
     *
     * @param array $pear_list  The PEAR module list.
     * <pre>
     * KEY:   PEAR class name
     * VALUE: An array with the following entries:
     *        'depends'   --  This module depends on another module
     *        'error'     --  Error Message
     *        'function'  --  Reference to function to run if module is found
     *        'path'      --  The path to the PEAR module
     *        'required'  --  Is this PEAR module required? (boolean)
     * </pre>
     *
     * @return string  The HTML output.
     */
    function PEARModuleCheck($pear_list)
    {
        $output = '';

        /* Turn tracking of errors on. */
        ini_set('track_errors', 1);

        /* Print the include_path. */
        $output .= $this->_outputLine(array("<strong>PEAR Search Path (PHP's include_path)</strong>", '&nbsp;<tt>' . ini_get('include_path') . '</tt>'));

        /* Check for PEAR in general. */
        {
            $entry = array();
            $entry[] = 'PEAR';
            @include_once 'PEAR.php';
            $entry[] = $this->_status(!isset($php_errormsg));
            if (isset($php_errormsg)) {
                $entry[] = 'Check your PHP include_path setting to make sure it has the PEAR library directory.';
                $output .= $this->_outputLine($entry);
                ini_restore('track_errors');
                return $output;
            }
            $output .= $this->_outputLine($entry);
        }

        /* Check for a recent PEAR version. */
        $entry = array();
        $newpear = $this->isRecentPEAR();
        $entry[] = 'Recent PEAR';
        $entry[] = $this->_status($newpear);
        if (!$newpear) {
            $entry[] = 'This version of PEAR is not recent enough. See the <a href="http://www.horde.org/pear/">Horde PEAR page</a> for details.';
        }
        $output .= $this->_outputLine($entry);

        /* Go through module list. */
        $succeeded = array();
        foreach ($pear_list as $key => $val) {
            $entry = array();

            /* If this module depends on another module that we
             * haven't succesfully found, fail the test. */
            if (!empty($val['depends']) && empty($succeeded[$val['depends']])) {
                $result = false;
            } else {
                $result = @include_once $val['path'];
            }
            $error_msg = $val['error'];
            if ($result && isset($val['function'])) {
                $func_output = call_user_func($val['function']);
                if ($func_output) {
                    $result = false;
                    $error_msg = $func_output;
                }
            }
            $entry[] = $key;
            $entry[] = $this->_status($result, !empty($val['required']));

            if ($result) {
                $succeeded[$key] = true;
            } else {
                if (!empty($val['required'])) {
                    $error_msg .= ' THIS IS A REQUIRED MODULE!';
                }
                $entry[] = $error_msg;
                if (empty($val['required'])) {
                    $entry[] = 1;
                }
            }

            $output .= $this->_outputLine($entry);
        }

        /* Restore previous value of 'track_errors'. */
        ini_restore('track_errors');

        return $output;
    }

    /**
     * Check the list of required files
     *
     * @param array $file_list  The file list.
     * <pre>
     * KEY:   file path
     * VALUE: The error message to use (null to use default message)
     * </pre>
     *
     * @return string  The HTML output.
     */
    function requiredFileCheck($file_list)
    {
        $output = '';

        foreach ($file_list as $key => $val) {
            $entry = array();
            $result = file_exists('./' . $key);

            $entry[] = $key;
            $entry[] = $this->_status($result);

            if (!$result) {
                if (empty($val)) {
                    $entry[] = 'The file <code>' . $key . '</code> appears to be missing. You probably just forgot to copy <code>' . $key . '.dist</code> over. While you do that, take a look at the settings and make sure they are appropriate for your site.';
                } else {
                    $entry[] = $val;
                }
            }

            $output .= $this->_outputLine($entry);
        }

        return $output;
    }

    /**
     * Displays an error screen with a list of all configuration files that
     * are missing, together with a description what they do and how they are
     * created. If a file can be automatically created from the defaults, then
     * we do that instead and don't display an error.
     *
     * @param string $app        The application name
     * @param string $appBase    The path to the application
     * @param array  $files      An array with the "standard" configuration
     *                           files that should be checked. Currently
     *                           supported:
     *                           - conf.php
     *                           - prefs.php
     *                           - mime_drivers.php
     * @param array $additional  An associative array containing more files (as
     *                           keys) and error message (as values) if they
     *                           don't exist.
     */
    function configFilesMissing($app, $appBase, $files, $additional = array())
    {
        /* Try to load a basic framework if we're testing an app other than
         * the Horde base files. */
        if ($app != 'Horde') {
            $GLOBALS['registry'] = &Registry::singleton();
            $GLOBALS['registry']->pushApp('horde', false);
        }

        if (!is_array($files)) {
            $files = array($files);
        }
        $files = array_merge($files, array_keys($additional));

        /* Try to auto-create missing .dist files. */
        $indices = array_keys($files);
        foreach ($indices as $index) {
            if (is_readable($appBase . '/config/' . $files[$index])) {
                unset($files[$index]);
            } else {
                if (file_exists($appBase . '/config/' . $files[$index] . '.dist') &&
                    @copy($appBase . '/config/' . $files[$index] . '.dist', $appBase . '/config/' . $files[$index])) {
                    unset($files[$index]);
                }
            }
        }

        /* Return if we have no missing files left. */
        if (!count($files)) {
            return;
        }

        $descriptions = array_merge(array(
            'conf.php' => sprintf('This is the main %s configuration file. ' .
                                  'It contains paths and options for the %s ' .
                                  'scripts. You need to login as an ' .
                                  'administrator and create the file with ' .
                                  'the web frontend under "Administration => ' .
                                  'Setup".',
                                  $app, $app, $appBase . '/config'),
            'prefs.php' => sprintf('This file controls the default preferences ' .
                                   'for %s, and also controls which preferences ' .
                                   'users can alter.', $app),
            'mime_drivers.php' => sprintf('This file controls local MIME ' .
                                          'drivers for %s, specifically what ' .
                                          'kinds of files are viewable and/or ' .
                                          'downloadable.', $app),
            'backends.php' => sprintf('This file controls what backends are ' .
                                      'available from %s.', $app),
            'sources.php' => sprintf('This file defines the list of available ' .
                                     'sources for %s.', $app)
        ), $additional);

        /* If we know the user is an admin, give them a direct link to
         * generate conf.php. In the future, should we try generating
         * a basic conf.php automagically here? */
        if (Auth::isAdmin()) {
            $setup_url = Horde::link(Horde::url($GLOBALS['registry']->get('webroot', 'horde') .
                                                '/admin/setup/config.php?app=' . String::lower($app))) .
                'Configuration Web Interface' . '</a>';
            $descriptions['conf.php'] =
                sprintf('This is the main %s configuration file. ' .
                        'Generate it by going to the %s.',
                        $app, $setup_url);
        }

        $title = sprintf('%s is not properly configured', $app);
        $header = sprintf('Some of %s\'s configuration files are missing or unreadable', $app);
        $footer = sprintf('Create these files from their .dist versions in %s and change them according to your needs.', $appBase . '/config');

        echo <<< HEADER
<html>
<head><title>$title</title></head>
<body style="background-color: white; color: black;">
<h1>$header</h1>
HEADER;

        foreach ($files as $file) {
            if (empty($descriptions[$file])) {
                continue;
            }
            $description = $descriptions[$file];
            echo <<< FILE
    <h3>$file</h3><p>$description</p>
FILE;
        }

        echo <<< FOOTER

<h2>$footer</h2>
</body>
</html>
FOOTER;
        exit;
    }

    /**
     * Check the list of required Horde applications.
     *
     * @param array $app_list  The application list.
     * <pre>
     * KEY:   application name
     * VALUE: An array with the following entries:
     *        'error'    --  Error Message
     *        'version'  --  The minimum version required
     * </pre>
     *
     * @return string  The HTML output.
     */
    function requiredAppCheck($app_list)
    {
        $output = '';

        $apps = $this->applicationList();

        foreach ($app_list as $key => $val) {
            $entry = array();
            $entry[] = $key;

            if (!isset($apps[$key])) {
                $entry[] = $this->_status(false, false);
                $entry[] = $val['error'];
                $entry[] = 1;
            } else {
                /* Strip '-cvs' and H3 (ver) from version string. */
                $appver = str_replace('-cvs', '', $apps[$key]->version);
                $appver = preg_replace('/H3 \((.*)\)/', '$1', $appver);
                if (version_compare($val['version'], $appver) === 1) {
                    $entry[] = $this->_status(false, false) . ' (Have version: ' . $apps[$key]->version . '; Need version: ' . $val['version'] . ')';
                    $entry[] = $val['error'];
                    $entry[] = 1;
                } else {
                    $entry[] = $this->_status(true) . ' (Version: ' . $apps[$key]->version . ')';
                }
            }
            $output .= $this->_outputLine($entry);
        }

        return $output;
    }

    /**
     * Is this a 'recent' version of PEAR?
     *
     * @param boolean  True if a recent version of PEAR.
     */
    function isRecentPEAR()
    {
        @include_once 'PEAR.php';
        $pear_methods = get_class_methods('PEAR');
        return (is_array($pear_methods) &&
                (in_array('registershutdownfunc', $pear_methods) ||
                 in_array('registerShutdownFunc', $pear_methods)));
    }

    /**
     * Obtain information on the PHP version.
     *
     * @return object stdClass  TODO
     */
    function getPhpVersionInformation()
    {
        $output = &new stdClass;
        $url = urlencode($_SERVER['PHP_SELF']);
        $vers_check = true;

        $testscript = 'test.php';
        $output->phpinfo = $testscript . '?mode=phpinfo&amp;url=' . $url;
        $output->extensions = $testscript . '?mode=extensions&amp;url=' . $url;
        $output->version = PHP_VERSION;
        $output->major = $this->_phpver['major'];
        if (isset($this->_phpver['minor'])) {
            $output->minor = $this->_phpver['minor'];
        }
        if (isset($this->_phpver['subminor'])) {
            $output->subminor = $this->_phpver['subminor'];
        }
        $output->class = $this->_phpver['class'];

        $output->status_color = 'red';
        if ($output->major < '4.3') {
            $output->status = 'This version of PHP is not supported. You need to upgrade to a more recent version.';
            $vers_check = false;
        } elseif (in_array($output->major, $this->_supported)) {
            $output->status = 'You are running a supported version of PHP.';
            $output->status_color = 'green';
        } else {
            $output->status = 'This version of PHP has not been fully tested with this version of Horde.';
            $output->status_color = 'orange';
        }

        if (!$vers_check) {
            $output->version_check = 'Horde requires PHP 4.3.0 or greater.';
        }

        return $output;
    }

    /**
     * Get the application list.
     *
     * @return array  List of stdClass objects.
     *                KEY: application name
     *                ELEMENT 'version': Version of application
     *                ELEMENT 'test': The location of the test script (if any)
     */
    function applicationList()
    {
        if (!empty($this->_appoutput)) {
            return $this->_appoutput;
        }

        foreach ($this->applications as $mod => $det) {
            if (($det['status'] != 'heading') &&
                ($det['status'] != 'block') &&
                is_readable($det['fileroot'] . '/lib/version.php')) {
                require_once $det['fileroot'] . '/lib/version.php';
                $version_constant = String::upper($mod) . '_VERSION';
                if (defined($version_constant)) {
                    $this->_appoutput[$mod] = &new stdClass;
                    $this->_appoutput[$mod]->version = constant($version_constant);
                    if (($mod != 'horde') &&
                        is_readable($det['fileroot'] . '/test.php')) {
                        $this->_appoutput[$mod]->test = $det['webroot'] . '/test.php';
                    }
                }
            }
        }

        return $this->_appoutput;
    }

    /**
     * Output the results of a status check.
     *
     * @access private
     *
     * @param boolean $bool      The result of the status check.
     * @param boolean $required  Whether the checked item is required.
     *
     * @return string  The HTML of the result of the status check.
     */
    function _status($bool, $required = true)
    {
        if ($bool) {
            return '<strong style="color:green">Yes</strong>';
        } elseif ($required) {
            return '<strong style="color:red">No</strong>';
        } else {
            return '<strong style="color:orange">No</strong>';
        }
    }

    /**
     * Internal output function.
     *
     * @access private
     *
     * @param array $entry  Array with the following values:
     * <pre>
     * 1st value: Header
     * 2nd value: Test Result
     * 3rd value: Error message (if present)
     * 4th value: Error level (if present): 0 = error, 1 = warning
     * </pre>
     *
     * @return string  HTML output.
     */
    function _outputLine($entry)
    {
        $output = '<li>' . array_shift($entry) . ': ' . array_shift($entry);
        if (!empty($entry)) {
            $msg = array_shift($entry);
            $output .= '<br /><strong style="color:' . (empty($entry) || !array_shift($entry) ? 'red' : 'orange') . '">' . $msg . "</strong>\n";
        }
        $output .= '</li>' . "\n";

        return $output;
    }

}
