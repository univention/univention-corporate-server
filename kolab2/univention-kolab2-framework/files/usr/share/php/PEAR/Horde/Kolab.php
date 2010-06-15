<?php

#require_once 'HTTP/WebDAV/Client.php';
require_once 'HTTP/Request.php';
require_once 'Horde.php';
require_once 'Horde/iCalendar.php';
require_once 'Horde/String.php';
require_once 'Horde/MIME.php';
require_once 'Horde/MIME/Message.php';
require_once 'Horde/MIME/Headers.php';
require_once 'Horde/MIME/Structure.php';
require_once 'Horde/NLS.php';

/**
 * The 'newline' character sequence used by Cyrus IMAP.
 */
define('CYRUS_NL', "\r\n");

/**
 * The Does Not Exist error message returned by the imap_last_error()
 * function if a specified mailbox does not exist on the IMAP server.
 */
define('ERR_MBOX_DNE', 'Mailbox does not exist');

/**
 * The name of an X-Header used in various messages to provide category
 * information for the relevant object (note, task, etc).
 */
define('X_HEAD_CAT', 'X-Horde-Category');

/**
 * The name of an X-Header used by the Kolab KDE Client to specify a
 * notes' UID.
 */
define('X_HEAD_K_NOTEID', 'X-KOrg-Note-Id');

/**
 * The name of an X-Property used in various iCalendar objects to
 * provide support for storing Horde category information.
 */
define('X_ICAL_CAT', 'X-HORDE-CATEGORY');



/**
 * The Kolab:: and Kolab_Cyrus:: utility libraries provide various
 * functions for dealing with a Kolab server (i.e. functions that
 * relate to Cyrus IMAP, WebDAV, etc.).
 *
 * $Horde: framework/Kolab/Kolab.php,v 1.11 2004/05/24 13:45:04 stuart Exp $
 *
 * Copyright 2003, 2004 Code Fusion, cc.
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Stuart Binge <s.binge@codefusion.co.za>
 * @package Horde_Kolab
 */
class Kolab {

/* ---------- GENERAL FUNCTIONS ---------- */

    /**
     * Convertes any newlines in the specified text to unix format.
     *
     * @access public
     *
     * @param string $text  The text to convert.
     *
     * @return string    $text with all newlines replaced by NL.
     */
    function unixNewlines($text)
    {
        return preg_replace("/\r\n|\n|\r/s", "\n", $text);
    }

    /**
     * Returns the unfolded representation of the given text.
     *
     * @access public
     *
     * @param string $text  The text to unfold.
     *
     * @return string  The unfolded representation of $text.
     */
    function unfoldText($text)
    {
        return preg_replace("/\r\n[ \t]+/", "", $text);
    }

/* ---------- GENERAL KOLAB FUNCTIONS ---------- */

    /**
     * Strips any superfluos domain suffix from an email address. This was
     * done as Kolab uses 'name@maildomain' user names, whereas horde was
     * returning 'name@maildomain@hostname' addresses for the username.
     *
     * @access public
     *
     * @param string $address  The address to strip the domain from, of the
     *                         form 'a@b@c' where any/all of '@b' and '@c'
     *                         may be missing.
     *
     * @return string  A string of the form 'a@b'.
     */
    function stripKolabUsername($address)
    {
        return preg_replace('/^([^@]*(@[^@]*)?).*$/', "\$1", $address);
    }

    /**
     * Strips any superfluos domain suffix from an email address.
     *
     * @access public
     *
     * @param string $address  The address to strip the domain from, of the
     *                         form 'a@b@c' where any/all of '@b' and '@c'
     *                         may be missing.
     *
     * @return string  A string of the form 'a'.
     */
    function stripBaseUsername($address)
    {
        return preg_replace('/^([^@]*).*$/', "\$1", $address);
    }

    /**
     * Returns the username of the currently logged on Horde user, suitable
     * for use in other Kolab authentication procedures (assuming Horde is
     * using LDAP authentication against the Kolab server).
     *
     * @access public
     *
     * @return string  The current users login name.
     */
    function getUser()
    {
        return Kolab::stripKolabUsername(Auth::getAuth());
    }

    /**
     * Returns the password of the currently logged on Horde user, suitable
     * for use in other Kolab authentication procedures (assuming Horde is
     * using LDAP authentication against the Kolab server).
     *
     * @access public
     *
     * @return string  The current users login password.
     */
    function getPassword()
    {
        return Auth::getCredential('password');
    }

    /**
     * Returns the username and password of the currently logged on Horde user,
     * suitable for use in other Kolab authentication procedures (assuming
     * Horde is using LDAP authentication against the Kolab server).
     *
     * @access public
     *
     * @return array  An array of the form (username, password).
     */
    function getAuthentication()
    {
        return array(Kolab::getUser(), Kolab::getPassword());
    }

/* ---------- WEBDAV FUNCTIONS ---------- */

    /**
     * Retrieves the contents of a specified users VFB file, stored on a
     * specified WebDAV server.
     *
     * @access public
     *
     * @param string $server         The address of the WebDAV server, of the
     *                               form host:port.
     * @param string $folder         The folder on $server where the VFB file is
     *                               stored.
     * @param optional string $user  The name of the user whose VFB file is to
     *                               be retrieved. Defaults to the current user.
     *
     * @return mixed  (string) The contents of the users VFB file, suitable for
     *                    parsing by a Horde_iCalendar object.
     *                (object) PEAR_Error on failure.
     */
    function retrieveFreeBusy($server, $folder, $user = '')
    {
        list($uname, $pass) = Kolab::getAuthentication();
        if (empty($user)) $user = $uname;

        $url = "http://$server/$folder/$user.vfb";
        $http = &new HTTP_Request(
            $url,
            array(
                'user'  => $uname,
                'pass'  => $pass
            )
        );

        $result = $http->sendRequest();
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        $status = $http->getResponseCode();
        if ($status != 200) {
            // Try `user' instead of `user@domain', for backward compatibility
            $url = "http://$server/$folder/" . Kolab::stripBaseUsername($user) . ".vfb";
            $http->setURL($url);
            $result = $http->sendRequest();
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }

            $status = $http->getResponseCode();

            if ($status != 200) {
                return PEAR::raiseError(sprintf(
                    _('%s %d (GET %s)'),
                    $http->_response->_protocol,
                    $status,
                    $url
                ), $status);
            }
        }

        return $http->getResponseBody();
    }

    /**
     * Stores the specified VFB data in the current users VFB file on the
     * specified WebDAV server.
     *
     * @access public
     *
     * @param string $server  The address of the WebDAV server, of the form
     *                        host:port.
     * @param string $folder  The folder on $server where the VFB file is stored.
     * @param string $vfb     The new VFB data to store.
     *
     * @return mixed  (boolean) True on success.
     *                (object)  PEAR_Error on failure.
     */
    function storeFreeBusy($server, $folder, $vfb)
    {
        list($user, $pass) = Kolab::getAuthentication();

        $path = 'webdav://' . urlencode($user) . ':' . urlencode($pass) . "@$server/$folder/$user.vfb";

        if (!$fh = fopen($path, 'w'))
            return PEAR::raiseError(sprintf(
                _('Unable to store free/busy information for user %s on server %s'),
                $user,
                $server
            ));

        if (!fwrite($fh, $vfb)) {
            fclose($fh);
            return PEAR::raiseError(sprintf(
                _('Unable to store free/busy information for user %s on server %s'),
                $user,
                $server
            ));
        }

        fclose($fh);

        return true;
    }

}

class Kolab_Cyrus {

    /**
     * The IMAP connection handle.
     *
     * @var resource $_imap
     */
    var $_imap = NULL;

    /**
     * The address of our Cyrus server.
     *
     * @var string $_server
    */
    var $_server = "";

    /**
     * The mailbox which we currently have opened.
     *
     * @var string $_mailbox
     */
    var $_mailbox = "";

/* ---------- UTILITY FUNCTIONS ---------- */

    /**
     * Returns an IMAP server address formatted for use in the PHP IMAP
     * functions.
     *
     * @param string $server  The address of the IMAP server.
     *
     * @return string  An address string suitable for use in functions such as
     *                 imap_open().
     */
    function serverURI($server)
    {
        return "{" . "$server/imap/notls/norsh}";
    }

    /**
     * Returns an address of a Cyrus mailbox, formatted for use in the PHP IMAP
     * functions.
     *
     * @param string $server            The address of the Cyrus server.
     * @param optional string $mailbox  The name of the mailbox (defaults to
     *                                  the current users' inbox).
     *
     * @return string  A mailbox address string suitable for use in functions
     *                 such as imap_open().
     */
    function mailboxURI($server, $mailbox = "INBOX")
    {
        $mailbox = imap_utf7_encode($mailbox);
        if (strncmp($mailbox, "user", 4) && strncmp($mailbox, "INBOX", 5)) {
            $mailbox = "INBOX/$mailbox";
        }
        return Kolab_Cyrus::serverURI($server) . $mailbox;
    }

    /**
     * Converts newlines of any format in the specified text to a
     * Cyrus-compatible format.
     *
     * @param string $text  The text to convert.
     *
     * @return string    $text with all newlines replaced by CRLF.
     */
    function convertNewlines($text)
    {
        return preg_replace("/\r\n|\n|\r/s", "\r\n", $text);
    }

    /**
     * Tests if $error was the last IMAP error that was generated.
     *
     * @param string $error  The error to test against.
     *
     * @return boolean  True if $error was the last IMAP error.
     */
    function testError($error)
    {
        return strcasecmp(imap_last_error(), $error) == 0;
    }

    /**
     * Returns the IMAP folder corresponding to the specified share.
     *
     * @param string $sharesname     The name of the shares object to query
     * @param string $shareobject    The name of the share
     * @param string $defaultfolder  What folder to use as the default. This
     *                               is also used if the name of the share is
     *                               the name of the user (i.e. the default
     *                               share), and as the root under which to
     *                               store the non-default subfolders (shares).
     * @param string $folder         A reference to the variable which will
     *                               store the folder name.
     * @param boolean $create        A reference to the variable which will
     *                               store the folder creation flag.
     *
     * @return mixed   (string) The name of the share if successful, PEAR_Error on failure
     */
    function shareToFolder($sharesname, $shareobject, $defaultfolder, &$folder, &$create)
    {
        $user = Auth::getAuth();
        $shares = $GLOBALS[$sharesname]->listShares($user, PERMS_EDIT, true);
        if (is_a($shares, 'PEAR_Error')) {
            return $shares;
        }

        if (empty($shareobject)) {
            // No share specified; use the first one
            $shareobject = array_keys($shares);
            $shareobject = $shareobject[0]->getName();
        }

        $shares = $GLOBALS[$sharesname]->listShares($user, PERMS_SHOW, false);
        if (!array_key_exists($shareobject, $shares)) {
            // Can't access the share; bork
            return PEAR::raiseError("Unable to access share $shareobject");
        }

        $owner = $shares[$shareobject]->get("owner");
        $name = $shares[$shareobject]->get("name");
        $name = ($owner == $shares[$shareobject]->getName() ? $defaultfolder : $name);

        if ($owner != $user) {
            // Shared Cyrus folder

            if ($GLOBALS['conf']['kolab']['virtual_domains']) {
                $owner = Kolab::stripBaseUsername($owner);
            }

            if ($defaultfolder == $name) {
                $folder = "user/$owner/$name";
            } else {
                $folder = "user/$owner/$defaultfolder/$name";
            }
            $create = false;
        } else {
            // Local Cyrus folder
            if ($defaultfolder == $name) {
                $folder = "$name";
            } else {
                $folder = "$defaultfolder/$name";
            }
            $create = true;
        }

        return $shareobject;
    }

/* ---------- CONNECTION FUNCTIONS ---------- */

    /**
     * Constructor - opens a connection to the specified Cyrus server.
     *
     * @param string $server  The address of the Kolab Cyrus server.
     */
    function Kolab_Cyrus($server) {
        $this->reconnect($server);
    }

    /**
     * Reconnects to a (possibly different) Cyrus server.
     *
     * @param optional string $server  If specified, connect to this server
     *                           instead of the default.
     *
     * @return mixed  True on success; PEAR_Error on failure.
     */
    function reconnect($server = "") {
        $this->disconnect();

        $this->_server = (empty($server) ? $this->_server : $server);

        $this->_imap = @imap_open(
            Kolab_Cyrus::serverURI($this->_server),
            Kolab::getUser(),
            Kolab::getPassword(),
            OP_HALFOPEN
        );

        if ($this->_imap === false) {
            $this->_imap = NULL;
            return PEAR::raiseError(sprintf(_("Unable to connect to the Cyrus server %s: " . imap_last_error()), $this->_server));
        }

        return true;
    }

    /**
     * Disconnects from the currently open Cyrus server,
     *
     * @param optional boolean $expunge  True to expunge the mailbox before
     *                                   closing.
     */
    function disconnect($expunge = true)
    {
        if (isset($this->_imap)) {
            @imap_close($this->_imap, ($expunge ? CL_EXPUNGE : 0));
            $this->_imap = NULL;
        }
        $this->_mailbox = "";
    }

    /**
     * Ensures that the connection to the Cyrus server is still active.
     */
    function ping()
    {
        if (!isset($this->_imap) || !imap_ping($this->_imap))
            $this->reconnect();
    }

/* ---------- MAILBOX FUNCTIONS ---------- */

    /**
     * Opens a mailbox on the active IMAP connection, optionally creating it
     * if it doesn't already exist.
     *
     * @param optional string $mailbox  Which mailbox to open. Defaults to
     *                                  the inbox.
     * @param optional boolean $create  True to create $mailbox if it doesn't
     *                                  already exist.
     *
     * @return mixed  True on success; PEAR_Error on failure.
     */
    function openMailbox($mailbox = "INBOX", $create = true)
    {
        if (@imap_reopen($this->_imap, Kolab_Cyrus::mailboxURI($this->_server, $mailbox))) {
            if (Kolab_Cyrus::testError(ERR_MBOX_DNE) && $create) {
                $result = $this->createMailbox($mailbox);
                if (is_a("PEAR_Error", $result))
                    return $result;

                if (!@imap_reopen($this->_imap, Kolab_Cyrus::mailboxURI($this->_server, $mailbox)))
                    return PEAR::raiseError(sprintf(_("Unable to open mailbox %s: " . imap_last_error()), $mailbox));
            }
        } else {
            return PEAR::raiseError(sprintf(_("Unable to open mailbox %s: " . imap_last_error()), $mailbox));
        }

        $this->_mailbox = $mailbox;

        return true;
    }

    /**
     * Closes the currently open mailbox.
     *
     * @return mixed  True on success; PEAR_Error on failure.
     */
    function closeMailbox()
    {
        /* return if we don't currently have a mailbox open */
        if ($this->_mailbox == "")
            return true;

        if (!@imap_reopen($this->_imap, Kolab_Cyrus::serverURI($this->_server), OP_HALFOPEN))
            return PEAR::raiseError(sprintf(_("Unable to close mailbox %s: " . imap_last_error()), $this->_mailbox));

        $this->_mailbox = "";

        return true;
    }

    /**
     * Creates a new mailbox.
     *
     * @param $mailbox  The name of the mailbox to create.
     *
     * @return mixed  True on success; PEAR_Error on failure.
     */
    function createMailbox($mailbox)
    {
        $result = $this->closeMailbox();
        if (is_a("PEAR_Error", $result))
            return $result;

        if (!@imap_createmailbox($this->_imap, Kolab_Cyrus::mailboxURI($this->_server, $mailbox)))
            return PEAR::raiseError(sprintf(_("Unable to create mailbox %s: " . imap_last_error()), $mailbox));

        return true;
    }

    /**
     * Removes an existing mailbox, including all messages in the mailbox.
     *
     * @param $mailbox  The name of the mailbox to remove.
     *
     * @return mixed  True on success; PEAR_Error on failure.
     */
    function deleteMailbox($mailbox)
    {
        $result = $this->closeMailbox();
        if (is_a("PEAR_Error", $result))
            return $result;

        if (!@imap_deletemailbox($this->_imap, Kolab_Cyrus::mailboxURI($this->_server, $mailbox)))
            return PEAR::raiseError(sprintf(_("Unable to delete mailbox %s: " . imap_last_error()), $mailbox));

        return true;
    }

    /**
     * Renames a mailbox.
     *
     * @param $old  The current name of the mailbox.
     * @param $new  The new name of the mailbox.
     *
     * @return mixed  True on success; PEAR_Error on failure.
     */
    function renameMailbox($old, $new)
    {
        $result = $this->closeMailbox();
        if (is_a("PEAR_Error", $result))
            return $result;

        if (!@imap_renamemailbox(
            $this->_imap,
            Kolab_Cyrus::mailboxURI($this->_server, $old),
            Kolab_Cyrus::mailboxURI($this->_server, $new)
        ))
            return PEAR::raiseError(sprintf(_("Unable to rename mailbox %s: " . imap_last_error()), $old));

        return true;
    }

    /**
     * Retrieves a list of all the current user's mailboxes.
     *
     * @return array  An array of mailbox names.
     */
    function listMailBoxes()
    {
        $result = $this->closeMailbox();
        if (is_a("PEAR_Error", $result))
            return $result;

        $mailboxes = @imap_list($this->_imap, Kolab_Cyrus::serverURI($this->_server), "*");
        if (!is_array($mailboxes))
            return PEAR::raiseError(_("Unable to retrieve mailbox list: " . imap_last_error()));

        return $mailboxes;
    }

/* ---------- MESSAGE FUNCTIONS ---------- */

    /**
     * Returns a list of messages in the opened mailbox, sorted by the
     * specified criteria, optinally matching specific search criteria.
     *
     * @access public
     *
     * @param (optional) integer $sortcriteria  Specifies how to sort the
     *                              returned message list. Defaults to
     *                              sorting by date.
     * @param (optional) bool $reverse  If TRUE, sorts the message list
     *                              in reverse order.
     * @param (optional) string $searchcriteria  Specifies the IMAP search
     *                              string which returned messages should
     *                              match. By default all messages are
     *                              returned. See "imap_sort" for the format
     *                              of this field.
     *
     * @return array    The list of messages in the mailbox that match the
     *                  specified criteria; an empty list is returned on
     *                  failure.
     */
    function getMessageList($sortcriteria = SORTDATE, $reverse = false, $searchcriteria = "")
    {
        $messages = @imap_sort($this->_imap, $sortcriteria, ($reverse ? 1 : 0), SE_UID, $searchcriteria);
        if (!is_array($messages)) {
            $messages = array();
        }
        return $messages;
    }

    /**
     * Returns the entire unaltered RFC822 message text from the specified
     * message store.
     *
     * @access public
     *
     * @param integer $messageid    The message of interest.
     *
     * @return string    The message data.
     */
    function getMessage($messageid)
    {
        if (is_array($messageid)) {
            $messageid = array_values($messageid);
            $messageid = $messageid[0];
        }
        $message = @imap_fetchheader($this->_imap, $messageid, FT_UID | FT_PREFETCHTEXT);
        $message .= @imap_body($this->_imap, $messageid, FT_UID);
        return $message;
    }

    /**
     * Returns the raw, unfolded RFC822 headers of a specified message.
     *
     * @access public
     *
     * @param integer $messageid    The message from which to read the headers.
     *
     * @return string  The raw RFC822 message headers.
     */
    function getMessageHeaders($messageid)
    {
        if (is_array($messageid)) {
            $messageid = array_values($messageid);
            $messageid = $messageid[0];
        }
        return Kolab::unfoldText(@imap_fetchheader($this->_imap, $messageid, FT_UID));
    }

    /**
     * Returns the body of the specified message.
     *
     * @access public
     *
     * @param integer $messageid    The message of interest.
     *
     * @return string    The message body.
     */
    function getMessageBody($messageid)
    {
        if (is_array($messageid)) {
            $messageid = array_values($messageid);
            $messageid = $messageid[0];
        }
        return @imap_body($this->_imap, $messageid, FT_UID);
    }

    /**
     * Deletes the specified message(s) from the relevant message store.
     *
     * @access public
     *
     * @param integer $messageid  The message to delete. This can also be
     *                            an array of message IDs if multiple messages
     *                            are to be deleted.
     * @param optional boolean $expunge  True to expunge the mailbox after
     *                                   deletion.
     */
    function deleteMessages($messageid, $expunge = false)
    {
        if (!is_array($messageid)) {
            $messageid = array($messageid);
        }

        foreach ($messageid as $mid) {
            @imap_delete($this->_imap, $mid, FT_UID);
        }

        if ($expunge)
            @imap_expunge($this->_imap);
    }

    /**
     * Returns a hash of the message headers of a specified message.
     *
     * @access public
     *
     * @param integer $messageid    The message from which to read the headers.
     *                              If this is an array, the first element is
     *                              used as the message.
     *
     * @return array  A hash of the headers, where each 'key => value' pair in
     *                the hash corresponds to a 'Name: Value' header line. This
     *                array is empty if an error occurs.
     */
    function getHeaderHash($messageid)
    {
        if (is_array($messageid)) {
            $messageid = array_values($messageid);
            $messageid = $messageid[0];
        }
        $headers = array();

        $headerlines = $this->getMessageHeaders($messageid);
        $headerlines = explode(CYRUS_NL, $headerlines);
        foreach ($headerlines as $headerline) {
            if (empty($headerline)) continue;

            list($hname, $hval) = explode(':', MIME::decode($headerline), 2);
            $headers[trim($hname)] = trim($hval);
        }

        return $headers;
    }

    /**
     * Returns the value of a header attribute in a hash returned by
     * Kolab::getHeaderHash(), or a specified default value if the header
     * attribute does not exist.
     *
     * @access public
     *
     * @param array $headers           The message header hash.
     * @param string $name             The attribute to search for.
     * @param optional mixed $default  The value to return if $name does not
     *                                 exist in $headers.
     *
     * @return mixed    The value of $default.
     */
    function headerValue(&$headers, $name, $default = '')
    {
        return array_key_exists($name, $headers) ? $headers[$name] : $default;
    }

/* ---------- GROUPWARE OBJECT FUNCTIONS ---------- */

    /**
     * Returns the body of the first MIME part within the specified message
     * that matches the specified content type (if such a part exists).
     *
     * @access public
     *
     * @param integer $messageid      The message to read.
     * @param string $conttype        The content type of the desired object.
     *                                The first MIME part in the specified
     *                                message with this content type is the
     *                                object that is returned.
     *
     * @return mixed  (string)  The first mime part matching $conttype
     *                (boolean) False if such a mime part does not exist.
     */
    function getObject($messageid, $conttype)
    {
        $message_text = $this->getMessage($messageid);
        $message = &MIME_Structure::parseTextMIMEMessage($message_text);

        $parts = $message->contentTypeMap();
        foreach ($parts as $mimeid => $ct) {
            if ($ct == $conttype) {
                $part = $message->getPart($mimeid);
                return $part->toString();
            }
        }

        return false;
    }

    /**
     * Inserts an object as a MIME part into a message, and adds the resulting
     * message to the specified mail store.
     *
     * @access public
     *
     * @param string $subject       What text to use for the message subject.
     * @param string $data          The data to use as the MIME part body
     * @param string $conttype      The MIME content type of the message.

     * @param optional string $filename The MIME attachment name that $body should
     *                              have.
     * @param optional string $ua   The user agent which is adding the message.
     * @param optional array $extraheaders A hash containing any extra headers to
     *                              append. Each 'key => value' pair is written
     *                              as 'key: value' in the message header.
     *
     * @return mixed    (boolean) True on success.
     *                  (object)  PEAR_Error on failure.
     */
    function addObject($subject, $data, $conttype, $filename = '', $ua = '', $extraheaders = array())
    {
        $current_user = Kolab::getUser();

        $message = &new MIME_Message();
        $part = &new MIME_Part($conttype, $data);
        $part->setName($filename);
        $part->setDisposition("attachment");
        $message->addPart($part);

        $headers = &new MIME_Headers();
        foreach ($extraheaders as $key => $value) {
            $headers->addHeader($key, $value);
        }
        $headers->addHeader("From", $current_user);
        $headers->addHeader("To", $current_user);
        $headers->addHeader("Subject", $subject);
        $headers->addHeader("User-Agent", "Horde/$ua/Kolab");
        $headers->addHeader("Reply-To", "");
        $headers->addHeader("Date", date("r"));
        $headers->addMIMEHeaders($message);

        $message = Kolab_Cyrus::convertNewlines($headers->toString() . $part->toString(false));

        if (!@imap_append($this->_imap, Kolab_Cyrus::mailboxURI($this->_server, $this->_mailbox), $message)) {
            return PEAR::raiseError(
                sprintf(
                    _('Unable to add object from %s to mailbox %s: ' . imap_last_error()),
                    $current_user,
                    $this->_mailbox
                )
            );
        }

        return true;
    }

}
