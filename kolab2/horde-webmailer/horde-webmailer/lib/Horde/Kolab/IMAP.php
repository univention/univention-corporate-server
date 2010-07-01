<?php
/**
 * @package Kolab_Storage
 *
 * $Horde: framework/Kolab_Server/lib/Horde/Kolab/IMAP.php,v 1.1.2.2 2009-01-06 15:23:15 jan Exp $
 */

/**
 * The Horde_Kolab_IMAP class provides a wrapper around two different Kolab IMAP
 * connection types.
 *
 * $Horde: framework/Kolab_Server/lib/Horde/Kolab/IMAP.php,v 1.1.2.2 2009-01-06 15:23:15 jan Exp $
 *
 * Copyright 2007-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Gunnar Wrobel <wrobel@pardus.de>
 * @author  Thomas Jarosch <thomas.jarosch@intra2net.com>
 * @package Kolab_Storage
 */
class Horde_Kolab_IMAP {

    /**
     * IMAP server to connect to.
     *
     * @var string
     */
    var $_server;

    /**
     * IMAP server port to connect to.
     *
     * @var int
     */
    var $_port;

    /**
     * IMAP connection.
     *
     * @var mixed
     */
    var $_imap;

    /**
     * Connection reuse detection signature.
     *
     * @var string
     */
    var $_reuse_detection;

    /**
     * Constructor.
     *
     * @param string     $server   Server to connect to
     * @param int        $port     Port to connect to
     */
    function Horde_Kolab_IMAP($server, $port)
    {
        $this->_server = $server;
        $this->_port   = $port;
    }

    /**
     * Attempts to return a reference to a concrete Horde_Kolab_IMAP instance.
     * It will only create a new instance if no Horde_Kolab_IMAP instance
     * exists.
     *
     * @static
     *
     * @param string     $server                Server name
     * @param int        $port                  Port
     * @param boolean    $annotation_required   Do we actually need
     *                                          the annotation calls?
     *
     * @return Horde_Kolab_IMAP|PEAR_Error The concrete reference.
     */
    function &singleton($server, $port, $annotation_required = true)
    {
        static $instances = array();

        /**
         * There are Kolab specific PHP functions available that make the IMAP
         * access more efficient. If these are detected, or if they are not
         * required for the current operation, the PHP IMAP implementation
         * should be used.
         *
         * The c-client Kolab driver provides quicker IMAP routines so is
         * preferable whenever possible.
         */
        if ($annotation_required) {
            if (function_exists('imap_status_current')
                && function_exists('imap_getannotation')) {
                $driver = 'cclient';
            } else {
                $driver = 'pear';
            }
        } else {
            $driver = 'cclient';
        }

        if (isset($GLOBALS['KOLAB_TESTING'])) {
            $driver = 'test';
        }

        $signature = "$server|$port|$driver";
        if (!isset($instances[$signature])) {
            $instances[$signature] = &Horde_Kolab_IMAP::factory($server, $port, $driver);
        }

        return $instances[$signature];
    }

    /**
     * Attempts to return a concrete Horde_Kolab_IMAP instance based on the
     * available PHP functionality.
     *
     * @param string     $server                Server name.
     * @param int        $port                  Server port.
     * @param string     $driver                Which driver should we use?
     *
     * @return Horde_Kolab_IMAP|PEAR_Error The newly created concrete
     *                                     Horde_Kolab_IMAP instance.
     */
    function &factory($server, $port, $driver = 'cclient')
    {
        @include_once dirname(__FILE__) . '/IMAP/' . $driver . '.php';

        $class = 'Horde_Kolab_IMAP_' . $driver;
        if (class_exists($class)) {
            $driver = &new $class($server, $port);
        } else {
            return PEAR::raiseError(sprintf(_("Failed to load Kolab IMAP driver %s"), $driver));
        }

        return $driver;
    }
}
