<?php

include_once 'XML/WBXML/DTD/SyncML.php';
include_once 'XML/WBXML/DTD/SyncMLMetInf.php';
include_once 'XML/WBXML/DTD/SyncMLDevInf.php';

/**
 * From Binary XML Content Format Specification Version 1.3, 25 July 2001
 * found at http://www.wapforum.org
 *
 * $Horde: framework/XML_WBXML/WBXML/DTDManager.php,v 1.3.12.15 2009-01-06 15:23:50 jan Exp $
 *
 * Copyright 2003-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Anthony Mills <amills@pyramid6.com>
 * @package XML_WBXML
 */
class XML_WBXML_DTDManager {

    /**
     * @var array
     */
    var $_strDTD = array();

    /**
     * @var array
     */
    var $_strDTDURI = array();

    /**
     */
    function XML_WBXML_DTDManager()
    {
        $this->registerDTD(DPI_DTD_SYNCML_1_0, 'syncml:syncml1.0', new XML_WBXML_DTD_SyncML(0));
        $this->registerDTD(DPI_DTD_SYNCML_1_1, 'syncml:syncml1.1', new XML_WBXML_DTD_SyncML(1));
        $this->registerDTD(DPI_DTD_SYNCML_1_2, 'syncml:syncml1.2', new XML_WBXML_DTD_SyncML(2));

        $this->registerDTD(DPI_DTD_METINF_1_0, 'syncml:metinf1.0', new XML_WBXML_DTD_SyncMLMetInf(0));
        $this->registerDTD(DPI_DTD_METINF_1_1, 'syncml:metinf1.1', new XML_WBXML_DTD_SyncMLMetInf(1));
        $this->registerDTD(DPI_DTD_METINF_1_2, 'syncml:metinf1.2', new XML_WBXML_DTD_SyncMLMetInf(2));

        $this->registerDTD(DPI_DTD_DEVINF_1_0, 'syncml:devinf1.0', new XML_WBXML_DTD_SyncMLDevInf(0));
        $this->registerDTD(DPI_DTD_DEVINF_1_1, 'syncml:devinf1.1', new XML_WBXML_DTD_SyncMLDevInf(1));
        $this->registerDTD(DPI_DTD_DEVINF_1_2, 'syncml:devinf1.2', new XML_WBXML_DTD_SyncMLDevInf(2));
    }

    /**
     */
    function &getInstance($publicIdentifier)
    {
        $publicIdentifier = strtolower($publicIdentifier);
        if (isset($this->_strDTD[$publicIdentifier])) {
            $dtd = &$this->_strDTD[$publicIdentifier];
        } else {
            $dtd = null;
        }
        return $dtd;
    }

    /**
     */
    function &getInstanceURI($uri)
    {
        $uri = strtolower($uri);

        // some manual hacks:
        if ($uri == 'syncml:syncml') {
            $uri = 'syncml:syncml1.0';
        }
        if ($uri == 'syncml:metinf') {
            $uri = 'syncml:metinf1.0';
        }
        if ($uri == 'syncml:devinf') {
            $uri = 'syncml:devinf1.0';
        }

        if (isset($this->_strDTDURI[$uri])) {
            $dtd = &$this->_strDTDURI[$uri];
        } else {
            $dtd = null;
        }
        return $dtd;
    }

    /**
     */
    function registerDTD($publicIdentifier, $uri, &$dtd)
    {
        $dtd->setDPI($publicIdentifier);

        $publicIdentifier = strtolower($publicIdentifier);

        $this->_strDTD[$publicIdentifier] = $dtd;
        $this->_strDTDURI[strtolower($uri)] = $dtd;
    }

}
