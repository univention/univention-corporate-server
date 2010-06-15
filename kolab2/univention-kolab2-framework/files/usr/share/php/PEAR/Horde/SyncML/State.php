<?php

define('ALERT_DISPLAY', 100);

// Not implemented.
define('ALERT_TWO_WAY', 200);
define('ALERT_SLOW_SYNC', 201);
define('ALERT_ONE_WAY_FROM_CLIENT', 202);
define('ALERT_REFRESH_FROM_CLIENT', 203);
define('ALERT_ONE_WAY_FROM_SERVER', 204);
define('ALERT_REFRESH_FROM_SERVER', 205);

// Not implemented.
define('ALERT_TWO_WAY_BY_SERVER', 206);
define('ALERT_ONE_WAY_FROM_CLIENT_BY_SERVER', 207);
define('ALERT_REFRESH_FROM_CLIENT_BY_SERVER', 208);
define('ALERT_ONE_WAY_FROM_SERVER_BY_SERVER', 209);
define('ALERT_REFRESH_FROM_SERVER_BY_SERVER', 210);

define('ALERT_RESULT_ALERT', 221);
define('ALERT_NEXT_MESSAGE', 222);
define('ALERT_NO_END_OF_DATA', 223);

define('MIME_SYNCML_XML', 'application/vnd.syncml+xml');
define('MIME_SYNCML_WBXML', 'application/vnd.syncml+wbxml');

define('MIME_SYNCML_DEVICE_INFO_XML', 'application/vnd.syncml-devinf+xml');
define('MIME_SYNCML_DEVICE_INFO_WBXML', 'application/vnd.syncml-devinf+wbxml');

define('MIME_TEXT_PLAIN', 'text/plain');
define('MIME_VCARD_V21', 'text/x-vcard');
define('MIME_VCARD_V30', 'text/vcard');

define('MIME_VCALENDAR', 'text/x-vcalendar');
define('MIME_ICALENDAR', 'text/calendar');
define('MIME_XML_ICALENDAR', 'application/vnd.syncml-xcal');

define('MIME_MESSAGE', 'text/message');

define('MIME_SYNCML_XML_EMAIL', 'application/vnd.syncml-xmsg');
define('MIME_SYNCML_XML_BOOKMARK', 'application/vnd.syncml-xbookmark');
define('MIME_SYNCML_RELATIONAL_OBJECT', 'application/vnd.syncml-xrelational');

define('RESPONSE_IN_PROGRESS', 101);

define('RESPONSE_OK', 200);
define('RESPONSE_ITEM_ADDED', 201);
define('RESPONSE_ACCEPTED_FOR_PROCESSING', 202);
define('RESPONSE_NONAUTHORIATATIVE_RESPONSE', 203);
define('RESPONSE_NO_CONTENT', 204);
define('RESPONSE_RESET_CONTENT', 205);
define('RESPONSE_PARTIAL_CONTENT', 206);
define('RESPONSE_CONFLICT_RESOLVED_WITH_MERGE', 207);
define('RESPONSE_CONFLICT_RESOLVED_WITH_CLIENT_WINNING', 208);
define('RESPONSE_CONFILCT_RESOLVED_WITH_DUPLICATE', 209);
define('RESPONSE_DELETE_WITHOUT_ARCHIVE', 210);
define('RESPONSE_ITEM_NO_DELETED', 211);
define('RESPONSE_AUTHENTICATION_ACCEPTED', 212);
define('RESPONSE_CHUNKED_ITEM_ACCEPTED_AND_BUFFERED', 213);
define('RESPONSE_OPERATION_CANCELLED', 214);
define('RESPONSE_NO_EXECUTED', 215);
define('RESPONSE_ATOMIC_ROLL_BACK_OK', 216);

define('RESPONSE_MULTIPLE_CHOICES', 300);
// Need to change names.
// define('RESPONSE_MULTIPLE_CHOICES', 301);
// define('RESPONSE_MULTIPLE_CHOICES', 302);
// define('RESPONSE_MULTIPLE_CHOICES', 303);
// define('RESPONSE_MULTIPLE_CHOICES', 304);
define('RESPONSE_USE_PROXY', 305);

define('RESPONSE_BAD_REQUEST', 400);
define('RESPONSE_INVALID_CREDENTIALS', 401);
// Need to change names.
// define('RESPONSE_INVALID_CREDENTIALS', 402);
// define('RESPONSE_INVALID_CREDENTIALS', 403);
define('RESPONSE_NOT_FOUND', 404);
// Need to change names.
// define('RESPONSE_INVALID_CREDENTIALS', 405);
// define('RESPONSE_INVALID_CREDENTIALS', 406);
// define('RESPONSE_INVALID_CREDENTIALS', 407);
// define('RESPONSE_INVALID_CREDENTIALS', 408);
// define('RESPONSE_INVALID_CREDENTIALS', 409);
// define('RESPONSE_INVALID_CREDENTIALS', 410);
// define('RESPONSE_INVALID_CREDENTIALS', 411);
// define('RESPONSE_INVALID_CREDENTIALS', 412);
// define('RESPONSE_INVALID_CREDENTIALS', 413);
// define('RESPONSE_INVALID_CREDENTIALS', 414);
// define('RESPONSE_INVALID_CREDENTIALS', 415);
define('RESPONSE_REQUEST_SIZE_TOO_BIG', 416);
// Need to change names.
// define('RESPONSE_INVALID_CREDENTIALS', 417);
// define('RESPONSE_INVALID_CREDENTIALS', 418);
// define('RESPONSE_INVALID_CREDENTIALS', 419);
// define('RESPONSE_INVALID_CREDENTIALS', 420);
// define('RESPONSE_INVALID_CREDENTIALS', 421);
// define('RESPONSE_INVALID_CREDENTIALS', 422);
// define('RESPONSE_INVALID_CREDENTIALS', 423);
define('RESPONSE_SIZE_MISMATCH', 424);

define('RESPONSE_COMMAND_FAILED', 500);
// Need to change names.
// define('RESPONSE_COMMAND_FAILED', 501);
// define('RESPONSE_COMMAND_FAILED', 502);
// define('RESPONSE_COMMAND_FAILED', 503);
// define('RESPONSE_COMMAND_FAILED', 504);
// define('RESPONSE_COMMAND_FAILED', 505);
// define('RESPONSE_COMMAND_FAILED', 506);
// define('RESPONSE_COMMAND_FAILED', 507);
// define('RESPONSE_COMMAND_FAILED', 508);
// define('RESPONSE_COMMAND_FAILED', 509);
// define('RESPONSE_COMMAND_FAILED', 510);
// define('RESPONSE_COMMAND_FAILED', 511);
// define('RESPONSE_COMMAND_FAILED', 512);
// define('RESPONSE_COMMAND_FAILED', 513);
// define('RESPONSE_COMMAND_FAILED', 514);
// define('RESPONSE_COMMAND_FAILED', 515);
define('RESPONSE_ATOMIC_ROLL_BACK_FAILED', 516);

define('NAME_SPACE_URI_SYNCML', 'syncml:syncml');
define('NAME_SPACE_URI_SYNCML_1_1', 'syncml:syncml1.1');
define('NAME_SPACE_URI_METINF', 'syncml:metinf');
define('NAME_SPACE_URI_METINF_1_1', 'syncml:metinf1.1');
define('NAME_SPACE_URI_DEVINF', 'syncml:devinf');
define('NAME_SPACE_URI_DEVINF_1_1', 'syncml:devinf1.1');

/**
 * The Horde_SyncML_State class provides a SyncML state object.
 *
 * $Horde: framework/SyncML/SyncML/State.php,v 1.9 2004/05/25 22:03:00 chuck Exp $
 *
 * Copyright 2003-2004 Anthony Mills <amills@pyramid6.com>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Anthony Mills <amills@pyramid6.com>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 * @package Horde_SyncML
 */
class Horde_SyncML_State {

    var $_sessionID;

    var $_verProto;

    var $_msgID;

    var $_targetURI;

    var $_sourceURI;

    var $_version;

    var $_locName;

    var $_password;

    var $_isAuthorized;

    var $_uri;

    var $_uriMeta;

    var $_syncs = array();

    var $_datatree;

    /**
     * Creates a new instance of Horde_SyncML_State.
     */
    function Horde_SyncML_State($sourceURI, $locName, $sessionID, $password = false)
    {
        $this->setSourceURI($sourceURI);
        $this->setLocName($locName);
        $this->setSessionID($sessionID);
        if ($password) {
            $this->setPassword($password);
        }

        $this->isAuthorized = false;

        $driver = $GLOBALS['conf']['datatree']['driver'];
        $params = Horde::getDriverConfig('datatree', $driver);
        $params = array_merge($params, array( 'group' => 'syncml' ));

        $this->_datatree = &DataTree::singleton($driver, $params);
    }

    function getLocName()
    {
        return $this->_locName;
    }

    function getSourceURI()
    {
        return $this->_sourceURI;
    }

    function getTargetURI()
    {
        return $this->_targetURI;
    }

    function getVersion()
    {
        return $this->_version;
    }

    function getMsgID()
    {
        return $this->_msgID;
    }

    /**
     * Setter for property msgID.
     * @param msgID New value of property msgID.
     */
    function setMsgID($msgID)
    {
        $this->_msgID = $msgID;
    }

    /**
     * Setter for property locName.
     * @param locName New value of property locName.
     */
    function setLocName($locName)
    {
        $this->_locName = $locName;
    }

    /**
     * Setter for property locName.
     * @param locName New value of property locName.
     */
    function setPassword($password)
    {
        $this->_password = $password;
    }

    function setSourceURI($sourceURI)
    {
        $this->_sourceURI = $sourceURI;
    }

    function setTargetURI($targetURI)
    {
        $this->_targetURI = $targetURI;
    }

    function setVersion($version)
    {
        $this->_version = $version;

        if ($version == 0) {
            $this->_uri = NAME_SPACE_URI_SYNCML;
            $this->_uriMeta = NAME_SPACE_URI_METINF;
        } else {
            $this->_uri = NAME_SPACE_URI_SYNCML_1_1;
            $this->_uriMeta = NAME_SPACE_URI_METINF_1_1;
        }
    }

    function setSessionID($sessionID)
    {
        $this->_sessionID = $sessionID;
    }

    function isAuthorized()
    {
        if (!$this->_isAuthorized) {
            $auth = &Auth::singleton($GLOBALS['conf']['auth']['driver']);
            $this->_isAuthorized = $auth->authenticate($this->_locName, array('password' => $this->_password));
        }

        return $this->_isAuthorized;
    }

    function setSync($target, $sync)
    {
        $this->_syncs[$target] = $sync;
    }

    function getSync($target)
    {
        if (isset($this->_syncs[$target])) {
            return $this->_syncs[$target];
        } else {
            return false;
        }
    }

    function getURI()
    {
        return $this->_uri;
    }

    function getURIMeta()
    {
        return $this->_uriMeta;
    }

    function getLocID($guid)
    {
        $id = $this->_datatree->getId($guid);
        $gid = $this->_datatree->get($id);

        return $gid->get('locid');
    }

    function setUID($type, $locid, $guid)
    {
        // Set $locid
        $gid = &new DataTreeObject($guid);
        $gid->set('type', $type);
        $gid->set('locid', $locid);
        $this->_datatree->add($gid);

        // Set $globaluid
        $lid = &new DataTreeObject($this->_locName . $this->_sourceURI . $type . $locid);
        $lid->set('globaluid', $locid);
        $this->_datatree->add($lid);
    }

    function getGlobalUID($type, $locid)
    {
        $id = $this->_datatree->getId($this->_locName . $this->_sourceURI . $type . $locid);
        $lid = $this->_datatree->get($id);
        return $lid->get('globaluid');
    }

    function removeUID($type, $locid)
    {
        $id = $this->_datatree->getId($this->_locName . $this->_sourceURI . $type . $locid);
        $lid = $this->_datatree->get($id);
        $guid = $lid->get('globaluid');
        $this->_datatree->remove($guid);
        $this->_datatree->remove($lid);

        return $guid;
    }

    /**
     * This function should use DevINF information.
     */
    function getPreferedContentType($type)
    {
        if ($type == 'contacts') {
            return 'text/x-vcard';
        } elseif ($type == 'notes') {
            return 'text/plain';
        } elseif ($type == 'tasks') {
            return 'text/x-vcalendar';
        } elseif ($type == 'calendar') {
            return 'text/x-vcalendar';
        }
    }

    function getLastSyncDate($type)
    {
        $id = $this->_datatree->getId($this->_locName . $this->_sourceURI . $type . 'lastSyncDate');
        $obj = $this->_datatree->get($id);
        return $obj->get('date');
    }

    function setLastSyncDate($type, $date)
    {
        $lsd = &new DataTreeObject($this->_locName . $this->_sourceURI . $type . 'lastSyncDate');
        $lsd->set('date', $date);
        $this->_datatree->add($lsd);
    }

    function getLastSyncAnchor($type)
    {
        $id = $this->_datatree->getId($this->_locName . $this->_sourceURI . $type . 'lastSyncAnchor');
        $obj = $this->_datatree->get($id);
        return $obj->get('anchor');
    }

    function setLastSyncAnchor($type, $date)
    {
        $lsd = &new DataTreeObject($this->_locName . $this->_sourceURI . $type . 'lastSyncAnchor');
        $lsd->set('anchor', $date);
        $this->_datatree->add($lsd);
    }

}
