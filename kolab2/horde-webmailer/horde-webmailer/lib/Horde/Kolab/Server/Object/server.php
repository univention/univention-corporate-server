<?php
/**
 * The server configuration.
 *
 * $Horde: framework/Kolab_Server/lib/Horde/Kolab/Server/Object/server.php,v 1.2.2.5 2009-04-25 08:56:33 wrobel Exp $
 *
 * PHP version 4
 *
 * @category Kolab
 * @package  Kolab_Server
 * @author   Gunnar Wrobel <wrobel@pardus.de>
 * @license  http://www.fsf.org/copyleft/lgpl.html LGPL
 * @link     http://pear.horde.org/index.php?package=Kolab_Server
 */

/**
 * This class provides methods to deal with Kolab server configuration.
 *
 * $Horde: framework/Kolab_Server/lib/Horde/Kolab/Server/Object/server.php,v 1.2.2.5 2009-04-25 08:56:33 wrobel Exp $
 *
 * Copyright 2008-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @category Kolab
 * @package  Kolab_Server
 * @author   Gunnar Wrobel <wrobel@pardus.de>
 * @license  http://www.fsf.org/copyleft/lgpl.html LGPL
 * @link     http://pear.horde.org/index.php?package=Kolab_Server
 */
class Horde_Kolab_Server_Object_server extends Horde_Kolab_Server_Object {

    /**
     * Return the filter string to retrieve this object type.
     *
     * @static
     *
     * @return string The filter to retrieve this object type from the server
     *                database.
     */
    public static function getFilter()
    {
        $criteria = array('AND' => array(
                              array('field' => 'k',
                                    'op'    => '=',
                                    'test'  => 'kolab'),
                              array('field' => KOLAB_ATTR_OC,
                                    'op'    => '=',
                                    'test'  => KOLAB_OC_KOLAB),
                          ),
        );
        return $criteria;
    }

    /**
     * The attributes supported by this class
     *
     * @var array
     */
    var $_supported_attributes = array(
        KOLAB_ATTR_FBPAST,
    );

}