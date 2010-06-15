<?php

include_once 'Log.php';
include_once 'Horde/Util.php';

/**
 * The Horde:: class provides the functionality shared by all Horde
 * applications.
 *
 * $Horde: framework/Horde/Horde.php,v 1.418 2004/05/30 11:54:09 jan Exp $
 *
 * Copyright 1999-2004 Chuck Hagenbuch <chuck@horde.org>
 * Copyright 1999-2004 Jon Parise <jon@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @author  Jon Parise <jon@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 1.3
 * @package Horde_Framework
 */
class Horde {

    /**
     * Log a message to the global Horde log backend.
     *
     * @access public
     *
     * @param mixed $message              Either a string or a PEAR_Error
     *                                    object.
     * @param string $file                What file was the log function
     *                                    called from (e.g. __FILE__) ?
     * @param integer $line               What line was the log function
     *                                    called from (e.g. __LINE__) ?
     * @param optional integer $priority  The priority of the message. One of:
     * <pre>
     * PEAR_LOG_EMERG
     * PEAR_LOG_ALERT
     * PEAR_LOG_CRIT
     * PEAR_LOG_ERR
     * PEAR_LOG_WARNING
     * PEAR_LOG_NOTICE
     * PEAR_LOG_INFO
     * PEAR_LOG_DEBUG
     * </pre>
     */
    function logMessage($message, $file, $line, $priority = PEAR_LOG_INFO)
    {
        static $logcheck;
        global $conf;

        if (!$conf['log']['enabled']) {
            return;
        }

        if ($priority > $conf['log']['priority']) {
            return;
        }

        if (!isset($logcheck)) {
            // Try to make sure that we can log messages somehow.
            if (empty($conf['log']) ||
                empty($conf['log']['type']) ||
                empty($conf['log']['name']) ||
                empty($conf['log']['ident']) ||
                !isset($conf['log']['params'])) {
                Horde::fatal(PEAR::raiseError('Horde is not correctly configured to log error messages. You must configure at least a text file log in horde/config/conf.php.'), __FILE__, __LINE__, false);
            }
            $logcheck = true;
        }

        $logger = &Log::singleton($conf['log']['type'], $conf['log']['name'],
                                  $conf['log']['ident'], $conf['log']['params']);

        if (!is_a($logger, 'Log')) {
            Horde::fatal(PEAR::raiseError('An error has occurred. Furthermore, Horde encountered an error attempting to log this error. Please check your Horde logging configuration in horde/config/conf.php.'), __FILE__, __LINE__, false);
        }

        if (is_a($message, 'PEAR_Error')) {
            $userinfo = $message->getUserInfo();
            $message = $message->getMessage();
            if (!empty($userinfo)) {
                if (is_array($userinfo)) {
                    $userinfo = implode(', ', $userinfo);
                }
                $message .= ': ' . $userinfo;
            }
        }

        $app = isset($GLOBALS['registry']) ? $GLOBALS['registry']->getApp() : 'horde';
        $message = '[' . $app . '] ' . $message . ' [on line ' . $line . ' of "' . $file . '"]';

        /* Make sure to log in the system's locale. */
        $locale = setlocale(LC_TIME, 0);
        setlocale(LC_TIME, 'C');

        $logger->log($message, $priority);

        /* Restore original locale. */
        setlocale(LC_TIME, $locale);

        return true;
    }

    /**
     * Destroy any existing session on login and make sure to use a new
     * session ID, to avoid session fixation issues. Should be called before
     * checking a login.
     *
     * @access public
     */
    function getCleanSession()
    {
        Auth::clearAuth();
        @session_destroy();

        // Make sure to force a completely new session ID.
        if (version_compare(phpversion(), '4.3.3') !== -1) {
            session_regenerate_id();
        } else {
            if (Util::extensionExists('posix')) {
                $new_session_id = md5(microtime() . posix_getpid());
            } else {
                $new_session_id = md5(uniqid(mt_rand(), true));
            }
            session_id($new_session_id);
        }

        // Restart the session, including setting up the session
        // handler.
        Horde::setupSessionHandler();
        @session_start();
    }

    /**
     * Abort with a fatal error, displaying debug information to the user.
     *
     * @access public
     *
     * @param mixed $error           A PEAR_Error object with debug information
     *                               or an error message.
     * @param integer $file          The file in which the error occured.
     * @param integer $line          The line on which the error occured.
     * @param optional boolean $log  Log this message via Horde::logMesage()?
     */
    function fatal($error, $file, $line, $log = true)
    {
        @include_once 'Horde/Auth.php';
        @include_once 'Horde/CLI.php';

        $admin = class_exists('Auth') && Auth::isAdmin();
        $cli = class_exists('Horde_CLI') && Horde_CLI::runningFromCLI();

        $errortext = '<h1>' . _("A fatal error has occurred") . '</h1>';
        if (is_a($error, 'PEAR_Error')) {
            global $registry;
            $message = $error->getMessage();
            $info = array_merge(array('file' => 'conf.php', 'variable' => '$conf'),
                                array($error->getUserInfo()));
            switch ($error->getCode()) {
                case HORDE_ERROR_DRIVER_CONFIG_MISSING:
                    $message = sprintf(_("No configuration information specified for %s."), $info['name']) . '<br />' .
                        sprintf(_("The file %s should contain some %s settings."),
                                $registry->getParam('fileroot') . '/config/' . $info['file'],
                                sprintf("%s['%s']['params']", $info['variable'], $info['driver']));
                    break;
                case HORDE_ERROR_DRIVER_CONFIG:
                    $message = sprintf(_("Required '%s' not specified in %s configuration."), $info['field'], $info['name']) . '<br />' .
                        sprintf(_("The file %s should contain a %s setting."),
                                $registry->getParam('fileroot') . '/config/' . $info['file'],
                                sprintf("%s['%s']['params']['%s']", $info['variable'], $info['driver'], $info['field']));
                    break;
            }
            $errortext .= '<h3>' . htmlspecialchars($message) . '</h3>';
        } elseif (is_object($error) && method_exists($error, 'getMessage')) {
            $errortext .= '<h3>' . htmlspecialchars($error->getMessage()) . '</h3>';
        } elseif (is_string($error)) {
            $errortext .= '<h3>' . $error . '</h3>';
        }

        if ($admin) {
            $errortext .= '<p><code>' . sprintf(_("[line %s of %s]"), $line, $file) . '</code></p>';
            if (is_object($error)) {
                $errortext .= '<h3>' . _("Details (also in Horde's logfile):") . '</h3>';
                $errortext .= '<p><pre>' . htmlspecialchars(Util::bufferOutput('var_dump', $error)) . '</pre></p>';
            }
        } elseif ($log) {
            $errortext .= '<h3>' . _("Details have been logged for the administrator.") . '</h3>';
        }

        // Log the error via Horde::logMessage() if requested.
        if ($log) {
            Horde::logMessage($error, $file, $line, PEAR_LOG_EMERG);
        }

        if ($cli) {
            echo strip_tags(str_replace(array('<br />', '<p>', '</p>', '<h1>', '</h1>', '<h3>', '</h3>'), "\n", $errortext));
        } else {
            echo <<< HTML
<html>
<head><title>Horde :: Fatal Error</title></head>
<body style="background-color: white; color: black;">$errortext</body>
</html>
HTML;
        }
        exit;
    }

    /**
     * Adds the javascript code to the output (if output has already
     * started) or to the list of script files to include via
     * includeScriptFiles().
     *
     * @access public
     *
     * @param string $file           The full javascript file name.
     * @param optional string $app   The application name.
     * @param optional bool $direct  Include the file directly without passing
     *                               it through javascript.php?
     */
    function addScriptFile($file, $app = null, $direct = false)
    {
        global $registry;
        static $included = array();

        if (empty($app)) {
            $app = $registry->getApp();
        }

        // Don't include scripts multiple times.
        if (!empty($included[$app][$file])) {
            return;
        }
        $included[$app][$file] = true;

        if (ob_get_length() || headers_sent()) {
            if ($direct) {
                $url = Horde::url($registry->getParam('webroot', $app) . $file);
            } else {
                $url = Horde::url($registry->getParam('webroot', 'horde') . '/services/javascript.php');
                $url = Util::addParameter($url, array('file' => $file,
                                                      'app'  => $app));
            }
            echo '<script language="JavaScript" type="text/javascript" src="' . $url . '"></script>';
        } else {
            global $_horde_script_files;
            $_horde_script_files[$app][] = array($file, $direct);
        }
    }

    /**
     * Include javascript files that were needed before any headers were sent.
     *
     * @access public
     */
    function includeScriptFiles()
    {
        global $_horde_script_files, $registry;

        if (!empty($_horde_script_files)) {
            $base_url = Horde::url($registry->getParam('webroot', 'horde') . '/services/javascript.php');
            foreach ($_horde_script_files as $app => $files) {
                foreach ($files as $file) {
                    if ($file[1]) {
                        $url = $registry->getParam('webroot', $app) . $file[0];
                        echo '<script language="JavaScript" type="text/javascript" src="' . Horde::url($url) . "\"></script>\n";
                    } else {
                        $url = Util::addParameter($base_url, array('file' => $file[0],
                                                                   'app'  => $app));
                        echo '<script language="JavaScript" type="text/javascript" src="' . $url . "\"></script>\n";
                    }
                }
            }
        }
    }

    /**
     * Return the driver parameters for the specified backend.
     *
     * @param mixed $backend         The backend system (e.g. 'prefs',
     *                               'categories', 'contacts') being used.
     *                               The used configuration array will be
     *                               $conf[$backend]. If an array gets passed,
     *                               it will be $conf[$key1][$key2].
     * @param optional string $type  The type of driver.
     *
     * @return array  The connection parameters.
     */
    function getDriverConfig($backend, $type = 'sql')
    {
        global $conf;

        $c = null;
        if (is_array($backend)) {
            require_once 'Horde/Array.php';
            $c = Horde_Array::getElement($conf, $backend);
        } elseif (isset($conf[$backend])) {
            $c = $conf[$backend];
        }
        if (!is_null($c) && isset($c['params'])) {
            if (isset($conf[$type])) {
                return array_merge($conf[$type], $c['params']);
            } else {
                return $c['params'];
            }
        }

        return isset($conf[$type]) ? $conf[$type] : array();
    }

    /**
     * Checks if all necessary parameters for a driver configuration
     * are set and throws a fatal error with a detailed explaination
     * how to fix this, if something is missing.
     *
     * @param array $params              The configuration array with all
     *                                   parameters.
     * @param string $driver             The key name (in the configuration
     *                                   array) of the driver.
     * @param array $fields              An array with mandatory parameter
     *                                   names for this driver.
     * @param optional string $name      The clear text name of the driver. If
     *                                   not specified, the application name
     *                                   will be used.
     * @param optional string $file      The configuration file that should
     *                                   contain these settings.
     * @param optional string $variable  The name of the configuration
     *                                   variable.
     */
    function assertDriverConfig($params, $driver, $fields, $name = null,
                                $file = 'conf.php', $variable = '$conf')
    {
        global $registry;

        if (is_null($name)) {
            $name = $registry->getApp();
        }

        if (!is_array($params) || !count($params)) {
            Horde::fatal(PEAR::raiseError(
                sprintf(_("No configuration information specified for %s."), $name) . '<br />' .
                sprintf(_("The file %s should contain some %s settings."),
                    $registry->getParam('fileroot') . '/config/' . $file,
                    sprintf("%s['%s']['params']", $variable, $driver))),
                __FILE__, __LINE__);
        }

        foreach ($fields as $field) {
            if (!isset($params[$field])) {
                Horde::fatal(PEAR::raiseError(
                    sprintf(_("Required '%s' not specified in %s configuration."), $field, $name) . '<br />' .
                    sprintf(_("The file %s should contain a %s setting."),
                        $registry->getParam('fileroot') . '/config/' . $file,
                        sprintf("%s['%s']['params']['%s']", $variable, $driver, $field))),
                    __FILE__, __LINE__);
            }
        }
    }

    /**
     * Return a session-id-ified version of $uri.
     *
     * @access public
     *
     * @param string $uri                       The URI to be modified.
     * @param optional boolean $full            Generate a full
     *                                          (http://server/path/) URL.
     * @param optional integer $append_session  0 = only if needed, 1 = always,
     *                                          -1 = never.
     *
     * @return string  The URL with the session id appended (if needed).
     */
    function url($uri, $full = false, $append_session = 0)
    {
        if ($full) {
            global $conf, $registry, $browser;

            /* Store connection parameters in local variables. */
            $server_name = $conf['server']['name'];
            $server_port = $conf['server']['port'];

            $protocol = 'http';
            if ($conf['use_ssl'] == 1) {
                $protocol = 'https';
            } elseif ($conf['use_ssl'] == 2) {
                if ($browser->usingSSLConnection()) {
                    $protocol = 'https';
                }
            }

            /* If using non-standard ports, add the port to the URL. */
            if (!empty($server_port) &&
                (($protocol == 'http') && ($server_port != 80)) ||
                (($protocol == 'https') && ($server_port != 443))) {
                $server_name .= ':' . $server_port;
            }

            /* Store the webroot in a local variable. */
            $webroot = $registry->getParam('webroot');

            $url = $protocol . '://' . $server_name;
            if (substr($uri, 0, 1) != '/') {
                if (substr($webroot, -1) == '/') {
                    $url .= $webroot . $uri;
                } else {
                    $url .= $webroot . '/' . $uri;
                }
            } else {
                $url .= $uri;
            }
        } else {
            $url = $uri;
        }

        if (($append_session == 1) ||
            (($append_session == 0) &&
             !isset($_COOKIE[session_name()]))) {
            $url = Util::addParameter($url, session_name(), session_id());
        }

        return ($full ? $url : htmlentities($url));
    }

    /**
     * Return a session-id-ified version of $uri, using the current
     * application's webroot setting.
     *
     * @access public
     *
     * @param string $uri                       The URI to be modified.
     * @param optional boolean $full            Generate a full
     *                                          (http://server/path/) URL.
     * @param optional integer $append_session  0 = only if needed, 1 = always,
     *                                          -1 = never.
     *
     * @return string  The url with the session id appended
     */
    function applicationUrl($uri, $full = false, $append_session = 0)
    {
        global $registry;

        /* Store the webroot in a local variable. */
        $webroot = $registry->getParam('webroot');

        if ($full) {
            return Horde::url($uri, $full, $append_session);
        } elseif (substr($webroot, -1) == '/') {
            return Horde::url($webroot . $uri, $full, $append_session);
        } else {
            return Horde::url($webroot . '/' . $uri, $full, $append_session);
        }
    }

    /**
     * Returns an external link passed through the dereferer to strip
     * session IDs from the referer.
     *
     * @param string $url            The external URL to link to.
     * @param optional boolean $tag  If true, a complete <a> tag is returned,
     *                               only the url otherwise.
     */
    function externalUrl($url, $tag = false)
    {
        $ext = Horde::url($GLOBALS['registry']->getParam('webroot', 'horde') .
                          '/services/go.php', true, -1);
        $ext = Util::addParameter($ext, 'url', $url);
        if ($tag) {
            $ext = Horde::link($ext, $url, '', '_blank');
        }
        return $ext;
    }

    /**
     * Returns a URL to be used for downloading, that takes into account
     * any special browser quirks (i.e. IE's broken filename handling).
     *
     * @access public
     *
     * @param string $filename        The filename of the download data.
     * @param optional array $params  Any additional parameters needed.
     * @param optional string $url    The URL to alter. If none passed in,
     *                                will use the file 'view.php' located
     *                                in the current module's base directory.
     *
     * @return string  The download URL.
     */
    function downloadUrl($filename, $params = array(), $url = null)
    {
        global $browser;

        $horde_url = false;

        if (is_null($url)) {
            global $registry;
            $url = Util::addParameter(Horde::url($registry->getParam('webroot', 'horde') . '/services/download/'), 'module', $registry->getApp());
            $horde_url = true;
        }

        /* Add parameters. */
        if (!is_null($params)) {
            foreach ($params as $key => $val) {
                $url = Util::addParameter($url, $key, $val);
            }
        }

        /* If we are using the default Horde download link, add the
         * filename to the end of the URL. Although not necessary for
         * many browsers, this should allow every browser to download
         * correctly. */
        if ($horde_url) {
            $url = Util::addParameter($url, 'fn=/' . rawurlencode($filename));
        } elseif ($browser->hasQuirk('break_disposition_filename')) {
            /* Some browsers will only obtain the filename correctly
             * if the extension is the last argument in the query
             * string and rest of the filename appears in the
             * PATH_INFO element. */
            $filename = rawurlencode($filename);

            /* Get the webserver ID. */
            $server = Horde::webServerID();

            /* Get the name and extension of the file.  Apache 2 does
             * NOT support PATH_INFO information being passed to the
             * PHP module by default, so disable that
             * functionality. */
            if (($server != 'apache2')) {
                if (($pos = strrpos($filename, '.'))) {
                    $name = '/' . preg_replace('/\./', '%2E', substr($filename, 0, $pos));
                    $ext = substr($filename, $pos);
                } else {
                    $name = '/' . $filename;
                    $ext = '';
                }

                /* Enter the PATH_INFO information. */
                if (($pos = strpos($url, '?'))) {
                    $url = substr($url, 0, $pos) . $name . substr($url, $pos);
                } else {
                    $url .= $name;
                }
            }

            /* Append the extension, if it exists. */
            if (($server == 'apache2') || !empty($ext)) {
                $url = Util::addParameter($url, 'fn_ext=/' . $filename);
            }
        }

        return $url;
    }

    /**
     * Return an anchor tag with the relevant parameters
     *
     * @access public
     *
     * @param string $url                 The full URL to be linked to
     * @param optional string $status     The JavaScript mouse-over string
     * @param optional string $class      The CSS class of the link
     * @param optional string $target     The window target to point to.
     * @param optional string $onclick    JavaScript action for the 'onclick'
     *                                    event.
     * @param optional string $title      The link title (tooltip).
     * @param optional string $accesskey  The access key to use.
     *
     * @return string  The full <a href> tag.
     */
    function link($url, $status = '', $class = '', $target = '', $onclick = '',
                  $title = '', $accesskey = '')
    {
        $ret = "<a href=\"$url\"";
        if (!empty($onclick)) {
            $ret .= " onclick=\"$onclick\"";
        }
        if (!empty($status)) {
            $ret .= ' onmouseout="window.status=\'\';" onmouseover="window.status=\'' . @htmlspecialchars(strtr(addslashes($status), array("\r" => '', "\n" => '')), ENT_QUOTES, NLS::getCharset()) . '\'; return true;"';
        }
        if (!empty($class)) {
            $ret .= " class=\"$class\"";
        }
        if (!empty($target)) {
            $ret .= " target=\"$target\"";
        }
        if (!empty($title)) {
            $ret .= ' title="' . @htmlspecialchars($title, ENT_QUOTES, NLS::getCharset()) . '"';
        }
        if (!empty($accesskey)) {
            $ret .= ' accesskey="' . htmlspecialchars($accesskey) . '"';
        }

        return "$ret>";
    }

    /**
     * Return an anchor sequence with the relevant parameters for a widget with
     * accesskey and text.
     *
     * @access public
     *
     * @param string $url               The full URL to be linked to
     * @param optional string $status   The JavaScript mouse-over string
     * @param optional string $class    The CSS class of the link
     * @param optional string $target   The window target to point to.
     * @param optional string $onclick  JavaScript action for the 'onclick'
     *                                  event.
     * @param optional string $title    The link title (tooltip).
     * @param optional boolean $nocheck Don't check if the access key already
     *                                  has been used?
     *
     * @return string  The full <a href>Title</a> sequence.
     */
    function widget($url, $status = '', $class = 'widget', $target = '',
                    $onclick = '', $title = '', $nocheck = false)
    {
        $ak = Horde::getAccessKey($title, $nocheck);
        $plaintitle = preg_replace('/_([A-Za-z])/', '\\1', $title);

        return Horde::link($url, $status, $class, $target, $onclick, $plaintitle, $ak) . Horde::highlightAccessKey($title, $ak) . '</a>';
    }

    /**
     * Return a session-id-ified version of $PHP_SELF.
     *
     * @access public
     *
     * @param optional boolean $query_string  Include any QUERY_STRING?
     * @param optional boolean $nocache       Include a nocache parameter in
     *                                        the URL?
     * @param optional boolean $full          Return a full URL?
     *
     * @return string  The requested URI.
     */
    function selfUrl($query_string = false, $nocache = true, $full = false)
    {
        $url = $_SERVER['PHP_SELF'];

        if ($query_string && !empty($_SERVER['QUERY_STRING'])) {
            $url .= '?' . $_SERVER['QUERY_STRING'];
        }

        $url = Horde::url($url, $full);

        if ($nocache) {
            return Util::nocacheUrl($url);
        } else {
            return $url;
        }
    }

    /**
     * Construct a correctly-pathed link to an image
     *
     * @access public
     *
     * @param string $src            The image file.
     * @param optional string $alt   Text describing the image.
     * @param optional string $attr  Any additional attributes for the image
     *                               tag.
     * @param optional string $dir   The root graphics directory.
     *
     * @return string  The full image tag.
     */
    function img($src, $alt = '', $attr = '', $dir = null)
    {
        global $browser;

        $alt = @htmlspecialchars($alt, ENT_COMPAT, NLS::getCharset());

        /* If browser does not support images, simply return the ALT text. */
        if (!$browser->hasFeature('images')) {
            return $alt;
        }

        /* If no directory has been specified, get it from the registry. */
        if ($dir === null) {
            global $registry;
            $dir = $registry->getParam('graphics');
        }

        /* If a directory has been provided, prepend it to the image source. */
        if (!empty($dir)) {
            $src = $dir . '/' . $src;
        }

        /* Build the image tag. */
        $img = "<img src=\"$src\" alt=\"$alt\" title=\"$alt\"";

        /* Add any additional attributes. Then, close the tag. */
        $img .= (!empty($attr)) ? " $attr />" : ' />';

        return $img;
    }

    /**
     * Determine the location of the system temporary directory. If a specific
     * setting cannot be found, it defaults to /tmp.
     *
     * @access public
     *
     * @return string  A directory name which can be used for temp files.
     *                 Returns false if one could not be found.
     */
    function getTempDir()
    {
        global $conf;

        /* If one has been specifically set, then use that */
        if (!empty($conf['tmpdir'])) {
            $tmp = $conf['tmpdir'];
        }

        /* Next, try Util::getTempDir(). */
        if (empty($tmp)) {
            $tmp = Util::getTempDir();
        }

        /* If it is still empty, we have failed, so return false;
         * otherwise return the directory determined. */
        return empty($tmp) ? false : $tmp;
    }

    /**
     * Create a temporary filename for the lifetime of the script, and
     * (optionally) register it to be deleted at request shutdown.
     *
     * @access public
     *
     * @param optional string $prefix   Prefix to make the temporary name more
     *                                  recognizable.
     * @param optional boolean $delete  Delete the file at the end of the
     *                                  request?
     * @param optional string $dir      Directory to create the temporary file
     *                                  in.
     * @param optional boolean $secure  If deleting file, should we securely
     *                                  delete the file?
     *
     * @return string   Returns the full path-name to the temporary file.
     *                  Returns false if a temp file could not be created.
     */
    function getTempFile($prefix = 'Horde', $delete = true, $dir = '',
                         $secure = false)
    {
        if (empty($dir) || !is_dir($dir)) {
            $dir = Horde::getTempDir();
        }

        return Util::getTempFile($prefix, $delete, $dir, $secure);
    }

    /**
     * Start output compression, if requested.
     *
     * @access public
     *
     * @since Horde 2.2
     */
    function compressOutput()
    {
        static $started;

        if (isset($started)) {
            return;
        }

        /* Compress output if requested and possible. */
        if ($GLOBALS['conf']['compress_pages'] &&
            !$GLOBALS['browser']->hasQuirk('buggy_compression') &&
            ini_get('zlib.output_compression') == '' &&
            ini_get('output_handler') != 'ob_gzhandler') {
            if (ob_get_level()) {
                ob_end_clean();
            }
            ob_start('ob_gzhandler');
        }

        $started = true;
    }

    /**
     * Determine if output compression can be used.
     *
     * @access public
     *
     * @return boolean  True if output compression can be used, false if not.
     */
    function allowOutputCompression()
    {
        require_once 'Horde/Browser.php';
        $browser = &Browser::singleton();

        /* Turn off compression for buggy browsers. */
        if ($browser->hasQuirk('buggy_compression')) {
            return false;
        }

        return (ini_get('zlib.output_compression') == '' &&
                ini_get('output_handler') != 'ob_gzhandler');
    }

    /**
     * Returns the Web server being used.
     * PHP string list built from the PHP 'configure' script.
     *
     * @access public
     *
     * @return string  A web server identification string.
     * <pre>
     * 'aolserver' = AOL Server
     * 'apache1'   = Apache 1.x
     * 'apache2'   = Apache 2.x
     * 'caudium'   = Caudium
     * 'cgi'       = Unknown server - PHP built as CGI program
     * 'cli'       = Command Line Interface build
     * 'embed'     = Embedded PHP
     * 'isapi'     = Zeus ISAPI
     * 'milter'    = Milter
     * 'nsapi'     = NSAPI
     * 'phttpd'    = PHTTPD
     * 'pi3web'    = Pi3Web
     * 'roxen'     = Roxen/Pike
     * 'servlet'   = Servlet
     * 'thttpd'    = thttpd
     * 'tux'       = Tux
     * 'webjames'  = Webjames
     * </pre>
     */
    function webServerID()
    {
        $server = php_sapi_name();

        if ($server == 'apache') {
            return 'apache1';
        } elseif (($server == 'apache2filter') ||
                  ($server == 'apache2handler')) {
            return 'apache2';
        } else {
            return $server;
        }
    }

    /**
     * Returns the <link> tag for the CSS stylesheet.
     *
     * @access public
     *
     * @param optional string $app       The Horde application.
     * @param optional mixed $theme      The theme to use; specify an empty
     *                                   value to retrieve the theme from
     *                                   user preferences, and false for no
     *                                   theme.
     * @param optional boolean $inherit  Inherit Horde-wide CSS?
     *
     * @return string  A <link> tag for a CSS stylesheet.
     */
    function stylesheetLink($app = null, $theme = '', $inherit = true)
    {
        global $registry;

        $css_link = Horde::url($registry->getParam('webroot', 'horde') . '/services/css.php', false, -1);
        if (!empty($app)) {
            if (substr($app, 0, 3) != 'app') {
                $app = 'app=' . $app;
            }
            $css_link = $css_link . '?' . $app;
        }
        if (!$inherit) {
            $css_link = Util::addParameter($css_link, 'inherit', 'no');
        }
        if ($theme !== false) {
            if (empty($theme)) {
                global $prefs;
                $theme = $prefs->getValue('theme');
            }
            if (!empty($theme)) {
                $css_link = Util::addParameter($css_link, 'theme', htmlspecialchars($theme));
            }
        }

        return '<link href="' . $css_link . '" rel="stylesheet" type="text/css" />';
    }

    /**
     * If there is a custom session handler, set it up now.
     *
     * @access public
     */
    function setupSessionHandler()
    {
        global $conf;

        ini_set('url_rewriter.tags', 0);
        session_set_cookie_params($conf['session']['timeout'],
                                  $conf['cookie']['path'], $conf['cookie']['domain'], $conf['use_ssl'] == 1 ? 1 : 0);
        session_cache_limiter($conf['session']['cache_limiter']);
        session_name(urlencode($conf['session']['name']));

        $type = !empty($conf['sessionhandler']['type']) ? $conf['sessionhandler']['type'] : 'none';

        if ($type == 'external') {
            $calls = $conf['sessionhandler']['params'];
            session_set_save_handler($calls['open'],
                                     $calls['close'],
                                     $calls['read'],
                                     $calls['write'],
                                     $calls['destroy'],
                                     $calls['gc']);
        } elseif ($type != 'none') {
            global $_session_handler;
            require_once 'Horde/SessionHandler.php';
            $_session_handler = &SessionHandler::singleton($conf['sessionhandler']['type']);
            if (!empty($_session_handler) &&
                !is_a($_session_handler, 'PEAR_Error')) {
                ini_set('session.save_handler', 'user');
                session_set_save_handler(array($_session_handler, 'open'),
                                         array($_session_handler, 'close'),
                                         array($_session_handler, 'read'),
                                         array($_session_handler, 'write'),
                                         array($_session_handler, 'destroy'),
                                         array($_session_handler, 'gc'));
            } else {
                Horde::fatal(PEAR::raiseError('Horde is unable to correctly start the custom session handler.'), __FILE__, __LINE__, false);
            }
        }
    }

    /**
     * Returns an un-used access key from the label given.
     *
     * @access public
     *
     * @param string $label             The label to choose an access key from.
     * @param optional boolean $nocheck Don't check if the access key already
     *                                  has been used?
     *
     * @return string  A single lower case character access key or empty
     *                 string if none can be found
     */
    function getAccessKey($label, $nocheck = false, $shutdown = false)
    {
        /* The access keys already used in this page */
        static $_used = array();

        /* The labels already used in this page */
        static $_labels = array();

        /* Shutdown call for translators? */
        if ($shutdown) {
            if (!count($_labels)) {
                return;
            }
            $script = basename($_SERVER['PHP_SELF']);
            $labels = array_keys($_labels);
            sort($labels);
            $used = array_keys($_used);
            sort($used);
            $remaining = str_replace($used, array(), 'abcdefghijklmnopqrstuvwxyz');
            Horde::logMessage('Access key information for ' . $script, __FILE__, __LINE__);
            Horde::logMessage('Used labels: ' . implode(',', $labels), __FILE__, __LINE__);
            Horde::logMessage('Used keys: ' . implode('', $used), __FILE__, __LINE__);
            Horde::logMessage('Free keys: ' . $remaining, __FILE__, __LINE__);
            return;
        }

        /* Use access keys at all? */
        static $notsupported;
        if (!isset($notsupported)) {
            $notsupported = !$GLOBALS['browser']->hasFeature('accesskey') ||
                !$GLOBALS['prefs']->getValue('widget_accesskey');
        }

        if ($notsupported || !preg_match('/_([A-Za-z])/', $label, $match)) {
            return '';
        }
        $key = $match[1];

        /* Has this key already been used? */
        if (isset($_used[strtolower($key)]) &&
            !($nocheck && isset($_labels[$label]))) {
            return '';
        }

        /* Save key and label. */
        $_used[strtolower($key)] = true;
        $_labels[$label] = true;

        return $key;
    }

    /**
     * Highlight an access key in a label.
     *
     * @access public
     *
     * @param string $label      The label to to highlight the access key in.
     * @param string $accessKey  The access key to highlight.
     *
     * @return string  The HTML version of the label with the access key
     *                 highlighted.
     */
    function highlightAccessKey($label, $accessKey)
    {
        include_once HORDE_BASE . '/config/nls.php';
        global $nls;

        $stripped_label = preg_replace('/_([A-Za-z])/', '\\1', $label);

        if (empty($accessKey)) {
            return $stripped_label;
        }

        if (isset($nls['multibyte'][NLS::getCharset(true)])) {
            return $stripped_label . '(' . '<span class="accessKey">' .
                strtoupper($accessKey) . '</span>' . ')';
        } else {
            return str_replace('_' . $accessKey, '<span class="accessKey">' . $accessKey . '</span>', $label);
        }
    }

    /**
     * Returns the appropriate "accesskey" and "title" attributes
     * for an HTML tag and the given label.
     *
     * @param string $label             The title of an HTML element
     * @param optional boolean $nocheck Don't check if the access key already
     *                                  has been used?
     *
     * @return string  The title, and if appropriate, the accesskey
     *                 attributes for the element.
     */
    function getAccessKeyAndTitle($label, $nocheck = false)
    {
        $ak = Horde::getAccessKey($label, $nocheck);
        $attributes = 'title="' . preg_replace('/_([A-Za-z])/', '\\1', $label);
        if (!empty($ak)) {
            $attributes .= sprintf(_(" (Accesskey %s)"), $ak);
            $attributes .= '" accesskey="' . $ak;
        }
        $attributes .= '"';
        return $attributes;
    }

    /**
     * Returns a label element including an access key for usage
     * in conjuction with a form field. User preferences regarding
     * access keys are respected.
     *
     * @param string $for    The form field's id attribute.
     * @param string $label  The label text.
     * @param string $ak     The access key to use. If null a new access key
     *                       will be generated.
     *
     * @return string  The html code for the label element.
     */
    function label($for, $label, $ak = null)
    {
        global $prefs;

        if (is_null($ak)) {
            $ak = Horde::getAccesskey($label, 1);
        }
        $label = Horde::highlightAccessKey($label, $ak);

        return sprintf('<label for="%s"%s>%s</label>',
                       $for,
                       !empty($ak) ? ' accesskey="' . $ak . '"' : '',
                       $label);
    }

    /**
     * Redirect to the main Horde login page on authentication failure.
     *
     * @access public
     */
    function authenticationFailureRedirect()
    {
        require_once 'Horde/CLI.php';
        if (Horde_CLI::runningFromCLI()) {
            $cli = &Horde_CLI::singleton();
            $cli->fatal(_("You are not authenticated."));
        }

        global $registry;

        $url = $registry->getParam('webroot', 'horde') . '/login.php';
        $url = Util::addParameter($url, 'url', Horde::selfURL(true));
        $url = Auth::addLogoutParameters($url);
        header('Location: ' . Horde::url($url, true));
        exit;
    }

    /**
     * Use DOM Tooltips (via javascript) to display the 'title' attribute
     * for Horde::link() calls.
     *
     * If using this function, the following function must be called:
     *   Horde::addScriptFile('tooltip.js', 'horde');
     *
     * @access public
     *
     * @param string $url                 The full URL to be linked to
     * @param optional string $status     The JavaScript mouse-over string
     * @param optional string $class      The CSS class of the link
     * @param optional string $target     The window target to point to.
     * @param optional string $onclick    JavaScript action for the 'onclick'
     *                                    event.
     * @param optional string $title      The link title (tooltip).
     * @param optional string $accesskey  The access key to use.
     *
     * @return string  The full <a href> tag.
     */
    function linkTooltip($url, $status = '', $class = '', $target = '',
                         $onclick = '', $title = '', $accesskey = '')
    {
        $url = substr(Horde::link($url, null, $class, $target, $onclick, null, $accesskey), 0, -1);

        if (!empty($status)) {
            $status = @htmlspecialchars(addslashes($status), ENT_QUOTES, NLS::getCharset());
        }

        $title = trim($title);
        if (!empty($title)) {
            require_once 'Horde/Text.php';
            $title = Text::toHTML($title, TEXT_HTML_NOHTML, '', '');
            $title = '<pre style="margin:0px;">' . strtr(addslashes($title), array("\r" => '', "\n" => '')) . '</pre>';
            $url .= ' onmouseover="tooltipLink(\'' . @htmlspecialchars($title, ENT_QUOTES, NLS::getCharset()) . '\', \'' . $status . '\'); return true;" onmouseout="tooltipClose();"';
        }
        $url .= '>';

        return $url;
    }

    /**
     * Provides a standardised function to call a Horde hook, checking whether
     * a hook config file exists and whether the function itself exists. If
     * these two conditions are not satisfied it will return a PEAR error to
     * differentiate from a hook which returns false or empty.
     *
     * @access public
     *
     * @param string $hook          The function to call.
     * @param optional array  $app  An array of any arguments to pass to the
     *                              hook function.
     * @param optional string $app  If specified look for hooks in the config
     *                              directory of this app.
     *
     * @return mixed  Either the results of the hook or PEAR error on failure.
     */
    function callHook($hook, $args = array(), $app = 'horde')
    {
        global $registry;

        if (file_exists($registry->getParam('fileroot', $app) . '/config/hooks.php')) {
            require_once $registry->getParam('fileroot', $app) . '/config/hooks.php';
            if (function_exists($hook)) {
                return call_user_func_array($hook, $args);
            }
        }

        $error = PEAR::raiseError(sprintf(_("Could not call function %s in application %s."), $hook, $app));
        Horde::logMessage($error, __FILE__, __LINE__, PEAR_LOG_DEBUG);

        return $error;
    }

    /**
     * Returns an array of available menu items when in a Horde script.
     *
     * @return array $menu  Available menu items.
     */
    function getHordeMenu()
    {
        global $registry;

        $menu = array();
        $menu[] = array('url' => Horde::applicationUrl('services/portal/'),
                        'text' =>  _("Home"),
                        'icon' => 'horde.gif',
                        'icon_path' => $registry->getParam('graphics'));
        if (Auth::isAdmin()) {
            $menu[] = array('url' => Horde::applicationUrl('admin/'),
                            'text' =>  _("Administration"),
                            'icon' => 'administration.gif',
                            'icon_path' => $registry->getParam('graphics'));
        }

        return $menu;
    }

}
