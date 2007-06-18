<?php

    require_once "HTTP/WebDAV/Server.php";
    
    /**
     * Filesystem access using WebDAV
     *
     * @access public
     */
    class HTTP_WebDAV_Server_Filesystem extends HTTP_WebDAV_Server 
    {
        /**
         * Root directory for WebDAV access
         *
         * Defaults to webserver document root (set by ServeRequest)
         *
         * @access private
         * @var    string
         */
        var $base = "";

        /** 
         * MySQL Host where property and locking information is stored
         *
         * @access private
         * @var    string
         */
        var $db_host = "localhost";

        /**
         * MySQL database for property/locking information storage
         *
         * @access private
         * @var    string
         */
        var $db_name = "webdav";

        /**
         * MySQL user for property/locking db access
         *
         * @access private
         * @var    string
         */
        var $db_user = "root";

        /**
         * MySQL password for property/locking db access
         *
         * @access private
         * @var    string
         */
        var $db_passwd = "";

        /**
         * Serve a webdav request
         *
         * @access public
         * @param  string  
         */
        function ServeRequest($base = false) 
        {
            // special treatment for litmus compliance test
            // reply on its identifier header
            // not needed for the test itself but eases debugging
            foreach(apache_request_headers() as $key => $value) {
                if(stristr($key,"litmus")) {
                    error_log("Litmus test $value");
                    header("X-Litmus-reply: ".$value);
                }
            }

            // set root directory, defaults to webserver document root if not set
            if ($base) { 
                $this->base = realpath($base); // TODO throw if not a directory
            } else if(!$this->base) {
                $this->base = $_SERVER['DOCUMENT_ROOT'];
            }
                
            // establish connection to property/locking db
            mysql_connect($this->db_host, $this->db_user, $this->db_passwd) or die(mysql_error());
            mysql_select_db($this->db_name) or die(mysql_error());
            // TODO throw on connection problems

            // let the base class do all the work
            parent::ServeRequest();
        }

        /**
         * No authentication is needed here
         *
         * @access private
         * @param  string  HTTP Authentication type (Basic, Digest, ...)
         * @param  string  Username
         * @param  string  Password
         */
        function check_auth($type, $user, $pass) 
        {
            return true;
        }

        
        function PROPFIND($options, &$files) 
        {
            // get absolute fs path to requested resource
            $fspath = realpath($this->base . $options["path"]);
            
            // sanity check
            if (!file_exists($fspath)) {
                return false;
            }

            // prepare property array
            $files["files"] = array();

            // store information for the requested path itself
            $files["files"][] = $this->fileinfo($options["path"], $options);

            // information for contained resources requested?
            if (!empty($options["depth"]))  { // TODO check for is_dir() first?
                
                // make sure path ends with '/'
                if (substr($options["path"],-1) != "/") { 
                    $options["path"] .= "/";
                }

                // try to open directory
                $handle = @opendir($fspath);
                
                if ($handle) {
                    // ok, now get all its contents
                    while ($filename = readdir($handle)) {
                        if ($filename != "." && $filename != "..") {
                            $files["files"][] = $this->fileinfo ($options["path"].$filename, $options);
                        }
                    }
                    // TODO recursion needed if "Depth: infinite"
                }
            }

            // ok, all done
            return true;
        } 

        function fileinfo($uri, $options) 
        {
            
            $fspath = $this->base . $uri;

            $file = array();
            $file["path"]= $uri;    

            $file["props"][] = $this->mkprop("displayname", strtoupper($uri));

            $file["props"][] = $this->mkprop("creationdate", filectime($fspath));
            $file["props"][] = $this->mkprop("getlastmodified", filemtime($fspath));

            if (is_dir($fspath)) {
                $file["props"][] = $this->mkprop("getcontentlength", 0);
                $file["props"][] = $this->mkprop("resourcetype", "collection");
                $file["props"][] = $this->mkprop("getcontenttype", "httpd/unix-directory");             
            } else {
                $file["props"][] = $this->mkprop("resourcetype", "");
                $file["props"][] = $this->mkprop("getcontentlength", filesize($fspath));
                if (is_readable($fspath)) {
                    $file["props"][] = $this->mkprop("getcontenttype", $this->_mimetype($fspath));
                } else {
                    $file["props"][] = $this->mkprop("getcontenttype", "application/x-non-readable");
                }               
            }
            
            $query = "SELECT ns, name, value FROM properties WHERE path = '$uri'";
            $res = mysql_query($query);
            while($row = mysql_fetch_assoc($res)) {
                $file["props"][] = $this->mkprop($row["ns"], $row["name"], $row["value"]);
            }
            mysql_free_result($res);
            return $file;
        }

        /* @@@ */
        function _can_execute($name, $path=false) 
        {
            if (!strncmp(PHP_OS, "WIN", 3)) {
                $exts = array(".exe", ".com");
            } else {
                $exts = array("");
            }

            if ($path===false) {
                $path = getenv("PATH");
            }

            foreach (explode(PATH_SEPARATOR, $path) as $dir) {
                if (!@is_dir($dir)) continue;
                foreach ($exts as $ext) {
                    if (@is_executable("$dir/$name".$ext)) return true;
                }
            }
        }


        function _mimetype($fspath) 
        {
            if (@is_dir($fspath)) {
                return "httpd/unix-directory"; // TODO what on Windows? ;>
            } else if (function_exists("mime_content_type")) {
                // use mime magic extension if available
                $mime_type = mime_content_type($fspath);
            } else if ($this->_can_execute("file")) {
                // it looks like we have a 'file' command, 
                // lets see it it does have mime support
                $fp = popen("file -i '$fspath' 2>/dev/null", "r");
                $reply = fgets($fp);
                pclose($fp);
                
                // popen will not return an error if the binary was not found
                // and find may not have mime support using "-i"
                // so we test the format of the returned string 
                
                // the reply begins with the requested filename
                if (!strncmp($reply, "$fspath: ", strlen($fspath)+2)) {                     
                    $reply = substr($reply, strlen($fspath)+2);
                    // followed by the mime type (maybe including options)
                    if (ereg("^[[:alnum:]_-]+/[[:alnum:]_-]+;?.*", $reply, $matches)) {
                        $mime_type = $matches[0];
                    }
                }
            } 
            
            if (empty($mime_type)) {
                // Fallback solution: try to guess the type by the file extension
                // TODO: add more ...
                // TODO: can we use the registry for this on Windows?
                //       OTOH if the server is Windos the clients are likely to 
                //       be Windows, too, and tend do ignore the Content-Type
                //       anyway (overriding it with information taken from
                //       the registry)
                // TODO: have a seperate PEAR class for mimetype detection?
                switch (strtolower(strrchr(basename($fspath), "."))) {
                case ".html":
                    $mime_type = "text/html";
                    break;
                case ".gif":
                    $mime_type = "image/gif";
                    break;
                case ".jpg":
                    $mime_type = "image/jpeg";
                    break;
                default: 
                    $mime_type = "application/octet-stream";
                    break;
                }
            }
            
            return $mime_type;
        }

        function GET(&$options) 
        {
            $fspath = $this->base . $options["path"];

            if (file_exists($fspath)) {             
                $options['mimetype'] = $this->_mimetype($fspath); 
                
                // see rfc2518, section 13.7
                // some clients seem to treat this as a reverse rule
                // requiering a Last-Modified header if the getlastmodified header was set
                $options['mtime'] = filemtime($fspath);
                
                $options['size'] = filesize($fspath);
            
                // TODO check permissions/result
                $options['stream'] = fopen($fspath, "r");

                return true;
            } else {
                return false;
            }               
        }

        function PUT(&$options) 
        {
            $fspath = $this->base . $options["path"];

            if(!@is_dir(dirname($fspath))) {
                return "409 Conflict";
            }

            $options["new"] = ! file_exists($fspath);

            $fp = fopen($fspath, "w");

            return $fp;
        }


        function MKCOL($options) 
        {           
            $path = $this->base .$options["path"];
            $parent = dirname($path);
            $name = basename($path);

            if(!file_exists($parent)) {
                return "409 Conflict";
            }

            if(!is_dir($parent)) {
                return "403 Forbidden";
            }

            if( file_exists($parent."/".$name) ) {
                return "405 Method not allowed";
            }

            if(!empty($_SERVER["CONTENT_LENGTH"])) { // no body parsing yet
                return "415 Unsupported media type";
            }
            
            $stat = mkdir ($parent."/".$name,0777);
            if(!$stat) {
                return "403 Forbidden";                 
            }

            return ("201 Created");
        }
        
        
        function delete($options) 
        {
            $path = $this->base . "/" .$options["path"];

            if(!file_exists($path)) return "404 Not found";

            if (is_dir($path)) {
                $query = "DELETE FROM properties WHERE path LIKE '$options[path]%'";
                mysql_query($query);
                system("rm -rf $path");
            } else {
                unlink ($path);
            }
            $query = "DELETE FROM properties WHERE path = '$options[path]'";
            mysql_query($query);

            return "204 No Content";
        }


        function move($options) 
        {
            return $this->copy($options, true);
        }

        function copy($options, $del=false) 
        {
            // TODO Property updates still broken (Litmus should detect this?)

            if(!empty($_SERVER["CONTENT_LENGTH"])) { // no body parsing yet
                return "415 Unsupported media type";
            }

            // no copying to different WebDAV Servers yet
            if(isset($options["dest_url"])) {
                return "502 bad gateway";
            }

            $source = $this->base .$options["path"];
            if(!file_exists($source)) return "404 Not found";

            $dest = $this->base . $options["dest"];

            $new = !file_exists($dest);
            $existing_col = false;

            if(!$new) {
                if($del && is_dir($dest)) {
                    if(!$options["overwrite"]) {
                        return "412 precondition failed";
                    }
                    $dest .= basename($source);
                    if(file_exists($dest.basename($source))) {
                        $options["dest"] .= basename($source);
                    } else {
                        $new = true;
                        $existing_col = true;
                    }
                }
            }

            if(!$new) {
                if($options["overwrite"]) {
                    $stat = $this->delete(array("path" => $options["dest"]));
                    if($stat{0} != "2") return $stat; 
                } else {                
                    return "412 precondition failed";
                }
            }

            if (is_dir($source)) {
                // RFC 2518 Section 9.2, last paragraph
                if ($options["depth"] != "infinity") {
                    error_log("---- ".$options["depth"]);
                    return "400 Bad request";
                }

                system("cp -R $source $dest");

                if($del) {
                    system("rm -rf $source");
                }
            } else {                
                if($del) {
                    @unlink($dest);
                    $query = "DELETE FROM properties WHERE path = '$options[dest]'";
                    mysql_query($query);
                    rename($source, $dest);
                    $query = "UPDATE properties SET path = '$options[dest]' WHERE path = '$options[path]'";
                    mysql_query($query);
                } else {
                    if(substr($dest,-1)=="/") $dest = substr($dest,0,-1);
                    copy($source, $dest);
                }
            }

            return ($new && !$existing_col) ? "201 Created" : "204 No Content";         
        }

        function proppatch(&$options) 
        {
            global $prefs, $tab;

            $msg = "";
            
            $path = $options["path"];
            
            $dir = dirname($path)."/";
            $base = basename($path);
            
            foreach($options["props"] as $key => $prop) {
                if($ns == "DAV:") {
                    $options["props"][$key][$status] = "403 Forbidden";
                } else {
                    if(isset($prop["val"])) {
                        $query = "REPLACE INTO properties SET path = '$options[path]', name = '$prop[name]', ns= '$prop[ns]', value = '$prop[val]'";
                    } else {
                        $query = "DELETE FROM properties WHERE path = '$options[path]' AND name = '$prop[name]' AND ns = '$prop[ns]'";
                    }       
                    mysql_query($query);
                }
            }
                        
            return "";
        }


        function lock(&$options) 
        {
            if(isset($options["update"])) { // Lock Update
                $query = "UPDATE locks SET expires = ".(time()+300);
                mysql_query($query);
                
                if(mysql_affected_rows()) {
                    $options["timeout"] = 300; // 5min hardcoded
                    return true;
                } else {
                    return false;
                }
            }
            
            $options["timeout"] = time()+300; // 5min. hardcoded

            $query = "INSERT INTO locks
                        SET token   = '$options[locktoken]'
                          , path    = '$options[path]'
                          , owner   = '$options[owner]'
                          , expires = '$options[timeout]'
                          , exclusivelock  = " .($options['scope'] === "exclusive" ? "1" : "0")
                ;
            mysql_query($query);
            return mysql_affected_rows() > 0;

            return "200 OK";
        }

        function unlock(&$options) 
        {
            $query = "DELETE FROM locks
                      WHERE path = '$options[path]'
                        AND token = '$options[token]'";
            mysql_query($query);

            return mysql_affected_rows() ? "200 OK" : "409 Conflict";
        }

        function checklock($path) 
        {
            $result = false;
            
            $query = "SELECT owner, token, expires, exclusivelock
                  FROM locks
                 WHERE path = '$path'
               ";
            $res = mysql_query($query);

            if($res) {
                $row = mysql_fetch_array($res);
                mysql_free_result($res);

                if($row) {
                    $result = array( "type"    => "write",
                                                     "scope"   => $row["exclusivelock"] ? "exclusive" : "shared",
                                                     "depth"   => 0,
                                                     "owner"   => $row['owner'],
                                                     "token"   => $row['token'],
                                                     "expires" => $row['expires']
                                                     );
                }
            }

            return $result;
        }


        function create_database() 
        {
            // TODO
        }
    }


?>
