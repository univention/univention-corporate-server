<?php
/**
 * The Horde_Crypt:: class provides an API for various cryptographic
 * systems used by Horde applications.
 *
 * $Horde: framework/Crypt/Crypt.php,v 1.26 2004/04/29 20:05:01 slusarz Exp $
 *
 * Copyright 2002-2004 Michael Slusarz <slusarz@bigworm.colorado.edu>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Michael Slusarz <slusarz@bigworm.colorado.edu>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 * @package Horde_Crypt
 */
class Horde_Crypt {

    /**
     * The temporary directory to use.
     *
     * @var string $_tempdir
     */
    var $_tempdir;

    /**
     * Attempts to return a concrete Horde_Crypt instance based on $driver.
     *
     * @access public
     *
     * @param mixed $driver           The type of concrete Crypt subclass to
     *                                return. This is based on the storage
     *                                driver ($driver). The code is dynamically
     *                                included. If $driver is an array, then we
     *                                will look in $driver[0]/lib/Crypt/ for
     *                                the subclass implementation named
     *                                $driver[1].php.
     * @param optional array $params  A hash containing any additional
     *                                configuration or parameters a subclass
     *                                might need.
     *
     * @return object Horde_Crypt  The newly created concrete Horde_Crypt
     *                             instance, or false on an error.
     */
    function &factory($driver, $params = array())
    {
        if (is_array($driver)) {
            list($app, $driver) = $driver;
        }

        /* Return a base Crypt object if no driver is specified. */
        $driver = basename($driver);
        if (empty($driver) || (strcmp($driver, 'none') == 0)) {
            return $ret = &new Horde_Crypt();
        }

        if (!empty($app)) {
            require_once $GLOBALS['registry']->getParam('fileroot', $app) . '/lib/Crypt/' . $driver . '.php';
        } elseif (@file_exists(dirname(__FILE__) . '/Crypt/' . $driver . '.php')) {
            require_once dirname(__FILE__) . '/Crypt/' . $driver . '.php';
        } else {
            @include_once 'Horde/Crypt/' . $driver . '.php';
        }
        $class = 'Horde_Crypt_' . $driver;
        if (class_exists($class)) {
            return $ret = &new $class($params);
        } else {
            return PEAR::raiseError('Class definition of ' . $class . ' not found.');
        }
    }

    /**
     * Attempts to return a reference to a concrete Crypt instance
     * based on $driver. It will only create a new instance if no
     * Crypt instance with the same parameters currently exists.
     *
     * This should be used if multiple crypto backends (and, thus,
     * multiple Crypt instances) are required.
     *
     * This method must be invoked as: $var = &Crypt::singleton()
     *
     * @access public
     *
     * @param mixed $driver           The type of concrete Crypt subclass to
     *                                return. This is based on the storage
     *                                driver ($driver). The code is dynamically
     *                                included. If $driver is an array, then
     *                                we will look in $driver[0]/lib/Crypt/ for
     *                                the subclass implementation named
     *                                $driver[1].php.
     * @param optional array $params  A hash containing any additional
     *                                configuration or connection parameters a
     *                                subclass might need.
     *
     * @return object Crypt  The concrete Crypt reference, or false on an error.
     */
    function &singleton($driver, $params = array())
    {
        static $instances;

        if (!isset($instances)) {
            $instances = array();
        }

        $signature = serialize(array($driver, $params));
        if (!isset($instances[$signature])) {
            $instances[$signature] = &Crypt::factory($driver, $params);
        }

        return $instances[$signature];
    }

    /**
     * Outputs error message if we are not using a secure connection.
     *
     * @access public
     *
     * @return object PEAR_Error  Returns a PEAR_Error object if there is no
     *                            secure connection.
     */
    function requireSecureConnection()
    {
        global $browser;

        if (!$browser->usingSSLConnection()) {
            return PEAR::raiseError(_("The encryption features require a secure web connection."));
        }
    }

    /**
     * Encrypt the requested data.
     * This method should be provided by all classes that extend Horde_Crypt.
     *
     * @access public
     *
     * @param string $data            The data to encrypt.
     * @param optional array $params  An array of arguments needed to encrypt
     *                                the data.
     *
     * @return array  The encrypted data.
     */
    function encrypt($data, $params = array())
    {
        return $data;
    }

    /**
     * Decrypt the requested data.
     * This method should be provided by all classes that extend Horde_Crypt.
     *
     * @access public
     *
     * @param string $data            The data to decrypt.
     * @param optional array $params  An array of arguments needed to decrypt
     *                                the data.
     *
     * @return array  The decrypted data.
     */
    function decrypt($data, $params = array())
    {
        return $data;
    }

    /**
     * Create a temporary file that will be deleted at the end of this
     * process.
     *
     * @access private
     *
     * @param optional string  $descrip  Description string to use in filename.
     * @param optional boolean $delete   Delete the file automatically?
     *
     * @return string  Filename of a temporary file.
     */
    function _createTempFile($descrip = 'horde-crypt', $delete = true)
    {
        return Util::getTempFile($descrip, $delete, $this->_tempdir, true);
    }

}
