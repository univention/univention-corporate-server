<?php

include_once 'XML/WBXML/DTD.php';

/**
 * $Horde: framework/XML_WBXML/WBXML/DTD/SyncMLDevInf.php,v 1.4 2004/01/01 15:14:46 jan Exp $
 *
 * Copyright 2003-2004 Anthony Mills <amills@pyramid6.com>
 *
 * From Binary XML Content Format Specification Version 1.3, 25 July 2001
 * found at http://www.wapforum.org
 *
 * See the enclosed file COPYING for license information (LGPL).  If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @package XML_WBXML
 */
class XML_WBXML_DTD_SyncMLDevInf extends XML_WBXML_DTD {

    function init()
    {
        $this->setTag(5, 'CTCap');                   // 0x05
        $this->setTag(6, 'CTType');                  // 0x06
        $this->setTag(7, 'DataStore');               // 0x07
        $this->setTag(8, 'DataType');                // 0x08
        $this->setTag(9, 'DevID');                   // 0x09
        $this->setTag(10, 'DevInf');                 // 0x0A
        $this->setTag(11, 'DevTyp');                 // 0x0B
        $this->setTag(12, 'DisplayName');            // 0x0C
        $this->setTag(13, 'DSMem');                  // 0x0D
        $this->setTag(14, 'Ext');                    // 0x0E
        $this->setTag(15, 'FwV');                    // 0x0F
        $this->setTag(16, 'HwV');                    // 0x10
        $this->setTag(17, 'Man');                    // 0x11
        $this->setTag(18, 'MaxGUIDSize');            // 0x12
        $this->setTag(19, 'MaxID');                  // 0x13
        $this->setTag(20, 'MaxMem');                 // 0x14
        $this->setTag(21, 'Mod');                    // 0x15
        $this->setTag(22, 'OEM');                    // 0x15
        $this->setTag(23, 'ParamName');              // 0x17
        $this->setTag(24, 'PropName');               // 0x18
        $this->setTag(25, 'Rx');                     // 0x19
        $this->setTag(26, 'Rx-Pref');                // 0x1A
        $this->setTag(27, 'SharedMem');              // 0x1B
        $this->setTag(28, 'Size');                   // 0x1C
        $this->setTag(29, 'SourceRef');              // 0x1D
        $this->setTag(30, 'SwV');                    // 0x1E
        $this->setTag(31, 'SyncCap');                // 0x1F
        $this->setTag(32, 'SyncType');               // 0x20
        $this->setTag(33, 'Tx');                     // 0x21
        $this->setTag(34, 'Tx-Pref');                // 0x22
        $this->setTag(35, 'ValEnum');                // 0x23
        $this->setTag(36, 'VerCT');                  // 0x24
        $this->setTag(37, 'VerDTD');                 // 0x25
        $this->setTag(38, 'Xnam');                   // 0x26
        $this->setTag(39, 'Xval');                   // 0x27
        $this->setTag(40, 'UTC');                    // 0x28
        $this->setTag(41, 'SupportNumberOfChanges'); // 0x29
        $this->setTag(42, 'SupportLargeObjs');       // 0x2A

        if ($this->version == 0) {
            $this->setCodePage(0, '-//SYNCML//DTD DevInf 1.0//EN', 'syncml:devinf');
            $this->setURI('sync:devinf');
        } else {
            $this->setCodePage(0, '-//SYNCML//DTD DevInf 1.1//EN', 'syncml:devinf1.1');
            $this->setURI('sync:devinf1.1');
        }
    }

}
