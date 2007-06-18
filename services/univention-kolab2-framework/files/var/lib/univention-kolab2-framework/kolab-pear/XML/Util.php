<?PHP
/* vim: set expandtab tabstop=4 shiftwidth=4: */
// +----------------------------------------------------------------------+
// | PHP Version 4                                                        |
// +----------------------------------------------------------------------+
// | Copyright (c) 1997-2002 The PHP Group                                |
// +----------------------------------------------------------------------+
// | This source file is subject to version 2.0 of the PHP license,       |
// | that is bundled with this package in the file LICENSE, and is        |
// | available at through the world-wide-web at                           |
// | http://www.php.net/license/2_02.txt.                                 |
// | If you did not receive a copy of the PHP license and are unable to   |
// | obtain it through the world-wide-web, please send a note to          |
// | license@php.net so we can mail you a copy immediately.               |
// +----------------------------------------------------------------------+
// | Authors: Stephan Schmidt <schst@php-tools.net>                       |
// +----------------------------------------------------------------------+
//
//    $Id: Util.php,v 1.1.2.1 2005/10/05 14:39:48 steuwer Exp $

/**
 * uses PEAR errors
 */
    require_once 'PEAR.php';

/**
 * error code for invalid chars in XML name
 */
define("XML_UTIL_ERROR_INVALID_CHARS", 51);

/**
 * error code for invalid chars in XML name
 */
define("XML_UTIL_ERROR_INVALID_START", 52);

/**
 * error code for non-scalar tag content
 */
define("XML_UTIL_ERROR_NON_SCALAR_CONTENT", 60);
    
/**
 * replace XML entities
 */
define("XML_UTIL_REPLACE_ENTITIES", 1);

/**
 * embedd content in a CData Section
 */
define("XML_UTIL_CDATA_SECTION", 2);
    
/**
 * utility class for working with XML documents
 *
 * @category XML
 * @package  XML_Util
 * @version  0.5.2
 * @author   Stephan Schmidt <schst@php.net>
 * @todo     method to get doctype declaration
 */
class XML_Util {

   /**
    * return API version
    *
    * @access   public
    * @static
    * @return   string  $version API version
    */
    function apiVersion()
    {
        return "0.5.2";
    }

   /**
    * replace XML entities
    *
    * chars that have to be replaced are '&' and '<',
    * furthermore '>', ''' and '"' have entities that can be used. 
    *
    * <code>
    * require_once 'XML/Util.php';
    * 
    * // replace XML entites:
    * $string = XML_Util::replaceEntities("This string contains < & >.");
    * </code>
    *
    * @access   public
    * @static
    * @param    string  $string string where XML special chars should be replaced
    * @return   string  $string string with replaced chars
    * @todo     optional parameter to supply additional entities
    */
    function replaceEntities($string)
    {
        return strtr($string,array(
                                  '&'  => '&amp;',
                                  '>'  => '&gt;',
                                  '<'  => '&lt;',
                                  '"'  => '&quot;',
                                  '\'' => '&apos;' ));
    }

   /**
    * build an xml declaration
    *
    * <code>
    * require_once 'XML/Util.php';
    * 
    * // get an XML declaration:
    * $xmlDecl = XML_Util::getXMLDeclaration("1.0", "UTF-8", true);
    * </code>
    *
    * @access   public
    * @static
    * @param    string  $version     xml version
    * @param    string  $encoding    character encoding
    * @param    boolean $standAlone  document is standalone (or not)
    * @return   string  $decl xml declaration
    * @uses     XML_Util::attributesToString() to serialize the attributes of the XML declaration
    */
    function getXMLDeclaration($version = "1.0", $encoding = null, $standalone = null)
    {
        $attributes = array(
                            "version" => $version,
                           );
        // add encoding
        if ($encoding !== null) {
            $attributes["encoding"] = $encoding;
        }
        // add standalone, if specified
        if ($standalone !== null) {
            $attributes["standalone"] = $standalone ? "yes" : "no";
        }
        
        return sprintf("<?xml%s?>", XML_Util::attributesToString($attributes, false));
    }


   /**
    * build a document type declaration
    *
    * <code>
    * require_once 'XML/Util.php';
    * 
    * // get a doctype declaration:
    * $xmlDecl = XML_Util::getDocTypeDeclaration("rootTag","myDocType.dtd");
    * </code>
    *
    * @access   public
    * @static
    * @param    string  $root         name of the root tag
    * @param    string  $uri          uri of the doctype definition (or array with uri and public id)
    * @param    string  $internalDtd  internal dtd entries   
    * @return   string  $decl         doctype declaration
    * @since    0.2
    */
    function getDocTypeDeclaration($root, $uri = null, $internalDtd = null)
    {
        if (is_array($uri)) {
            $ref = sprintf( ' PUBLIC "%s" "%s"', $uri["id"], $uri["uri"] );
        } elseif (!empty($uri)) {
            $ref = sprintf( ' SYSTEM "%s"', $uri );
        } else {
            $ref = "";
        }

        if (empty($internalDtd)) {
            return sprintf("<!DOCTYPE %s%s>", $root, $ref);
        } else {
            return sprintf("<!DOCTYPE %s%s [\n%s\n]>", $root, $ref, $internalDtd);
        }
    }

   /**
    * create string representation of an attribute list
    *
    * <code>
    * require_once 'XML/Util.php';
    * 
    * // build an attribute string
    * $att = array(
    *              "foo"   =>  "bar",
    *              "argh"  =>  "tomato"
    *            );
    *
    * $attList = XML_Util::attributesToString($att);    
    * </code>
    *
    * @access   public
    * @static
    * @param    array   $attributes  attribute array
    * @param    boolean $sort        sort attribute list alphabetically
    * @param    boolean $multiline   use linebreaks, if more than one attribute is given
    * @param    string  $indent      string used for indentation of multiline attributes
    * @param    string  $linebreak   string used for linebreaks of multiline attributes
    * @return   string  $string      string representation of the attributes
    * @uses     XML_Util::replaceEntities() to replace XML entities in attribute values
    */
    function attributesToString($attributes, $sort = true, $multiline = false, $indent = '    ', $linebreak = "\n")
    {
        $string = "";
        if (is_array($attributes) && !empty($attributes)) {
            if ($sort) {
                ksort($attributes);
            }
            if( !$multiline || count($attributes) == 1) {
                foreach ($attributes as $key => $value) {
                    $string .= " ".$key.'="'.XML_Util::replaceEntities($value).'"';
                }
            } else {
                $first = true;
                foreach ($attributes as $key => $value) {
                    if ($first) {
                        $string .= " ".$key.'="'.XML_Util::replaceEntities($value).'"';
                        $first = false;
                    } else {
                        $string .= $linebreak.$indent.$key.'="'.XML_Util::replaceEntities($value).'"';
                    }
                }
            }
        }
        return $string;
    }

   /**
    * create a tag
    *
    * This method will call XML_Util::createTagFromArray(), which
    * is more flexible.
    *
    * <code>
    * require_once 'XML/Util.php';
    * 
    * // create an XML tag:
    * $tag = XML_Util::createTag("myNs:myTag", array("foo" => "bar"), "This is inside the tag", "http://www.w3c.org/myNs#");
    * </code>
    *
    * @access   public
    * @static
    * @param    string  $qname             qualified tagname (including namespace)
    * @param    array   $attributes        array containg attributes
    * @param    mixed   $content
    * @param    string  $namespaceUri      URI of the namespace
    * @param    integer $replaceEntities   whether to replace XML special chars in content, embedd it in a CData section or none of both
    * @param    boolean $multiline         whether to create a multiline tag where each attribute gets written to a single line
    * @param    string  $indent            string used to indent attributes (_auto indents attributes so they start at the same column)
    * @param    string  $linebreak         string used for linebreaks
    * @return   string  $string            XML tag
    * @see      XML_Util::createTagFromArray()
    * @uses     XML_Util::createTagFromArray() to create the tag
    */
    function createTag($qname, $attributes = array(), $content = null, $namespaceUri = null, $replaceEntities = XML_UTIL_REPLACE_ENTITIES, $multiline = false, $indent = "_auto", $linebreak = "\n")
    {
        $tag = array(
                     "qname"      => $qname,
                     "attributes" => $attributes
                    );

        // add tag content
        if ($content !== null) {
            $tag["content"] = $content;
        }
        
        // add namespace Uri
        if ($namespaceUri !== null) {
            $tag["namespaceUri"] = $namespaceUri;
        }

        return XML_Util::createTagFromArray($tag, $replaceEntities, $multiline, $indent, $linebreak);
    }

   /**
    * create a tag from an array
    * this method awaits an array in the following format
    * <pre>
    * array(
    *  "qname"        => $qname         // qualified name of the tag
    *  "namespace"    => $namespace     // namespace prefix (optional, if qname is specified or no namespace)
    *  "localpart"    => $localpart,    // local part of the tagname (optional, if qname is specified)
    *  "attributes"   => array(),       // array containing all attributes (optional)
    *  "content"      => $content,      // tag content (optional)
    *  "namespaceUri" => $namespaceUri  // namespaceUri for the given namespace (optional)
    *   )
    * </pre>
    *
    * <code>
    * require_once 'XML/Util.php';
    * 
    * $tag = array(
    *           "qname"        => "foo:bar",
    *           "namespaceUri" => "http://foo.com",
    *           "attributes"   => array( "key" => "value", "argh" => "fruit&vegetable" ),
    *           "content"      => "I'm inside the tag",
    *            );
    * // creating a tag with qualified name and namespaceUri
    * $string = XML_Util::createTagFromArray($tag);
    * </code>
    *
    * @access   public
    * @static
    * @param    array   $tag               tag definition
    * @param    integer $replaceEntities   whether to replace XML special chars in content, embedd it in a CData section or none of both
    * @param    boolean $multiline         whether to create a multiline tag where each attribute gets written to a single line
    * @param    string  $indent            string used to indent attributes (_auto indents attributes so they start at the same column)
    * @param    string  $linebreak         string used for linebreaks
    * @return   string  $string            XML tag
    * @see      XML_Util::createTag()
    * @uses     XML_Util::attributesToString() to serialize the attributes of the tag
    * @uses     XML_Util::splitQualifiedName() to get local part and namespace of a qualified name
    */
    function createTagFromArray($tag, $replaceEntities = XML_UTIL_REPLACE_ENTITIES, $multiline = false, $indent = "_auto", $linebreak = "\n" )
    {
        if (isset($tag["content"]) && !is_scalar($tag["content"])) {
            return PEAR::raiseError( "Supplied non-scalar value as tag content", XML_UTIL_ERROR_NON_SCALAR_CONTENT );
        }

        // if no attributes hav been set, use empty attributes
        if (!isset($tag["attributes"]) || !is_array($tag["attributes"])) {
            $tag["attributes"] = array();
        }
        
        // qualified name is not given
        if (!isset($tag["qname"])) {
            // check for namespace
            if (isset($tag["namespace"]) && !empty($tag["namespace"])) {
                $tag["qname"] = $tag["namespace"].":".$tag["localPart"];
            } else {
                $tag["qname"] = $tag["localPart"];
            }
        // namespace URI is set, but no namespace
        } elseif (isset($tag["namespaceUri"]) && !isset($tag["namespace"])) {
            $parts = XML_Util::splitQualifiedName($tag["qname"]);
            $tag["localPart"] = $parts["localPart"];
            if (isset($parts["namespace"])) {
                $tag["namespace"] = $parts["namespace"];
            }
        }

        if (isset($tag["namespaceUri"]) && !empty($tag["namespaceUri"])) {
            // is a namespace given
            if (isset($tag["namespace"]) && !empty($tag["namespace"])) {
                $tag["attributes"]["xmlns:".$tag["namespace"]] = $tag["namespaceUri"];
            } else {
                // define this Uri as the default namespace
                $tag["attributes"]["xmlns"] = $tag["namespaceUri"];
            }
        }

        // check for multiline attributes
        if ($multiline === true) {
            if ($indent === "_auto") {
                $indent = str_repeat(" ", (strlen($tag["qname"])+2));
            }
        }
        
        // create attribute list
        $attList    =   XML_Util::attributesToString($tag["attributes"], true, $multiline, $indent, $linebreak );
        if (!isset($tag["content"]) || (string)$tag["content"] == '') {
            $tag    =   sprintf("<%s%s />", $tag["qname"], $attList);
        } else {
            if ($replaceEntities == XML_UTIL_REPLACE_ENTITIES) {
                $tag["content"] = XML_Util::replaceEntities($tag["content"]);
            } elseif ($replaceEntities == XML_UTIL_CDATA_SECTION) {
                $tag["content"] = XML_Util::createCDataSection($tag["content"]);
            }
            $tag    =   sprintf("<%s%s>%s</%s>", $tag["qname"], $attList, $tag["content"], $tag["qname"] );
        }        
        return  $tag;
    }

   /**
    * create a start element
    *
    * <code>
    * require_once 'XML/Util.php';
    * 
    * // create an XML start element:
    * $tag = XML_Util::createStartElement("myNs:myTag", array("foo" => "bar") ,"http://www.w3c.org/myNs#");
    * </code>
    *
    * @access   public
    * @static
    * @param    string  $qname             qualified tagname (including namespace)
    * @param    array   $attributes        array containg attributes
    * @param    string  $namespaceUri      URI of the namespace
    * @param    boolean $multiline         whether to create a multiline tag where each attribute gets written to a single line
    * @param    string  $indent            string used to indent attributes (_auto indents attributes so they start at the same column)
    * @param    string  $linebreak         string used for linebreaks
    * @return   string  $string            XML start element
    * @see      XML_Util::createEndElement(), XML_Util::createTag()
    */
    function createStartElement($qname, $attributes = array(), $namespaceUri = null, $multiline = false, $indent = '_auto', $linebreak = "\n")
    {
        // if no attributes hav been set, use empty attributes
        if (!isset($attributes) || !is_array($attributes)) {
            $attributes = array();
        }
        
        if ($namespaceUri != null) {
            $parts = XML_Util::splitQualifiedName($qname);
        }

        // check for multiline attributes
        if ($multiline === true) {
            if ($indent === "_auto") {
                $indent = str_repeat(" ", (strlen($qname)+2));
            }
        }

        if ($namespaceUri != null) {
            // is a namespace given
            if (isset($parts["namespace"]) && !empty($parts["namespace"])) {
                $attributes["xmlns:".$parts["namespace"]] = $namespaceUri;
            } else {
                // define this Uri as the default namespace
                $attributes["xmlns"] = $namespaceUri;
            }
        }

        // create attribute list
        $attList    =   XML_Util::attributesToString($attributes, true, $multiline, $indent, $linebreak);
        $element    =   sprintf("<%s%s>", $qname, $attList);
        return  $element;
    }

   /**
    * create an end element
    *
    * <code>
    * require_once 'XML/Util.php';
    * 
    * // create an XML start element:
    * $tag = XML_Util::createEndElement("myNs:myTag");
    * </code>
    *
    * @access   public
    * @static
    * @param    string  $qname             qualified tagname (including namespace)
    * @return   string  $string            XML end element
    * @see      XML_Util::createStartElement(), XML_Util::createTag()
    */
    function createEndElement($qname)
    {
        $element    =   sprintf("</%s>", $qname);
        return  $element;
    }
    
   /**
    * create an XML comment
    *
    * <code>
    * require_once 'XML/Util.php';
    * 
    * // create an XML start element:
    * $tag = XML_Util::createComment("I am a comment");
    * </code>
    *
    * @access   public
    * @static
    * @param    string  $content           content of the comment
    * @return   string  $comment           XML comment
    */
    function createComment($content)
    {
        $comment    =   sprintf("<!-- %s -->", $content);
        return  $comment;
    }
    
   /**
    * create a CData section
    *
    * <code>
    * require_once 'XML/Util.php';
    * 
    * // create a CData section
    * $tag = XML_Util::createCDataSection("I am content.");
    * </code>
    *
    * @access   public
    * @static
    * @param    string  $data              data of the CData section
    * @return   string  $string            CData section with content
    */
    function createCDataSection($data)
    {
        return  sprintf("<![CDATA[%s]]>", $data);
    }

   /**
    * split qualified name and return namespace and local part
    *
    * <code>
    * require_once 'XML/Util.php';
    * 
    * // split qualified tag
    * $parts = XML_Util::splitQualifiedName("xslt:stylesheet");
    * </code>
    * the returned array will contain two elements:
    * <pre>
    * array(
    *       "namespace" => "xslt",
    *       "localPart" => "stylesheet"
    *      );
    * </pre>
    *
    * @access public
    * @static
    * @param  string    $qname      qualified tag name
    * @param  string    $defaultNs  default namespace (optional)
    * @return array     $parts      array containing namespace and local part
    */
    function splitQualifiedName($qname, $defaultNs = null)
    {
        if (strstr($qname, ':')) {
            $tmp = explode(":", $qname);
            return array(
                          "namespace" => $tmp[0],
                          "localPart" => $tmp[1]
                        );
        }
        return array(
                      "namespace" => $defaultNs,
                      "localPart" => $qname
                    );
    }

   /**
    * check, whether string is valid XML name
    *
    * <p>XML names are used for tagname, attribute names and various
    * other, lesser known entities.</p>
    * <p>An XML name may only consist of alphanumeric characters,
    * dashes, undescores and periods, and has to start with a letter
    * or an underscore.
    * </p>
    *
    * <code>
    * require_once 'XML/Util.php';
    * 
    * // verify tag name
    * $result = XML_Util::isValidName("invalidTag?");
    * if (XML_Util::isError($result)) {
    *    print "Invalid XML name: " . $result->getMessage();
    * }
    * </code>
    *
    * @access  public
    * @static
    * @param   string  $string string that should be checked
    * @return  mixed   $valid  true, if string is a valid XML name, PEAR error otherwise
    * @todo    support for other charsets
    */
    function isValidName($string)
    {
        // check for invalid chars
        if (!preg_match("/^[[:alnum:]_\-.]+$/", $string)) {
            return PEAR::raiseError( "XML name may only contain alphanumeric chars, period, hyphen and underscore", XML_UTIL_ERROR_INVALID_CHARS );
        }

        //  check for invalid starting character
        if (!preg_match("/[[:alpha:]_]/", $string{0})) {
            return PEAR::raiseError( "XML name may only start with letter or underscore", XML_UTIL_ERROR_INVALID_START );
        }

        // XML name is valid
        return true;
    }
}
?>