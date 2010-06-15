<?php

include_once 'Horde/SyncML/State.php';
include_once 'Horde/SyncML/Command.php';

/**
 * The Horde_SyncML_Alert class provides a SyncML implementation of
 * the Alert command as defined in SyncML Representation Protocol,
 * version 1.1 5.5.2.
 *
 * $Horde: framework/SyncML/SyncML/Command/Alert.php,v 1.16 2004/05/26 17:41:30 chuck Exp $
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
class Horde_SyncML_Command_Alert extends Horde_SyncML_Command {

    /**
     * @var integer $_alert
     */
    var $_alert;

    /**
     * @var string $_sourceURI
     */
    var $_sourceLocURI;

    /**
     * @var string $_targetURI
     */
    var $_targetLocURI;

    /**
     * @var string $_metaAnchorNext
     */
    var $_metaAnchorNext;

    /**
     * @var integer $_metaAnchorLast
     */
    var $_metaAnchorLast;

    /**
     * @var integer $_alert
     */
    var $_outputMetaAnchorNext;

    /**
     * @var integer $_alert
     */
    var $_outputMetaAnchorLast;

    /**
     * Use in xml tag.
     */
    var $_isInSource;

    /**
     * Creates a new instance of Alert.
     */
    function Horde_SyncML_Command_Alert($alert = null)
    {
        if ($alert != null) {
            $this->_alert = $alert;
        }
    }

    function output($currentCmdID, &$output)
    {
        $attrs = array();

        $state = $_SESSION['SyncML.state'];

        $status = &new Horde_SyncML_Command_Status($state->isAuthorized() ? RESPONSE_OK : RESPONSE_INVALID_CREDENTIALS, 'Alert');
        $status->setCmdRef($this->_cmdID);

        if ($state->isAuthorized() && isset($this->_metaAnchorNext)) {
            $status->setItemDataAnchorNext($this->_metaAnchorNext);
        }

        $currentCmdID = $status->output($currentCmdID, $output);

        if ($state->isAuthorized()) {
            $output->startElement($state->getURI(), 'Alert', $attrs);

            $output->startElement($state->getURI(), 'CmdID', $attrs);
            $chars = $currentCmdID;
            $output->characters($chars);
            $output->endElement($state->getURI(), 'CmdID');

            $output->startElement($state->getURI(), 'Data', $attrs);
            $chars = $this->_alert;
            $output->characters($chars);
            $output->endElement($state->getURI(), 'Data');

            $output->startElement($state->getURI(), 'Item', $attrs);

            if ($this->_sourceLocURI != null) {
                $output->startElement($state->getURI(), 'Target', $attrs);
                $output->startElement($state->getURI(), 'LocURI', $attrs);
                $chars = $this->_sourceLocURI;
                $output->characters($chars);
                $output->endElement($state->getURI(), 'LocURI');
                $output->endElement($state->getURI(), 'Target');
            }

            if ($this->_targetLocURI != null) {
                $output->startElement($state->getURI(), 'Source', $attrs);
                $output->startElement($state->getURI(), 'LocURI', $attrs);
                $chars = $this->_targetLocURI;
                $output->characters($chars);
                $output->endElement($state->getURI(), 'LocURI');
                $output->endElement($state->getURI(), 'Source');
            }

            $output->startElement($state->getURI(), 'Meta', $attrs);

            $output->startElement($state->getURIMeta(), 'Anchor', $attrs);

            if (isset($this->_outputMetaAnchorLast)) {
                $output->startElement($state->getURIMeta(), 'Last', $attrs);
                $chars = $this->_outputMetaAnchorLast;
                $output->characters($chars);
                $output->endElement($state->getURIMeta(), 'Last');
            }

            if (isset($this->_outputMetaAnchorNext)) {
                $output->startElement($state->getURIMeta(), 'Next', $attrs);
                $chars = $this->_outputMetaAnchorNext;
                $output->characters($chars);
                $output->endElement($state->getURIMeta(), 'Next');
            }

            $output->endElement($state->getURIMeta(), 'Anchor');
            $output->endElement($state->getURI(), 'Meta');
            $output->endElement($state->getURI(), 'Item');
            $output->endElement($state->getURI(), 'Alert');

            $currentCmdID++;
        }

        return $currentCmdID;
    }

    /**
     * Setter for property sourceURI.
     *
     * @param string $sourceURI  New value of property sourceURI.
     */
    function setSourceLocURI($sourceURI)
    {
        $this->_sourceURI = $sourceURI;
    }

    function getTargetLocURI()
    {
        return $this->_targetURI;
    }

    /**
     * Setter for property targetURI.
     *
     * @param string $targetURI  New value of property targetURI.
     */
    function setTargetURI($targetURI)
    {
        $this->_targetURI = $targetURI;
    }

    function startElement($uri, $element, $attrs)
    {
        parent::startElement($uri, $element, $attrs);

        switch ($this->_xmlStack) {
        case 3:
            if ($element == 'Target') {
                $this->_isInSource = false;
            } else {
                $this->_isInSource = true;
            }
            break;
        }
    }

    function endElement($uri, $element)
    {
        switch ($this->_xmlStack) {
        case 1:
            $state = $_SESSION['SyncML.state'];
            Horde::logMessage('looking for sync for: ' . $this->_targetLocURI, __FILE__, __LINE__,  PEAR_LOG_DEBUG);
            $sync = $state->getSync($this->_targetLocURI);

            if (!$sync) {
                Horde::logMessage('create new sync for: ' . $this->_targetLocURI . ' ' . $this->_alert, __FILE__, __LINE__,  PEAR_LOG_DEBUG);
                $sync = &Horde_SyncML_Sync::factory($this->_alert);
                $state->setSync($this->_targetLocURI, $sync);
            }

            $_SESSION['SyncML.state'] = $state;
            break;

        case 2:
            if ($element == 'Data') {
                $this->_alert = intval(trim($this->_chars));
            }
            break;

        case 4:
            if ($element == 'LocURI') {
                Horde::logMessage('<'. $element . ' stack ' . $this->_xmlStack . ' source ' . $this->_isInSource, __FILE__, __LINE__, PEAR_LOG_DEBUG);
                if ($this->_isInSource) {
                    $this->_sourceLocURI = trim($this->_chars);
                } else {
                    $this->_targetLocURI = trim($this->_chars);
                }
            }
            break;

        case 5:
            if ($element == 'Next') {
                $this->_metaAnchorNext = trim($this->_chars);
                $this->_outputMetaAnchorNext = $this->_metaAnchorNext;
            }
            break;
        }

        parent::endElement($uri, $element);
    }

    function getAlert()
    {
        return $this->_alert;
    }

    function setAlet($alert)
    {
        $this->_alert = $alert;
    }

}
