<?php

require_once 'Horde/Maintenance.php';
require_once $GLOBALS['registry']->get('fileroot', 'imp') . '/lib/base.php';

/**
 * $Horde: imp/lib/Maintenance/imp.php,v 1.19.10.9 2009-01-06 15:24:10 jan Exp $
 *
 * The Maintenance_IMP class defines the maintenance operations run upon
 * login to IMP.
 *
 * Copyright 2001-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author  Michael Slusarz <slusarz@horde.org>
 * @since   IMP 3.0
 * @package Horde_Maintenance
 */
class Maintenance_IMP extends Maintenance {

    /**
     * Hash holding maintenance preference names.
     *
     * @var array
     */
    var $maint_tasks = array(
        'tos_agreement'              => MAINTENANCE_FIRST_LOGIN,
        'fetchmail_login'            => MAINTENANCE_EVERY,
        'rename_sentmail_monthly'    => MAINTENANCE_MONTHLY,
        'delete_sentmail_monthly'    => MAINTENANCE_MONTHLY,
        'delete_attachments_monthly' => MAINTENANCE_MONTHLY,
        'purge_sentmail'             => MAINTENANCE_MONTHLY,
        'purge_spam'                 => MAINTENANCE_MONTHLY,
        'purge_trash'                => MAINTENANCE_MONTHLY
    );

}
