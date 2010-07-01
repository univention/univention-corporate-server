<?php
/**
 * A Kolab object of type administrator.
 *
 * $Horde: framework/Kolab_Server/lib/Horde/Kolab/Server/Object/adminrole.php,v 1.1.2.4 2009-04-25 08:56:33 wrobel Exp $
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
 * This class provides methods to deal with administrator object types.
 *
 * $Horde: framework/Kolab_Server/lib/Horde/Kolab/Server/Object/adminrole.php,v 1.1.2.4 2009-04-25 08:56:33 wrobel Exp $
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
class Horde_Kolab_Server_Object_adminrole extends Horde_Kolab_Server_Object {

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
        KOLAB_ATTR_SID,
        KOLAB_ATTR_USERPASSWORD,
        KOLAB_ATTR_DELETED,
    );

    /**
     * The attributes required when creating an object of this class.
     *
     * @var array
     */
    var $_required_attributes = array(
        KOLAB_ATTR_SN,
        KOLAB_ATTR_GIVENNAME,
        KOLAB_ATTR_USERPASSWORD,
        KOLAB_ATTR_SID,
    );

    /**
     * Attributes derived from the LDAP values.
     *
     * @var array
     */
    var $_derived_attributes = array(
        KOLAB_ATTR_ID,
        KOLAB_ATTR_LNFN,
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
                              array('field' => KOLAB_ATTR_CN,
                                    'op'    => '=',
                                    'test'  => '*'),
                              array('field' => KOLAB_ATTR_SN,
                                    'op'    => '=',
                                    'test'  => '*'),
                              array('field' => KOLAB_ATTR_OC,
                                    'op'    => '=',
                                    'test'  => KOLAB_OC_INETORGPERSON),
                              array('NOT' => array(
                                        array('field' => KOLAB_ATTR_SID,
                                              'op'    => '=',
                                              'test'  => 'manager'),
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
                KOLAB_ATTR_SID,
                KOLAB_ATTR_LNFN,
            );
        }
        return parent::toHash($attrs);
    }

    /**
     * Saves object information.
     *
     * @param array $info The information about the object.
     *
     * @return boolean|PEAR_Error True on success.
     */
    function save($info)
    {
        if (!isset($info['cn'])) {
            if (!isset($info['sn']) || !isset($info['givenName'])) {
                return PEAR::raiseError('Either the last name or the given name is missing!');
            } else {
                $info['cn'] = $this->generateId($info);
            }
        }

        $admins_uid = sprintf('%s,%s', $this->required_group,
                              $this->_db->getBaseUid());

        $admin_group = $this->_db->fetch($admins_uid, KOLAB_OBJECT_GROUP);
        if (is_a($admin_group, 'PEAR_Error') || !$admin_group->exists()) {

            $members = array($this->_uid);

            //FIXME: This is not okay and also contains too much LDAP knowledge
            $parts = split(',', $this->required_group);
            list($groupname) = sscanf($parts[0], 'cn=%s');

            $result = $this->_db->add(array(KOLAB_ATTR_CN => $groupname,
                                            'type' => KOLAB_OBJECT_GROUP,
                                            KOLAB_ATTR_MEMBER => $members,
                                            KOLAB_ATTR_VISIBILITY => false));
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        } else {
            $result = $admin_group->isMember($this->_uid);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
            if ($result === false) {
                $members   = $admin_group->getMembers();
                $members[] = $this->_uid;
                $admin_group->save(array(KOLAB_ATTR_MEMBER => $members));
            }
        }
        return parent::save($info);
    }

}
