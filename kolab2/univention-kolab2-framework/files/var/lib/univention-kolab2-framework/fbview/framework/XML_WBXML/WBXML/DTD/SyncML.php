<?php

include_once 'XML/WBXML/DTD.php';

/**
 * $Horde: framework/XML_WBXML/WBXML/DTD/SyncML.php,v 1.6 2004/01/01 15:14:46 jan Exp $
 *
 * From Binary XML Content Format Specification Version 1.3, 25 July 2001
 * found at http://www.wapforum.org
 *
 * Copyright 2003-2004 Anthony Mills <amills@pyramid6.com>
 *
 * See the enclosed file COPYING for license information (LGPL).  If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @package XML_WBXML
 */
class XML_WBXML_DTD_SyncML extends XML_WBXML_DTD {

    function init()
    {
        $this->setTag(5, 'Add');                       // 0x05
        $this->setTag(6, 'Alert');                     // 0x06
        $this->setTag(7, 'Archive');                   // 0x07
        $this->setTag(8, 'Atomic');                    // 0x08
        $this->setTag(9, 'Chal');                      // 0x09
        $this->setTag(10, 'Cmd');                      // 0x0A
        $this->setTag(11, 'CmdID');                    // 0x0B
        $this->setTag(12, 'CmdRef');                   // 0x0C
        $this->setTag(13, 'Copy');                     // 0x0D
        $this->setTag(14, 'Cred');                     // 0x0E
        $this->setTag(15, 'Data');                     // 0x0F

        $this->setTag(16, 'Delete');                   // 0x10
        $this->setTag(17, 'Exec');                     // 0x11
        $this->setTag(18, 'Final');                    // 0x12
        $this->setTag(19, 'Get');                      // 0x13
        $this->setTag(20, 'Item');                     // 0x14
        $this->setTag(21, 'Lang');                     // 0x15
        $this->setTag(22, 'LocName');                  // 0x16
        $this->setTag(23, 'LocURI');                   // 0x17
        $this->setTag(24, 'Map');                      // 0x18
        $this->setTag(25, 'MapItem');                  // 0x19
        $this->setTag(26, 'Meta');                     // 0x1A
        $this->setTag(27, 'MsgID');                    // 0x1B
        $this->setTag(28, 'MsgRef');                   // 0x1C
        $this->setTag(29, 'NoRssp');                   // 0x1D
        $this->setTag(30, 'NoResults');                // 0x1E
        $this->setTag(31, 'Put');                      // 0x1F

        $this->setTag(32, 'Replace');                  // 0x10
        $this->setTag(33, 'RespURI');                  // 0x21
        $this->setTag(34, 'Results');                  // 0x22
        $this->setTag(35, 'Search');                   // 0x23
        $this->setTag(36, 'Sequence');                 // 0x24
        $this->setTag(37, 'SessionID');                // 0x25
        $this->setTag(38, 'SftDel');                   // 0x26
        $this->setTag(39, 'Source');                   // 0x27
        $this->setTag(40, 'SourceRef');                // 0x28
        $this->setTag(41, 'Status');                   // 0x29
        $this->setTag(42, 'Sync');                     // 0x2A
        $this->setTag(43, 'SyncBody');                 // 0x2B
        $this->setTag(44, 'SyncHdr');                  // 0x2C
        $this->setTag(45, 'SyncML');                   // 0x2D
        $this->setTag(46, 'Target');                   // 0x2E
        $this->setTag(47, 'TargetRef');                // 0x2F

        $this->setTag(48, 'Reserved for future use.'); // 0x30
        $this->setTag(49, 'VerDTD');                   // 0x31
        $this->setTag(50, 'VerProto');                 // 0x32
        $this->setTag(51, 'NumberOfChanged');          // 0x33
        $this->setTag(52, 'MoreData');                 // 0x34

        if ($this->version == 0) {
            $this->setCodePage(0, '-//SYNCML//DTD SyncML 1.0//EN', 'syncml:syncml');
            $this->setCodePage(1, '-//SYNCML//DTD MetInf 1.0//EN', 'syncml:metinf');
            $this->setURI('syncml:syncml');
        } else {
            $this->setCodePage(0, '-//SYNCML//DTD SyncML 1.1//EN', 'syncml:syncml1.1');
            $this->setCodePage(1, '-//SYNCML//DTD MetInf 1.1//EN', 'syncml:metinf1.1');
            $this->setURI('syncml:syncml1.1');
        }
    }

}
