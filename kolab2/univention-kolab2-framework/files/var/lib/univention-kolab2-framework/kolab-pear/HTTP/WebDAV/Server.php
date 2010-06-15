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
// | Authors: Hartmut Holzgraefe <hholzgra@php.net>                       |
// |          Christian Stocker <chregu@bitflux.ch>                       |
// +----------------------------------------------------------------------+
//
// $Id: Server.php,v 1.1.2.1 2005/10/05 14:39:45 steuwer Exp $
//
// WebDAV server base class, needs to be extended to do useful work
//
// require_once "HTTP/HTTP.php";
require_once "HTTP/WebDAV/Tools/_parse_propfind.php";
require_once "HTTP/WebDAV/Tools/_parse_proppatch.php";
require_once "HTTP/WebDAV/Tools/_parse_lockinfo.php";



  /**
   * Virtual base class for implementing WebDAV servers 
   *
   * this is it
   * bla bla
   * 
   * @package HTTP_WebDAV_Server
   * @author Hartmut Holzgraefe <hholzgra@php.net>
   * @version 0.95dev
   */
class HTTP_WebDAV_Server {
    // {{{ Member Variables 
    
                /**
         * URI path for this request
         *
         * @var string 
         */
    var $path;

                /**
         * Realm string to be used in authentification popups
         *
         * @var string 
         */
    var $http_auth_realm = "PHP WebDAV";

                /**
         * Remember parsed If: (RFC2518/9.4) header conditions  
         *
         * @var array
         */
    var $_if_header_uris = array();


    var $_http_status = "200 OK";

    var $_prop_encoding = "utf-8";
    // }}}

    // {{{ Constructor 

                /** 
         * Constructor
         *
         * @param void
         */
    function HTTP_WebDAV_Server() {
        // PHP messages destroy XML output -> switch them off
        ini_set("display_errors", 0);
    }

    // }}}
    // {{{ ServeRequest() 
/** 
         * Serve WebDAV HTTP request
         *
         * dispatch WebDAV HTTP request to the apropriate method handler
         * 
         * @param void
         * @return void
         */
    function ServeRequest() {
            // identify ourselves
            header("X-Dav-Powered-By: PHP class: ".get_class($this));

            if (!$this->_check_auth()) {
                // RFC2518 says we must use Digest instead of Basic
                // but Microsoft Clients do not support Digest
                // and we don't support NTLM and M$-Kerberos
                // so we are stuck with Basic here
                header('WWW-Authenticate: Basic realm="'.($this->http_auth_realm).'"');
                header('HTTP/1.0 401 Unauthorized');

                exit;
            }

            if(! $this->_check_if_header_conditions()) {
                header("HTTP/1.0 412 Precondition failed");
                exit;
            }

            // set path
            $this->path =
                $this->_urldecode(!empty($_SERVER["PATH_INFO"]) ? $_SERVER["PATH_INFO"] : "/");
            if(ini_get("magic_quotes_gpc")) {
                $this->path = stripslashes($this->path);
            }


            // detect requested method names
            $method = strtolower($_SERVER["REQUEST_METHOD"]);
            $wrapper = "http_".$method;

            // activate HEAD emulation by GET if no HEAD method found
            if ($method == "head" && !method_exists($this, "head")) {
                $method = "get";
            }

            if (method_exists($this, $wrapper) &&
                    ($method == "options" || method_exists($this, $method))) {
                $this->$wrapper();  // call method by name
            } else {
                if ($_SERVER["REQUEST_METHOD"] == "LOCK") {
                    $this->http_status("412 Precondition failed");
                } else {
                    $this->http_status("405 Method not allowed");
                    header("Allow: ".join(", ", $this->_allow()));  // tell client what's allowed
                }
            }

    }

    // }}}

    // {{{ abstract WebDAV methods 

    // {{{ GET() 
                 /**
         * GET implementation
         *
         * overload this method to retrieve resources from your server
         * <br>
         * 
         *
         * @abstract 
         * @param array &$params Array of input and output parameters
         * <br><b>input</b><ul>
         * <li> path - 
         * </ul>
         * <br><b>output</b><ul>
         * <li> size - 
         * </ul>
         * @returns int HTTP-Statuscode
         */

    /* abstract
       function GET(&$params) {
       // dummy entry for PHPDoc
       } 
     */

    // }}}

    // {{{ PUT() 
                /**
         * PUT implementation
         *
         * PUT implementation
         *
         * @abstract 
         * @param array &$params
         * @returns int HTTP-Statuscode
         */

    /* abstract
       function PUT() {
       // dummy entry for PHPDoc
       } 
     */

    // }}}

    // {{{ COPY() 

                /**
         * COPY implementation
         *
         * COPY implementation
         *
         * @abstract 
         * @param array &$params
         * @returns int HTTP-Statuscode
         */

    /* abstract
       function COPY() {
       // dummy entry for PHPDoc
       } 
     */

    // }}}

    // {{{ MOVE() 

                /**
         * MOVE implementation
         *
         * MOVE implementation
         *
         * @abstract 
         * @param array &$params
         * @returns int HTTP-Statuscode
         */

    /* abstract
       function MOVE() {
       // dummy entry for PHPDoc
       } 
     */

    // }}}

    // {{{ DELETE() 

                /**
         * DELETE implementation
         *
         * DELETE implementation
         *
         * @abstract 
         * @param array &$params
         * @returns int HTTP-Statuscode
         */

    /* abstract
       function DELETE() {
       // dummy entry for PHPDoc
       } 
     */
    // }}}

    // {{{ PROPFIND() 

                /**
         * PROPFIND implementation
         *
         * PROPFIND implementation
         *
         * @abstract 
         * @param array &$params
         * @returns int HTTP-Statuscode
         */

    /* abstract
       function PROPFIND() {
       // dummy entry for PHPDoc
       } 
     */

    // }}}

    // {{{ PROPPATCH() 

                /**
         * PROPPATCH implementation
         *
         * PROPPATCH implementation
         *
         * @abstract 
         * @param array &$params
         * @returns int HTTP-Statuscode
         */

    /* abstract
       function PROPPATCH() {
       // dummy entry for PHPDoc
       } 
     */
    // }}}

    // {{{ LOCK() 

                /**
         * LOCK implementation
         *
         * LOCK implementation
         *
         * @abstract 
         * @param array &$params
         * @returns int HTTP-Statuscode
         */

    /* abstract
       function LOCK() {
       // dummy entry for PHPDoc
       } 
     */
    // }}}

    // {{{ UNLOCK() 

                /**
         * UNLOCK implementation
         *
         * UNLOCK implementation
         *
         * @abstract 
         * @param array &$params
         * @returns int HTTP-Statuscode
         */

    /* abstract
       function UNLOCK() {
       // dummy entry for PHPDoc
       } 
     */
    // }}}

    // }}}

    // {{{ other abstract methods 

    // {{{ check_auth() 

                 /**
         * check authentication
         *
         * overload this method to retrieve and confirm authentication information
         *
         * @abstract 
         * @param string type Authentication type, e.g. "basic" or "digest"
         * @param string username Transmitted username
         * @param string passwort Transmitted password
         * @returns bool Authentication status
         */

    /* abstract
       function check_auth($type, $username, $password) {
       // dummy entry for PHPDoc
       } 
     */

    // }}}

    // {{{ checklock() 

                 /**
         * check lock status for a resource
         *
         * overload this method to return shared and exclusive locks 
         * active for this resource
         *
         * @abstract 
         * @param string resource Resource path to check
         * @returns array An array of lock entries each consisting
         *                of 'type' ('shared'/'exclusive'), 'token' and 'timeout'
         */

    /* abstract
       function checklock($resource) {
       // dummy entry for PHPDoc
       } 
     */

    // }}}

    // }}}

    // {{{ WebDAV HTTP method wrappers 

    // {{{ http_OPTIONS() 

                /**
         * OPTIONS method handler
         *
         * The OPTIONS method handler creates a valid OPTIONS reply
         * including Dav: and Allowed: heaers
         * based on the implemented methods found in the actual instance
         *
         * @param void
         * @returns void
         */

    function http_OPTIONS() {
        $this->http_status("200 OK");

        // be nice to M$ clients
        header("MS-Author-Via: DAV");

        // get allowed methods
        $allow = $this->_allow();

        // dav header
        $dav = array(1);        // assume we are always dav class 1 compliant
        if (isset($allow['lock']))
            $dav[] = 2;         // dav class 2 requires locking 

        header("DAV: ".join(",", $dav));
        header("Allow: ".join(", ", $allow));
    }

    // }}}


    // {{{ http_PROPFIND() 

    function http_PROPFIND() {
        $options = Array();
        $options["path"] = $this->path;

            if (isset($_SERVER['HTTP_DEPTH'])) {
                $options["depth"] = $_SERVER["HTTP_DEPTH"];
            } else {
                $options["depth"] = "infinity";
            }
            
            $propinfo = new _parse_propfind("php://input");

            if (!$propinfo->success) {
                $this->http_status("400 Error");
                return;
            }
            
            $options['props'] = $propinfo->props;
            
            if ($this->propfind($options, $files)) {
                // collect namespaces
                $ns_hash = array();
                $ns_defs = "xmlns:ns0=\"urn:uuid:c2f41010-65b3-11d1-a29f-00aa00c14882/\"";    // M$ needs this for time values
                foreach($files["files"] as $filekey => $file) {
                    if (@is_array($file["props"])) {
                        foreach($file["props"] as $key => $prop) {
                            // clean up returned properties, leave only requested entries

                            switch($options['props']) {
                            case "all":   
                                break;
                            case "names":
                                unset($files["files"][$filekey]["props"][$key]["val"]);
                                break;
                            default:
                                $found = false;
                                
                                if (is_array($options["props"])) {
                                    foreach($options["props"] as $reqprop) {
                                        if ($reqprop["name"] == $prop["name"]) {
                                            // todo NameSpaces
                                            $found = true;
                                            break;
                                        }
                                    }
                                }
                                
                                if (!$found) {
                                    $files["files"][$filekey]["props"][$key]="";
                                    continue(2);
                                }
                                break;
                            }

                            if (empty($prop["ns"]))
                                continue;
                            $ns = $prop["ns"];
                            if ($ns == "DAV:")
                                continue;
                            if (isset($ns_hash[$ns]))
                                continue;
                            $ns_name = "ns".(count($ns_hash) + 1);
                            $ns_hash[$ns] = $ns_name;
                            $ns_defs .= " xmlns:$ns_name=\"$ns\"";
                        }
                    }
                    // add entries requested but not found
                    if (is_array($options['props'])) {
                        foreach($options["props"] as $reqprop) {
                            if($reqprop['name']=="") continue;
                            $found = false;
                            foreach($file["props"] as $prop) {
                                if ($reqprop["name"] == $prop["name"]) {
                                    // todo NameSpaces
                                    $found = true;
                                    break;
                                }
                            }
                            if (!$found) {
                                if($reqprop["xmlns"]==="DAV:" && $reqprop["name"]==="lockdiscovery") {
                                    $files["files"][$filekey]["props"][] 
                                        = $this->mkprop("DAV:", "lockdiscovery" , $this->lockdiscovery($files["files"][$filekey]['path']));
                                } else {
                                    $files["files"][$filekey]["noprops"][] =
                                        $this->mkprop($reqprop["xmlns"], $reqprop["name"], "");
                                    if ($reqprop["xmlns"] != "DAV:" &&
                                        !isset($ns_hash[$reqprop["xmlns"]])) {
                                        $ns_name = "ns".(count($ns_hash) + 1);
                                        $ns_hash[$reqprop["xmlns"]] = $ns_name;
                                        $ns_defs .= " xmlns:$ns_name=\"$reqprop[xmlns]\"";
                                    }
                                }
                            }
                        }
                    }
                }
                
                $this->http_status("207 Multi-Status");
                header('Content-Type: text/xml; charset="utf-8"');

                echo "<?xml version=\"1.0\" encoding=\"utf-8\"?>\n";
                echo "<D:multistatus xmlns:D=\"DAV:\">\n";

                foreach($files["files"] as $file) {
                    if(!is_array($file) || empty($file) || !isset($file["path"])) continue;
                    echo " <D:response $ns_defs>\n";
                    $path = $file['path'];                  
                    if(!is_string($path) || $path==="") continue;
                    // todo: make sure collection hrefs end in '/'
                    // http://$_SERVER[HTTP_HOST]
                    echo "  <D:href>".$this->_urlencode($_SERVER["SCRIPT_NAME"].$path)."</D:href>\n";
                    echo "   <D:propstat>\n";
                    echo "    <D:prop>\n";
                    if (@is_array($file["props"])) {
                        foreach($file["props"] as $key => $prop) {
                            if (!is_array($prop)) continue;
                            if (!isset($prop["name"])) continue;

                            if (!isset($prop["val"]) || $prop["val"] === "" || $prop["val"] === false) {
                                if($prop["ns"]=="DAV:") {
                                    echo "     <D:$prop[name]/>\n";
                                } else if($prop["ns"]) {
                                    echo "     <".$ns_hash[$prop["ns"]].":$prop[name]/>\n";
                                } else {
                                    echo "     <$prop[name] xmlns=\"\"/>";
                                }
                            } else if ($prop["ns"] == "DAV:") {
                                switch ($prop["name"]) {
                                case "creationdate":
                                    echo "     <D:creationdate ns0:dt=\"dateTime.tz\">".
                                        date("Y-m-d\\TH:i:s\\Z",$prop['val']).
                                        "</D:creationdate>\n";
                                    break;
                                case "getlastmodified":
                                    echo "     <D:getlastmodified ns0:dt=\"dateTime.rfc1123\">".
                                        date("D, j M Y H:m:s ",
                                                 $prop['val']).
                                        "GMT</D:getlastmodified>\n";
                                    break;
                                case "resourcetype":
                                    echo "     <D:resourcetype><D:$prop[val]/></D:resourcetype>\n";
                                    break;
                                case "supportedlock":
                                    echo "     <D:supportedlock>$prop[val]</D:supportedlock>\n";
                                    break;
                                case "lockdiscovery":  
                                    echo "     <D:lockdiscovery>\n";
                                    echo $prop["val"];
                                    echo "     </D:lockdiscovery>\n";
                                    break;
                                default:                                    
                                    echo "     <D:$prop[name]>".
                                        $this->prop_encode(htmlspecialchars
                                                                ($prop['val'])).
                                        "</D:$prop[name]>\n";                               
                                    break;
                                }
                            } else {
                                if ($prop["ns"]) {
                                    echo "     <".$ns_hash[$prop["ns"]].
                                        ":$prop[name]>".
                                        $this->prop_encode(htmlspecialchars
                                                                ($prop['val']))."</".
                                        $ns_hash[$prop["ns"]].
                                        ":$prop[name]>\n";
                                } else {
                                    echo "     <$prop[name] xmlns=\"\">".
                                        $this->prop_encode(htmlspecialchars
                                                                ($prop['val'])).
                                        "</$prop[name]>\n";
                                }                               
                            }
                        }
                    }
                    echo "   </D:prop>\n";
                    echo "   <D:status>HTTP/1.1 200 OK</D:status>\n";
                    echo "  </D:propstat>\n";

                    if (@is_array($file["noprops"])) {
                        echo "   <D:propstat>\n";
                        echo "    <D:prop>\n";
                        foreach($file["noprops"] as $key => $prop) {
                            if (!is_array($prop))
                                $prop = array("val" => $prop);
                            if ($prop["ns"] == "DAV:") {
                                echo "     <D:$prop[name]/>\n";
                            } else if ($prop["ns"] == "") {
                                echo "     <$prop[name] xmlns=\"\"/>\n";
                            } else {
                                echo "     <".$ns_hash[$prop["ns"]].
                                    ":$prop[name]/>\n";
                            }
                        }
                        echo "   </D:prop>\n";
                        echo "   <D:status>HTTP/1.1 404 Not Found</D:status>\n";
                        echo "  </D:propstat>\n";
                    }

                    echo " </D:response>\n";
                }

                echo "</D:multistatus>\n";
            } else {
                $this->http_status("404 Not Found");
            }
    }

    // }}}

    // {{{ http_PROPPATCH() 

    function http_PROPPATCH() {
        if($this->_check_lock_status($this->path)) {
            $options = Array();
            $options["path"] = $this->path;

            $propinfo = new _parse_proppatch("php://input");

            if (!$propinfo->success) {
                $this->http_status("400 Error");
                return;
            }

            $options['props'] = $propinfo->props;

            $responsedescr = $this->proppatch($options);

            $this->http_status("207 Multi-Status");
            header('Content-Type: text/xml; charset="utf-8"');

            echo "<?xml version=\"1.0\" encoding=\"utf-8\"?>\n";

            echo "<D:multistatus xmlns:D=\"DAV:\">\n";
            echo " <D:response>\n";
            echo "  <D:href>".$this->_urlencode($_SERVER["SCRIPT_NAME"].$this->path)."</D:href>\n";

            foreach($options["props"] as $prop) {
                echo "   <D:propstat>\n";
                echo "    <D:prop><$prop[name] xmlns=\"$prop[ns]\"/></D:prop>\n";
                echo "    <D:status>HTTP/1.1 $prop[status]</D:status>\n";
                echo "   </D:propstat>\n";
            }

            if ($responsedescr) {
                echo "  <D:responsedescription>".
                    $this->prop_encode(htmlspecialchars($responsedescr)).
                    "</D:responsedescription>\n";
            }

            echo " </D:response>\n";
            echo "</D:multistatus>\n";
        } else {
            $this->http_status("423 Locked");
        }
    }

    // }}}


    // {{{ http_MKCOL() 

    function http_MKCOL() {
        $options = Array();
        $options["path"] = $this->path;

        $stat = $this->mkcol($options);

        $this->http_status($stat);
    }

    // }}}


    // {{{ http_GET() 

                /**
         * GET wrapper
         *
         * GET wrapper
         *
         * @param void
         * @returns void
         */

    function http_GET() {
        $options = Array();
        $options["path"] = $this->path;

        $this->_get_ranges($options);

        if (true == ($status = $this->get($options))) {
            if (!headers_sent()) {
                $status = "200 OK";

                if (!isset($options['mimetype'])) {
                    $options['mimetype'] = "application/octet-stream";
                }
                header("Content-type: $options[mimetype]");
                    
                if (isset($options['mtime'])) {
                    header("Last-modified:".date("D, j M Y H:m:s ", $options['mtime'])."GMT");
                }
                
                if (isset($options['stream'])) {
                    // GET handler returned a stream
                    if (!empty($options['ranges']) && (0===fseek($options['stream'], 0, SEEK_SET))) {
                        // partial request and stream is seekable 
                    
                        if (count($options['ranges']) === 1) {
                            $range = $options['ranges'][0];

                            if (isset($range['start'])) {
                                fseek($options['stream'], $range['start'], SEEK_SET);
                                if (feof($options['stream'])) {
                                    http_status("416 Requested range not satisfiable");
                                    exit;
                                }

                                if (isset($range['end'])) {
                                    $size = $range['end']-$range['start']+1;
                                    http_status("206 partial");
                                    header("Content-length: $size");
                                    header("Content-range: $range[start]-$range[end]/". (isset($options['size']) ? $options['size'] : "*"));
                                    while ($size && !feof($options['stream'])) {
                                        $buffer = fread($options['stream'], 4096);
                                        $size -= strlen($buffer);
                                        echo $buffer;
                                    }
                                } else {
                                    http_status("206 partial");
                                    if (isset($options['size'])) {
                                        header("Content-length: ".($options['size'] - $range['start']));
                                        header("Content-range: $start-$end/". (isset($options['size']) ? $options['size'] : "*"));
                                    }
                                    fpassthru($options['stream']);
                                }
                            } else {
                                header("Content-length: ".$range['last']);
                                fseek($options['stream'], -$range['last'], SEEK_END);
                                fpassthru($options['stream']);
                            }
                        } else {
                            $this->_multipart_byterange_header(); // init multipart
                            foreach ($options['ranges'] as $range) {
                                // TODO what if size unknown? 500?
                                if (isset($range['start'])) {
                                    $from  = $range['start'];
                                    $to    = !empty($range['end']) ? $range['end'] : $options['size']-1; 
                                } else {
                                    $from = $options['size'] - $range['last']-1;
                                    $to = $options['size'] -1;
                                }
                                $total = isset($options['size']) ? $options['size'] : "*"; 
                                $size = $to - $from + 1;
                                $this->_multipart_byterange_header($options['mimetype'], $from, $to, $total);


                                fseek($options['stream'], $start, SEEK_SET);
                                while ($size && !feof($options['stream'])) {
                                    $buffer = fread($options['stream'], 4096);
                                    $size -= strlen($buffer);
                                    echo $buffer;
                                }
                            }
                            $this->_multipart_byterange_header(); // end multipart
                        }
                    } else {
                        // normal request or stream isn't seekable, return full content
                        if (isset($options['size'])) {
                            header("Content-length: ".$options['size']);
                        }
                        fpassthru($options['stream']);
                        return; // no more headers
                    }
                } elseif (isset($options['data']))  {
                    if (is_array($options['data'])) {
                        // reply to partial request
                    } else {
                        header("Content-length: ".strlen($options['data']));
                        echo $data;
                    }
                }
            } 
        } 

        if (false === $status) {
            $this->http_status("404 not found");
        }

        $this->http_status("$status");
    }


    function _get_ranges(&$options) {
        if (isset($_SERVER['HTTP_RANGE'])) {
            if (ereg("bytes[[:space:]]*=[[:space:]]*(.*)", $_SERVER['HTTP_RANGE'], $matches)) {
                $options["ranges"] = array();
                foreach (explode(",", $matches[1]) as $range) {
                    list($start, $end) = explode("-", $range);
                    $options["ranges"][] = ($start==="") ? array("last"=>$end) : array("start"=>$start, "end"=>$end);
                }
            }
        }
    }

    function _multipart_byterange_header($mimetype = false, $from = false, $to=false, $total=false) {
        if ($mimetype == false) {
            if (!isset($this->multipart_separator)) {
                // initial
                $this->multipart_separator = "SEPPARATOR_".md5(microtime());
                header("Content-type: multipart/byteranges; boundary=".$this->multipart_separator);
            } else {
                // final
                echo "\n--{$this->multipart_separator}--";
            }
        } else {
            echo "\n--{$this->multipart_separator}\n";
            echo "Content-type: $mimetype\n";
            echo "Content-range: $from-$to/". ($total === false ? "*" : $total);
            echo "\n\n";
        }
    }

            

    // }}}

    // {{{ http_HEAD() 

    function http_HEAD() {
        $status = false;
        $options = Array();
        $options["path"] = $this->path;
        
        if (method_exists($this, "HEAD")) {
            $status = $this->head($options);
        } else if (method_exists($this, "GET")) {
            ob_start();
            $status = $this->GET($options);
            ob_end_clean();
        }
        
        if($status===true)  $status = "200 OK";
        if($status===false) $status = "404 Not found";
        
        $this->http_status($status);
    }

    // }}}

    // {{{ http_PUT() 

    function http_PUT() {
        if ($this->_check_lock_status($this->path)) {
            $options = Array();
            $options["path"] = $this->path;
            $options["content_length"] = $_SERVER["CONTENT_LENGTH"];

            // get the Content-type 
            if (isset($_SERVER["CONTENT_TYPE"])) {
                // for now we do not support any sort of multipart requests
                if (!strncmp($_SERVER["CONTENT_TYPE"], "multipart/", 10)) {
                    $this->http_status(501); 
                    return;
                }
                $options["content_type"] = $_SERVER["CONTENT_TYPE"];
            } else {
                // default content type if none given
                $options["content_type"] = "application/octet-stream";
            }

            /* RFC 2616 2.6 says "The recipient of the entity MUST NOT 
               ignore any Content-* (e.g. Content-Range) headers that it 
               does not understand or implement and MUST return a 501 
               (Not Implemented) response in such cases.
            */
            foreach ($_SERVER as $key => $val) {
                if (strncmp($key, "HTTP_CONTENT", 11)) continue;
                switch ($key) {
                case 'HTTP_CONTENT_ENCODING': // RFC 2616 14.11
                    // TODO support this if ext/zlib filters are available
                    $this->http_status(501); 
                    return;

                case 'HTTP_CONTENT_LANGUAGE': // RFC 2616 14.12
                    // we assume it is not critical if this one is ignored
                    // in the actual PUT implementation ...
                    $options["content_language"] = $value;
                    break;

                case 'HTTP_CONTENT_LOCATION': // RFC 2616 14.14
                    /* The meaning of the Content-Location header in PUT 
                       or POST requests is undefined; servers are free 
                       to ignore it in those cases. */
                    break;

                case 'HTTP_CONTENT_RANGE':    // RFC 2616 14.16
                    // single byte range requests are supported
                    // the header format is also specified in RFC 2616 14.16
                    // TODO we have to ensure that implementations support this or send 501 instead
                    if (!preg_match('@bytes\s+(\d+)-(\d+)/((\d+)|\*)@', $value, $matches)) {
                        $this->http_status(400); 
                        return;
                    }
                    
                    $range = array("start"=>$matches[1], "end"=>$matches[2]);
                    if (is_numeric($matches[3])) {
                        $range["total_length"] = $matches[3];
                    }
                    $option["ranges"][] = $range;

                    // TODO make sure the implementation supports partial PUT
                    // this has to be done in advance to avoid data being overwritten
                    // on implementations that do not support this ...
                    break;

                case 'HTTP_CONTENT_MD5':      // RFC 2616 14.15
                    // TODO: maybe we can just pretend here?
                    $this->http_status(501); 
                    return;

                default: 
                    // any other unknown Content-* headers
                    $this->http_status(501); 
                    return;
                }
            }

            $options["stream"] = fopen("php://input", "r");

            $stat = $this->PUT($options);

            if (is_resource($stat) && get_resource_type($stat) == "stream") {
                $stream = $stat;
                if (!empty($options["ranges"])) {
                    // TODO multipart support is missing (see also above)
                    // TODO error checking
                    $stat = fseek($stream, $range[0]["start"], SEEK_SET);
                    fwrite($stream, fread($options["stream"], $range[0]["end"]-$range[0]["start"]+1));
                } else {
                    while (!feof($options["stream"])) {
                        fwrite($stream, fread($options["stream"], 4096));
                    }
                }
                fclose($stream);
            
                $stat = $options["new"] ? "201 Created" : "204 No Content";
            } 

            $this->http_status($stat);
        } else {
            $this->http_status("423 Locked");
        }
    }

    // }}}


    // {{{ http_DELETE() 

    function http_DELETE() {
        // RFC 2518 Section 9.2, last paragraph
        if (isset($_SERVER["HTTP_DEPTH"])) {
            if ($_SERVER["HTTP_DEPTH"] != "infinity") {
                $this->http_status("400 Bad Request");
                return;
            }
        }

        if ($this->_check_lock_status($this->path)) {
            $options = Array();
            $options["path"] = $this->path;

            $stat = $this->delete($options);

            $this->http_status($stat);
        } else {
            $this->http_status("423 Locked");
        }
    }

    // }}}

    // {{{ http_COPY() 

    function http_COPY() {
        $this->_copymove("copy");
    }

    // }}}

    // {{{ http_MOVE() 

    function http_MOVE() {
        if ($this->_check_lock_status($this->path)) {
            $this->_copymove("move");
        } else {
            $this->http_status("423 Locked");
        }
    }

    // }}}


    // {{{ http_LOCK() 

    function http_LOCK() {
        $lockinfo = new _parse_lockinfo("php://input");

        if($this->_check_lock_status($this->path, $lockinfo->lockscope === "shared")) {
            $options = Array();
            $options["path"] = $this->path;

            if (isset($_SERVER['HTTP_DEPTH'])) {
                $options["depth"] = $_SERVER["HTTP_DEPTH"];
            } else {
                $options["depth"] = "infinity";
            }

            if (isset($_SERVER["HTTP_TIMEOUT"])) {
                $options["timeout"] = explode(",", $_SERVER["HTTP_TIMEOUT"]);
            }

            if(empty($_SERVER['CONTENT_LENGTH']) && !empty($_SERVER['HTTP_IF'])) {
                $options["update"] = substr($_SERVER['HTTP_IF'],2,-2);
                $stat = $this->lock($options);
            } else { 
                // new lock 
                
                if ($lockinfo->success) {
                    $options["scope"] = $lockinfo->lockscope;
                    $options["type"]  = $lockinfo->locktype;
                    $options["owner"] = $lockinfo->owner;
                }
                

                $options["locktoken"] = $this->_new_locktoken();
                
                $stat = $this->lock($options);              
            }
            
            if(is_bool($stat)) {
                $http_stat = $stat ? "200 OK" : "423 Locked";
            } else {
                $http_stat = $stat;
            }

            $this->http_status($http_stat);

            if($options["timeout"]) {
                // more than a million is considered an absolute timestamp
                // less is more likely a relative value
                if($options["timeout"]>1000000) {
                    $timeout = "Second-".($options['timeout']-time());
                } else {
                    $timeout = "Second-$options[timeout]";
                }
            } else {
                $timeout = "Infinite";
            }
            
            if ($stat == true) {        // ok 
                header('Content-Type: text/xml; charset="utf-8"');
                header("Lock-Token: <$options[locktoken]>");
                echo "<?xml version=\"1.0\" encoding=\"utf-8\"?>\n";
                echo "<D:prop xmlns:D=\"DAV:\">\n";
                echo " <D:lockdiscovery>\n";
                echo "  <D:activelock>\n";
                echo "   <D:lockscope><D:$options[scope]/></D:lockscope>\n";
                echo "   <D:locktype><D:$options[type]/></D:locktype>\n";
                echo "   <D:depth>$options[depth]</D:depth>\n";
                echo "   <D:owner>$options[owner]</D:owner>\n";
                echo "   <D:timeout>$timeout</D:timeout>\n";
                echo "   <D:locktoken><D:href>$options[locktoken]</D:href></D:locktoken>\n";
                echo "  </D:activelock>\n";
                echo " </D:lockdiscovery>\n";
                echo "</D:prop>\n\n";
            } else {                // fail 
                // TODO!!!
            }
        } else {
            $this->http_status("423 Locked");
        }
    }

    // }}}

    // {{{ http_UNLOCK() 

    function http_UNLOCK() {
        $options = Array();
        $options["path"] = $this->path;

        if (isset($_SERVER['HTTP_DEPTH'])) {
            $options["depth"] = $_SERVER["HTTP_DEPTH"];
        } else {
            $options["depth"] = "infinity";
        }

        $options["token"] = substr($_SERVER["HTTP_LOCK_TOKEN"], 1, -1); // strip <> 

        $stat = $this->unlock($options);

        $this->http_status($stat);
    }

    // }}}

    // }}}

    // {{{ _copymove() 

    function _copymove($what) {
        $options = Array();
        $options["path"] = $this->path;

        if (isset($_SERVER["HTTP_DEPTH"])) {
            $options["depth"] = $_SERVER["HTTP_DEPTH"];
        } else {
            $options["depth"] = "infinity";
        }

        extract(parse_url($_SERVER["HTTP_DESTINATION"]));
        $http_host = $host;
        if (isset($port))
            $http_host.= ":$port";

        if ($http_host == $_SERVER["HTTP_HOST"] &&
            !strncmp($_SERVER["SCRIPT_NAME"], $path,
                     strlen($_SERVER["SCRIPT_NAME"]))) {
            $options["dest"] = substr($path, strlen($_SERVER["SCRIPT_NAME"]));
            if (!$this->_check_lock_status($options["dest"])) {
                $this->http_status("423 Locked");
                return;
            }

        } else {
            $options["dest_url"] = $_SERVER["HTTP_DESTINATION"];
        }

        // see RFC 2518 Sections 9.6, 8.8.4 and 8.9.3
        if (isset($_SERVER["HTTP_OVERWRITE"])) {
            $options["overwrite"] = $_SERVER["HTTP_OVERWRITE"] == "T";
        } else {
            $options["overwrite"] = true;
        }

        $stat = $this->$what($options);
        $this->http_status($stat);
    }

    // }}}

    // {{{ _allow() 

    /**
         * check for implemented HTTP methods
         *
         * check for implemented HTTP methods
         *
         * @param void
         * @returns array something
         */
    function _allow() {
        // OPTIONS is always there
        $allow = array("options" =>"OPTIONS");

        // all other METHODS need both a http_method() wrapper
        // and a method() implementation
        // the base class supplies wrappers only
        foreach(get_class_methods($this) as $method) {
            if (!strncmp("http_", $method, 5)) {
                $method = substr($method, 5);
                if (method_exists($this, $method)) {
                    $allow[$method] = strtoupper($method);
                }
            }
        }

        // we can emulate a missing HEAD implemetation using GET
        if (isset($allow["get"]))
            $allow["head"] = "HEAD";

        // no LOCK without checklok()
        if (!method_exists($this, "checklock")) {
            unset($allow["lock"]);
            unset($allow["unlock"]);
        }

        return $allow;
    }

    // }}}


    function mkprop() {
        $args = func_get_args();
        if (count($args) == 3) {
            return array("name" =>$args[1],
                         "ns" =>$args[0], "val" =>$args[2]);
        } else {
            return array("name" =>$args[0],
                         "ns" =>"DAV:", "val" =>$args[1]);
        }
    }

    // {{{ _check_auth 

    function _check_auth() {
        if (method_exists($this, "check_auth")) {
            return $this->check_auth(@$_SERVER["AUTH_TYPE"],
                                     @$_SERVER["PHP_AUTH_USER"],
                                     @$_SERVER["PHP_AUTH_PW"]);
        } else {
            return true;
        }
    }

    // }}}

    // {{{ UUID stuff 

    function _new_uuid() {
        if (function_exists("uuid_create")) {
            return uuid_create();
        }
        // fallback
        $uuid = md5(microtime().getmypid());    // this should be random enough for now

        // set variant and version fields for 'true' random uuid
        $uuid {
        12}
        = "4";
        $n = 8 + (ord($uuid {
                      16}
                  ) & 3);
        $hex = "0123456789abcdef";
        $uuid {
        16}
        = $hex {
        $n};

        // return formated uuid
        return substr($uuid, 0, 8)."-".substr($uuid, 8, 4)."-".substr($uuid,
                                                                      12,
                                                                      4)."-".
            substr($uuid, 16, 4)."-".substr($uuid, 20);
    }

    function _new_locktoken() {
        return "opaquelocktoken:".$this->_new_uuid();
    }

    // }}}

    // {{{ WebDAV If: header parsing 

    function _if_header_lexer($string,
                              &$pos) {

        while (ctype_space($string{$pos}))
            ++$pos;             // skip whitespace

        if (strlen($string) <= $pos)
            return false;

        $c = $string{$pos++};
        switch ($c) {
            case "<":
                $pos2 = strpos($string, ">", $pos);
                $uri = substr($string, $pos, $pos2 - $pos);
                $pos = $pos2 + 1;
                return array("URI", $uri);

            case "[":
                if ($string {
                    $pos}
                    == "W") {
                    $type = "ETAG_WEAK";
                    $pos += 2;
                } else {
                    $type = "ETAG_STRONG";
                }
                $pos2 = strpos($string, "]", $pos);
                $etag = substr($string, $pos + 1, $pos2 - $pos - 2);
                $pos = $pos2 + 1;
                return array($type, $etag);

            case "N":
                $pos += 2;
                return array("NOT", "Not");

            default:
                return array("CHAR", $c);
        }
    }

        /** 
         * parse If: header
         *
         * dispatch WebDAV HTTP request to the apropriate method handler
         * 
         * @param $str
         * @return void
         */
    function _if_header_parser($str) {
        $pos = 0;
        $len = strlen($str);

        $uris = array();

        while ($pos < $len) {
            $token = $this->_if_header_lexer($str, $pos);

            if ($token[0] == "URI") {
                $uri = $token[1];
                $token = $this->_if_header_lexer($str, $pos);
            } else {
                $uri = "";
            }

            if ($token[0] != "CHAR" || $token[1] != "(")
                return false;

            $list = array();
            $level = 1;
            $not = "";
            while ($level) {
                $token = $this->_if_header_lexer($str, $pos);
                if ($token[0] == "NOT") {
                    $not = "!";
                    continue;
                }
                switch ($token[0]) {
                    case "CHAR":
                        switch ($token[1]) {
                            case "(":
                                $level++;
                                break;
                            case ")":
                                $level--;
                                break;
                            default:
                                return false;
                        }
                        break;

                    case "URI":
                        $list[] = $not."<$token[1]>";
                        break;

                    case "ETAG_WEAK":
                        $list[] = $not."[W/'$token[1]']>";
                        break;

                    case "ETAG_STRONG":
                        $list[] = $not."['$token[1]']>";
                        break;

                    default:
                        return false;
                }
                $not = "";
            }

            if (@is_array($uris[$uri]))
                $uris[$uri] = array_merge($uris[$uri],$list);
            else
                $uris[$uri] = $list;
        }

        return $uris;
    }

    function _check_if_header_conditions() {
        // see rfc 2518 sec. 9.4
        if (isset($_SERVER["HTTP_IF"])) {
            $this->_if_header_uris =
                $this->_if_header_parser($_SERVER["HTTP_IF"]);

            foreach($this->_if_header_uris as $uri => $conditions) {
                if ($uri == "") {
                    // default uri is the complete request uri
                    $uri = (@$_SERVER["HTTPS"] === "on" ? "https:" : "http:");
                    $uri.=
                        "//$_SERVER[HTTP_HOST]$_SERVER[SCRIPT_NAME]$_SERVER[PATH_INFO]";
                }
                // all must match
                $state = true;
                foreach($conditions as $condition) {
                    // lock tokens may be free form (RFC2518 6.3)
                    // but if opatuelocktokens are used (RFC2518 6.4)
                    // we have to check the format (litmus tests this)
                    if (!strncmp($condition, "<opaquelocktoken:", strlen("<opaquelocktoken"))) {
                        if (!ereg("^<opaquelocktoken:[[:xdigit:]]{8}-[[:xdigit:]]{4}-[[:xdigit:]]{4}-[[:xdigit:]]{4}-[[:xdigit:]]{12}>$", $condition)) {
                            return false;
                        }
                    }
                    if (!$this->_check_uri_condition($uri, $condition)) {
                        $state = false;
                        break;
                    }
                }

                // any match is ok
                if ($state == true)
                    return true;
            }
            return false;
        }
        return true;
    }

        /**
     * Check a single URI condition parsed from an if-header
     *
     * Check a single URI condition parsed from an if-header
     *
     * @abstract 
     * @param string $uri URI to check
     * @param string $condition Condition to check for this URI
     * @returns bool Condition check result
     */
    function _check_uri_condition($uri, $condition) {
        // not really implemented here, 
        // implementations must override
        return true;
    }


    function _check_lock_status($path, $exclusive_only = false) {
        // FIXME depth -> ignored for now
        if (method_exists($this, "checklock")) {
            // is locked?
            $lock = $this->checklock($path);

            // ... and lock is not owned?
            if (is_array($lock) && count($lock)) {
                // FIXME doesn't check uri restrictions yet
                if (!strstr($_SERVER["HTTP_IF"], $lock["token"])) {
                    if (!$exclusive_only || ($lock["scope"] !== "shared"))
                        return false;
                }
            }
        }
        return true;
    }


    // }}}



    function lockdiscovery($path) {
        if (!method_exists($this, "checklock")) {
            return "";
        }

        $lock = $this->checklock($path);

        $activelocks = "";

        if (is_array($lock) && count($lock)) {
            if (!empty($lock["expires"])) {
                $timeout = "Second-".($lock["expires"] - time());
            } else if (!empty($lock["timeout"])) {
                $timeout = "Second-$lock[timeout]";
            } else {
                $timeout = "Infinite";
            }
            $activelocks.= "
              <D:activelock>
               <D:lockscope><D:$lock[scope]/></D:lockscope>
               <D:locktype><D:$lock[type]/></D:locktype>
               <D:depth>$lock[depth]</D:depth>
               <D:owner>$lock[owner]</D:owner>
               <D:timeout>$timeout</D:timeout>
               <D:locktoken><D:href>$lock[token]</D:href></D:locktoken>
              </D:activelock>
      ";
        }

        return $activelocks;
    }

    function http_status($status) {
        if($status === true) $status = "200 OK";
        $this->_http_status = $status;
        header("HTTP/1.1 $status");
        header("X-WebDAV-Status: $status");
    }

    function _urlencode($path, $for_html=false) {
        $return = strtr($path,array(" "=>"%20",
                                    "&"=>"%26",
                                    "<"=>"%3C",
                                    ">"=>"%3E",
                                    ));
        if ($for_html) {
            $return = str_replace("'", "%27", $return);
        }

        return $return;
    }

    function _urldecode($path) {
        return urldecode($path);
    }


    function prop_encode($text) {
        switch ($this->_prop_encoding) {
        case "utf-8":
            return $text;
        default:
            return utf8_encode($text);
        }
    }
} 

  /*
   * Local variables:
   * tab-width: 4
   * c-basic-offset: 4
   * End:
   */
?>
