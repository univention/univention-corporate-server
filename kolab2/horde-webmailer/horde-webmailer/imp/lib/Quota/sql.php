<?php
/**
 * Implementation of the Quota API for servers keeping quota information in a
 * custom SQL database.
 *
 * Driver must be configured in imp/config/servers.php. Parameters supported:
 * <pre>
 * phptype     -- Database type to connect to
 * hostspec    -- Database host
 * username    -- User name for DB connection
 * password    -- Password for DB connection
 * database    -- Database name
 * query_quota -- SQL query which returns single row/column with user quota
 *                (in bytes). %u is replaced with current user name, %U with
 *                the user name without the domain part, %d with the domain.
 * query_used  -- SQL query which returns single row/column with user used
 *                space (in bytes). Placeholders are the same like in
 *                query_quota.
 * </pre>
 *
 * Example how to reuse Horde's global SQL configuration:
 * <code>
 * 'quota' => array(
 *     'driver' => 'sql',
 *     'params' => array_merge($GLOBALS['conf']['sql'],
 *                             array('query_quota' => 'SELECT quota FROM quotas WHERE user = ?',
 *                                   'query_used' => 'SELECT used FROM quotas WHERE user = ?'))
 * ),
 * </code>
 *
 * $Horde: imp/lib/Quota/sql.php,v 1.6.2.5 2009-02-17 17:13:51 chuck Exp $
 *
 * Copyright 2006-2007 Tomas Simonaitis <haden@homelan.lt>
 * Copyright 2006-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author  Tomas Simonaitis <haden@homelan.lt>
 * @author  Jan Schneider <jan@horde.org>
 * @since   IMP 4.2
 * @package IMP_Quota
 */
class IMP_Quota_sql extends IMP_Quota {

    /**
     * SQL connection object.
     *
     * @var DB
     */
    var $_db;

    /**
     * State of SQL connection.
     *
     * @var boolean
     */
    var $_connected = false;

    /**
     * Connects to the database
     *
     * @return boolean  True on success, PEAR_Error on failure.
     */
    function _connect()
    {
        if (!$this->_connected) {
            require_once 'DB.php';
            $this->_db = &DB::connect($this->_params,
                                      array('persistent' => !empty($this->_params['persistent']),
                                            'ssl' => !empty($this->_params['ssl'])));
            if (is_a($this->_db, 'PEAR_Error')) {
                return PEAR::raiseError(_("Unable to connect to SQL server."));
            }

            $this->_connected = true;
        }

        return true;
    }

    /**
     * Returns quota information.
     *
     * @return mixed  An associative array:
     *		  'limit' => Maximum quota allowed (in bytes),
     *		  'usage' => Currently used space (in bytes).
     *		  PEAR_Error on failure.
     */
    function getQuota()
    {
        $conn = $this->_connect();
        if (is_a($conn, 'PEAR_Error')) {
            return $conn;
        }

        $user = $_SESSION['imp']['user'];
        $quota = array('limit' => 0, 'usage' => 0);

        if (!empty($this->_params['query_quota'])) {
            @list($bare_user, $domain) = explode('@', $user, 2);
            $query = str_replace(array('?', '%u', '%U', '%d'),
                                 array($this->_db->quote($user),
                                       $this->_db->quote($user),
                                       $this->_db->quote($bare_user),
                                       $this->_db->quote($domain)),
                                 $this->_params['query_quota']);
            $result = $this->_db->query($query);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }

            $row = $result->fetchRow(DB_FETCHMODE_ASSOC);
            if (is_array($row)) {
                $quota['limit'] = current($row);
            }
        } else {
            Horde::logMessage('IMP_Quota_sql: query_quota SQL query not set', __FILE__, __LINE__, PEAR_LOG_DEBUG);
        }

        if (!empty($this->_params['query_used'])) {
            @list($bare_user, $domain) = explode('@', $user, 2);
            $query = str_replace(array('?', '%u', '%U', '%d'),
                                 array($this->_db->quote($user),
                                       $this->_db->quote($user),
                                       $this->_db->quote($bare_user),
                                       $this->_db->quote($domain)),
                                 $this->_params['query_used']);
            $result = $this->_db->query($query);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }

            $row = $result->fetchRow(DB_FETCHMODE_ASSOC);
            if (is_array($row)) {
                $quota['usage'] = current($row);
            }
        } else {
            Horde::logMessage('IMP_Quota_sql: query_used SQL query not set', __FILE__, __LINE__, PEAR_LOG_DEBUG);
        }

        return $quota;
    }

}
