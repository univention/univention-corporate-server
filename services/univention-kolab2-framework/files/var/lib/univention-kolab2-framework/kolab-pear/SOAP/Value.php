<?php
//
// +----------------------------------------------------------------------+
// | PHP Version 4                                                        |
// +----------------------------------------------------------------------+
// | Copyright (c) 1997-2003 The PHP Group                                |
// +----------------------------------------------------------------------+
// | This source file is subject to version 2.02 of the PHP license,      |
// | that is bundled with this package in the file LICENSE, and is        |
// | available at through the world-wide-web at                           |
// | http://www.php.net/license/2_02.txt.                                 |
// | If you did not receive a copy of the PHP license and are unable to   |
// | obtain it through the world-wide-web, please send a note to          |
// | license@php.net so we can mail you a copy immediately.               |
// +----------------------------------------------------------------------+
// | Authors: Shane Caraveo <Shane@Caraveo.com>   Port to PEAR and more   |
// | Authors: Dietrich Ayala <dietrich@ganx4.com> Original Author         |
// +----------------------------------------------------------------------+
//
// $Id: Value.php,v 1.1.2.1 2005/10/05 14:39:47 steuwer Exp $
//
require_once 'SOAP/Base.php';

/**
*  SOAP::Value
* this class converts values between PHP and SOAP
*
* originaly based on SOAPx4 by Dietrich Ayala http://dietrich.ganx4.com/soapx4
*
* @access public
* @version $Id: Value.php,v 1.1.2.1 2005/10/05 14:39:47 steuwer Exp $
* @package SOAP::Client
* @author Shane Caraveo <shane@php.net> Conversion to PEAR and updates
* @author Dietrich Ayala <dietrich@ganx4.com> Original Author
*/
class SOAP_Value
{
    /**
    *
    *
    * @var  string
    */
    var $value = NULL;
    
    /**
    *
    * @var  string
    */
    var $name = '';
    
    /**
    *
    * @var  string
    */
    var $type = '';
    
    /**
    * Namespace
    *
    * @var  string
    */
    var $namespace = '';
    var $type_namespace = '';
    
    var $attributes = array();

    /**
    *
    * @var string
    */
    var $arrayType = '';
    
    var $options = array();

    var $nqn;
    var $tqn;
    /**
    *
    *
    * @param    string  name of the soap-value {namespace}name
    * @param    mixed   soap value {namespace}type, if not set an automatic 
    * @param    mixed   value to set
    */
    function SOAP_Value($name = '', $type = false, $value=NULL, $attributes = array())
    {
        // detect type if not passed
        $this->nqn =& new QName($name);
        $this->name = $this->nqn->name;
        $this->namespace = $this->nqn->namespace;
        $this->tqn =& new QName($type);
        $this->type = $this->tqn->name;
        $this->type_prefix = $this->tqn->ns;
        $this->type_namespace = $this->tqn->namespace;
        $this->value =& $value;
        $this->attributes = $attributes;
    }
    
    /**
    * Serialize
    * 
    * @return   string  xml representation
    */
    function &serialize(&$serializer)
    {
        return $serializer->_serializeValue($this->value, $this->name, $this->type, $this->namespace, $this->type_namespace, $this->options, $this->attributes, $this->arrayType);
    }
}


/**
 *  SOAP::Header
 * this class converts values between PHP and SOAP
 * it is a simple wrapper around SOAP_Value, adding support for
 * soap actor and mustunderstand parameters
 *
 * originaly based on SOAPx4 by Dietrich Ayala http://dietrich.ganx4.com/soapx4
 *
 * @access public
 * @version $Id: Value.php,v 1.1.2.1 2005/10/05 14:39:47 steuwer Exp $
 * @package SOAP::Header
 * @author Shane Caraveo <shane@php.net> Conversion to PEAR and updates
 * @author Dietrich Ayala <dietrich@ganx4.com> Original Author
 */
class SOAP_Header extends SOAP_Value
{

    /**
     * Constructor
     *
     * @param    string  name of the soap-value <value_name>
     * @param    mixed   soap header value
     * @param    string namespace
     * @param    int mustunderstand (zero or one)
     * @param    string actor
     */
    function SOAP_Header($name = '', $type, $value,
                         $mustunderstand = 0,
                         $actor = 'http://schemas.xmlsoap.org/soap/actor/next')
    {
        parent::SOAP_Value($name, $type, $value);
        $this->attributes['SOAP-ENV:actor'] = $actor;
        $this->attributes['SOAP-ENV:mustUnderstand'] = (int)$mustunderstand;
    }
}

/**
 *  SOAP::Attachment
 * this class converts values between PHP and SOAP
 * it handles Mime attachements per W3C Note on Soap Attachements at
 * http://www.w3.org/TR/SOAP-attachments
 *
 *
 * @access public
 * @package SOAP::Attachment
 * @author Shane Caraveo <shane@php.net> Conversion to PEAR and updates
 */
class SOAP_Attachment extends SOAP_Value
{

    /**
     * Constructor
     *
     * @param    string  name of the soap-value <value_name>
     * @param    mixed   soap header value
     * @param    string namespace
     */
    function SOAP_Attachment($name = '', $type = 'application/octet-stream',
                             $filename, $file=NULL)
    {
        global $SOAP_options;
        if (!isset($SOAP_options['Mime'])) {
            return PEAR::raiseError('Mail_mime is not installed, unable to support SOAP Attachements');
        }
        parent::SOAP_Value($name, NULL, NULL);
        
        $filedata = ($file === NULL) ? $this->_file2str($filename) : $file;
        $filename = basename($filename);
        if (PEAR::isError($filedata)) {
            return $filedata;
        }
        
        $cid = md5(uniqid(time()));
        
        $this->attributes['href'] = 'cid:'.$cid;
        
        $this->options['attachment'] = array(
                                'body'     => $filedata,
                                'disposition'     => $filename,
                                'content_type'   => $type,
                                'encoding' => 'base64',
                                'cid' => $cid
                               );
    }

    /*
    * Returns the contents of the given file name as string
    * @param string $file_name
    * @return string
    * @acces private
    */
    function & _file2str($file_name)
    {
        if (!is_readable($file_name)) {
            return PEAR::raiseError('File is not readable ' . $file_name);
        }
        if (!$fd = fopen($file_name, 'rb')) {
            return PEAR::raiseError('Could not open ' . $file_name);
        }
        $cont = fread($fd, filesize($file_name));
        fclose($fd);
        return $cont;
    }
}
?>