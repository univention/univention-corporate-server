<?php
/**
 * Representation of a Kolab distribution list.
 *
 * $Horde: framework/Kolab_Server/lib/Horde/Kolab/Server/Object/distlist.php,v 1.1.2.3 2009-04-25 08:56:33 wrobel Exp $
 *
 * PHP version 4
 *
 * @category Kolab
 * @package  Kolab_Server
 * @author   Gunnar Wrobel <wrobel@pardus.de>
 * @license  http://www.fsf.org/copyleft/lgpl.html LGPL
 * @link     http://pear.horde.org/index.php?package=Kolab_Server
 */

require_once 'Horde/Kolab/Server/Object/group.php';

/**
 * This class provides methods to deal with distribution lists for Kolab.
 *
 * $Horde: framework/Kolab_Server/lib/Horde/Kolab/Server/Object/distlist.php,v 1.1.2.3 2009-04-25 08:56:33 wrobel Exp $
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
class Horde_Kolab_Server_Object_distlist extends Horde_Kolab_Server_Object_group {

    /**
     * The attributes required when creating an object of this class.
     *
     * @var array
     */
    var $_required_attributes = array(
        KOLAB_ATTR_MAIL,
    );

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
                              array('field' => KOLAB_ATTR_MAIL,
                                    'op'    => '=',
                                    'test'  => '*'),
                              array('field' => KOLAB_ATTR_OC,
                                    'op'    => '=',
                                    'test'  => KOLAB_OC_KOLABGROUPOFNAMES),
                          ),
        );
        return $criteria;
    }
};
