<?php
/**
 * The class SyncML_Command_SyncElement stores information from the <Add>,
 * <Delete> and <Replace> elements found inside a <Sync> command.
 *
 * Instances of this class are created during the XML parsing by
 * SyncML_Command_Sync.
 *
 * $Horde: framework/SyncML/SyncML/Command/SyncElement.php,v 1.3.2.10 2009-04-05 20:24:43 jan Exp $
 *
 * Copyright 2005-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Karsten Fourmont <karsten@horde.org>
 * @author  Jan Schneider <jan@horde.org>
 * @since   Horde 3.0.5
 * @package SyncML
 */
class SyncML_SyncElement {

    /**
     * The MIME content type of the sync command.
     *
     * @var string
     */
    var $contentType;

    /**
     * Encoding format of the content as specified in the <Meta><Format>
     * element, like 'b64'.
     *
     * @var string
     */
    var $contentFormat;

    /**
     * The actual data content of the sync command.
     *
     * @var string $content
     */
    var $content = '';

    /**
     * The size of the data item of the sync command in bytes as specified by
     * a <Size> element.
     *
     * @var integer
     */
    var $size;

    /**
     * The command ID (<CmdID>) of the sync command.
     *
     * @var integer
     */
    var $cmdID;

    /**
     * Name of the sync command, like 'Add'.
     *
     * @var string
     */
    var $elementType;

    /**
     * The client ID for the data item processed in the sync command.
     *
     * @var string
     */
    var $cuid;

    /**
     * The code to be sent as status response in a <Status> element, one of
     * the RESPONSE_* constants.
     *
     * This is set in SyncML_Sync::handleClientSyncItem() when "processing"
     * the item.
     *
     * @var integer
     */
    var $responseCode;

    /**
     * The Sync object for this element is part of.
     *
     * @var object SyncML_Sync
     */
    var $sync;

    /**
     * Constructor.
     *
     * @param SyncML_Sync $sync
     * @param string $elementType
     * @param integer $cmdID
     * @param integer $size
     */
    function SyncML_SyncElement(&$sync, $elementType, $cmdID, $size)
    {
        $this->sync = &$sync;
        $this->elementType = $elementType;
        $this->cmdID = $cmdID;
        $this->size = $size;
    }

}

