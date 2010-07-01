<?php
/**
 * An entry in the global addressbook.
 *
 * $Horde: framework/Kolab_Server/lib/Horde/Kolab/Server/Object/address.php,v 1.2.2.6 2009-04-25 08:56:33 wrobel Exp $
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
 * This class provides methods to deal with global address book
 * entries for Kolab.
 *
 * $Horde: framework/Kolab_Server/lib/Horde/Kolab/Server/Object/address.php,v 1.2.2.6 2009-04-25 08:56:33 wrobel Exp $
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
class Horde_Kolab_Server_Object_address extends Horde_Kolab_Server_Object {

    /**
     * The attributes supported by this class
     *
     * @var array
     */
    var $_supported_attributes = array(
        KOLAB_ATTR_SN,
        KOLAB_ATTR_CN,
        KOLAB_ATTR_GIVENNAME,
        KOLAB_ATTR_FN,
        KOLAB_ATTR_LNFN,
        KOLAB_ATTR_MAIL,
        KOLAB_ATTR_DELETED,
    );

    /**
     * Attributes derived from the LDAP values.
     *
     * @var array
     */
    var $_derived_attributes = array(
        KOLAB_ATTR_LNFN,
        KOLAB_ATTR_FNLN,
    );

    /**
     * The attributes required when creating an object of this class.
     *
     * @var array
     */
    var $_required_attributes = array(
        KOLAB_ATTR_SN,
        KOLAB_ATTR_GIVENNAME,
    );

    /**
     * The ldap classes for this type of object.
     *
     * @var array
     */
    var $_object_classes = array(
        KOLAB_OC_TOP,
        KOLAB_OC_INETORGPERSON,
        KOLAB_OC_KOLABINETORGPERSON,
    );

    /**
     * The LDAP filter to retrieve this object type
     *
     * @return string
     */
    function getFilter()
    {
        $criteria = array('AND' => array(
                              array('field' => KOLAB_ATTR_SN,
                                    'op'    => '=',
                                    'test'  => '*'),
                              array('field' => KOLAB_ATTR_OC,
                                    'op'    => '=',
                                    'test'  => KOLAB_OC_INETORGPERSON),
                              array('NOT' => array(
                                        array('field' => KOLAB_ATTR_SID,
                                              'op'    => '=',
                                              'test'  => '*'),
                                    ),
                              ),
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
                KOLAB_ATTR_LNFN,
            );
        }
        return parent::toHash($attrs);
    }

}
