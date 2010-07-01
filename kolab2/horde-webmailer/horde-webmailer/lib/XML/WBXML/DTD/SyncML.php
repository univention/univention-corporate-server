<?php

include_once 'XML/WBXML/DTD.php';

/**
 * From Binary XML Content Format Specification Version 1.3, 25 July 2001
 * found at http://www.wapforum.org
 *
 * $Horde: framework/XML_WBXML/WBXML/DTD/SyncML.php,v 1.6.12.9 2009-01-06 15:23:50 jan Exp $
 *
 * Copyright 2003-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Anthony Mills <amills@pyramid6.com>
 * @package XML_WBXML
 */
class XML_WBXML_DTD_SyncML extends XML_WBXML_DTD {

    function init()
    {
        /* this code table has been extracted from libwbxml
         * (see http://libwbxml.aymerick.com/) by using
         *
         * grep '\"[^\"]*\", *0x.., 0x.. },' wbxml_tables.c
         * | sed -e 's#^.*\"\([^\"]*\)\", *\(0x..\), \(0x..\) },.*$#        \$this->setTag\(\3, \"\1\"\); // \2#g'
         */

        $this->setTag(0x05, "Add"); // 0x00
        $this->setTag(0x06, "Alert"); // 0x00
        $this->setTag(0x07, "Archive"); // 0x00
        $this->setTag(0x08, "Atomic"); // 0x00
        $this->setTag(0x09, "Chal"); // 0x00
        $this->setTag(0x0a, "Cmd"); // 0x00
        $this->setTag(0x0b, "CmdID"); // 0x00
        $this->setTag(0x0c, "CmdRef"); // 0x00
        $this->setTag(0x0d, "Copy"); // 0x00
        $this->setTag(0x0e, "Cred"); // 0x00
        $this->setTag(0x0f, "Data"); // 0x00
        $this->setTag(0x10, "Delete"); // 0x00
        $this->setTag(0x11, "Exec"); // 0x00
        $this->setTag(0x12, "Final"); // 0x00
        $this->setTag(0x13, "Get"); // 0x00
        $this->setTag(0x14, "Item"); // 0x00
        $this->setTag(0x15, "Lang"); // 0x00
        $this->setTag(0x16, "LocName"); // 0x00
        $this->setTag(0x17, "LocURI"); // 0x00
        $this->setTag(0x18, "Map"); // 0x00
        $this->setTag(0x19, "MapItem"); // 0x00
        $this->setTag(0x1a, "Meta"); // 0x00
        $this->setTag(0x1b, "MsgID"); // 0x00
        $this->setTag(0x1c, "MsgRef"); // 0x00
        $this->setTag(0x1d, "NoResp"); // 0x00
        $this->setTag(0x1e, "NoResults"); // 0x00
        $this->setTag(0x1f, "Put"); // 0x00
        $this->setTag(0x20, "Replace"); // 0x00
        $this->setTag(0x21, "RespURI"); // 0x00
        $this->setTag(0x22, "Results"); // 0x00
        $this->setTag(0x23, "Search"); // 0x00
        $this->setTag(0x24, "Sequence"); // 0x00
        $this->setTag(0x25, "SessionID"); // 0x00
        $this->setTag(0x26, "SftDel"); // 0x00
        $this->setTag(0x27, "Source"); // 0x00
        $this->setTag(0x28, "SourceRef"); // 0x00
        $this->setTag(0x29, "Status"); // 0x00
        $this->setTag(0x2a, "Sync"); // 0x00
        $this->setTag(0x2b, "SyncBody"); // 0x00
        $this->setTag(0x2c, "SyncHdr"); // 0x00
        $this->setTag(0x2d, "SyncML"); // 0x00
        $this->setTag(0x2e, "Target"); // 0x00
        $this->setTag(0x2f, "TargetRef"); // 0x00
        $this->setTag(0x30, "Reserved for future use"); // 0x00
        $this->setTag(0x31, "VerDTD"); // 0x00
        $this->setTag(0x32, "VerProto"); // 0x00
        $this->setTag(0x33, "NumberOfChanges"); // 0x00
        $this->setTag(0x34, "MoreData"); // 0x00
        $this->setTag(0x35, "Field"); // 0x00
        $this->setTag(0x36, "Filter"); // 0x00
        $this->setTag(0x37, "Record"); // 0x00
        $this->setTag(0x38, "FilterType"); // 0x00
        $this->setTag(0x39, "SourceParent"); // 0x00
        $this->setTag(0x3a, "TargetParent"); // 0x00
        $this->setTag(0x3b, "Move"); // 0x00
        $this->setTag(0x3c, "Correlator"); // 0x00

        if ($this->version == 1) {
            $this->setCodePage(0, DPI_DTD_SYNCML_1_1, 'syncml:syncml1.1');
            $this->setCodePage(1, DPI_DTD_METINF_1_1, 'syncml:metinf1.1');
            $this->setURI('syncml:syncml1.1');
        } elseif ($this->version == 2) {
            $this->setCodePage(0, DPI_DTD_SYNCML_1_2, 'syncml:syncml1.2');
            $this->setCodePage(1, DPI_DTD_METINF_1_2, 'syncml:metinf1.2');
            $this->setURI('syncml:syncml1.2');
        } else {
            $this->setCodePage(0, DPI_DTD_SYNCML_1_0, 'syncml:syncml1.0');
            $this->setCodePage(1, DPI_DTD_METINF_1_0, 'syncml:metinf1.0');
            $this->setURI('syncml:syncml1.0');
        }
    }

}
