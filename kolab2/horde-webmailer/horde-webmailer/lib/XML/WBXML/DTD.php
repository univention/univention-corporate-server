<?php
/**
 * From Binary XML Content Format Specification Version 1.3, 25 July 2001
 * found at http://www.wapforum.org
 *
 * $Horde: framework/XML_WBXML/WBXML/DTD.php,v 1.6.12.9 2009-01-06 15:23:50 jan Exp $
 *
 * Copyright 2003-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Anthony Mills <amills@pyramid6.com>
 * @package XML_WBXML
 */
class XML_WBXML_DTD {

    var $version;
    var $intTags;
    var $intAttributes;
    var $strTags;
    var $strAttributes;
    var $intCodePages;
    var $strCodePages;
    var $strCodePagesURI;
    var $URI;
    var $XMLNS;
    var $DPI;

    function XML_WBXML_DTD($v)
    {
        $this->version = $v;
        $this->init();
    }

    function init()
    {
    }

    function setAttribute($intAttribute, $strAttribute)
    {
        $this->strAttributes[$strAttribute] = $intAttribute;
        $this->intAttributes[$intAttribute] = $strAttribute;
    }

    function setTag($intTag, $strTag)
    {
        $this->strTags[$strTag] = $intTag;
        $this->intTags[$intTag] = $strTag;
    }

    function setCodePage($intCodePage, $strCodePage, $strCodePageURI)
    {
        $this->strCodePagesURI[$strCodePageURI] = $intCodePage;
        $this->strCodePages[$strCodePage] = $intCodePage;
        $this->intCodePages[$intCodePage] = $strCodePage;
    }

    function toTagStr($tag)
    {
        return isset($this->intTags[$tag]) ? $this->intTags[$tag] : false;
    }

    function toAttributeStr($attribute)
    {
        return isset($this->intTags[$attribute]) ? $this->intTags[$attribute] : false;
    }

    function toCodePageStr($codePage)
    {
        return isset($this->intCodePages[$codePage]) ? $this->intCodePages[$codePage] : false;
    }

    function toTagInt($tag)
    {
        return isset($this->strTags[$tag]) ? $this->strTags[$tag] : false;
    }

    function toAttributeInt($attribute)
    {
        return isset($this->strAttributes[$attribute]) ? $this->strAttributes[$attribute] : false;
    }

    function toCodePageInt($codePage)
    {
        return isset($this->strCodePages[$codePage]) ? $this->strCodePages[$codePage] : false;
    }

    function toCodePageURI($uri)
    {
        $uri = strtolower($uri);
        if (!isset($this->strCodePagesURI[$uri])) {
            die("unable to find codepage for $uri!\n");
        }

        $ret = isset($this->strCodePagesURI[$uri]) ? $this->strCodePagesURI[$uri] : false;

        return $ret;
    }

    /**
     * Getter for property version.
     * @return Value of property version.
     */
    function getVersion()
    {
        return $this->version;
    }

    /**
     * Setter for property version.
     * @param integer $v  New value of property version.
     */
    function setVersion($v)
    {
        $this->version = $v;
    }

    /**
     * Getter for property URI.
     * @return Value of property URI.
     */
    function getURI()
    {
        return $this->URI;
    }

    /**
     * Setter for property URI.
     * @param string $u  New value of property URI.
     */
    function setURI($u)
    {
        $this->URI = $u;
    }

    /**
     * Getter for property DPI.
     * @return Value of property DPI.
     */
    function getDPI()
    {
        return $this->DPI;
    }

    /**
     * Setter for property DPI.
     * @param DPI New value of property DPI.
     */
    function setDPI($d)
    {
        $this->DPI = $d;
    }

}
