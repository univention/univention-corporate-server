<?php
/**
 * A Kolab domain maintainer.
 *
 * $Horde: framework/Kolab_Server/lib/Horde/Kolab/Server/Object/domainmaintainer.php,v 1.2.2.5 2009-01-06 15:23:15 jan Exp $
 *
 * PHP version 4
 *
 * @category Kolab
 * @package  Kolab_Server
 * @author   Gunnar Wrobel <wrobel@pardus.de>
 * @license  http://www.fsf.org/copyleft/lgpl.html LGPL
 * @link     http://pear.horde.org/index.php?package=Kolab_Server
 */

require_once 'Horde/Kolab/Server/Object/adminrole.php';

/**
 * This class provides methods associated to Kolab domain maintainers.
 *
 * $Horde: framework/Kolab_Server/lib/Horde/Kolab/Server/Object/domainmaintainer.php,v 1.2.2.5 2009-01-06 15:23:15 jan Exp $
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
class Horde_Kolab_Server_Object_domainmaintainer extends Horde_Kolab_Server_Object_adminrole {

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
        KOLAB_ATTR_DOMAIN,
    );

    /**
     * Attributes derived from the LDAP values.
     *
     * @var array
     */
    var $_derived_attributes = array(
        KOLAB_ATTR_ID,
        KOLAB_ATTR_LNFN,
        KOLAB_ATTR_DOMAIN,
    );

    /**
     * The group the UID must be member of so that this object really
     * matches this class type. This may not include the root UID.
     *
     * @var string
     */
    var $required_group = 'cn=domain-maintainer,cn=internal';

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
                KOLAB_ATTR_DOMAIN,
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
        foreach ($info[KOLAB_ATTR_DOMAIN] as $domain) {
            $domain_uid = sprintf('cn=%s,cn=domain,cn=internal,%s',
                                  $domain, $this->_db->getBaseUid());

            //FIXME: This should be made easier by the group object

            $domain_group = $this->_db->fetch($domain_uid, KOLAB_OBJECT_GROUP);
            if (is_a($domain_group, 'PEAR_Error')) {
                return $domain_group;
            }
            if (!$domain_group->exists()) {
                $members = array($this->_uid);
                $domain_group->save(array(KOLAB_ATTR_MEMBER => $members));
            } else {
                $result = $domain_group->isMember($this->_uid);
                if (is_a($result, 'PEAR_Error')) {
                    return $result;
                }
                if ($result === false) {
                    $members   = $domain_group->getMembers();
                    $members[] = $this->_uid;
                    $domain_group->save(array(KOLAB_ATTR_MEMBER => $members));
                }
            }
        }
        return parent::save($info);
    }

}
