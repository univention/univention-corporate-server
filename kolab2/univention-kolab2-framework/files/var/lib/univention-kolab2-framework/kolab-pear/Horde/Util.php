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
 * $Horde: framework/Util/Util.php,v 1.371 2004/04/29 20:05:02 slusarz Exp $
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
        if (version_compare(zend_version(), '2', '>')) {
            return clone($obj);
        } else {
            $newObj = $obj;
            return $newObj;
        }
    }

    /**
     * Buffer the output from a function call, like readfile() or
     * highlight_string(), that prints the output directly, so that
     * instead it can be returned as a string and used.
     *
     * @access public
     *
     * @param string $function        The function to run.
     * @param optional mixed $arg1    First argument to $function().
     * @param optional mixed $arg2    Second argument to $function().
     * @param optional mixed $arg...  ...
     * @param optional mixed $argN    Nth argument to $function().
     *
     * @return string  The output of the function.
     */
    function bufferOutput()
    {
        if (func_num_args() == 0) {
            return false;
        }
        $eval = false;
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
            $eval = true;
        } elseif (!function_exists($function) &&
                  ($function != 'eval')) {
            return false;
        }

        ob_start();
        if ($eval) {
            eval($function . " '" . implode(',', $args) . "';");
        } elseif ($function == 'eval') {
            eval($args[0]);
        } else {
            call_user_func_array($function, $args);
        }
        $output = ob_get_contents();
        ob_end_clean();

        return $output;
    }

    /**
     * Check to see if a value has been set by the script and not by GET,
     * POST, or cookie input. The value being checked MUST be in the global
     * scope.
     *
     * @access public
     *
     * @param string $varname  The variable name to check.
     *
     * @return mixed  Null if the var is in user input, the variable value
     *                otherwise.
     */
    function nonInputVar($varname)
    {
        if (isset($_GET[$varname]) ||
            isset($_POST[$varname]) ||
            isset($_COOKIE[$varname])) {
            return null;
        } else {
            return isset($GLOBALS[$varname]) ? $GLOBALS[$varname] : null;
        }
    }

    /**
     * Add a name=value pair to the end of an URL, taking care of whether
     * there are existing parameters and whether to use ? or & as the glue.
     * All data will be urlencoded.
     *
     * @access public
     *
     * @param string $url             The URL to modify
     * @param mixed $parameter        Either the name=value pair to add
     *                                (DEPRECATED) -or-
     *                                the name value -or-
     *                                an array of name/value pairs.
     * @param optional string $value  If specified, the value part ($parameter
     *                                is then assumed to just be the parameter
     *                                name).
     *
     * @return string  The modified URL.
     *
     * @since Horde 2.1
     */
    function addParameter($url, $parameter, $value = null)
    {
        if (empty($parameter)) {
            return $url;
        }

        $arg = ini_get('arg_separator.output');

        if (!is_array($parameter)) {
            /* This is deprecated should be removed in the future. */
            if (is_null($value)) {
                @list($parameter, $value) = explode('=', $parameter, 2);
            }
            $add = array($parameter => $value);
        } else {
            $add = $parameter;
        }

        if (($pos = strpos($url, '?')) === false) {
            $url .= '?';
        } else {
            /* Check if the argument separator has been already
             * htmlentities-ized in the URL. */
            $query = substr($url, $pos + 1);
            if (preg_match('/=.*?' . htmlentities($arg) . '.*?=/', $query)) {
                $arg = htmlentities($arg);
                $query = strtr($query, array_flip(get_html_translation_table(HTML_ENTITIES)));
            }
            parse_str($query, $params);
            $url .= $arg;
        }

        $url_params = array();
        foreach ($add as $parameter => $value) {
            if (!isset($params[$parameter])) {
                $url_params[] = urlencode($parameter) . '=' . urlencode($value);
            }
        }

        return $url . join($arg, $url_params);
    }

    /**
     * Removes name=value pairs from a URL.
     *
     * @access public
     *
     * @param string $url    The URL to modify.
     * @param mixed $remove  Either a single parameter to remove or an array
     *                       of parameters to remove.
     *
     * @return string  The modified URL.
     *
     * @since Horde 2.2
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

        $arg = ini_get('arg_separator.output');
        $entities = false;
        list($url, $query) = explode('?', $url, 2);

        /* Check if the argument separator has been already
         * htmlentities-ized in the URL. */
        if (preg_match('/=.*?' . htmlentities($arg) . '.*?=/', $query)) {
            $entities = true;
            $query = strtr($query, array_flip(get_html_translation_table(HTML_ENTITIES)));
        }

        /* Get the list of parameters. */
        parse_str($query, $params);

        /* Remove the parameters. */
        foreach ($remove as $param) {
            unset($params[$param]);
        }

        if (!count($params)) {
            return $url;
        }

        /* Flatten arrays.
         * FIXME: should handle more than one array level somehow. */
        $keys = array();
        $vals = array();
        foreach ($params as $key => $val) {
            if (is_array($val)) {
                foreach ($val as $v) {
                    $keys[] = $key . '[]';
                    $vals[] = $v;
                }
            } else {
                $keys[] = $key;
                $vals[] = $val;
            }
        }

        $query = implode($arg, array_map(create_function('$a,$b', 'return str_replace(urlencode("[]"), "[]", urlencode($a)) . "=" . urlencode($b);'), $keys, $vals));
        if ($entities) {
            $query = htmlentities($query);
        }

        return $url . '?' . $query;
    }

    /**
     * Returns a url with the 'nocache' parameter added, if the browser is
     * buggy and caches old URLs.
     *
     * @access public
     *
     * @param string $url  The URL to modify.
     *
     * @return string  The requested URI.
     */
    function nocacheUrl($url)
    {
        static $rand_num;

        // FIXME: load from include_path.
        require_once 'Horde/Browser.php';
        $browser = &Browser::singleton();

        if (!isset($rand_num)) {
            $rand_num = base_convert(microtime(), 10, 36);
        }

        /* We may need to set a dummy parameter 'nocache' since some
         * browsers do not always honor the 'no-cache' header. */
        if ($browser->hasQuirk('cache_same_url')) {
            return Util::addParameter($url, 'nocache', $rand_num);
        } else {
            return $url;
        }
    }

    /**
     * Return a hidden form input containing the session name and id.
     *
     * @access public
     *
     * @param optional boolean $append_session  0 = only if needed, 1 = always.
     *
     * @return string  The hidden form input, if needed/requested.
     */
    function formInput($append_session = 0)
    {
        if (($append_session == 1) ||
            !array_key_exists(session_name(), $_COOKIE)) {
            return '<input type="hidden" name="' . session_name() . '" value="' . session_id() . "\" />\n";
        } else {
            return '';
        }
    }

    /**
     * Print a hidden form input containing the session name and id.
     *
     * @access public
     *
     * @param optional boolean $append_session  0 = only if needed, 1 = always.
     *
     * @return string  The hidden form input, if needed/requested.
     */
    function pformInput($append_session = 0)
    {
        echo Util::formInput($append_session);
    }

    /**
     * If magic_quotes_gpc is in use, run stripslashes() on $var.
     *
     * @access public
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
     * Get a form variable from GET or POST data, stripped of magic quotes if
     * necessary. If the variable is somehow set in both the GET data and the
     * POST data, the value from the POST data will be returned and the GET
     * value will be ignored.
     *
     * @access public
     *
     * @param string $var               The name of the form variable to look
     *                                  for.
     * @param optional string $default  The value to return if the variable is
     *                                  not there.
     *
     * @return string  The cleaned form variable, or $default.
     */
    function getFormData($var, $default = null)
    {
        return (($val = Util::getPost($var)) !== null)
            ? $val : Util::getGet($var, $default);
    }

    /**
     * Get a form variable from GET data, stripped of magic quotes if necessary.
     * This function will NOT return a POST variable.
     *
     * @access public
     *
     * @param string $var               The name of the form variable to look
     *                                  for.
     * @param optional string $default  The value to return if the variable is
     *                                  not there.
     *
     * @return string  The cleaned form variable, or $default.
     *
     * @since Horde 2.2
     */
    function getGet($var, $default = null)
    {
        return (isset($_GET[$var]))
            ? Util::dispelMagicQuotes($_GET[$var])
            : $default;
    }

    /**
     * Get a form variable from POST data, stripped of magic quotes if
     * necessary. This function will NOT return a GET variable.
     *
     * @access public
     *
     * @param string $var               The name of the form variable to look
     *                                  for.
     * @param optional string $default  The value to return if the variable is
     *                                  not there.
     *
     * @return string  The cleaned form variable, or $default.
     *
     * @since Horde 2.2
     */
    function getPost($var, $default = null)
    {
        return (isset($_POST[$var]))
            ? Util::dispelMagicQuotes($_POST[$var])
            : $default;
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
        $tmp_locations = array('/tmp', '/var/tmp', 'c:\WUTemp', 'c:\temp', 'c:\windows\temp', 'c:\winnt\temp');

        /* First, try PHP's upload_tmp_dir directive. */
        if (empty($tmp)) {
            $tmp = ini_get('upload_tmp_dir');
        }

        /* Otherwise, try to determine the TMPDIR environment
           variable. */
        if (empty($tmp)) {
            $tmp = getenv('TMPDIR');
        }

        /* If we still cannot determine a value, then cycle through a
         * list of preset possibilities. */
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
     * Create a temporary filename for the lifetime of the script, and
     * (optionally) register it to be deleted at request shutdown.
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

        /* If the file was created, then register it for deletion and return */
        if (empty($tmp_file)) {
            return false;
        } else {
            if ($delete) {
                Util::deleteAtShutdown($tmp_file, true, $secure);
            }
            return $tmp_file;
        }
    }

    /**
     * Create a temporary directory in the system's temporary directory.
     *
     * @access public
     *
     * @param optional boolean $delete   Delete the temporary directory at the
     *                                   end of the request?
     * @param optional string $temp_dir  Use this temporary directory as the
     *                                   directory where the temporary
     *                                   directory will be created.
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
            $temp_dir .= '/' . substr(base_convert(mt_rand() . microtime(), 10, 36), 0, 8);
        } while (file_exists($temp_dir));

        $old_umask = umask(0000);
        if (!mkdir($temp_dir, 0700)) {
            $temp_dir = false;
        } elseif ($delete) {
            Util::deleteAtShutdown($temp_dir);
        }
        umask($old_umask);

        return $temp_dir;
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
     * @access public
     *
     * @param optional string $filename   The filename to be deleted at the end
     *                                    of the request.
     * @param optional boolean $register  If true, then register the element for
     *                                    deletion, otherwise, unregister it.
     * @param optional boolean $secure    If deleting file, should we securely
     *                                    delete the file?
     */
    function deleteAtShutdown($filename = false, $register = true,
                              $secure = false)
    {
        static $dirs, $files, $securedel;

        /* Initialization of variables and shutdown functions. */
        if (is_null($dirs)){
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
     * Delete registered files at request shutdown.
     *
     * This function should never be called manually; it is registered as a
     * shutdown function by Util::deleteAtShutdown() and called automatically
     * at the end of the request. It will retrieve the list of folders and files
     * to delete from Util::deleteAtShutdown()'s static array, and then iterate
     * through, deleting folders recursively.
     *
     * Contains code from gpg_functions.php.
     * Copyright (c) 2002-2003 Braverock Ventures
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
            if ($val && @file_exists($file)) {
                /* Should we securely delete the file by overwriting the
                   data with a random string? */
                if (isset($secure[$file])) {
                    $random_str = '';
                    for ($i = 0; $i < filesize($file); $i++) {
                        $random_str .= chr(mt_rand(0, 255));
                    }
                    $fp = fopen($file, 'r+');
                    fwrite($fp, $random_str);
                    fclose($fp);
                }
                @unlink($file);
            }
        }

        foreach ($dirs as $dir => $val) {
            /* Delete directories */
            if ($val && @file_exists($dir)) {
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
     * Output javascript code to close the current window.
     *
     * @access public
     *
     * @param string $code  Any addtional javascript code to run before
     *                      closing the window.
     */
    function closeWindowJS($code = null)
    {
        echo '<script language="JavaScript" type="text/javascript">' . $code . 'window.close();</script>';
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
     * Try to load a PHP extension, behaving correctly for all
     * operating systems.
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

        /* See if we can call dl() at all, by the current ini
         * settings. */
        if ((ini_get('enable_dl') != 1) || (ini_get('safe_mode') == 1)) {
            return false;
        }

        if (substr(PHP_OS, 0, 3) == 'WIN') {
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
     * Checks if all necessary parameters for a driver's configuration
     * are set and returns a PEAR_Error if something is missing.
     *
     * @param array $params   The configuration array with all parameters.
     * @param array $fields   An array with mandatory parameter names for
     *                        this driver.
     * @param string $name    The clear text name of the driver. If
     *                        not specified, the application name will be used.
     * @param array $info     (optional) A hash containing detailed information
     *                        about the driver. Will be passed as the userInfo
     *                        to the PEAR_Error.
     */
    function assertDriverConfig($params, $fields, $name, $info = array())
    {
        $info = array_merge($info,
                            array('params' => $params,
                                  'fields' => $fields,
                                  'name' => $name));

        if (!is_array($params) || !count($params)) {
            return PEAR::throwError(sprintf(_("No configuration information specified for %s."), $name),
                                    HORDE_ERROR_DRIVER_CONFIG_MISSING,
                                    $info);
        }

        foreach ($fields as $field) {
            if (!isset($params[$field])) {
                return PEAR::throwError(sprintf(_("Required '%s' not specified in configuration."), $field, $name),
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

        return str_replace($dateSymbols, $strftimeSymbols, $format);
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

}

if (!function_exists('_')) {
    function _($string)
    {
        return $string;
    }

    function bindtextdomain()
    {
    }

    function textdomain()
    {
    }
}
