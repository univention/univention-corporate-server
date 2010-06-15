<?php
/**
 * SessionHandler:: implementation for DBM files.
 * NOTE: The PHP DBM functions are deprecated.
 *
 * No additional configuration parameters needed.
 *
 * $Horde: framework/SessionHandler/SessionHandler/dbm.php,v 1.9 2004/01/01 15:14:27 jan Exp $
 *
 * Copyright 2002-2004 Chuck Hagenbuch <chuck@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 * @package Horde_SessionHandler
 */
class SessionHandler_dbm extends SessionHandler {

    /**
     * Our pointer to the DBM file, if open.
     *
     * @var resource $_dbm
     */
    var $_dbm;

    /**
     * Constructs a new DBM SessionHandler object.
     *
     * @access public
     *
     * @param optional array $params  [Unused].
     */
    function SessionHandler_dbm($params = array())
    {
    }

    /**
     * TODO
     */
    function open($save_path, $session_name)
    {
        $this->_dbm = @dbmopen("$save_path/$session_name", 'c');
        return $this->_dbm;
    }

    /**
     * TODO
     */
    function close()
    {
        return @dbmclose($this->_dbm);
    }

    /**
     * TODO
     */
    function read($id)
    {
        if ($data = dbmfetch($this->_dbm, $id)) {
            return base64_decode(substr($data, strpos($data, '|') + 1));
        } else {
            return '';
        }
    }

    /**
     * TODO
     */
    function write($id, $session_data)
    {
        return @dbmreplace($this->_dbm, $id, time() . '|' . base64_encode($session_data));
    }

    /**
     * TODO
     */
    function destroy($id)
    {
        if (!(@dbmdelete($this->_dbm, $id))) {
            Horde::logMessage('Failed to delete session (id = ' . $id . ')', __FILE__, __LINE__, PEAR_LOG_ERR);
            return false;
        }

        return true;
    }

    /**
     * TODO
     */
    function gc($maxlifetime = 300) 
    {
        $expired = time() - $maxlifetime;
        $id = dbmfirstkey($this->_dbm);

        while ($id) {
            if ($data = dbmfetch($this->_dbm, $id)) {
                $age = substr($tmp, 0, strpos($data, '|'));
                if ($expired > $age) {
                    $this->destroy($id);
                }
            }

            $id = dbmnextkey($this->_dbm, $id);
        }

        return true;
    }

}
