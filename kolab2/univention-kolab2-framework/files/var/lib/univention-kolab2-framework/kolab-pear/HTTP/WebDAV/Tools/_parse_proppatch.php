<?php

        // helper class for parsing PROPPATCH request bodies
class _parse_proppatch {
    function _parse_proppatch($path) {
        $this->success = true;

        $this->depth = 0;
        $this->props = array();
				$had_input = false;
        $xml_parser = xml_parser_create_ns("UTF-8",
                                           " ");
        xml_set_element_handler($xml_parser,
                                array(&$this,
                                      "_startElement"),
                                array(&$this,
                                      "_endElement"));
        xml_set_character_data_handler($xml_parser,
                                       array(&$this,
                                             "_data"));
        xml_parser_set_option($xml_parser,
                              XML_OPTION_CASE_FOLDING,
                              false);

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
            if ($ns == "")
                $this->success = false;
        } else {
            $ns = "";
            $tag = $name;
        }
        if ($this->depth == 1) {
            $this->mode = $tag;
        }
        if ($this->depth == 3) {
            $prop = array("name" => $tag);
            $this->current = array("name" => $tag, "ns" => $ns, "status"=> 200);
            if ($this->mode == "set")
                $this->current["val"] = "";     // default set val
        }
        $this->depth++;
    }

    function _endElement($parser,
                         $name) {
        if (isset($this->current)) {
            $this->props[] = $this->current;
            unset($this->current);
        }
        $this->depth--;
    }

    function _data($parser,
                   $data) {
        if (isset($this->current)) {
            $this->current["val"] = $data;
        }
    }
}

?>