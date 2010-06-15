<?php
	// helper class for parsing PROPFIND request bodies
	class _parse_propfind 
  {
		// get requested properties as array containing name/namespace pairs
		function _parse_propfind($path) 
		{
			$this->success = true;

			$this->depth = 0;
			$this->props = array();
			$had_input = false;
			$xml_parser = xml_parser_create_ns("UTF-8", " ");
			xml_set_element_handler($xml_parser,
									array(&$this, "_startElement"),
									array(&$this, "_endElement"));
			xml_parser_set_option($xml_parser, XML_OPTION_CASE_FOLDING,
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

			if(!count($this->props)) $this->props = "all"; // default
		}
	
	
	function _startElement($parser, $name, $attrs) 
  {
		if (strstr($name, " ")) {
			list($ns, $tag) = explode(" ", $name);
			if ($ns == "")
				$this->success = false;
		} else {
			$ns = "";
			$tag = $name;
		}
		if ($this->depth == 1) {
			if ($tag == "allprop")
				$this->props = "all";
			if ($tag == "propname")
				$this->props = "names";
		}
		if ($this->depth == 2) {
			$prop = array("name" => $tag);
			if ($ns)
				$prop["xmlns"] = $ns;
			$this->props[] = $prop;
		}
		$this->depth++;
	}

	function _endElement($parser, $name) 
  {
		$this->depth--;
	}
}


?>