<?php
/**
 * A shared IMAP folder.
 *
 * $Horde: framework/Kolab_Server/lib/Horde/Kolab/Server/Object/sharedfolder.php,v 1.2.2.5 2009-04-25 08:56:33 wrobel Exp $
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
 * This class provides methods to deal with shared folders
 * entries for Kolab.
 *
 * $Horde: framework/Kolab_Server/lib/Horde/Kolab/Server/Object/sharedfolder.php,v 1.2.2.5 2009-04-25 08:56:33 wrobel Exp $
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
class Horde_Kolab_Server_Object_sharedfolder extends Horde_Kolab_Server_Object {

    /**
     * The attributes supported by this class
     *
     * @var array
     */
    var $_supported_attributes = array(
        KOLAB_ATTR_CN,
        KOLAB_ATTR_DELETED,
        KOLAB_ATTR_FOLDERTYPE,
        KOLAB_ATTR_HOMESERVER,
        KOLAB_ATTR_IMAPHOST,
        KOLAB_ATTR_QUOTA,
        KOLAB_ATTR_ACL,
    );

    /**
     * The attributes required when creating an object of this class.
     *
     * @var array
     */
    var $_required_attributes = array(
        KOLAB_ATTR_CN,
        KOLAB_ATTR_HOMESERVER,
    );

    /**
     * The ldap classes for this type of object.
     *
     * @var array
     */
    var $_object_classes = array(
        KOLAB_OC_TOP,
        KOLAB_OC_KOLABSHAREDFOLDER,
    );

    /**
     * Generates an ID for the given information.
     *
     * @param array $info The data of the object.
     *
     * @static
     *
     * @return string|PEAR_Error The ID.
     */
    function generateId($info)
    {
        return trim($info['cn'], " \t\n\r\0\x0B,");
    }

    /**
     * Return the filter string to retrieve this object type.
     *
     * @return string The filter to retrieve this object type from the server
     *                database.
     */
    public static function getFilter()
    {
        $criteria = array('AND' => array(array('field' => KOLAB_ATTR_OC,
                                               'op'    => '=',
                                               'test'  => KOLAB_OC_KOLABSHAREDFOLDER),
                          ),
        );
        return $criteria;
    }

    /**
     * Convert the object attributes to a hash.
     *
     * @param string $attrs The attributes to return.
     *
     * @return array|PEAR_Error The hash representing this object.
     */
    function toHash($attrs = null)
    {
        if (!isset($attrs)) {
            $attrs = array(
                KOLAB_ATTR_CN,
                KOLAB_ATTR_HOMESERVER,
                KOLAB_ATTR_FOLDERTYPE,
            );
        }
        return parent::toHash($attrs);
    }
}
