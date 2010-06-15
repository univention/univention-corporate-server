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
// $Id: WSDL.php,v 1.1.2.1 2005/10/05 14:39:47 steuwer Exp $
//
require_once 'SOAP/Base.php';
require_once 'SOAP/Fault.php';
require_once 'HTTP/Request.php';

define('WSDL_CACHE_MAX_AGE', 43200);
define('WSDL_CACHE_USE',     0); // set to zero to turn off caching

/**
 *  SOAP_WSDL
 *  this class parses wsdl files, and can be used by SOAP::Client to properly register
 * soap values for services
 *
 * originaly based on SOAPx4 by Dietrich Ayala http://dietrich.ganx4.com/soapx4
 *
 * TODO:
 *    add wsdl caching
 *   refactor namespace handling ($namespace/$ns)
 *    implement IDL type syntax declaration so we can generate WSDL
 *
 * @access public
 * @version $Id: WSDL.php,v 1.1.2.1 2005/10/05 14:39:47 steuwer Exp $
 * @package SOAP::Client
 * @author Shane Caraveo <shane@php.net> Conversion to PEAR and updates
 * @author Dietrich Ayala <dietrich@ganx4.com> Original Author
 */
class SOAP_WSDL extends SOAP_Base
{
    var $tns = null;
    var $definition = array();
    var $namespaces = array();
    var $ns = array();
    var $xsd = SOAP_XML_SCHEMA_VERSION;
    var $complexTypes = array();
    var $elements = array();
    var $messages = array();
    var $portTypes = array();
    var $bindings = array();
    var $imports = array();
    var $services = array();
    var $service = '';
    var $uri = '';

    /**
     * Proxy parameters
     *
     * @var array
     */
    var $proxy = null;

    var $trace = 0;

    /**
     * Use WSDL cache
     *
     * @var boolean
     */
    var $cacheUse = null;

    /**
     * Cache max lifetime (in seconds)
     *
     * @var int
     */
    var $cacheMaxAge = null;

    /**
    * SOAP_WSDL constructor
    *
    * @param string  endpoint_uri (URL to WSDL file)
    * @param array   contains options for HTTP_Request class (see HTTP/Request.php)
    * @param boolean use WSDL caching
    * @param int     cache max lifetime (in seconds)
    * @access public
    */
    function SOAP_WSDL($wsdl_uri = false, $proxy = array(),
                       $cacheUse    = WSDL_CACHE_USE,
                       $cacheMaxAge = WSDL_CACHE_MAX_AGE) {
        parent::SOAP_Base('WSDL');
        $this->uri         = $wsdl_uri;
        $this->proxy       = $proxy;
        $this->cacheUse    = $cacheUse;
        $this->cacheMaxAge = $cacheMaxAge;
        if ($wsdl_uri) {
            $this->parseURL($wsdl_uri);
            reset($this->services);
            $this->service = key($this->services);
        }
    }

    function set_service($service) {
        if (array_key_exists($service, $this->services)) {
            $this->service = $service;
        }
    }

    /**
     * @deprecated use parseURL instead
     */
    function parse($wsdl_uri, $proxy = array()) {
        $this->parseURL($wsdl_uri, $proxy);
    }

    /**
     * Fill the WSDL array tree with data from a WSDL file
     *
     * @param  string
     * @param  array  proxi related parameters
     * @return void
     */
    function parseURL($wsdl_uri, $proxy = array()) {
        $parser =& new SOAP_WSDL_Parser($wsdl_uri, $this);

        if ($parser->fault) {
            $this->_raiseSoapFault($parser->fault);
        }
    }

    /**
     * Fill the WSDL array tree with data from one or more PHP class objects
     *
     * @param  mixed  $wsdl_obj An object or array of objects to add to the internal WSDL tree
     * @param  string  $service_name Name of the WSDL <service>
     * @param  string  $service_desc Optional description of the WSDL <service>
     * @return void
     */
    function parseObject(&$wsdl_obj, $targetNamespace, $service_name, $service_desc = '')
    {
        $parser =& new SOAP_WSDL_ObjectParser($wsdl_obj, $this, $targetNamespace, $service_name, $service_desc);

         if ($parser->fault) {
             $this->_raiseSoapFault($parser->fault);
         }
    }

    function getEndpoint($portName)
    {
        return (isset($this->services[$this->service]['ports'][$portName]['address']['location']))
                ? $this->services[$this->service]['ports'][$portName]['address']['location']
                : $this->_raiseSoapFault("no endpoint for port for $portName", $this->uri);
    }

    function _getPortName($operation,$service) {
        if (isset($this->services[$service]['ports'])) {
            foreach ($this->services[$service]['ports'] as $port => $portAttrs) {
                $type = $this->services[$service]['ports'][$port]['type'];
                if ($type == 'soap' &&
                    isset($this->bindings[$portAttrs['binding']]['operations'][$operation])) {
                        return $port;
                }
            }
        }
        return null;
    }

    // find the name of the first port that contains an operation of name $operation
    // always returns a the soap portName
    function getPortName($operation, $service = null)
    {
        if (!$service) $service = $this->service;
        if (isset($this->services[$service]['ports'])) {
            $portName = $this->_getPortName($operation,$service);
            if ($portName) return $portName;
        }
        // try any service in the wsdl
        foreach ($this->services as $serviceName=>$service) {
            if (isset($this->services[$serviceName]['ports'])) {
                $portName = $this->_getPortName($operation,$serviceName);
                if ($portName) {
                    $this->service = $serviceName;
                    return $portName;
                }
            }
        }
        return $this->_raiseSoapFault("no operation $operation in wsdl", $this->uri);
    }

    function getOperationData($portName,$operation)
    {
        if (isset($this->services[$this->service]['ports'][$portName]['binding'])
            && $binding = $this->services[$this->service]['ports'][$portName]['binding']) {
            // get operation data from binding
            if (is_array($this->bindings[$binding]['operations'][$operation])) {
                $opData = $this->bindings[$binding]['operations'][$operation];
            }
            // get operation data from porttype
            $portType = $this->bindings[$binding]['type'];
            if (!$portType) {
                return $this->_raiseSoapFault("no port type for binding $binding in wsdl " . $this->uri);
            }
            if (is_array($this->portTypes[$portType][$operation])) {
                if (isset($this->portTypes[$portType][$operation]['parameterOrder']))
                    $opData['parameterOrder'] = $this->portTypes[$portType][$operation]['parameterOrder'];
                $opData['input'] = array_merge($opData['input'], $this->portTypes[$portType][$operation]['input']);
                $opData['output'] = array_merge($opData['output'], $this->portTypes[$portType][$operation]['output']);
            }
            if (!$opData)
                return $this->_raiseSoapFault("no operation $operation for port $portName, in wsdl", $this->uri);
            $opData['parameters'] = false;
            if (isset($this->bindings[$this->services[$this->service]['ports'][$portName]['binding']]['operations'][$operation]['input']['namespace']))
                $opData['namespace'] = $this->bindings[$this->services[$this->service]['ports'][$portName]['binding']]['operations'][$operation]['input']['namespace'];
            // message data from messages
            $inputMsg = $opData['input']['message'];
            if (is_array($this->messages[$inputMsg])) {
            foreach ($this->messages[$inputMsg] as $pname => $pattrs) {
                if ($opData['style'] == 'document' && $opData['input']['use'] == 'literal'
                    && $pname == 'parameters') {
                        $opData['parameters'] = true;
                        $opData['namespace'] = $this->namespaces[$pattrs['namespace']];
                        $el = $this->elements[$pattrs['namespace']][$pattrs['type']];
                        if (isset($el['elements'])) {
                            foreach ($el['elements'] as $elname => $elattrs) {
                                $opData['input']['parts'][$elname] = $elattrs;
                            }
                        }
                } else {
                    $opData['input']['parts'][$pname] = $pattrs;
                }
            }
            }
            $outputMsg = $opData['output']['message'];
            if (is_array($this->messages[$outputMsg])) {
            foreach ($this->messages[$outputMsg] as $pname => $pattrs) {
                if ($opData['style'] == 'document' && $opData['output']['use'] == 'literal'
                    && $pname == 'parameters') {

                        $el = $this->elements[$pattrs['namespace']][$pattrs['type']];
                        if (isset($el['elements'])) {
                            foreach ($el['elements'] as $elname => $elattrs) {
                                $opData['output']['parts'][$elname] = $elattrs;
                            }
                        }

                } else {
                    $opData['output']['parts'][$pname] = $pattrs;
                }
            }
            }
            return $opData;
        }
        return $this->_raiseSoapFault("no binding for port $portName in wsdl", $this->uri);
    }

    function matchMethod(&$operation) {
        // Overloading lowercases function names :(
        foreach ($this->services[$this->service]['ports'] as $port => $portAttrs) {
            foreach (array_keys($this->bindings[$portAttrs['binding']]['operations']) as $op) {
                if (strcasecmp($op, $operation) == 0) {
                    $operation = $op;
                }
            }
        }
    }

    /**
     * getDataHandler
     *
     * Given a datatype, what function handles the processing?
     * this is used for doc/literal requests where we receive
     * a datatype, and we need to pass it to a method in out
     * server class
     *
     * @param string datatype
     * @param string namespace
     * @returns string methodname
     * @access public
     */
    function getDataHandler($datatype, $namespace) {
        // see if we have an element by this name
        if (isset($this->namespaces[$namespace]))
            $namespace = $this->namespaces[$namespace];
        if (isset($this->ns[$namespace])) {
            $nsp = $this->ns[$namespace];
            #if (!isset($this->elements[$nsp]))
            #    $nsp = $this->namespaces[$nsp];
            if (isset($this->elements[$nsp][$datatype])) {
                $checkmessages = array();
                // find what messages use this datatype
                foreach ($this->messages as $messagename=>$message) {
                    foreach ($message as $partname=>$part) {
                        if ($part['type']==$datatype) {
                            $checkmessages[] = $messagename;
                            break;
                        }
                    }
                }
                // find the operation that uses this message
                $dataHandler = NULL;
                foreach($this->portTypes as $portname=>$porttype) {
                    foreach ($porttype as $opname=>$opinfo) {
                        foreach ($checkmessages as $messagename) {
                            if ($opinfo['input']['message'] == $messagename) {
                                return $opname;
                            }
                        }
                    }
                }
            }
        }
        return null;
    }

    function getSoapAction($portName, $operation)
    {
        if (isset($this->bindings[$this->services[$this->service]['ports'][$portName]['binding']]['operations'][$operation]['soapAction']) &&
            $soapAction = $this->bindings[$this->services[$this->service]['ports'][$portName]['binding']]['operations'][$operation]['soapAction']) {
            return $soapAction;
        }
        return false;
    }

    function getNamespace($portName, $operation)
    {
        if (isset($this->bindings[$this->services[$this->service]['ports'][$portName]['binding']]) &&
            isset($this->bindings[$this->services[$this->service]['ports'][$portName]['binding']]['operations'][$operation]['input']['namespace']) &&
            $namespace = $this->bindings[$this->services[$this->service]['ports'][$portName]['binding']]['operations'][$operation]['input']['namespace']) {
            return $namespace;
        }
        return false;
    }

    function getNamespaceAttributeName($namespace) {
        /* if it doesn't exist at first, flip the array and check again */
        if (!array_key_exists($namespace, $this->ns)) {
            $this->ns = array_flip($this->namespaces);
        }
        /* if it doesn't exist now, add it */
        if (!array_key_exists($namespace, $this->ns)) {
            return $this->addNamespace($namespace);
        }
        return $this->ns[$namespace];
    }

    function addNamespace($namespace) {
        if (array_key_exists($namespace, $this->ns)) {
            return $this->ns[$namespace];
        }
        $n = count($this->ns);
        $attr = 'ns'.$n;
        $this->namespaces['ns'.$n] = $namespace;
        $this->ns[$namespace] = $attr;
        return $attr;
    }

    function _validateString($string) {
        // XXX this should be done sooner or later
        return true;
        #if (preg_match("/^[\w_:#\/]+$/",$string)) return true;
        #return false;
    }

    function _addArg(&$args, &$argarray, $argname)
    {
        if ($args) $args .= ", ";
        $args .= "\$".$argname;
        if (!$this->_validateString($argname)) return NULL;
        if ($argarray) $argarray .= ", ";
        $argarray .= "\"$argname\"=>\$".$argname;
    }

    function _elementArg(&$args, &$argarray, &$_argtype, $_argname)
    {
        $comments = '';
        $el = $this->elements[$_argtype['namespace']][$_argtype['type']];
        $tns = isset($this->ns[$el['namespace']])?$this->ns[$el['namespace']]:$_argtype['namespace'];
        if (isset($this->complexTypes[$tns][$el['type']])) {
            // the element is actually a complex type!
            $comments = "        // {$el['type']} is a ComplexType, refer to wsdl for more info\n";
            $attrname = "{$_argtype['type']}_attr";
            if (isset($this->complexTypes[$tns][$el['type']]['attribute'])) {
                $comments .= "        // {$el['type']} may require attributes, refer to wsdl for more info\n";
            }
            $comments .= "        \${$attrname}['xmlns'] = '{$this->namespaces[$_argtype['namespace']]}';\n";
            $comments .= "        \${$_argtype['type']} =& new SOAP_Value('{$_argtype['type']}',false,\${$_argtype['type']},\$$attrname);\n";
            $this->_addArg($args,$argarray,$_argtype['type']);
            if (isset($this->complexTypes[$tns][$el['type']]['attribute'])) {
                if ($args) $args .= ", ";
                $args .= "\$".$attrname;
            }
            #$comments = $this->_complexTypeArg($args,$argarray,$el,$_argtype['type']);
        } else if (isset($el['elements'])) {
            foreach ($el['elements'] as $ename => $element) {
                $comments .= "        \$$ename =& new SOAP_Value('{{$this->namespaces[$element['namespace']]}}$ename','{$element['type']}',\$$ename);\n";
                $this->_addArg($args,$argarray,$ename);
            }
        } else {
            #$echoStringParam =& new SOAP_Value('{http://soapinterop.org/xsd}echoStringParam',false,$echoStringParam);
            $comments .= "        \$$_argname =& new SOAP_Value('{{$this->namespaces[$tns]}}$_argname','{$el['type']}',\$$_argname);\n";
            $this->_addArg($args,$argarray,$_argname);
        }
        return $comments;
    }

    function _complexTypeArg(&$args, &$argarray, &$_argtype, $_argname)
    {
        $comments = '';
        if (isset($this->complexTypes[$_argtype['namespace']][$_argtype['type']])) {
            $comments  = "        // $_argname is a ComplexType {$_argtype['type']},\n";
            $comments .= "        //refer to wsdl for more info\n";
            if (isset($this->complexTypes[$_argtype['namespace']][$_argtype['type']]['attribute'])) {
                $comments .= "        // $_argname may require attributes, refer to wsdl for more info\n";
            }
            $wrapname = '{'.$this->namespaces[$_argtype['namespace']].'}'.$_argtype['type'];
            $comments .= "        \$$_argname =& new SOAP_Value('$_argname','$wrapname',\$$_argname);\n";

        }
        $this->_addArg($args,$argarray,$_argname);
        return $comments;
    }

    /**
     * generateProxyCode
     * generates stub code from the wsdl that can be saved to a file, or eval'd into existence
     */
    function generateProxyCode($port = '', $classname='')
    {
        $multiport = count($this->services[$this->service]['ports']) > 1;
        if (!$port) {
            reset($this->services[$this->service]['ports']);
            $port = current($this->services[$this->service]['ports']);
        }
        // XXX currently do not support HTTP ports
        if ($port['type'] != 'soap') return NULL;

        // XXX currentPort is BAD
        $clienturl = $port['address']['location'];
        if (!$classname) {
            if ($multiport || $port) {
                $classname = 'WebService_'.$this->service.'_'.$port['name'];
            } else {
                $classname = 'WebService_'.$this->service;
            }
            $classname = str_replace('.','_',$classname);
        }

        if (!$this->_validateString($classname)) return NULL;

        if (is_array($this->proxy) && count($this->proxy) > 0) {
            $class = "class $classname extends SOAP_Client\n{\n".
            "    function $classname()\n{\n".
            "        \$this->SOAP_Client(\"$clienturl\", 0, 0,
                    array(";

            foreach($this->proxy as $key => $val) {
                if (is_array($val)) {
                    $class .= "\"$key\" => array(";
                    foreach ($val as $key2 => $val2) {
                        $class .= "\"$key2\" => \"$val2\",";
                    }
                    $class .= ')';
                } else {
                    $class .= "\"$key\"=>\"$val\",";
                }
            }
            $class .= "));\n }\n";
            $class = str_replace(',))', '))', $class);
        } else {
            $class = "class $classname extends SOAP_Client\n{\n".
            "    function $classname()\n{\n".
            "        \$this->SOAP_Client(\"$clienturl\", 0);\n".
            "    }\n";
        }

        // get the binding, from that get the port type
        $primaryBinding = $port['binding']; //$this->services[$this->service]['ports'][$port['name']]["binding"];
        $primaryBinding = preg_replace("/^(.*:)/","",$primaryBinding);
        $portType = $this->bindings[$primaryBinding]['type'];
        $portType = preg_replace("/^(.*:)/","",$portType);
        $style = $this->bindings[$primaryBinding]['style'];

        // XXX currentPortType is BAD
        foreach ($this->portTypes[$portType] as $opname => $operation) {
            $soapaction = $this->bindings[$primaryBinding]['operations'][$opname]['soapAction'];
            if (isset($this->bindings[$primaryBinding]['operations'][$opname]['style'])) {
                $opstyle = $this->bindings[$primaryBinding]['operations'][$opname]['style'];
            } else {
                $opstyle = $style;
            }
            $use = $this->bindings[$primaryBinding]['operations'][$opname]['input']['use'];
            if ($use == 'encoded') {
                $namespace = $this->bindings[$primaryBinding]['operations'][$opname]['input']['namespace'];
            } else {
                $bindingType = $this->bindings[$primaryBinding]['type'];
                $ns = $this->portTypes[$bindingType][$opname]['input']['namespace'];
                $namespace = $this->namespaces[$ns];
            }

            $args = '';
            $argarray = '';
            $comments = '';
            $wrappers = '';
            foreach ($operation['input'] as $argname => $argtype) {
                if ($argname == "message") {
                    foreach ($this->messages[$argtype] as $_argname => $_argtype) {
                        $comments = '';
                        if ($opstyle == 'document' && $use == 'literal' &&
                            $_argtype['name'] == 'parameters') {
                                // the type or element refered to is used for parameters!
                                $elattrs = null;
                                $element = $_argtype['element'];
                                $el = $this->elements[$_argtype['namespace']][$_argtype['type']];

                                if($el['complex']) {
                                    $namespace = $this->namespaces[$_argtype['namespace']];
                                    // XXX need to wrap the parameters in a soap_value
                                }
                                if (isset($el['elements'])) {
                                    foreach ($el['elements'] as $elname => $elattrs) {
                                        // is the element a complex type?
                                        if (isset($this->complexTypes[$elattrs['namespace']][$elname])) {
                                            $comments .= $this->_complexTypeArg($args, $argarray, $_argtype, $_argname);
                                        } else {
                                            $this->_addArg($args, $argarray, $elname);
                                        }
                                    }
                                }/* else {
                                    $comments = $this->_complexTypeArg($args, $argarray, $elattrs, $elattrs['name']);
                                }*/
                                if($el['complex'] && $argarray) {
                                    $wrapname = '{'.$this->namespaces[$_argtype['namespace']].'}'.$el['name'];
                                    $comments .= "        \${$el['name']} =& new SOAP_Value('$wrapname',false,\$v=array($argarray));\n";
                                    $argarray = "'{$el['name']}'=>\${$el['name']}";
                                }
                        } else
                        if (isset($_argtype['element'])) {
                            // element argument
                            $comments = $this->_elementArg($args, $argarray, $_argtype, $_argtype['type']);
                        } else {
                            // complex type argument
                            $comments = $this->_complexTypeArg($args, $argarray, $_argtype, $_argname);
                        }
                    }
                }
            }

            // validate entries
            if (!$this->_validateString($opname)) return NULL;
            if (!$this->_validateString($namespace)) return NULL;
            if (!$this->_validateString($soapaction)) return NULL;

            if ($argarray) {
                $argarray = "array($argarray)";
            } else {
                $argarray = 'null';
            }

            $class .= "    function &$opname($args) {\n$comments$wrappers".
            "        return \$this->call(\"$opname\", \n".
            "                        \$v = $argarray, \n".
            "                        array('namespace'=>'$namespace',\n".
            "                            'soapaction'=>'$soapaction',\n".
            "                            'style'=>'$opstyle',\n".
            "                            'use'=>'$use'".
            ($this->trace?",'trace'=>1":"")." ));\n".
            "    }\n";
        }
        $class .= "}\n";
        return $class;
    }

    function generateAllProxies()
    {
        $proxycode = '';
        foreach (array_keys($this->services[$this->service]['ports']) as $key) {
            $port =& $this->services[$this->service]['ports'][$key];
            $proxycode .= $this->generateProxyCode($port);
        }
        return $proxycode;
    }

    function &getProxy($port = '', $name = '')
    {
        $multiport = count($this->services[$this->service]['ports']) > 1;

        if (!$port) {
            reset($this->services[$this->service]['ports']);
            $port = current($this->services[$this->service]['ports']);
        }

        if ($multiport || $port) {
            $classname = 'WebService_' . $this->service . '_' . $port['name'];
        } else {
            $classname = 'WebService_' . $this->service;
        }

        if ($name) {
            $classname = $name . '_' . $classname;
        }

        $classname = preg_replace('/[ .\(\)]+/', '_', $classname);

        if (!class_exists($classname)) {
            $proxy = $this->generateProxyCode($port, $classname);
            eval($proxy);
        }

        return new $classname;
    }

    function &_getComplexTypeForElement($name, $namespace)
    {
        $t = NULL;
        if (isset($this->ns[$namespace]) &&
            isset($this->elements[$this->ns[$namespace]][$name]['type'])) {

            $type = $this->elements[$this->ns[$namespace]][$name]['type'];
            $ns = $this->elements[$this->ns[$namespace]][$name]['namespace'];

            if (isset($this->complexTypes[$ns][$type])) {
                $t = $this->complexTypes[$ns][$type];
            }
        }
        return $t;
    }

    function getComplexTypeNameForElement($name, $namespace)
    {
        $t = $this->_getComplexTypeForElement($name, $namespace);
        if ($t) {
            return $t['name'];
        }
        return NULL;
    }

    function getComplexTypeChildType($ns, $name, $child_ns, $child_name) {
        // is the type an element?
        $t = $this->_getComplexTypeForElement($name, $ns);
        if ($t) {
            // no, get it from complex types directly
            if (isset($t['elements'][$child_name]['type']))
                return $t['elements'][$child_name]['type'];
        }
        return NULL;
    }

    function getSchemaType($type, $name, $type_namespace)
    {
        # see if it's a complex type so we can deal properly with SOAPENC:arrayType
        if ($name && $type) {
            # XXX TODO:
            # look up the name in the wsdl and validate the type
            foreach ($this->complexTypes as $ns=> $types) {
                if (array_key_exists($type, $types)) {
                    if (array_key_exists('type', $types[$type])) {
                        list($arraytype_ns, $arraytype, $array_depth) = isset($types[$type]['arrayType'])?
                            $this->_getDeepestArrayType($types[$type]['namespace'], $types[$type]['arrayType'])
                            : array($this->namespaces[$types[$type]['namespace']], NULL, 0);
                        return array($types[$type]['type'], $arraytype, $arraytype_ns, $array_depth);
                    }
                    if (array_key_exists('arrayType', $types[$type])) {
                        list($arraytype_ns, $arraytype, $array_depth) =
                                $this->_getDeepestArrayType($types[$type]['namespace'], $types[$type]['arrayType']);
                        return array('Array', $arraytype, $arraytype_ns, $array_depth);
                    }
                    if (array_key_exists('elements', $types[$type]) &&
                        array_key_exists($name, $types[$type]['elements'])) {
                        $type = $types[$type]['elements']['type'];
                        return array($type, NULL, $this->namespaces[$types[$type]['namespace']], NULL);
                    }
                }
            }
        }
        if ($type && $type_namespace) {
            $arrayType = NULL;
            # XXX TODO:
            # this code currently handles only one way of encoding array types in wsdl
            # need to do a generalized function to figure out complex types
            $p = $this->ns[$type_namespace];
            if ($p &&
                array_key_exists($p, $this->complexTypes) &&
                array_key_exists($type, $this->complexTypes[$p])) {
                if ($arrayType = $this->complexTypes[$p][$type]['arrayType']) {
                    $type = 'Array';
                } else if ($this->complexTypes[$p][$type]['order']=='sequence' &&
                           array_key_exists('elements', $this->complexTypes[$p][$type])) {
                    reset($this->complexTypes[$p][$type]['elements']);
                    # assume an array
                    if (count($this->complexTypes[$p][$type]['elements']) == 1) {
                        $arg = current($this->complexTypes[$p][$type]['elements']);
                        $arrayType = $arg['type'];
                        $type = 'Array';
                    } else {
                        foreach($this->complexTypes[$p][$type]['elements'] as $element) {
                            if ($element['name'] == $type) {
                                $arrayType = $element['type'];
                                $type = $element['type'];
                            }
                        }
                    }
                } else {
                    $type = 'Struct';
                }
                return array($type, $arrayType, $type_namespace, null);
            }
        }
        return array(null, null, null, null);
    }

    /** Recurse through the WSDL structure looking for the innermost array type of multi-dimensional arrays.
     *
     *  Takes a namespace prefix and a type, which can be in the form 'type' or 'type[]',
     *  and returns the full namespace URI, the type of the most deeply nested array type found,
     *  and the number of levels of nesting.
     *
     * @access private
     * @return mixed array or nothing
     */
    function _getDeepestArrayType($nsPrefix, $arrayType)
    {
        static $trail = array();

        $arrayType = ereg_replace('\[\]$', '', $arrayType);

        // Protect against circular references
        // XXX We really need to remove trail from this altogether (it's very inefficient and
        // in the wrong place!) and put circular reference checking in when the WSDL info
        // is generated in the first place
        if (array_search($nsPrefix . ':' . $arrayType, $trail)) {
            return array(NULL, NULL, -count($trail));
        }

        if (array_key_exists($nsPrefix, $this->complexTypes) &&
            array_key_exists($arrayType, $this->complexTypes[$nsPrefix]) &&
            array_key_exists('arrayType', $this->complexTypes[$nsPrefix][$arrayType])) {
            $trail[] = $nsPrefix . ':' . $arrayType;
            $result = $this->_getDeepestArrayType( $this->complexTypes[$nsPrefix][$arrayType]['namespace'],
                                                   $this->complexTypes[$nsPrefix][$arrayType]['arrayType']);
            return array($result[0], $result[1], $result[2] + 1);
        }
        return array($this->namespaces[$nsPrefix], $arrayType, 0);
    }
}

class SOAP_WSDL_Cache extends SOAP_Base
{
    // Cache settings

    /**
     * Use WSDL cache
     *
     * @var boolean
     */
    var $_cacheUse = null;

    /**
     * Cache max lifetime (in seconds)
     *
     * @var int
     */
    var $_cacheMaxAge = null;

    /**
     * SOAP_WSDL_Cache constructor
     *
     * @param  boolean use caching
     * @param  int     cache max lifetime (in seconds)
     * @access public
     */
    function SOAP_WSDL_Cache($cacheUse = WSDL_CACHE_USE,
                             $cacheMaxAge = WSDL_CACHE_MAX_AGE) {
        parent::SOAP_Base('WSDLCACHE');
        $this->_cacheUse = $cacheUse;
        $this->_cacheMaxAge = $cacheMaxAge;
    }

    /**
     * _cacheDir
     * return the path to the cache, if it doesn't exist, make it
     */
    function _cacheDir() {
        $dir = getenv("WSDLCACHE");
        if (!$dir) $dir = "./wsdlcache";
        @mkdir($dir, 0700);
        return $dir;
    }

    /**
     * Retrieves a file from cache if it exists, otherwise retreive from net,
     * add to cache, and return from cache.
     *
     * @param  string   URL to WSDL
     * @param  array    proxy parameters
     * @param  int      expected MD5 of WSDL URL
     * @access public
     * @return string  data
     */
    function get($wsdl_fname, $proxy_params = array(), $cache = 0) {
        $cachename = $md5_wsdl = $file_data = '';
        if ($this->_cacheUse) {
            // Try to retrieve WSDL from cache
            $cachename = SOAP_WSDL_Cache::_cacheDir() . '/' . md5($wsdl_fname). '.wsdl';
            if (file_exists($cachename)) {
                $wf = fopen($cachename,'rb');
                if ($wf) {
                    // Reading cached file
                    $file_data = fread($wf, filesize($cachename));
                    $md5_wsdl = md5($file_data);
                    fclose($wf);
                }
                if ($cache) {
                    if ($cache != $md5_wsdl) {
                        return $this->_raiseSoapFault('WSDL Checksum error!', $wsdl_fname);
                    }
                } else {
                    $fi = stat($cachename);
                    $cache_mtime = $fi[8];
                    #print cache_mtime, time()
                    if ($cache_mtime + $this->_cacheMaxAge < time()) {
                        # expired
                        $md5_wsdl = ''; # refetch
                    }
                }
            }
        }

        if (!$md5_wsdl) {
            // Not cached or not using cache. Retrieve WSDL from URL

            // is it a local file?
            // this section should be replace by curl at some point
            if (!preg_match('/^(https?|file):\/\//',$wsdl_fname)) {
                if (!file_exists($wsdl_fname)) {
                    return $this->_raiseSoapFault("Unable to read local WSDL $wsdl_fname", $wsdl_fname);
                }
                if (function_exists('file_get_contents')) {
                    $file_data = file_get_contents($wsdl_fname);
                } else {
                    $file_data = implode('',file($wsdl_fname));
                }
            } else {
                $uri = explode('?',$wsdl_fname);
                $rq =& new HTTP_Request($uri[0], $proxy_params);
                // the user agent HTTP_Request uses fouls things up
                if (isset($uri[1])) {
                    $rq->addRawQueryString($uri[1]);
                }

                if (isset($proxy_params['proxy_user']) && isset($proxy_params['proxy_pass'])) {
                    $rq->setProxy($proxy_params["proxy_host"],$proxy_params["proxy_port"],
                                  $proxy_params["proxy_user"],$proxy_params["proxy_pass"]);
                }

                $result = $rq->sendRequest();
                if (PEAR::isError($result)) {
                    return $this->_raiseSoapFault("Unable to retrieve WSDL $wsdl_fname," . $rq->getResponseCode(), $wsdl_fname);
            }
               $file_data = $rq->getResponseBody();
                if (!$file_data) {
                    return $this->_raiseSoapFault("Unable to retrieve WSDL $wsdl_fname, no http body", $wsdl_fname);
                }
            }

            $md5_wsdl = md5($file_data);

            if ($this->_cacheUse) {
                $fp = fopen($cachename, "wb");
                fwrite($fp, $file_data);
                fclose($fp);
            }
        }
        if ($this->_cacheUse && $cache && $cache != $md5_wsdl) {
            return $this->_raiseSoapFault("WSDL Checksum error!", $wsdl_fname);
        }
        return $file_data;
    }
}

class SOAP_WSDL_Parser extends SOAP_Base
{
    // define internal arrays of bindings, ports, operations, messages, etc.
    var $currentMessage;
    var $currentOperation;
    var $currentPortType;
    var $currentBinding;
    var $currentPort;

    // parser vars
    var $cache;

    var $tns = null;
    var $soapns = array('soap');
    var $uri = '';
    var $wsdl = null;

    var $status = '';
    var $element_stack = array();
    var $parentElement = '';

    var $schema = '';
    var $schemaStatus = '';
    var $schema_stack = array();
    var $currentComplexType;
    var $schema_element_stack = array();
    var $currentElement;

    // constructor
    function SOAP_WSDL_Parser($uri, &$wsdl, $docs = false) {
        parent::SOAP_Base('WSDLPARSER');
        $this->cache =& new SOAP_WSDL_Cache($wsdl->cacheUse, $wsdl->cacheMaxAge);
        $this->uri = $uri;
        $this->wsdl = &$wsdl;
        $this->docs = $docs;
        $this->parse($uri);
    }

    function parse($uri) {
        // Check whether content has been read.
        $fd = $this->cache->get($uri, $this->wsdl->proxy);
        if (PEAR::isError($fd)) {
            return $this->_raiseSoapFault($fd);
        }

        // Create an XML parser.
        $parser = xml_parser_create();
        xml_parser_set_option($parser, XML_OPTION_CASE_FOLDING, 0);
        xml_set_object($parser, $this);
        xml_set_element_handler($parser, 'startElement', 'endElement');
        if ($this->docs) {
            xml_set_character_data_handler($parser, 'characterData');
        }

        if (!xml_parse($parser,$fd, true)) {
            $detail = sprintf('XML error on line %d: %s',
                                    xml_get_current_line_number($parser),
                                    xml_error_string(xml_get_error_code($parser)));
            //print $fd;
            return $this->_raiseSoapFault("Unable to parse WSDL file $uri\n$detail");
        }
        xml_parser_free($parser);
        return true;
    }

    // start-element handler
    function startElement($parser, $name, $attrs) {
        // get element prefix
        $qname =& new QName($name);
        if ($qname->ns) {
            $ns = $qname->ns;
            if ($ns && ((!$this->tns && strcasecmp($qname->name,'definitions') == 0) || $ns == $this->tns)) {
                $name = $qname->name;
            }
        }
        $this->currentTag = $qname->name;
        $this->parentElement = '';
        $stack_size = count($this->element_stack);
        if ($stack_size > 0) {
            $this->parentElement = $this->element_stack[$stack_size-1];
        }
        $this->element_stack[] = $this->currentTag;

        // find status, register data
        switch($this->status) {
        case 'types':
            // sect 2.2 wsdl:types
            // children: xsd:schema
            $parent_tag = '';
            $stack_size = count($this->schema_stack);
            if ($stack_size > 0) {
                $parent_tag = $this->schema_stack[$stack_size-1];
            }

            switch($qname->name) {
            case 'schema':
                // no parent should be in the stack
                if (!$parent_tag || $parent_tag == 'types') {
                    if (array_key_exists('targetNamespace', $attrs)) {
                        $this->schema = $this->wsdl->getNamespaceAttributeName($attrs['targetNamespace']);
                    } else {
                        $this->schema = $this->wsdl->getNamespaceAttributeName($this->wsdl->tns);
                    }
                    $this->wsdl->complexTypes[$this->schema] = array();
                    $this->wsdl->elements[$this->schema] = array();
                }
            break;
            case 'complexType':
                if ($parent_tag == 'schema') {
                    $this->currentComplexType = $attrs['name'];
                    if (!isset($attrs['namespace'])) $attrs['namespace'] = $this->schema;
                    $this->wsdl->complexTypes[$this->schema][$this->currentComplexType] = $attrs;
                    if (array_key_exists('base',$attrs)) {
                        $qn =& new QName($attrs['base']);
                        $this->wsdl->complexTypes[$this->schema][$this->currentComplexType]['type'] = $qn->name;
                        $this->wsdl->complexTypes[$this->schema][$this->currentComplexType]['namespace'] = $qn->ns;
                    } else {
                        $this->wsdl->complexTypes[$this->schema][$this->currentComplexType]['type'] = 'Struct';
                    }
                    $this->schemaStatus = 'complexType';
                } else {
                    $this->wsdl->elements[$this->schema][$this->currentElement]['complex'] = TRUE;
                }
            break;
            case 'element':
                if (isset($attrs['type'])) {
                    $qn =& new QName($attrs['type']);
                    $attrs['type'] = $qn->name;
                    #$this->wsdl->getNamespaceAttributeName
                    if ($qn->ns && array_key_exists($qn->ns, $this->wsdl->namespaces)) {
                        $attrs['namespace'] = $qn->ns;
                    }
                }

                $parentElement = '';
                $stack_size = count($this->schema_element_stack);
                if ($stack_size > 0) {
                    $parentElement = $this->schema_element_stack[$stack_size-1];
                }

                if (isset($attrs['ref'])) {
                    $this->currentElement = $attrs['ref'];
                } else {
                    $this->currentElement = $attrs['name'];
                }
                $this->schema_element_stack[] = $this->currentElement;
                if (!isset($attrs['namespace'])) $attrs['namespace'] = $this->schema;

                if ($parent_tag == 'schema') {
                    $this->wsdl->elements[$this->schema][$this->currentElement] = $attrs;
                    $this->wsdl->elements[$this->schema][$this->currentElement]['complex'] = FALSE;
                    $this->schemaStatus = 'element';
                } else if ($this->currentComplexType) {
                    // we're inside a complexType
                    if ((isset($this->wsdl->complexTypes[$this->schema][$this->currentComplexType]['order']) &&
                         $this->wsdl->complexTypes[$this->schema][$this->currentComplexType]['order'] == 'sequence')
                        && $this->wsdl->complexTypes[$this->schema][$this->currentComplexType]['type'] == 'Array') {
                            $this->wsdl->complexTypes[$this->schema][$this->currentComplexType]['arrayType'] = $attrs['type'];
                    }
                    $this->wsdl->complexTypes[$this->schema][$this->currentComplexType]['elements'][$this->currentElement] = $attrs;
                } else {
                    $this->wsdl->elements[$this->schema][$parentElement]['elements'][$this->currentElement] = $attrs;
                }
            break;
            case 'complexContent':
            case 'simpleContent':
            break;
            case 'extension':
            case 'restriction':
                if ($this->schemaStatus == 'complexType') {
                    if ($attrs['base']) {
                        $qn =& new QName($attrs['base']);
                        $this->wsdl->complexTypes[$this->schema][$this->currentComplexType]['type'] = $qn->name;
                        $this->wsdl->complexTypes[$this->schema][$this->currentComplexType]['namespace'] = $qn->ns;
                    } else {
                        $this->wsdl->complexTypes[$this->schema][$this->currentComplexType]['type'] = 'Struct';
                    }
                }
            break;
            case 'sequence':
                if ($this->schemaStatus == 'complexType') {
                    $this->wsdl->complexTypes[$this->schema][$this->currentComplexType]['order'] = $qname->name;
                    #if (!array_key_exists('type',$this->wsdl->complexTypes[$this->schema][$this->currentComplexType])) {
                        $this->wsdl->complexTypes[$this->schema][$this->currentComplexType]['type'] = 'Array';
                    #}
                }
            break;
            case 'all':
                $this->wsdl->complexTypes[$this->schema][$this->currentComplexType]['order'] = $qname->name;
                if (!array_key_exists('type',$this->wsdl->complexTypes[$this->schema][$this->currentComplexType])) {
                    $this->wsdl->complexTypes[$this->schema][$this->currentComplexType]['type'] = 'Struct';
                }
            break;
            case 'choice':
                $this->wsdl->complexTypes[$this->schema][$this->currentComplexType]['order'] = $qname->name;
                if (!array_key_exists('type',$this->wsdl->complexTypes[$this->schema][$this->currentComplexType])) {
                    $this->wsdl->complexTypes[$this->schema][$this->currentComplexType]['type'] = 'Array';
                }
            case 'attribute':
                if ($this->schemaStatus == 'complexType') {
                    if (isset($attrs['name'])) {
                        $this->wsdl->complexTypes[$this->schema][$this->currentComplexType]['attribute'][$attrs['name']] = $attrs;
                    } else
                    if (isset($attrs['ref'])) {
                        $q =& new QName($attrs['ref']);
                        foreach ($attrs as $k => $v) {
                            if ($k != 'ref' && strstr($k, $q->name)) {
                                $vq =& new QName($v);
                                if ($q->name == 'arrayType') {
                                    $this->wsdl->complexTypes[$this->schema][$this->currentComplexType][$q->name] = $vq->name.$vq->arrayInfo;
                                    $this->wsdl->complexTypes[$this->schema][$this->currentComplexType]['type'] = 'Array';
                                    $this->wsdl->complexTypes[$this->schema][$this->currentComplexType]['namespace'] = $vq->ns;
                                } else {
                                    $this->wsdl->complexTypes[$this->schema][$this->currentComplexType][$q->name] = $vq->name;
                                }
                            }
                        }
                    }
                }
            break;
            }

            $this->schema_stack[] = $qname->name;

        break;
        case 'message':
            // sect 2.3 wsdl:message child wsdl:part
            switch($qname->name) {
            case 'part':
                $qn = NULL;
                if (isset($attrs['type'])) {
                    $qn =& new QName($attrs['type']);
                } else if (isset($attrs['element'])) {
                    $qn =& new QName($attrs['element']);
                }
                if ($qn) {
                    $attrs['type'] = $qn->name;
                    $attrs['namespace'] = $qn->ns;
                }
                $this->wsdl->messages[$this->currentMessage][$attrs['name']] = $attrs;
                // error in wsdl
            case 'documentation':
                break;
            default:
                break;
            }
        break;
        case 'portType':
            // sect 2.4
            switch($qname->name) {
            case 'operation':
                // attributes: name
                // children: wsdl:input wsdl:output wsdl:fault
                $this->currentOperation = $attrs['name'];
                #$this->wsdl->portTypes[$this->currentPortType][$this->currentOperation]['parameterOrder'] = $attrs['parameterOrder'];
                $this->wsdl->portTypes[$this->currentPortType][$this->currentOperation] = $attrs;
                break;
            case 'input':
            case 'output':
            case 'fault':
                // wsdl:input wsdl:output wsdl:fault
                // attributes: name message parameterOrder(optional)
                if ($this->currentOperation) {
                    if (isset($this->wsdl->portTypes[$this->currentPortType][$this->currentOperation][$name])) {
                        $this->wsdl->portTypes[$this->currentPortType][$this->currentOperation][$name] = array_merge($this->wsdl->portTypes[$this->currentPortType][$this->currentOperation][$name],$attrs);
                    } else {
                        $this->wsdl->portTypes[$this->currentPortType][$this->currentOperation][$name] = $attrs;
                    }
                    if (array_key_exists('message',$attrs)) {
                        $qn =& new QName($attrs['message']);
                        $this->wsdl->portTypes[$this->currentPortType][$this->currentOperation][$name]['message'] = $qn->name;
                        $this->wsdl->portTypes[$this->currentPortType][$this->currentOperation][$name]['namespace'] = $qn->ns;
                    }
                }
                break;
            case 'documentation':
                break;
            default:
                break;
            }
        break;
        case 'binding':
            $ns = $qname->ns ? $this->wsdl->namespaces[$qname->ns] : SCHEMA_WSDL;
            switch($ns) {
            case SCHEMA_SOAP:
                // this deals with wsdl section 3 soap binding
                switch($qname->name) {
                case 'binding':
                    // sect 3.3
                    // soap:binding, attributes: transport(required), style(optional, default = document)
                    // if style is missing, it is assumed to be 'document'
                    if (!isset($attrs['style'])) $attrs['style'] = 'document';
                    $this->wsdl->bindings[$this->currentBinding] = array_merge($this->wsdl->bindings[$this->currentBinding],$attrs);
                    break;
                case 'operation':
                    // sect 3.4
                    // soap:operation, attributes: soapAction(required), style(optional, default = soap:binding:style)
                    if (!isset($attrs['style'])) $attrs['style'] = $this->wsdl->bindings[$this->currentBinding]['style'];
                    $this->wsdl->bindings[$this->currentBinding]['operations'][$this->currentOperation] = $attrs;
                    break;
                case 'body':
                    // sect 3.5
                    // soap:body attributes:
                    // part - optional.  listed parts must appear in body, missing means all parts appear in body
                    // use - required. encoded|literal
                    // encodingStyle - optional.  space seperated list of encodings (uri's)
                    $this->wsdl->bindings[$this->currentBinding]
                                    ['operations'][$this->currentOperation][$this->opStatus] = $attrs;
                    break;
                case 'fault':
                    // sect 3.6
                    // soap:fault attributes: name use  encodingStyle namespace
                    $this->wsdl->bindings[$this->currentBinding]
                                    ['operations'][$this->currentOperation][$this->opStatus] = $attrs;
                    break;
                case 'header':
                    // sect 3.7
                    // soap:header attributes: message part use encodingStyle namespace
                    $this->wsdl->bindings[$this->currentBinding]
                                    ['operations'][$this->currentOperation][$this->opStatus]['headers'][] = $attrs;
                    break;
                case 'headerfault':
                    // sect 3.7
                    // soap:header attributes: message part use encodingStyle namespace
                    $header = count($this->wsdl->bindings[$this->currentBinding]
                                    ['operations'][$this->currentOperation][$this->opStatus]['headers'])-1;
                    $this->wsdl->bindings[$this->currentBinding]
                                    ['operations'][$this->currentOperation][$this->opStatus]['headers'][$header]['fault'] = $attrs;
                    break;
                case 'documentation':
                    break;
                default:
                    // error!  not a valid element inside binding
                    break;
                }
                break;
            case SCHEMA_WSDL:
                // XXX verify correct namespace
                // for now, default is the 'wsdl' namespace
                // other possible namespaces include smtp, http, etc. for alternate bindings
                switch($qname->name) {
                case 'operation':
                    // sect 2.5
                    // wsdl:operation attributes: name
                    $this->currentOperation = $attrs['name'];
                    break;
                case 'output':
                case 'input':
                case 'fault':
                    // sect 2.5
                    // wsdl:input attributes: name
                    $this->opStatus = $qname->name;
                    break;
                case 'documentation':
                    break;
                default:
                    break;
                }
                break;
            case SCHEMA_WSDL_HTTP:
                switch($qname->name) {
                case 'binding':
                    // sect 4.4
                    // http:binding attributes: verb
                    // parent: wsdl:binding
                    $this->wsdl->bindings[$this->currentBinding] = array_merge($this->wsdl->bindings[$this->currentBinding],$attrs);
                    break;
                case 'operation':
                    // sect 4.5
                    // http:operation attributes: location
                    // parent: wsdl:operation
                    $this->wsdl->bindings[$this->currentBinding]['operations']
                                                        [$this->currentOperation] = $attrs;
                    break;
                case 'urlEncoded':
                    // sect 4.6
                    // http:urlEncoded attributes: location
                    // parent: wsdl:input wsdl:output etc.
                    $this->wsdl->bindings[$this->currentBinding]['operations'][$this->opStatus]
                                                        [$this->currentOperation]['uri'] = 'urlEncoded';
                    break;
                case 'urlReplacement':
                    // sect 4.7
                    // http:urlReplacement attributes: location
                    // parent: wsdl:input wsdl:output etc.
                    $this->wsdl->bindings[$this->currentBinding]['operations'][$this->opStatus]
                                                        [$this->currentOperation]['uri'] = 'urlReplacement';
                    break;
                case 'documentation':
                    break;
                default:
                    // error
                    break;
                }
            case SCHEMA_MIME:
                // sect 5
                // all mime parts are children of wsdl:input, wsdl:output, etc.
                // unsuported as of yet
                switch($qname->name) {
                case 'content':
                    // sect 5.3 mime:content
                    // <mime:content part="nmtoken"? type="string"?/>
                    // part attribute only required if content is child of multipart related,
                    //        it contains the name of the part
                    // type attribute contains the mime type
                case 'multipartRelated':
                    // sect 5.4 mime:multipartRelated
                case 'part':
                case 'mimeXml':
                    // sect 5.6 mime:mimeXml
                    // <mime:mimeXml part="nmtoken"?/>
                    //
                case 'documentation':
                    break;
                default:
                    // error
                    break;
                }
            case SCHEMA_DIME:
                // DIME is defined in:
                // http://gotdotnet.com/team/xml_wsspecs/dime/WSDL-Extension-for-DIME.htm
                // all DIME parts are children of wsdl:input, wsdl:output, etc.
                // unsuported as of yet
                switch($qname->name) {
                case 'message':
                    // sect 4.1 dime:message
                    // appears in binding section
                    $this->wsdl->bindings[$this->currentBinding]['dime'] = $attrs;
                    break;
                default:
                    break;
                }
            default:
                break;
            }
        break;
        case 'service':
            $ns = $qname->ns ? $this->wsdl->namespaces[$qname->ns] : SCHEMA_WSDL;

            switch($qname->name) {
            case 'port':
                // sect 2.6 wsdl:port attributes: name binding
                $this->currentPort = $attrs['name'];
                $this->wsdl->services[$this->currentService]['ports'][$this->currentPort] = $attrs;
                // XXX hack to deal with binding namespaces
                $qn =& new QName($attrs['binding']);
                $this->wsdl->services[$this->currentService]['ports'][$this->currentPort]['binding'] = $qn->name;
                $this->wsdl->services[$this->currentService]['ports'][$this->currentPort]['namespace'] = $qn->ns;
            break;
            case 'address':
                $this->wsdl->services[$this->currentService]['ports'][$this->currentPort]['address'] = $attrs;
                // what TYPE of port is it?  SOAP or HTTP?
                $ns = $qname->ns ? $this->wsdl->namespaces[$qname->ns] : SCHEMA_WSDL;
                switch($ns) {
                case SCHEMA_WSDL_HTTP:
                    $this->wsdl->services[$this->currentService]['ports'][$this->currentPort]['type']='http';
                    break;
                case SCHEMA_SOAP:
                    $this->wsdl->services[$this->currentService]['ports'][$this->currentPort]['type']='soap';
                    break;
                default:
                    // shouldn't happen, we'll assume soap
                    $this->wsdl->services[$this->currentService]['ports'][$this->currentPort]['type']='soap';
                }

            break;
            case 'documentation':
                break;
            default:
                break;
            }
        }

        // top level elements found under wsdl:definitions
        // set status
        switch($qname->name) {
        case 'import':
            // sect 2.1.1 wsdl:import attributes: namespace location
            if (array_key_exists('location',$attrs) &&
                !isset($this->wsdl->imports[$attrs['namespace']])) {
                $uri = $attrs['location'];
                $location = parse_url($uri);
                if (!isset($location['scheme'])) {
                    $base = parse_url($this->uri);
                    $uri = $this->merge_url($base,$uri);
                }
                $import_parser =& new SOAP_WSDL_Parser($uri, $this->wsdl);
                if ($import_parser->fault) {
                    return FALSE;
                }
                $this->currentImport = $attrs['namespace'];
                $this->wsdl->imports[$this->currentImport] = $attrs;
            }
            $this->status = '';
        case 'types':
            // sect 2.2 wsdl:types
            $this->status = 'types';
        break;
        case 'message':
            // sect 2.3 wsdl:message attributes: name children:wsdl:part
            $this->status = 'message';
            if (isset($attrs['name'])) {
                $this->currentMessage = $attrs['name'];
                $this->wsdl->messages[$this->currentMessage] = array();
            }
        break;
        case 'portType':
            // sect 2.4 wsdl:portType
            // attributes: name
            // children: wsdl:operation
            $this->status = 'portType';
            $this->currentPortType = $attrs['name'];
            $this->wsdl->portTypes[$this->currentPortType] = array();
        break;
        case 'binding':
            // sect 2.5 wsdl:binding attributes: name type
            // children: wsdl:operation soap:binding http:binding
            if ($qname->ns && $qname->ns != $this->tns) break;
            $this->status = 'binding';
            $this->currentBinding = $attrs['name'];
            $qn =& new QName($attrs['type']);
            $this->wsdl->bindings[$this->currentBinding]['type'] = $qn->name;
            $this->wsdl->bindings[$this->currentBinding]['namespace'] = $qn->ns;
        break;
        case 'service':
            // sect 2.7 wsdl:service attributes: name children: ports
            $this->currentService = $attrs['name'];
            $this->wsdl->services[$this->currentService]['ports'] = array();
            $this->status = 'service';
        break;
        case 'definitions':
            // sec 2.1 wsdl:definitions
            // attributes: name targetNamespace xmlns:*
            // children: wsdl:import wsdl:types wsdl:message wsdl:portType wsdl:binding wsdl:service
            #$this->status = 'definitions';
            $this->wsdl->definition = $attrs;
            foreach ($attrs as $key => $value) {
                if (strstr($key,'xmlns:') !== FALSE) {
                    $qn =& new QName($key);
                    // XXX need to refactor ns handling
                    $this->wsdl->namespaces[$qn->name] = $value;
                    $this->wsdl->ns[$value] = $qn->name;
                    if ($key == 'targetNamespace' ||
                        strcasecmp($value,SOAP_SCHEMA) == 0) {
                        $this->soapns[] = $qn->name;
                    } else {
                        if (in_array($value, $this->_XMLSchema)) {
                            $this->wsdl->xsd = $value;
                        }
                    }
                }
            }
            if (isset($ns) && $ns) {
                $namespace = 'xmlns:'.$ns;
                if (!$this->wsdl->definition[$namespace]) {
                    return $this->_raiseSoapFault("parse error, no namespace for $namespace",$this->uri);
                }
                $this->tns = $ns;
            }
        break;
        }
    }


    // end-element handler
    function endElement($parser, $name)
    {
        $stacksize = count($this->element_stack);
        if ($stacksize > 0) {
            if ($this->element_stack[count($this->element_stack)-1] ==  'definitions') {
                $this->status = '';
            }
            array_pop($this->element_stack);
        }
        if (stristr($name,'schema')) {
            array_pop($this->schema_stack);
            $this->schema = '';
        }
        if ($this->schema) {
            array_pop($this->schema_stack);
            if (count($this->schema_stack) <= 1) {
                /* correct the type for sequences with multiple elements */
                if (isset($this->currentComplexType) && isset($this->wsdl->complexTypes[$this->schema][$this->currentComplexType]['type'])
                    && $this->wsdl->complexTypes[$this->schema][$this->currentComplexType]['type'] == 'Array'
                    && array_key_exists('elements',$this->wsdl->complexTypes[$this->schema][$this->currentComplexType])
                    && count($this->wsdl->complexTypes[$this->schema][$this->currentComplexType]['elements']) > 1) {
                        $this->wsdl->complexTypes[$this->schema][$this->currentComplexType]['type'] = 'Struct';
                }
            }
            if (stristr($name,'complexType')) {
                $this->currentComplexType = '';
                if (count($this->schema_element_stack) > 0)
                    $this->currentElement = array_pop($this->schema_element_stack);
                else
                    $this->currentElement = '';
            } else if (stristr($name,'element')) {
                if (count($this->schema_element_stack) > 0)
                    $this->currentElement = array_pop($this->schema_element_stack);
                else
                    $this->currentElement = '';
            }
        }
        // position of current element is equal to the last value left in depth_array for my depth
        //$pos = $this->depth_array[$this->depth];
        // bring depth down a notch
        //$this->depth--;
    }

    // element content handler
    function characterData($parser, $data)
    {
        # store the documentation in the WSDL file
        if ($this->currentTag == 'documentation') {
            if ($this->status ==  'service') {
                $this->wsdl->services[$this->currentService][$this->currentTag] .= $data;
            } else if ($this->status ==  'portType') {
                if ($this->wsdl->portTypes[$this->currentPortType][$this->currentOperation][$this->currentTag])
                    $this->wsdl->portTypes[$this->currentPortType][$this->currentOperation][$this->currentTag] .= data;
                else
                    $this->wsdl->portTypes[$this->currentPortType][$this->currentOperation][$this->currentTag] = data;
            } else if ($this->status ==  'binding') {
                if ($this->wsdl->bindings[$this->currentBinding][$this->currentTag])
                    $this->wsdl->bindings[$this->currentBinding][$this->currentTag] .= data;
                else
                    $this->wsdl->bindings[$this->currentBinding][$this->currentTag] = data;
            } else if ($this->status ==  'message') {
                if ($this->wsdl->messages[$this->currentMessage][$this->currentTag])
                    $this->wsdl->messages[$this->currentMessage][$this->currentTag] .= data;
                else
                    $this->wsdl->messages[$this->currentMessage][$this->currentTag] = data;
            } else if ($this->status ==  'operation') {
                if ($this->wsdl->portTypes[$this->currentPortType][$this->currentOperation][$this->currentTag])
                    $this->wsdl->portTypes[$this->currentPortType][$this->currentOperation][$this->currentTag] .= data;
                else
                    $this->wsdl->portTypes[$this->currentPortType][$this->currentOperation][$this->currentTag] = data;
            }
        }
    }


    // $parsed is a parse_url() resulting array
    function merge_url($parsed,$path) {

        if (! is_array($parsed)) return false;

        if (isset($parsed['scheme'])) {
            $sep = (strtolower($parsed['scheme']) == 'mailto' ? ':' : '://');
            $uri = $parsed['scheme'] . $sep;
        } else {
            $uri = '';
        }

        if (isset($parsed['pass'])) {
            $uri .= "$parsed[user]:$parsed[pass]@";
        } elseif (isset($parsed['user'])) {
            $uri .= "$parsed[user]@";
        }

        if (isset($parsed['host']))     $uri .= $parsed['host'];
        if (isset($parsed['port']))     $uri .= ":$parsed[port]";
        if ($path[0]!='/' && isset($parsed['path'])) {
            if ($parsed['path'][strlen($parsed['path'])-1] != '/') {
                $path = dirname($parsed['path']).'/'.$path;
            } else {
                $path = $parsed['path'].$path;
            }
            $path = $this->_normalize($path);
        }
        $sep = $path[0]=='/'?'':'/';
        $uri .= $sep.$path;

        return $uri;
    }

    function _normalize($path_str){
        $pwd='';
        $strArr=preg_split("/(\/)/",$path_str,-1,PREG_SPLIT_NO_EMPTY);
        $pwdArr="";
        $j=0;
        for($i=0;$i<count($strArr);$i++){
            if($strArr[$i]!=".."){
                if($strArr[$i]!="."){
                $pwdArr[$j]=$strArr[$i];
                $j++;
                }
            }else{
                array_pop($pwdArr);
                $j--;
            }
        }
        $pStr=implode("/",$pwdArr);
        $pwd=(strlen($pStr)>0) ? ("/".$pStr) : "/";
        return $pwd;
    }
}

/**
 * Parses the types and methods used in web service objects into the internal
 * data structures used by SOAP_WSDL.
 *
 * Assumes the SOAP_WSDL class is unpopulated to start with.
 *
 * @author Chris Coe <info@intelligentstreaming.com>
 */
class SOAP_WSDL_ObjectParser extends SOAP_Base
{
    // Target namespace for the WSDL document will have the following prefix
    var $tnsPrefix = 'tns';

    // Reference to the SOAP_WSDL object to populate
    var $wsdl = null;

    /** Constructor
     *
     * @param  $objects Reference to the object or array of objects to parse
     * @param  $wsdl Reference to the SOAP_WSDL object to populate
     * @param  $targetNamespace The target namespace of schema types etc.
     * @param  $service_name Name of the WSDL <service>
     * @param  $service_desc Optional description of the WSDL <service>
     */
    function SOAP_WSDL_ObjectParser(&$objects, &$wsdl, $targetNamespace, $service_name, $service_desc = '') {
        parent::SOAP_Base('WSDLOBJECTPARSER');

        $this->wsdl = &$wsdl;

        // Set up the SOAP_WSDL object
        $this->_initialise($service_name);

        // Parse each web service object
        $wsdl_ref = (is_array($objects)? $objects : array(&$objects));

        foreach ($wsdl_ref as $ref_item) {
            if (!is_object($ref_item))
                return $this->_raiseSoapFault('Invalid web service object passed to object parser', 'urn:' . get_class($object));

            if ($this->_parse($ref_item, $targetNamespace, $service_name) != true)
                break;
        }

        // Build bindings from abstract data
        if ($this->fault == NULL)
            $this->_generateBindingsAndServices($targetNamespace, $service_name, $service_desc);
    }

    /** Initialise the SOAP_WSDL tree (destructive)
     *
     * If the object has already been initialised, the only effect will be to
     * change the tns namespace to the new service name
     *
     * @param  $service_name Name of the WSDL <service>
     * @access private
     */
    function _initialise($service_name) {
        // Set up the basic namespaces that all WSDL definitions use

        $this->wsdl->namespaces['wsdl'] = SCHEMA_WSDL;                                      // WSDL language
        $this->wsdl->namespaces['soap'] = SCHEMA_SOAP;                                      // WSDL SOAP bindings
        $this->wsdl->namespaces[$this->tnsPrefix] = 'urn:' . $service_name;                 // Target namespace
        $this->wsdl->namespaces['xsd'] = array_search('xsd', $this->_namespaces);           // XML Schema
        $this->wsdl->namespaces['SOAP-ENC'] = array_search('SOAP-ENC', $this->_namespaces); // SOAP types

        // XXX Refactor $namespace/$ns for Shane :-)
        unset($this->wsdl->ns['urn:' . $service_name]);
        $this->wsdl->ns += array_flip($this->wsdl->namespaces);

        // Imports are not implemented in WSDL generation from classes
        // *** <wsdl:import> ***
    }

    /** Parser - takes a single object to add to tree (non-destructive)
     *
     * @param  $object Reference to the object to parse
     * @param  $service_name Name of the WSDL <service>
     * @access private
     */
    function _parse(&$object, $schemaNamespace, $service_name) {
        // Create namespace prefix for the schema
        // XXX not very elegant :-(

        list ($schPrefix, $foo) = $this->_getTypeNs('{'.$schemaNamespace.'}');
        unset($foo);

        // Parse all the types defined by the object in whatever
        // schema language we are using (currently __typedef arrays)
        // *** <wsdl:types> ***

        foreach ($object->__typedef as $typeName => $typeValue)
        {
            // Get/create namespace definition

            list($nsPrefix, $typeName) = $this->_getTypeNs($typeName);

            // Create type definition

            $this->wsdl->complexTypes[$schPrefix][$typeName] = array("name" => $typeName);
            $thisType =& $this->wsdl->complexTypes[$schPrefix][$typeName];

            // According to Dmitri's documentation, __typedef comes in two
            // flavors:
            // Array = array(array("item" => "value"))
            // Struct = array("item1" => "value1", "item2" => "value2", ...)

            if (is_array($typeValue))
            {
                reset($typeValue);
                if (is_array(current($typeValue)) && count($typeValue) == 1
                        && count(current($typeValue)) == 1)
                {
                    // It's an array

                    $thisType['type'] = 'Array';
                    reset(current($typeValue));
                    list($nsPrefix, $typeName) = $this->_getTypeNs(current(current($typeValue)));
                    $thisType['namespace'] = $nsPrefix;
                    $thisType['arrayType'] = $typeName . '[]';

                }
                else if (!is_array(current($typeValue)))
                {
                    // It's a struct

                    $thisType['type'] = 'Struct';
                    $thisType['order'] = 'all';
                    $thisType['namespace'] = $nsPrefix;
                    $thisType['elements'] = array();

                    foreach ($typeValue as $elementName => $elementType)
                    {
                        list($nsPrefix, $typeName) = $this->_getTypeNs($elementType);
                        $thisType['elements'][$elementName]['name'] = $elementName;
                        $thisType['elements'][$elementName]['type'] = $typeName;
                        $thisType['elements'][$elementName]['namespace'] = $nsPrefix;
                    }
                }
                else
                {
                    // It's erroneous

                    return $this->_raiseSoapFault("The type definition for $nsPrefix:$typeName is invalid.", 'urn:' . get_class($object));
                }
            } else {
                // It's erroneous

               return $this->_raiseSoapFault("The type definition for $nsPrefix:$typeName is invalid.", 'urn:' . get_class($object));
            }
        }

        // Create an empty element array with the target namespace prefix,
        // to match the results of WSDL parsing

        $this->wsdl->elements[$schPrefix] = array();

        // Populate tree with message information
        // *** <wsdl:message> ***

        foreach ($object->__dispatch_map as $operationName => $messages)
        {
            foreach ($messages as $messageType => $messageParts)
            {
                unset($thisMessage);

                switch ($messageType) {
                case 'in':
                    $this->wsdl->messages[$operationName . 'Request'] = array();
                    $thisMessage =& $this->wsdl->messages[$operationName . 'Request'];
                    break;

                case 'out':
                    $this->wsdl->messages[$operationName . 'Response'] = array();
                    $thisMessage =& $this->wsdl->messages[$operationName . 'Response'];
                    break;

                case 'alias':
                    // Do nothing
                    break;

                default:
                    // Error condition
                    break;
                }

                if (isset($thisMessage))
                {
                    foreach ($messageParts as $partName => $partType)
                    {
                        list ($nsPrefix, $typeName) = $this->_getTypeNs($partType);

                        $thisMessage[$partName] = array(
                            'name' => $partName,
                            'type' => $typeName,
                            'namespace' => $nsPrefix
                            );
                    }
                }
            }
        }

        // Populate tree with portType information
        // XXX Current implementation only supports one portType that
        // encompasses all of the operations available.
        // *** <wsdl:portType> ***

        if (!isset($this->wsdl->portTypes[$service_name . 'Port']))
            $this->wsdl->portTypes[$service_name . 'Port'] = array();
        $thisPortType =& $this->wsdl->portTypes[$service_name . 'Port'];

        foreach ($object->__dispatch_map as $operationName => $messages)
        {
            $thisPortType[$operationName] = array('name' => $operationName);

            foreach ($messages as $messageType => $messageParts)
            {
                switch ($messageType) {
                case 'in':
                    $thisPortType[$operationName]['input'] = array(
                            'message' => $operationName . 'Request',
                            'namespace' => $this->tnsPrefix);
                    break;

                case 'out':
                    $thisPortType[$operationName]['output'] = array(
                            'message' => $operationName . 'Response',
                            'namespace' => $this->tnsPrefix);
                    break;

                default:
                    break;
                }
            }
        }

        return true;
    }

    /** Take all the abstract WSDL data and build concrete bindings and services (destructive)
     *
     * XXX Current implementation discards $service_desc.
     *
     * @param  $schemaNamespace Namespace for types etc.
     * @param  $service_name Name of the WSDL <service>
     * @param  $service_desc Optional description of the WSDL <service>
     * @access private
     */
    function _generateBindingsAndServices($schemaNamespace, $service_name, $service_desc = '')
    {
        // Populate tree with bindings information
        // XXX Current implementation only supports one binding that
        // matches the single portType and all of its operations.
        // XXX Is this the correct use of $schemaNamespace here?
        // *** <wsdl:binding> ***

        $this->wsdl->bindings[$service_name . 'Binding'] = array(
                'type' => $service_name . 'Port',
                'namespace' => $this->tnsPrefix,
                'style' => 'rpc',
                'transport' => SCHEMA_SOAP_HTTP,
                'operations' => array());
        $thisBinding =& $this->wsdl->bindings[$service_name . 'Binding'];

        foreach ($this->wsdl->portTypes[$service_name . 'Port'] as $operationName => $operationData)
        {
            $thisBinding['operations'][$operationName] = array(
                'soapAction' => $schemaNamespace . '#' . $operationName,
                'style' => $thisBinding['style']);

            foreach (array('input', 'output') as $messageType)
                if (isset($operationData[$messageType]))
                    $thisBinding['operations'][$operationName][$messageType] = array(
                            'use' => 'encoded',
                            'namespace' => $schemaNamespace,
                            'encodingStyle' => SOAP_SCHEMA_ENCODING);
        }

        // Populate tree with service information
        // XXX Current implementation supports one service which groups
        // all of the ports together, one port per binding
        // XXX What about https?
        // *** <wsdl:service> ***

        $this->wsdl->services[$service_name . 'Service'] = array('ports' => array());
        $thisService =& $this->wsdl->services[$service_name . 'Service']['ports'];

        foreach ($this->wsdl->bindings as $bindingName => $bindingData)
        {
            $thisService[$bindingData['type']] = array(
                    'name' => $bindingData['type'],
                    'binding' => $bindingName,
                    'namespace' => $this->tnsPrefix,
                    'address' => array('location' =>
                        'http://' . $_SERVER['SERVER_NAME'] . $_SERVER['PHP_SELF'] .
                        (isset($_SERVER['QUERY_STRING']) ? '?' . $_SERVER['QUERY_STRING'] : '')),
                    'type' => 'soap');
        }

        // Set service
        $this->wsdl->set_service($service_name . 'Service');
        $this->wsdl->uri = $this->wsdl->namespaces[$this->tnsPrefix];

        // Create WSDL definition
        // *** <wsdl:definitions> ***

        $this->wsdl->definition = array(
                'name' => $service_name,
                'targetNamespace' => $this->wsdl->namespaces[$this->tnsPrefix],
                'xmlns' => SCHEMA_WSDL);

        foreach ($this->wsdl->namespaces as $nsPrefix => $namespace)
            $this->wsdl->definition['xmlns:' . $nsPrefix] = $namespace;
    }

    // This function is adapted from Dmitri V's implementation of
    // DISCO/WSDL generation. It separates namespace from type name in a
    // __typedef key and creates a new namespace entry in the WSDL structure
    // if the namespace has not been used before. The namespace prefix and
    // type name are returned. If no namespace is specified, xsd is assumed.
    //
    // We will not need this function anymore once __typedef is eliminated.
    function _getTypeNs($type) {
        preg_match_all("'\{(.*)\}'sm",$type,$m);
        if (isset($m[1][0]) && $m[1][0] != '') {
            if (!array_key_exists($m[1][0],$this->wsdl->ns)) {
                $ns_pref = 'ns' . count($this->wsdl->namespaces);
                $this->wsdl->ns[$m[1][0]] = $ns_pref;
                $this->wsdl->namespaces[$ns_pref] = $m[1][0];
            }
            $typens = $this->wsdl->ns[$m[1][0]];
            $type = ereg_replace($m[0][0],'',$type);
        } else {
            $typens = 'xsd';
        }
        return array($typens,$type);
    }
}
?>
