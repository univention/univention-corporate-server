<?php

include_once 'Horde/SyncML/Command.php';
include_once 'Horde/SyncML/Command/Status.php';
include_once 'Horde/SyncML/Command/Alert.php';
include_once 'Horde/SyncML/Command/Sync.php';
include_once 'Horde/SyncML/Sync.php';

/**
 * The Horde_SyncML_SyncHdr and Horde_SyncML_SyncBody classes provides
 * a SyncHdr and SyncBody in SyncML Representation Protocol, version
 * 1.1 5.2.2 and 5.2.3.  Most of the work is passed on to
 * Horde_SyncML_Command_Alert and Horde_SyncML_Command_Sync.
 *
 * $Horde: framework/SyncML/SyncML.php,v 1.17 2004/05/26 17:32:49 chuck Exp $
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
class Horde_SyncML_ContentHandler {

    /**
     * Output ContentHandler used to output XML events.
     * @var object $_output
     */
    var $_output;

    /**
     * @var integer $_xmlStack
     */
    var $_xmlStack = 1;

    /**
     * @var string $_chars
     */
    var $_chars;

    function setOutput(&$output)
    {
        $this->_output = &$output;
    }

    function startElement($uri, $element, $attrs)
    {
        $this->_xmlStack++;
    }

    function endElement($uri, $element)
    {
        if (isset($this->_chars)) {
            unset($this->_chars);
        }

        $this->_xmlStack--;
    }

    function characters($str)
    {
        if (isset($this->_chars)) {
            $this->_chars = $this->_chars . $str;
        } else {
            $this->_chars = $str;
        }
    }

}

/**
 * Defined in SyncML Representation Protocol, version 1.1 5.2.2
 *
 * @package Horde_SyncML
 */
class Horde_SyncML_SyncMLHdr extends Horde_SyncML_ContentHandler {

    /**
     * Used to specify if in Source tag.  Defined in SyncML
     * Representation Protocol, version 1.1 5.1.20.
     *
     * @var boolean $_isSource
     */
    var $_isSource = false;

    /**
     * Defined in SyncML Representation Protocol, version 1.1
     * 5.1.9. User name.
     *
     * @var string $_locName
     */
    var $_locName;

    /**
     * Defined in SyncML Representation Protocol, version 1.1 5.1.18
     *
     * @var string $_sessionID
     */

    var $_sessionID;

    /**
     * Defined in SyncML Representation Protocol, version 1.1.  Must
     * be 1.0 (0) or 1.1 (1).
     *
     * @var string $_version
     */
    var $_version;

    /**
     * Defined in SyncML Representation Protocol, version 1.1 5.1.12
     *
     * @var string $_msgID
     */
    var $_msgID;

    /**
     * Defined in SyncML Representation Protocol, version 1.1 5.1.10
     *
     * @var string $_targetURI
     */
    var $_targetURI;

    /**
     * Defined in SyncML Representation Protocol, version 1.1 5.1.10,
     * 5.1.20
     *
     * @var string $_sourceURI
     */
    var $_sourceURI;

    var $_isCred;

    var $_credData;

    var $_credFormat;

    var $_credType;

    function getStateFromSession($sourceURI, $locName, $sessionID)
    {
        // Remove any existing session since we'll be contructing a
        // custom session id.
        session_destroy();

        // It would seem multisync does not send the user name once it
        // has been authorized. Make sure we have a valid session id.
        session_id('syncml' . preg_replace('/[^a-zA-Z0-9]/', '', $sourceURI . $sessionID));
        session_start();
        Horde::logMessage('SyncML: session id = ' . session_id(), __FILE__, __LINE__,  PEAR_LOG_DEBUG);

        if (!isset($_SESSION['SyncML.state'])) {
            // Create a new state if one does not already exist.
            Horde::logMessage('SyncML: new session state', __FILE__, __LINE__,  PEAR_LOG_DEBUG);

            $_SESSION['SyncML.state'] = &new Horde_SyncML_State($sourceURI, $locName, $sessionID);
        }

        return $_SESSION['SyncML.state'];
    }

    function startElement($uri, $element, $attrs)
    {
        parent::startElement($uri, $element, $attrs);

        switch ($this->_xmlStack) {
        case 3:
            if ($element == 'Source') {
                // <SyncML><SyncHdr><Source>
                $this->_isSource = true;
            } elseif ($element == 'Cred') {
                $this->_isCred = true;
            }
            break;
        }
    }

    function endElement($uri, $element)
    {
        switch ($this->_xmlStack) {
        case 2:
            /*
            $str = 'localname=' . $this->_locName;
            $str .= ' version=' . $this->_version;
            $str .= ' msgid=' . $this->_msgID;
            $str .= ' source=' . $this->_sourceURI;
            $str .= ' target=' . $this->_targetURI;
            $str .= ' sessionID=' . $this->_sessionID;
            */
            // </SyncHdr></SyncML>
            // Find the state.
            $state = $this->getStateFromSession($this->_sourceURI, $this->_locName, $this->_sessionID);

            $state->setVersion($this->_version);
            $state->setMsgID($this->_msgID);
            $state->setTargetURI($this->_targetURI);
            $state->setPassword($this->_credData);

            $str = 'authorized=' . $state->isAuthorized();
            $str .= ' version=' . $state->getVersion();
            $str .= ' msgid=' . $state->getMsgID();
            $str .= ' source=' . $state->getSourceURI();
            $str .= ' target=' . $state->getTargetURI();
            $str .= ' locName=' . $state->getLocName();

            $_SESSION['SyncML.state'] = $state;

            Horde::logMessage('SymcML: ' . $str, __FILE__, __LINE__,  PEAR_LOG_DEBUG);

            // Got the state; now write our SyncHdr header.
            $this->outputSyncHdr($this->_output);
            break;

        case 3:
            if ($element == 'VerProto') {
                // </VerProto></SyncHdr></SyncML>
                if (trim($this->_chars) == 'SyncML/1.1') {
                    $this->_version = 1;
                } else {
                    $this->_version = 0;
                }
            } elseif ($element == 'SessionID') {
                // </SessionID></SyncHdr></SyncML>
                $this->_sessionID = trim($this->_chars);
            } elseif ($element == 'MsgID') {
                // </MsgID></SyncHdr></SyncML>
                $this->_msgID = intval(trim($this->_chars));
            } elseif ($element == 'Source') {
                // </Source></SyncHdr></SyncML>
                $this->_isSource = false;
            } elseif ($element == 'Cred') {
                // </Cred></SyncHdr></SyncML>
                $this->_isCred = false;

                //multisync does not specify the cred format
                //if ($this->_credFormat == 'b64') {
                $this->_credData = base64_decode($this->_credData);
                //}

                $tmp = split(':', $this->_credData);
                $this->_locName = $tmp[0];
                $this->_credData = $tmp[1];

                Horde::logMessage('SyncML: $this->_locName: ' . $this->_locName, __FILE__, __LINE__,  PEAR_LOG_DEBUG);
            }
            break;

        case 4:
            if ($element == 'LocURI') {
                if ($this->_isSource) {
                    // </LocURI></Source></SyncHdr></SyncML>
                    $this->_sourceURI = trim($this->_chars);
                } else {
                    // </LocURI></Target></SyncHdr></SyncML>
                    $this->_targetURI = trim($this->_chars);
                }
            } elseif ($element == 'LocName') {
                if ($this->_isSource) {
                    // </LocName></Source></SyncHdr></SyncML>
                    $this->_locName = trim($this->_chars);
                }
            } elseif ($element == 'Data') {
                    // </Data></Cred></SyncHdr></SyncML>
                if ($this->_isCred) {
                    $this->_credData = trim($this->_chars);
                }
            }
            break;
        case 5:
            if ($this->_isCred) {
                if ($element == 'Format') {
                    // </Format></Meta></Cred></SyncHdr></SyncML>
                    $this->_credFormat = trim($this->_chars);
                } elseif ($element == 'Type') {
                    // </Type></Meta></Cred></SyncHdr></SyncML>
                    $this->_credType = trim($this->_chars);
                }
            }
            break;
        }

        parent::endElement($uri, $element);
    }

    function outputSyncHdr(&$output)
    {
        $attrs = array();

        $state = $_SESSION['SyncML.state'];

        $uri = $state->getURI();
        $uriMeta = $state->getURIMeta();

        $output->startElement($uri, 'SyncHdr', $attrs);

        $output->startElement($uri, 'VerDTD', $attrs);
        $chars = ($this->_version == 1) ? '1.1' : '1.0';
        $output->characters($chars);
        $output->endElement($uri, 'VerDTD');

        $output->startElement($uri, 'VerProto', $attrs);
        $chars = ($this->_version == 1) ? 'SyncML/1.1' : 'SyncML/1.0';
        $output->characters($chars);
        $output->endElement($uri, 'VerProto');

        $output->startElement($uri, 'SessionID', $attrs);
        $output->characters($this->_sessionID);
        $output->endElement($uri, 'SessionID');

        $output->startElement($uri, 'MsgID', $attrs);
        $output->characters($this->_msgID);
        $output->endElement($uri, 'MsgID');

        $output->startElement($uri, 'Target', $attrs);
        $output->startElement($uri, 'LocURI', $attrs);
        $output->characters($this->_sourceURI);
        $output->endElement($uri, 'LocURI');

        if (isset($this->_locName)) {
            $output->startElement($uri, 'LocName', $attrs);
            $output->characters($this->_locName);
            $output->endElement($uri, 'LocName');
        }

        $output->endElement($uri, 'Target');

        $output->startElement($uri, 'Source', $attrs);
        $output->startElement($uri, 'LocURI', $attrs);
        $output->characters($this->_targetURI);
        $output->endElement($uri, 'LocURI');
        $output->endElement($uri, 'Source');

        $output->startElement($uri, 'Meta', $attrs);

        // Dummy Max MsqSize, this is just put in to make the packet
        // work, it is not a real value.
        $output->startElement($uriMeta, 'MaxMsgSize', $attrs);
        $chars = '50000';
        $output->characters($chars);
        $output->endElement($uriMeta, 'MaxMsgSize');

        // Dummy MaxObjSize, this is just put in to make the packet
        // work, it is not a real value.
        $output->startElement($uriMeta, 'MaxObjSize', $attrs);
        $chars = '4000000';
        $output->characters($chars);
        $output->endElement($uriMeta, 'MaxObjSize');

        $output->endElement($uri, 'Meta');
        $output->endElement($uri, 'SyncHdr');
    }

    function getSourceURI()
    {
        return $this->_sourceURI;
    }

    function getLocName()
    {
        return $this->_locName;
    }

    function getSessionID()
    {
        return $this->_sessionID;
    }

    function getVersion()
    {
        return $this->_version;
    }

    function getMsgID()
    {
        return $this->_msgID;
    }

    function getTargetURI()
    {
        return $this->_targetURI;
    }

    function opaque($o)
    {
    }

}

/**
 * Defined in SyncML Representation Protocol, version 1.1 5.2.3
 *
 * @package Horde_SyncML
 */
class Horde_SyncML_SyncMLBody extends Horde_SyncML_ContentHandler {

    var $_currentCmdID = 1;

    var $_currentCommand;

    function startElement($uri, $element, $attrs)
    {
        parent::startElement($uri, $element, $attrs);

        switch ($this->_xmlStack) {
        case 2:
            $state = $_SESSION['SyncML.state'];

            // <SyncML><SyncBody>
            $this->_output->startElement($uri, $element, $attrs);

            // Right our status about the header.
            $status = &new Horde_SyncML_Command_Status(($state->isAuthorized()) ?
                                                       RESPONSE_AUTHENTICATION_ACCEPTED : RESPONSE_INVALID_CREDENTIALS, 'SyncHdr');
            $status->setSourceRef($state->getSourceURI());
            $status->setTargetRef($state->getTargetURI());
            $status->setCmdRef(0);

            /*$str = 'authorized=' . $state->isAuthorized();
            $str .= ' version=' . $state->getVersion();
            $str .= ' msgid=' . $state->getMsgID();
            $str .= ' source=' . $state->getSourceURI();
            $str .= ' target=' . $state->getTargetURI();
            */
            $this->_currentCmdID = $status->output($this->_currentCmdID, $this->_output);
            break;

        case 3:
            // <SyncML><SyncBody><[Command]>
            $this->_currentCommand = Horde_SyncML_Command::factory($element);

            $this->_currentCommand->startElement($uri, $element, $attrs);
            break;

        default:
            // <SyncML><SyncBody><Command><...>
            $this->_currentCommand->startElement($uri, $element, $attrs);
            break;
        }
    }

    function endElement($uri, $element)
    {
        switch ($this->_xmlStack) {
        case 2:
            // </SyncBody></SyncML>
            $this->_output->endElement($uri, $element);
            break;

        case 3:
            // </[Command]></SyncBody></SyncML>
            $this->_currentCommand->endElement($uri, $element);

            $this->_currentCmdID = $this->_currentCommand->output($this->_currentCmdID, $this->_output);

            unset($this->_currentCommand);
            break;

        default:
            // </...></[Command]></SyncBody></SyncML>
            $this->_currentCommand->endElement($uri, $element);
            break;
        }

        parent::endElement($uri, $element);
    }

    function characters($str)
    {
        if (isset($this->_currentCommand)) {
            $this->_currentCommand->characters($str);
        }

    }

}
