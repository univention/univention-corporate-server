<?php

/**
 * Error code for a missing driver configuration.
 */
define('HORDE_ERROR_DRIVER_CONFIG_MISSING', 1);

/**
 * Error code for an incomplete driver configuration.
 */
define('HORDE_ERROR_DRIVER_CONFIG', 2);

/**
 * The Util:: class provides generally useful methods of different kinds.
 *
 * $Horde: framework/Util/Util.php,v 1.384.6.37 2009-07-21 18:17:23 slusarz Exp $
 *
 * Copyright 1999-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @author  Jon Parise <jon@horde.org>
 * @since   Horde 3.0
 * @package Horde_Util
 */
class Util {

    /**
     * Returns an object's clone.
     *
     * @param object &$obj  The object to clone.
     *
     * @return object  The cloned object.
     */
    function &cloneObject(&$obj)
    {
        if (!is_object($obj)) {
            $bt = debug_backtrace();
            if (isset($bt[1])) {
                $caller = $bt[1]['function'];
                if (isset($bt[1]['class'])) {
                    $caller = $bt[1]['class'].$bt[1]['type'].$caller;
                }
            } else {
                $caller = 'main';
            }
            $caller .= ' on line ' . $bt[0]['line'] . ' of ' . $bt[0]['file'];
            Horde::logMessage('Util::cloneObject called on variable of type ' . gettype($obj) . ' by ' . $caller, __FILE__, __LINE__, PEAR_LOG_DEBUG);

            $ret = $obj;
            return $ret;
        }

        $ret = unserialize(serialize($obj));
        return $ret;
    }

    /**
     * Buffers the output from a function call, like readfile() or
     * highlight_string(), that prints the output directly, so that instead it
     * can be returned as a string and used.
     *
     * @param string $function  The function to run.
     * @param mixed $arg1       First argument to $function().
     * @param mixed $arg2       Second argument to $function().
     * @param mixed $arg...     ...
     * @param mixed $argN       Nth argument to $function().
     *
     * @return string  The output of the function.
     */
    function bufferOutput()
    {
        if (func_num_args() == 0) {
            return false;
        }
        $include = false;
        $args = func_get_args();
        $function = array_shift($args);
        if (is_array($function)) {
            if (!is_callable($function)) {
                return false;
            }
        } elseif (($function == 'include') ||
                  ($function == 'include_once') ||
                  ($function == 'require') ||
                  ($function == 'require_once')) {
            $include = true;
        } elseif (!function_exists($function)) {
            return false;
        }

        ob_start();
        if ($include) {
            $file = implode(',', $args);
            switch ($function) {
            case 'include':
                include $file;
                break;

            case 'include_once':
                include_once $file;
                break;

            case 'require':
                require $file;
                break;

            case 'require_once':
                require_once $file;
                break;
            }
        } else {
            call_user_func_array($function, $args);
        }

        return ob_get_clean();
    }

    /**
     * Checks to see if a value has been set by the script and not by GET,
     * POST, or cookie input. The value being checked MUST be in the global
     * scope.
     *
     * @param string $varname  The variable name to check.
     * @param mixed $default   Default value if the variable isn't present
     *                         or was specified by the user. Defaults to null.
     *                         @since Horde 3.1
     *
     * @return mixed  $default if the var is in user input or not present,
     *                the variable value otherwise.
     */
    function nonInputVar($varname, $default = null)
    {
        if (isset($_GET[$varname]) ||
            isset($_POST[$varname]) ||
            isset($_COOKIE[$varname])) {
            return $default;
        } else {
            return isset($GLOBALS[$varname]) ? $GLOBALS[$varname] : $default;
        }
    }

    /**
     * Adds a name=value pair to the end of an URL, taking care of whether
     * there are existing parameters and whether to use ?, & or &amp; as the
     * glue.  All data will be urlencoded.
     *
     * @param string $url       The URL to modify
     * @param mixed $parameter  Either the name=value pair to add
     *                          (DEPRECATED) -or-
     *                          the name value -or-
     *                          an array of name/value pairs.
     * @param string $value     If specified, the value part ($parameter is
     *                          then assumed to just be the parameter name).
     * @param boolean $encode   Encode the argument separator?
     *
     * @return string  The modified URL.
     */
    function addParameter($url, $parameter, $value = null, $encode = true)
    {
        if (empty($parameter)) {
            return $url;
        }

        $add = array();
        $arg = $encode ? '&amp;' : '&';

        if (strpos($url, '?') !== false) {
            list($url, $query) = explode('?', $url);

            /* Check if the argument separator has been already
             * htmlentities-ized in the URL. */
            if (preg_match('/=.*?&amp;.*?=/', $query)) {
                $query = html_entity_decode($query);
                $arg = '&amp;';
            } elseif (preg_match('/=.*?&.*?=/', $query)) {
                $arg = '&';
            }
            $pairs = explode('&', $query);
            foreach ($pairs as $pair) {
                $pair = explode('=', urldecode($pair), 2);
                $pair_val = (count($pair) == 2) ? $pair[1] : '';
                if (substr($pair[0], -2) == '[]') {
                    $name = substr($pair[0], 0, -2);
                    if (!isset($add[$name])) {
                        $add[$name] = array();
                    }
                    $add[$name][] = $pair_val;
                } else {
                    $add[$pair[0]] = $pair_val;
                }
            }
        }
        if (is_array($parameter)) {
            $add = array_merge($add, $parameter);
        } else {
            $add[$parameter] = $value;
        }

        $url_params = array();
        foreach ($add as $parameter => $value) {
            if (is_array($value)) {
                foreach ($value as $val) {
                    $url_params[] = urlencode($parameter) . '[]=' . urlencode($val);
                }
            } else {
                $url_params[] = urlencode($parameter) . '=' . urlencode($value);
            }
        }

        if (count($url_params)) {
            return $url . '?' . implode($arg, $url_params);
        } else {
            return $url;
        }
    }

    /**
     * Removes name=value pairs from a URL.
     *
     * @param string $url    The URL to modify.
     * @param mixed $remove  Either a single parameter to remove or an array
     *                       of parameters to remove.
     *
     * @return string  The modified URL.
     */
    function removeParameter($url, $remove)
    {
        if (!is_array($remove)) {
            $remove = array($remove);
        }

        /* Return immediately if there are no parameters to remove. */
        if (($pos = strpos($url, '?')) === false) {
            return $url;
        }

        $entities = false;
        list($url, $query) = explode('?', $url, 2);

        /* Check if the argument separator has been already
         * htmlentities-ized in the URL. */
        if (preg_match('/=.*?&amp;.*?=/', $query)) {
            $entities = true;
            $query = html_entity_decode($query);
        }

        /* Get the list of parameters. */
        $pairs = explode('&', $query);
        $params = array();
        foreach ($pairs as $pair) {
            $pair = explode('=', $pair, 2);
            $params[$pair[0]] = count($pair) == 2 ? $pair[1] : '';
        }

        /* Remove the parameters. */
        foreach ($remove as $param) {
            unset($params[$param]);
        }

        if (!count($params)) {
            return $url;
        }

        /* Flatten arrays.
         * FIXME: should handle more than one array level somehow. */
        $add = array();
        foreach ($params as $key => $val) {
            if (is_array($val)) {
                foreach ($val as $v) {
                    $add[] = $key . '[]=' . $v;
                }
            } else {
                $add[] = $key . '=' . $val;
            }
        }

        $query = implode('&', $add);
        if ($entities) {
            $query = htmlentities($query);
        }

        return $url . '?' . $query;
    }

    /**
     * Returns a url with the 'nocache' parameter added, if the browser is
     * buggy and caches old URLs.
     *
     * @param string $url       The URL to modify.
     * @param boolean $encode   Encode the argument separator? (since
     *                          Horde 3.2)
     *
     * @return string  The requested URI.
     */
    function nocacheUrl($url, $encode = true)
    {
        static $rand_num;

        require_once 'Horde/Browser.php';
        $browser = &Browser::singleton();

        /* We may need to set a dummy parameter 'nocache' since some
         * browsers do not always honor the 'no-cache' header. */
        if ($browser->hasQuirk('cache_same_url')) {
            if (!isset($rand_num)) {
                $rand_num = base_convert(microtime(), 10, 36);
            }
            return Util::addParameter($url, 'nocache', $rand_num, $encode);
        } else {
            return $url;
        }
    }

    /**
     * Returns a hidden form input containing the session name and id.
     *
     * @param boolean $append_session  0 = only if needed, 1 = always.
     *
     * @return string  The hidden form input, if needed/requested.
     */
    function formInput($append_session = 0)
    {
        if ($append_session == 1 ||
            !isset($_COOKIE[session_name()])) {
            return '<input type="hidden" name="' . htmlspecialchars(session_name()) . '" value="' . htmlspecialchars(session_id()) . "\" />\n";
        } else {
            return '';
        }
    }

    /**
     * Prints a hidden form input containing the session name and id.
     *
     * @param boolean $append_session  0 = only if needed, 1 = always.
     */
    function pformInput($append_session = 0)
    {
        echo Util::formInput($append_session);
    }

    /**
     * If magic_quotes_gpc is in use, run stripslashes() on $var.
     *
     * @param string &$var  The string to un-quote, if necessary.
     *
     * @return string  $var, minus any magic quotes.
     */
    function dispelMagicQuotes(&$var)
    {
        static $magic_quotes;

        if (!isset($magic_quotes)) {
            $magic_quotes = get_magic_quotes_gpc();
        }

        if ($magic_quotes) {
            if (!is_array($var)) {
                $var = stripslashes($var);
            } else {
                array_walk($var, array('Util', 'dispelMagicQuotes'));
            }
        }

        return $var;
    }

    /**
     * Gets a form variable from GET or POST data, stripped of magic quotes if
     * necessary. If the variable is somehow set in both the GET data and the
     * POST data, the value from the POST data will be returned and the GET
     * value will be ignored.
     *
     * @param string $var      The name of the form variable to look for.
     * @param string $default  The value to return if the variable is not
     *                         there.
     *
     * @return string  The cleaned form variable, or $default.
     */
    function getFormData($var, $default = null)
    {
        return (($val = Util::getPost($var)) !== null)
            ? $val : Util::getGet($var, $default);
    }

    /**
     * Gets a form variable from GET data, stripped of magic quotes if
     * necessary. This function will NOT return a POST variable.
     *
     * @param string $var      The name of the form variable to look for.
     * @param string $default  The value to return if the variable is not
     *                         there.
     *
     * @return string  The cleaned form variable, or $default.
     */
    function getGet($var, $default = null)
    {
        return (isset($_GET[$var]))
            ? Util::dispelMagicQuotes($_GET[$var])
            : $default;
    }

    /**
     * Gets a form variable from POST data, stripped of magic quotes if
     * necessary. This function will NOT return a GET variable.
     *
     * @param string $var      The name of the form variable to look for.
     * @param string $default  The value to return if the variable is not
     *                         there.
     *
     * @return string  The cleaned form variable, or $default.
     */
    function getPost($var, $default = null)
    {
        return (isset($_POST[$var]))
            ? Util::dispelMagicQuotes($_POST[$var])
            : $default;
    }

    /**
     * Determines the location of the system temporary directory.
     *
     * @return string  A directory name which can be used for temp files.
     *                 Returns false if one could not be found.
     */
    function getTempDir()
    {
        /* First, try PHP's upload_tmp_dir directive. */
        $tmp = ini_get('upload_tmp_dir');

        /* Otherwise, try to determine the TMPDIR environment
         * variable. */
        if (empty($tmp)) {
            $tmp = getenv('TMPDIR');
        }

        /* If we still cannot determine a value, then cycle through a
         * list of preset possibilities. */
        $tmp_locations = array('/tmp', '/var/tmp', 'c:\WUTemp', 'c:\temp',
                               'c:\windows\temp', 'c:\winnt\temp');
        while (empty($tmp) && count($tmp_locations)) {
            $tmp_check = array_shift($tmp_locations);
            if (@is_dir($tmp_check)) {
                $tmp = $tmp_check;
            }
        }

        /* If it is still empty, we have failed, so return false;
         * otherwise return the directory determined. */
        return empty($tmp) ? false : $tmp;
    }

    /**
     * Creates a temporary filename for the lifetime of the script, and
     * (optionally) register it to be deleted at request shutdown.
     *
     * @param string $prefix   Prefix to make the temporary name more
     *                         recognizable.
     * @param boolean $delete  Delete the file at the end of the request?
     * @param string $dir      Directory to create the temporary file in.
     * @param boolean $secure  If deleting file, should we securely delete the
     *                         file?
     *
     * @return string   Returns the full path-name to the temporary file.
     *                  Returns false if a temp file could not be created.
     */
    function getTempFile($prefix = '', $delete = true, $dir = '', $secure = false)
    {
        if (empty($dir) || !is_dir($dir)) {
            $tmp_dir = Util::getTempDir();
        } else {
            $tmp_dir = $dir;
        }

        if (empty($tmp_dir)) {
            return false;
        }

        $tmp_file = tempnam($tmp_dir, $prefix);

        /* If the file was created, then register it for deletion and return. */
        if (empty($tmp_file)) {
            return false;
        }

        if ($delete) {
            Util::deleteAtShutdown($tmp_file, true, $secure);
        }
        return $tmp_file;
    }

    /**
     * Creates a temporary directory in the system's temporary directory.
     *
     * @param boolean $delete   Delete the temporary directory at the end of
     *                          the request?
     * @param string $temp_dir  Use this temporary directory as the directory
     *                          where the temporary directory will be created.
     *
     * @return string  The pathname to the new temporary directory.
     *                 Returns false if directory not created.
     */
    function createTempDir($delete = true, $temp_dir = null)
    {
        if (is_null($temp_dir)) {
            $temp_dir = Util::getTempDir();
        }

        if (empty($temp_dir)) {
            return false;
        }

        /* Get the first 8 characters of a random string to use as a temporary
           directory name. */
        do {
            $new_dir = $temp_dir . '/' . substr(base_convert(mt_rand() . microtime(), 10, 36), 0, 8);
        } while (file_exists($new_dir));

        $old_umask = umask(0000);
        if (!mkdir($new_dir, 0700)) {
            $new_dir = false;
        } elseif ($delete) {
            Util::deleteAtShutdown($new_dir);
        }
        umask($old_umask);

        return $new_dir;
    }

    /**
     * Returns the canonical path of the string.  Like PHP's built-in
     * realpath() except the directory need not exist on the local server.
     *
     * Algorithim loosely based on code from the Perl File::Spec::Unix module
     * (version 1.5).
     *
     * @since Horde 3.0.5
     *
     * @param string $path  A file path.
     *
     * @return string  The canonicalized file path.
     */
    function realPath($path)
    {
        /* Standardize on UNIX directory separators. */
        if (!strncasecmp(PHP_OS, 'WIN', 3)) {
            $path = str_replace('\\', '/', $path);
        }

        /* xx////xx -> xx/xx
         * xx/././xx -> xx/xx */
        $path = preg_replace(array("|/+|", "@(/\.)+(/|\Z(?!\n))@"), array('/', '/'), $path);

        /* ./xx -> xx */
        if ($path != './') {
            $path = preg_replace("|^(\./)+|", '', $path);
        }

        /* /../../xx -> xx */
        $path = preg_replace("|^/(\.\./?)+|", '/', $path);

        /* xx/ -> xx */
        if ($path != '/') {
            $path = preg_replace("|/\Z(?!\n)|", '', $path);
        }

        /* /xx/.. -> / */
        while (strpos($path, '/..') !== false) {
            $path = preg_replace("|/[^/]+/\.\.|", '', $path);
        }

        return empty($path) ? '/' : $path;
    }

    /**
     * Removes given elements at request shutdown.
     *
     * If called with a filename will delete that file at request shutdown; if
     * called with a directory will remove that directory and all files in that
     * directory at request shutdown.
     *
     * If called with no arguments, return all elements to be deleted (this
     * should only be done by Util::_deleteAtShutdown).
     *
     * The first time it is called, it initializes the array and registers
     * Util::_deleteAtShutdown() as a shutdown function - no need to do so
     * manually.
     *
     * The second parameter allows the unregistering of previously registered
     * elements.
     *
     * @param string $filename   The filename to be deleted at the end of the
     *                           request.
     * @param boolean $register  If true, then register the element for
     *                           deletion, otherwise, unregister it.
     * @param boolean $secure    If deleting file, should we securely delete
     *                           the file?
     */
    function deleteAtShutdown($filename = false, $register = true,
                              $secure = false)
    {
        static $dirs, $files, $securedel;

        /* Initialization of variables and shutdown functions. */
        if (is_null($dirs)) {
            $dirs = array();
            $files = array();
            $securedel = array();
            register_shutdown_function(array('Util', '_deleteAtShutdown'));
        }

        if ($filename) {
            if ($register) {
                if (@is_dir($filename)) {
                    $dirs[$filename] = true;
                } else {
                    $files[$filename] = true;
                }
                if ($secure) {
                    $securedel[$filename] = true;
                }
            } else {
                unset($dirs[$filename]);
                unset($files[$filename]);
                unset($securedel[$filename]);
            }
        } else {
            return array($dirs, $files, $securedel);
        }
    }

    /**
     * Deletes registered files at request shutdown.
     *
     * This function should never be called manually; it is registered as a
     * shutdown function by Util::deleteAtShutdown() and called automatically
     * at the end of the request. It will retrieve the list of folders and
     * files to delete from Util::deleteAtShutdown()'s static array, and then
     * iterate through, deleting folders recursively.
     *
     * Contains code from gpg_functions.php.
     * Copyright 2002-2003 Braverock Ventures
     *
     * @access private
     */
    function _deleteAtShutdown()
    {
        $registered = Util::deleteAtShutdown();
        $dirs = $registered[0];
        $files = $registered[1];
        $secure = $registered[2];

        foreach ($files as $file => $val) {
            /* Delete files */
            if ($val && file_exists($file)) {
                /* Should we securely delete the file by overwriting the data
                   with a random string? */
                if (isset($secure[$file])) {
                    $filesize = filesize($file);
                    /* See http://www.cs.auckland.ac.nz/~pgut001/pubs/secure_del.html.
                     * We save the random overwrites for efficiency reasons. */
                    $patterns = array("\x55", "\xaa", "\x92\x49\x24", "\x49\x24\x92", "\x24\x92\x49", "\x00", "\x11", "\x22", "\x33", "\x44", "\x55", "\x66", "\x77", "\x88", "\x99", "\xaa", "\xbb", "\xcc", "\xdd", "\xee", "\xff", "\x92\x49\x24", "\x49\x24\x92", "\x24\x92\x49", "\x6d\xb6\xdb", "\xb6\xdb\x6d", "\xdb\x6d\xb6");
                    $fp = fopen($file, 'r+');
                    foreach ($patterns as $pattern) {
                        $pattern = substr(str_repeat($pattern, floor($filesize / strlen($pattern)) + 1), 0, $filesize);
                        fwrite($fp, $pattern);
                        fseek($fp, 0);
                    }
                    fclose($fp);
                }
                @unlink($file);
            }
        }

        foreach ($dirs as $dir => $val) {
            /* Delete directories */
            if ($val && file_exists($dir)) {
                /* Make sure directory is empty. */
                $dir_class = dir($dir);
                while (false !== ($entry = $dir_class->read())) {
                    if ($entry != '.' && $entry != '..') {
                        @unlink($dir . '/' . $entry);
                    }
                }
                $dir_class->close();
                @rmdir($dir);
            }
        }
    }

    /**
     * Outputs javascript code to close the current window.
     *
     * @param string $code  Any additional javascript code to run before
     *                      closing the window.
     */
    function closeWindowJS($code = '')
    {
        echo '<script type="text/javascript">//<![CDATA[' . "\n"
            . $code . 'window.close();' . "\n//]]></script>\n";
    }

    /**
     * Caches the result of extension_loaded() calls.
     *
     * @access private
     *
     * @param string $ext  The extension name.
     *
     * @return boolean  Is the extension loaded?
     */
    function extensionExists($ext)
    {
        static $cache = array();

        if (!isset($cache[$ext])) {
            $cache[$ext] = extension_loaded($ext);
        }

        return $cache[$ext];
    }

    /**
     * Tries to load a PHP extension, behaving correctly for all operating
     * systems.
     *
     * @param string $ext  The extension to load.
     *
     * @return boolean  True if the extension is now loaded, false if not.
     *                  True can mean that the extension was already loaded,
     *                  OR was loaded dynamically.
     */
    function loadExtension($ext)
    {
        /* If $ext is already loaded, our work is done. */
        if (Util::extensionExists($ext)) {
            return true;
        }

        /* See if we can call dl() at all, by the current ini settings. */
        if ((ini_get('enable_dl') != 1) || (ini_get('safe_mode') == 1)) {
            return false;
        }

        if (!strncasecmp(PHP_OS, 'WIN', 3)) {
            $suffix = 'dll';
        } else {
            switch (PHP_OS) {
            case 'HP-UX':
                $suffix = 'sl';
                break;

            case 'AIX':
                $suffix = 'a';
                break;

            case 'OSX':
                $suffix = 'bundle';
                break;

            default:
                $suffix = 'so';
            }
        }

        return @dl($ext . '.' . $suffix) || @dl('php_' . $ext . '.' . $suffix);
    }

    /**
     * Checks if all necessary parameters for a driver's configuration are set
     * and returns a PEAR_Error if something is missing.
     *
     * @param array $params   The configuration array with all parameters.
     * @param array $fields   An array with mandatory parameter names for this
     *                        driver.
     * @param string $name    The clear text name of the driver. If not
     *                        specified, the application name will be used.
     * @param array $info     A hash containing detailed information about the
     *                        driver. Will be passed as the userInfo to the
     *                        PEAR_Error.
     */
    function assertDriverConfig($params, $fields, $name, $info = array())
    {
        $info = array_merge($info,
                            array('params' => $params,
                                  'fields' => $fields,
                                  'name' => $name));

        if (!is_array($params) || !count($params)) {
            require_once 'PEAR.php';
            return PEAR::throwError(sprintf(_("No configuration information specified for %s."), $name),
                                    HORDE_ERROR_DRIVER_CONFIG_MISSING,
                                    $info);
        }

        foreach ($fields as $field) {
            if (!isset($params[$field])) {
                require_once 'PEAR.php';
                return PEAR::throwError(sprintf(_("Required \"%s\" not specified in configuration."), $field, $name),
                                        HORDE_ERROR_DRIVER_CONFIG,
                                        $info);
            }
        }
    }

    /**
     * Returns a format string to be used by strftime().
     *
     * @param string $format  A format string as used by date().
     *
     * @return string  A format string as similar as possible to $format.
     */
    function date2strftime($format)
    {
        $dateSymbols = array('a', 'A', 'd', 'D', 'F', 'g', 'G', 'h', 'H', 'i', 'j', 'l', 'm', 'M', 'n', 'r', 's', 'T', 'w', 'W', 'y', 'Y', 'z', 'm/d/Y', 'M', "\n", 'g:i a', 'G:i', "\t", 'H:i:s', '%');
        $strftimeSymbols = array('%p', '%p', '%d', '%a', '%B', '%I', '%H', '%I', '%H', '%M', '%e', '%A', '%m', '%b', '%m', '%a, %e %b %Y %T %Z', '%S', '%Z', '%w', '%V', '%y', '%Y', '%j', '%D', '%h', '%n', '%r', '%R', '%t', '%T', '%%');

        $result = '';
        for ($pos = 0; $pos < strlen($format);) {
            for ($symbol = 0; $symbol < count($dateSymbols); $symbol++) {
                if (strpos($format, $dateSymbols[$symbol], $pos) === $pos) {
                    $result .= $strftimeSymbols[$symbol];
                    $pos += strlen($dateSymbols[$symbol]);
                    continue 2;
                }
            }
            $result .= substr($format, $pos, 1);
            $pos++;
        }

        return $result;
    }

    /**
     * Returns a format string to be used by date().
     *
     * @param string $format  A format string as used by strftime().
     *
     * @return string  A format string as similar as possible to $format.
     */
    function strftime2date($format)
    {
        $dateSymbols = array('a', 'A', 'd', 'D', 'F', 'g', 'G', 'h', 'H', 'i', 'j', 'l', 'm', 'M', 'n', 'r', 's', 'T', 'w', 'W', 'y', 'Y', 'z', 'm/d/Y', 'M', "\n", 'g:i a', 'G:i', "\t", 'H:i:s', '%');
        $strftimeSymbols = array('%p', '%p', '%d', '%a', '%B', '%I', '%H', '%I', '%H', '%M', '%e', '%A', '%m', '%b', '%m', '%a, %e %b %Y %T %Z', '%S', '%Z', '%w', '%V', '%y', '%Y', '%j', '%D', '%h', '%n', '%r', '%R', '%t', '%T', '%%');

        return str_replace($strftimeSymbols, $dateSymbols, $format);
    }

    /**
     * Utility function to obtain PATH_INFO information.
     *
     * @since Horde 3.2
     *
     * @return string  The PATH_INFO string.
     */
    function getPathInfo()
    {
        if (isset($_SERVER['PATH_INFO']) &&
            strpos($_SERVER['SERVER_SOFTWARE'], 'lighttpd') === false) {
            return $_SERVER['PATH_INFO'];
        } elseif (isset($_SERVER['REQUEST_URI']) &&
                  isset($_SERVER['SCRIPT_NAME'])) {
            $search = array((basename($_SERVER['SCRIPT_NAME']) == 'index.php') ? dirname($_SERVER['SCRIPT_NAME']) . '/' : $_SERVER['SCRIPT_NAME']);
            $replace = array('');
            if (!empty($_SERVER['QUERY_STRING'])) {
                $search[] = '?' . $_SERVER['QUERY_STRING'];
                $replace[] = '';
            }
            return str_replace($search, $replace, $_SERVER['REQUEST_URI']);
        }

        return '';
    }

    /**
     * Calculate an HMAC for a given $data and secret $key using SHA-1.
     *
     * @param string $data  Data to sign
     * @param string $key   Secret key
     * @param boolean $raw_output  Return binary data? Default to hex.
     *
     * @return string | binary  HMAC
     *
     * @since Horde 3.3
     */
    function hmac($data, $key, $raw_output = false)
    {
        if (function_exists('hash_hmac')) {
            return hash_hmac('sha1', $data, $key, $raw_output);
        }

        if (strlen($key) > 64) {
            $key =  pack('H40', sha1($key));
        }
        if (strlen($key) < 64) {
            $key = str_pad($key, 64, chr(0));
        }

        /* Calculate the padded keys and save them */
        $ipad = substr($key, 0, 64) ^ str_repeat(chr(0x36), 64);
        $opad = substr($key, 0, 64) ^ str_repeat(chr(0x5C), 64);

        if ($raw_output) {
            return pack('H*', sha1($opad . pack('H40', sha1($ipad . $data))));
        }
        return sha1($opad . pack('H40', sha1($ipad . $data)));
    }

    /**
     * URL-safe base64 encoding, with trimmed =
     *
     * @since Horde 3.3
     *
     * @param string $string  String to encode.
     *
     * @return string  URL-safe, base64 encoded data.
     */
    function uriB64Encode($string)
    {
        $data = base64_encode($string);
        $data = str_replace(array('+', '/', '='), array('-', '_', ''), $data);
        return $data;
    }

    /**
     * Decode URL-safe base64 data, dealing with missing =
     *
     * @since Horde 3.3
     *
     * @param string $string  Encoded data
     *
     * @return string  Decoded data.
     */
    function uriB64Decode($string)
    {
        $data = str_replace(array('-', '_'), array('+', '/'), $string);
        $mod4 = strlen($data) % 4;
        if ($mod4) {
            $data .= substr('====', $mod4);
        }
        return base64_decode($data);
    }

}

if (!function_exists('_')) {
    function _($string)
    {
        return $string;
    }

    function ngettext($msgid1, $msgid2, $n)
    {
        return $n > 1 ? $msgid2 : $msgid1;
    }

    function bindtextdomain()
    {
    }

    function textdomain()
    {
    }

}
