<?php
/**
 * Implementation of the Quota API for a generic hook function.  This
 * requires hook_get_quota to be set in config/hooks.php .  The
 * function takes an array as argument and returns an array where the
 * first item is the disk space used in bytes and the second the
 * maximum diskspace in bytes.  See there for an example.
 *
 * You must configure this driver in horde/imp/config/servers.php.  The
 * driver supports the following parameters:
 *   'params'       => Array of parameters to pass to the quota function.
 *
 * $Horde: imp/lib/Quota/hook.php,v 1.1.2.5 2009-11-06 22:22:17 slusarz Exp $
 *
 * Copyright 2002-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author  Michael Redinger <Michael.Redinger@uibk.ac.at>
 * @package IMP_Quota
 */
class IMP_Quota_hook extends IMP_Quota {

    /**
     * Get quota information (used/allocated), in bytes.
     *
     * @return mixed  An associative array.
     *                'limit' = Maximum quota allowed
     *                'usage' = Currently used portion of quota (in bytes)
     *                Returns PEAR_Error on failure.
     */
    function getQuota()
    {
        $quota = Horde::callHook('_imp_hook_quota', array($this->_params), 'imp');
        if (is_a($quota, 'PEAR_Error')) {
            return $quota;
        }

        if (count($quota) != 2) {
            Horde::logMessage('Incorrect number of return values from quota hook.', __FILE__, __LINE__, PEAR_LOG_ERR);
            return PEAR::raiseError(_("Unable to retrieve quota"), 'horde.error');
        }

        return array('usage' => $quota[0], 'limit' => $quota[1]);
    }

}
