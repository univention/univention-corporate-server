<?php
/**
 * A Kolab maintainer.
 *
 * $Horde: framework/Kolab_Server/lib/Horde/Kolab/Server/Object/maintainer.php,v 1.2.2.4 2009-01-06 15:23:15 jan Exp $
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
 * This class provides methods to deal with maintainer
 * entries for Kolab.
 *
 * $Horde: framework/Kolab_Server/lib/Horde/Kolab/Server/Object/maintainer.php,v 1.2.2.4 2009-01-06 15:23:15 jan Exp $
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
class Horde_Kolab_Server_Object_maintainer extends Horde_Kolab_Server_Object_adminrole {

    /**
     * The group the UID must be member of so that this object really
     * matches this class type. This may not include the root UID.
     *
     * @var string
     */
    var $required_group = 'cn=maintainer,cn=internal';

}
