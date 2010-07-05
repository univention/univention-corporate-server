<?php
/**
 * SessionHandler implementation for LDAP directories.
 *
 * Required parameters:<pre>
 *   'hostspec' - (string) The hostname of the ldap server.
 *   'port'     - (integer) The port number of the ldap server.
 *   'dn'       - (string) The bind DN.
 *   'password' - (string) The bind password.
 * </pre>
 *
 * $Horde: framework/SessionHandler/SessionHandler/ldap.php,v 1.2.2.3 2007-12-20 13:49:39 jan Exp $
 *
 * This code is adapted from the comments at
 * http://www.php.net/session-set-save-handler.
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @since   Horde 3.1
 * @package Horde_SessionHandler
 */
class SessionHandler_ldap extends SessionHandler {

    /**
     * Handle for the current database connection.
     *
     * @var resource
     */
    var $_conn;

    /**
     * Open the SessionHandler backend.
     *
     * @access private
     *
     * @param string $save_path     The path to the session object.
     * @param string $session_name  The name of the session.
     *
     * @return boolean  True on success, false otherwise.
     */
    function _open($save_path = null, $session_name = null)
    {
        $this->_conn = @ldap_connect($this->_params['hostspec'], $this->_params['port']);

        // Set protocol version if necessary.
        if (isset($this->_params['version'])) {
            if (!@ldap_set_option($this->_ds, LDAP_OPT_PROTOCOL_VERSION, $this->_params['version'])) {
                return PEAR::raiseError(sprintf('Set LDAP protocol version to %d failed: [%d] %s',
                                        $this->_params['version'],
                                        ldap_errno($conn),
                                        ldap_error($conn)));
            }
        }

        return @ldap_bind($this->_conn, $this->_params['dn'], $this->_params['password']);
    }

    /**
     * Close the SessionHandler backend.
     *
     * @access private
     *
     * @return boolean  True on success, false otherwise.
     */
    function _close()
    {
        return @ldap_close($this->_conn);
    }

    /**
     * Read the data for a particular session identifier from the
     * SessionHandler backend.
     *
     * @access private
     *
     * @param string $id  The session identifier.
     *
     * @return string  The session data.
     */
    function _read($id)
    {
        $sr = @ldap_search($this->_conn, $this->_params['dn'], "(cn=$id)");
        $info = @ldap_get_entries($this->_conn, $sr);
        return ($info['count'] > 0) ? $info[0]['session'][0] : '';
    }

    /**
     * Write session data to the SessionHandler backend.
     *
     * @access private
     *
     * @param string $id            The session identifier.
     * @param string $session_data  The session data.
     *
     * @return boolean  True on success, false otherwise.
     */
    function _write($id, $session_data)
    {
        $update = array('objectClass' => array('phpsession', 'top'),
                        'session' => $session_data);
        $dn = "cn=$id," . $this->_params['dn'];
        @ldap_delete($this->_conn, $dn);
        return @ldap_add($this->_conn, $dn, $update);
    }

    /**
     * Destroy the data for a particular session identifier in the
     * SessionHandler backend.
     *
     * @param string $id  The session identifier.
     *
     * @return boolean  True on success, false otherwise.
     */
    function destroy($id)
    {
        $dn = "cn=$id," . $this->_params['dn'];
        return @ldap_delete($this->_conn, $dn);
    }

    /**
     * Garbage collect stale sessions from the SessionHandler backend.
     *
     * @param integer $maxlifetime  The maximum age of a session.
     *
     * @return boolean  True on success, false otherwise.
     */
    function gc($maxlifetime = 300)
    {
        $sr = @ldap_search($this->_conn, $this->_params['dn'],
                           '(objectClass=phpsession)', array('+', 'cn'));
        $info = @ldap_get_entries($this->_conn, $sr);
        if ($info['count'] > 0) {
            for ($i = 0; $i < $info['count']; $i++) {
                $id = $info[$i]['cn'][0];
                $dn = "cn=$id," . $this->_params['dn'];
                $ldapstamp = $info[$i]['modifytimestamp'][0];
                $year = substr($ldapstamp, 0, 4);
                $month = substr($ldapstamp, 4, 2);
                $day = substr($ldapstamp, 6, 2);
                $hour = substr($ldapstamp, 8, 2);
                $minute = substr($ldapstamp, 10, 2);
                $modified = gmmktime($hour, $minute, 0, $month, $day, $year);
                if (time() - $modified >= $maxlifetime) {
                    @ldap_delete($this->_conn, $dn);
                }
            }
        }

        return true;
    }

}
