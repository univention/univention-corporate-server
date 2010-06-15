<?php
/**
 * Net_IMSP_Utils::
 *
 * $Horde: framework/Net_IMSP/IMSP/Utils.php,v 1.2 2004/03/18 16:49:41 chuck Exp $
 *
 * Copyright 2003-2004 Michael Rubinsky <mike@theupstairsroom.com>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Michael Rubinsky <mike@theupstairsroom.com>
 * @package Net_IMSP
 */
class Net_IMSP_Utils {

    /**
     * Utility function to retrieve the names of all the addressbooks
     * that the user has access to, along with the acl for those
     * books.  For information about the $serverInfo array see
     * turba/config/sources.php as this is the cfgSources[] entry for
     * the addressbooks.
     *
     * @param array $serverInfo  Information about the server
     *                           and the current user.
     *
     * @return array  Information about all the addressbooks.
     */
    function getAllBooks($serverInfo)
    {
        require_once 'Net/IMSP.php';

        $results = array();
        $imsp = &Net_IMSP::singleton('Book', $serverInfo['params']);
        $result = $imsp->init();

        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        $books = $imsp->getAddressBookList();

        for ($i = 0; $i < count($books); $i++) {
            if ($books[$i] != $serverInfo['params']['username']) {
                $newBook = $serverInfo;
                $newBook['title'] = 'IMSP_' . $books[$i];
                $newBook['params']['name'] = $books[$i];
                if (strstr($imsp->myRights($books[$i]), 'w')) {
                    $newBook['readonly'] = false;
                } else {
                    $newBook['readonly'] = true;
                }

                $results[] = $newBook;
            }
        }

        return $results;
    }

}
