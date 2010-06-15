<?php

	// helper class for parsing LOCK request bodies
	class _parse_lockinfo 
  {
		var $owner = "";
		var $collect_owner = false;
	
    function _parse_lockinfo($path) 
		{
				$this->success = true;
				$had_input = false;

				$xml_parser = xml_parser_create_ns("UTF-8", " ");
				xml_set_element_handler($xml_parser,
																array(&$this, "_startElement"),
																array(&$this, "_endElement"));
				xml_set_character_data_handler($xml_parser,
																			 array(&$this, "_data"));
				xml_parser_set_option($xml_parser,
															XML_OPTION_CASE_FOLDING, false);

				$f_in = fopen($path, "r");
				while($this->success && !feof($f_in)) {
					$line = fgets($f_in);
					if (is_string($line)) {
						$line = trim($line);
						if($line == "") continue;
						$had_input = true;
						$this->success &= xml_parse($xml_parser, $line, false);
					}
				} 
				if($had_input) {
					$this->success &= xml_parse($xml_parser, "", true);
				}
				fclose($f_in);

				xml_parser_free($xml_parser);
		}
    

    function _startElement($parser,
                           $name,
                           $attrs) {
        if (strstr($name, " ")) {
            list($ns, $tag) = explode(" ", $name);
        } else {
            $ns = "";
            $tag = $name;
        }

        if ($this->collect_owner) {
            $ns_short = "";
            $ns_attr = "";
            if ($ns) {
                if ($ns == "DAV:") {
                    $ns_short = "D:";
                } else {
                    $ns_attr = " xmlns='$ns'";
                }
            }
            $this->owner .= "<$ns_short$tag$ns_attr>";
        } else if ($ns == "DAV:") {
            switch ($tag) {
                case "write":
                    $this->locktype = $tag;
                    break;
                case "exclusive":
                case "shared":
                    $this->lockscope = $tag;
                    break;
                case "owner":
                    $this->collect_owner = true;
                    break;
            }
        }
    }

    function _data($parser,
                   $data) {
        if ($this->collect_owner) {
            $this->owner .= $data;
        }
    }

    function _endElement($parser, $name) {
			if (strstr($name, " ")) {
				list($ns, $tag) = explode(" ", $name);
			} else {
				$ns = "";
				$tag = $name;
			}
			if (($ns == "DAV:") && ($tag == "owner")) {
				$this->collect_owner = false;
			}
			if ($this->collect_owner) {
				$ns_short = "";
				$ns_attr = "";
				if ($ns) {
					if ($ns == "DAV:") {
                    $ns_short = "D:";
					} else {
						$ns_attr = " xmlns='$ns'";
					}
				}
				$this->owner .= "</$ns_short$tag$ns_attr>";
			}
    }
}

?>