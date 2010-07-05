<?php

require_once 'Horde/IMAP/ACL/rfc2086.php';

/**
 * Contains functions related to managing Access Control Lists on an IMAP
 * server using RFC 4314.
 *
 * Required parameters:<pre>
 *   'username'  The username for the server connection
 *   'password'  The password for the server connection
 *   'hostspec'  The hostname or IP address of the server.
 *               DEFAULT: 'localhost'
 *   'port'      The server port to which we will connect.
 *               IMAP is generally 143, while IMAP-SSL is generally 993.
 *               DEFAULT: 143
 *   'protocol'  The connection protocol (e.g. 'imap', 'pop3', 'nntp').
 *               Protocol is one of 'imap/notls' (or only 'imap' if you
 *               have a c-client version 2000c or older), 'imap/ssl', or
 *               'imap/ssl/novalidate-cert' (for a self-signed certificate).
 *               DEFAULT: 'imap'</pre>
 *
 * $Horde: framework/IMAP/IMAP/ACL/rfc4314.php,v 1.2.2.5 2009-01-06 15:23:12 jan Exp $
 *
 * Copyright 2006-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Matt Selsky <selsky@columbia.edu>
 * @since   Horde 3.1
 * @package Horde_IMAP
 */
class IMAP_ACL_rfc4314 extends IMAP_ACL_rfc2086 {

    /**
     * Constructor.
     *
     * @param array $params  Any additional parameters this driver may need.
     */
    function IMAP_ACL_rfc4314($params = array())
    {
        parent::IMAP_ACL_rfc2086($params);

        $this->_rightsList = array(
             'l' => _("List - user can see the folder"),
             'r' => _("Read messages"),
             's' => _("Mark with Seen/Unseen flags"),
             'w' => _("Mark with other flags (e.g. Important/Answered)"),
             'i' => _("Insert messages"),
             'p' => _("Post to this folder (not enforced by IMAP)"),
             'k' => _("Create sub folders"),
             'x' => _("Delete sub folders"),
             't' => _("Delete messages"),
             'e' => _("Purge messages"),
             'a' => _("Administer - set permissions for other users")
        );
        
        $this->_rightsListTitles = array(
             'l' => _("List"),
             'r' => _("Read"),
             's' => _("Mark (Seen)"),
             'w' => _("Mark (Other)"),
             'i' => _("Insert"),
             'p' => _("Post"),
             'k' => _("Create Folders"),
             'x' => _("Delete Folders"),
             't' => _("Delete"),
             'e' => _("Purge"),
             'a' => _("Administer")
        );
    }

}
