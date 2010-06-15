<?php

include_once 'XML/WBXML/DTD/SyncML.php';
include_once 'XML/WBXML/DTD/SyncMLMetInf.php';
include_once 'XML/WBXML/DTD/SyncMLDevInf.php';

/**
 * $Horde: framework/XML_WBXML/WBXML/DTDManager.php,v 1.3 2004/01/01 15:14:45 jan Exp $
 *
 * Copyright 2003-2004 Anthony Mills <amills@pyramid6.com>
 *
 * See the enclosed file COPYING for license information (LGPL).  If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * From Binary XML Content Format Specification Version 1.3, 25 July
 * 2001 found at http://www.wapforum.org
 *
 * @package XML_WBXML
 */
class XML_WBXML_DTDManager {

    var $_strDTD = array();
    var $_strDTDURI = array();

    function XML_WBXML_DTDManager()
    {
        $this->registerDTD('-//SYNCML//DTD SyncML 1.0//EN', 'syncml:syncml', new XML_WBXML_DTD_SyncML(0));
        $this->registerDTD('-//SYNCML//DTD SyncML 1.1//EN', 'syncml:syncml1.1', new XML_WBXML_DTD_SyncML(1));

        $this->registerDTD('-//SYNCML//DTD MetInf 1.0//EN', 'syncml:metinf', new XML_WBXML_DTD_SyncMLMetInf(0));
        $this->registerDTD('-//SYNCML//DTD MetInf 1.1//EN', 'syncml:metinf1.1', new XML_WBXML_DTD_SyncMLMetInf(1));

        $this->registerDTD('-//SYNCML//DTD DevInf 1.0//EN', 'syncml:devinf', new XML_WBXML_DTD_SyncMLDevInf(0));
        $this->registerDTD('-//SYNCML//DTD DevInf 1.1//EN', 'syncml:devinf1.1', new XML_WBXML_DTD_SyncMLDevInf(1));
    }

    function getInstance($publicIdentifier)
    {
        return isset($this->_strDTD[$publicIdentifier]) ? $this->_strDTD[$publicIdentifier] : null;
    }

    function getInstanceURI($uri)
    {
        $uri = strtolower($uri);
        return isset($this->_strDTDURI[$uri]) ? $this->_strDTDURI[$uri] : null;
    }

    function registerDTD($publicIdentifier, $uri, &$dtd)
    {
        $dtd->setDPI($publicIdentifier);

        $this->_strDTD[$publicIdentifier] = $dtd;
        $this->_strDTDURI[$uri] = $dtd;
    }

}
