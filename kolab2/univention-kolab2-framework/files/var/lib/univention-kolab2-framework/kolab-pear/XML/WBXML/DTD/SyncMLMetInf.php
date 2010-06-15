<?php

include_once 'XML/WBXML/DTD.php';

/**
 * $Horde: framework/XML_WBXML/WBXML/DTD/SyncMLMetInf.php,v 1.4 2004/01/01 15:14:46 jan Exp $
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
class XML_WBXML_DTD_SyncMLMetInf extends XML_WBXML_DTD {

    function init()
    {
        $this->setTag(5, 'Anchor');      // 0x05
        $this->setTag(6, 'EMI');         // 0x06
        $this->setTag(7, 'Format');      // 0x07
        $this->setTag(8, 'FreeID');      // 0x08
        $this->setTag(9, 'FreeMem');     // 0x09
        $this->setTag(10, 'Last');       // 0x0A
        $this->setTag(11, 'Mark');       // 0x0B
        $this->setTag(12, 'MaxMsgSize'); // 0x0C
        $this->setTag(13, 'Mem');        // 0x0D
        $this->setTag(14, 'MetInf');     // 0x0E
        $this->setTag(15, 'Next');       // 0x0F
        $this->setTag(16, 'NextNonce');  // 0x10
        $this->setTag(17, 'SharedMem');  // 0x11
        $this->setTag(18, 'Size');       // 0x12
        $this->setTag(19, 'Type');       // 0x13
        $this->setTag(20, 'Version');    // 0x14
        $this->setTag(21, 'MaxObjSize'); // 0x15

        if ($this->version == 0) {
            $this->setCodePage(0, '-//SYNCML//DTD SyncML 1.0//EN', 'syncml:syncml');
            $this->setCodePage(1, '-//SYNCML//DTD MetInf 1.0//EN', 'syncml:metinf');
            $this->setURI('syncml:metinf');
        } else {
            $this->setCodePage(0, '-//SYNCML//DTD SyncML 1.1//EN', 'syncml:syncml1.1');
            $this->setCodePage(1, '-//SYNCML//DTD MetInf 1.1//EN', 'syncml:metinf1.1');
            $this->setURI('syncml:metinf1.1');
        }
    }

}
