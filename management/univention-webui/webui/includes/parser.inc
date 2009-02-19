<?php
/*
 * Univention Webui
 *  parser.inc
 *
 * Copyright (C) 2004-2009 Univention GmbH
 *
 * http://www.univention.de/
 *
 * All rights reserved.
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License version 2 as
 * published by the Free Software Foundation.
 *
 * Binary versions of this file provided by Univention to you as
 * well as other copyrighted, protected or trademarked materials like
 * Logos, graphics, fonts, specific documentations and configurations,
 * cryptographic keys etc. are subject to a license agreement between
 * you and Univention.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 */

class webui_in{			# Python ---> PHP
	var $ref_trans;
	var $ref_config;
	var $value;
	var $html;

	function webui_in(&$config,&$translator)
	{
  		$this->ref_trans = &$translator;
		$this->ref_config = &$config;
		$this->value = "";
		$this->html = FALSE;
		$file = $config->session_dir.$config->number;
		$config->debug_put("Parse Datei ".$file);
    		if (file_exists($file) && is_file($file)){
			$fp=fopen($file,'r+');
			if(!flock($fp,LOCK_EX)) $config->debug_put("F-Lock fehlgeschlagen");
	  		$config->debug_put("New XML: ".filesize($file)."Byte");
    			$p = xml_parser_create($config->encoding);
    			xml_parser_set_option($p, XML_OPTION_CASE_FOLDING, 0);
	    		xml_parser_set_option($p, XML_OPTION_TARGET_ENCODING, 'UTF-8');
    			xml_parser_set_option($p,XML_OPTION_SKIP_WHITE,1);
    			xml_set_object($p, $this);
	    		xml_set_element_handler($p, 'startTag', 'closeTag');
    			xml_set_character_data_handler($p, 'value');

    			while( $data = fread( $fp, 1024 )){
	 			if( !xml_parse( $p, $data, feof( $fp )))
      					$config->debug_put("1.Parser: ".xml_error_string(xml_get_error_code($p))."<br />line ".xml_get_current_line_number($p)."<br />column ".xml_get_current_column_number($p)."<br />byte-index ".xml_get_current_byte_index($p));
      				}
	    		xml_parser_free($p);
    			flock($fp,LOCK_UN);
    			fclose($fp);
		    	}
			else {
				if($_SERVER["SERVER_PORT"]=='80') $port="http";
				else $port="https";
				header("Location:$port://".$_SERVER['HTTP_HOST'].dirname($_SERVER['PHP_SELF'])."/index.php?logout=2");
				exit();
			}
  	}

	function startTag($p, $tag, $attribute){
		if($tag == "htmltext")$this->html = TRUE;
		$this->ref_trans->start($tag, $attribute, xml_get_current_byte_index($p));
	}

	function closeTag($p, $tag){
		if($tag == "htmltext")$this->html = FALSE;
		$this->ref_trans->value(trim($this->value));
		$this->value = "";
		$this->ref_trans->end($tag);
	}

	function value($p, $value){
		if($value != "&" && !$this->html)$this->value .= htmlspecialchars($value);
		else $this->value .= $value;
	}
}


class webui_out{			# PHP ---> Python
	var $input;
	var $pipe;
	var $change;
	var $valid;
	var $content;
  	var $ref_trans;
	var $ref_config;
	var $session_data;

	function webui_out(&$config,&$usrinput,&$session_data)
	{
		$this->change='';
  		$this->session_data=&$session_data;
		$this->valid=FALSE;
		$this->content=FALSE;
		$this->ref_config = &$config;
		$this->input($usrinput);
		$file = $config->session_dir.($config->number-1);
		$socket_file = $config->socket_filename;
		if (file_exists($socket_file)) {
			$this->pipe=fsockopen("unix://".$config->socket_filename, 0);  	# Python Backend
		} else { $file=""; }

		if (file_exists($file) && is_file($file) && $this->pipe){

			fwrite($this->pipe, "Number: ".($config->number-1)."\n\n"); # Python Backend


			$config->debug_put("Oeffne Pipe: ".$config->run);

			$fp=fopen($file,'r+');
			if(!flock($fp,LOCK_EX)) $config->debug_put("F-Lock fehlgeschlagen");
	  		$config->debug_put("Old XML: ".filesize($file)."Byte");
    			$p = xml_parser_create($config->encoding);
    			xml_parser_set_option($p, XML_OPTION_CASE_FOLDING, 0);
	    		xml_parser_set_option($p, XML_OPTION_TARGET_ENCODING, 'UTF-8');
    			xml_parser_set_option($p,XML_OPTION_SKIP_WHITE,1);
    			xml_set_object($p, $this);
			$config->debug_put("Fuege Inhalte in ".$file." ein");
			xml_set_element_handler($p, 'startTag', 'closeTag');
			xml_set_character_data_handler($p, 'value');

			while( $data = fread( $fp, 1024 )){
		 		if( !xml_parse( $p, $data, feof( $fp )))
      					$config->debug_put("2.Parser: ".xml_error_string(xml_get_error_code($p))."<br />line ".xml_get_current_line_number($p)."<br />column ".xml_get_current_column_number($p)."<br />byte-index ".xml_get_current_byte_index($p));
      				}
	    		xml_parser_free($p);
			flock($fp,LOCK_UN);
    			fclose($fp);

			fwrite($this->pipe, "\0");		# Python Backend
			$fp=fopen($config->session_dir.$config->number, "w");
			while (($buf = fread($this->pipe, 1024))) {
				fwrite($fp, $buf);
				if (strlen($buf) < 1024 )
					break;
			}
			fclose($fp);
			fclose($this->pipe);	# Python Backend
		    }
	    	else {
			if($_SERVER["SERVER_PORT"]=='80') $port="http";
			else $port="https";
			header("Location: $port://".$_SERVER['HTTP_HOST'].dirname($_SERVER['PHP_SELF'])."/index.php?logout=2");
			exit();
		}
	}

	function input(&$usrinput){
		foreach($usrinput as $key=>$value){
			if(is_array($value)){
				$type=split("#",$key);
				switch($type[0]){
				case 'date':

					$this->input[$type[1]] = $value[0].".".trim($value[1]).".".$value[2];
                                        if(trim($this->input[$type[1]])=="..")$this->input[$type[1]]="";
					break;
				case 'language_dojo_select':
				case 'question_select':
				  // with enabled dijit.form.FilteringSelect and IE, this array contains not only 
				  // the selected ID but also the string representation. We need only the ID which 
				  // is the second value. As we don't know the browser, we just get the last item.
					if (end($value)) { // check if the value is set, see Bug #13063
						$this->input[end($value)] = '1';
					}
					break;					
				case 'multiple':
					$value = array_flip($value);
					foreach($value as $k => $v)
						if($k) $this->input[$k] = '1';
					break;
					}
				}
			else
			  {
			    $this->input[$key] = $value;
			  }
			}
		ksort($this->input, SORT_NUMERIC);
		reset($this->input);
		if($this->ref_config->debugger=="on"){
			$this->ref_config->debug_put("Userinput:");
			foreach($this->input as $key=>$value)
				$this->ref_config->debug_put("Byteindex ".$key." ==> ".$value);
			reset($this->input);
			}
	}

	function startTag($p, $tag, $attribute){
		if(trim($tag) == 'content') $this->content = TRUE;
		if(xml_get_current_byte_index($p)==key($this->input)){
			$this->change=$this->input[key($this->input)];
			next($this->input);
			}
		foreach($attribute as $key=>$value){
			if(trim($key) == 'internal') $this->valid = trim($tag);
			$attr .= " $key=\"".$value."\"";
			}
		fwrite($this->pipe,"<".$tag.$attr.">");
	}

	function closeTag($p, $tag){
		if($this->valid == trim($tag)) $this->valid = FALSE;
		if(trim($tag)=='content') $this->content=FALSE;
		fwrite($this->pipe,htmlspecialchars(stripslashes($this->change), ENT_COMPAT));
		$this->change='';
		fwrite($this->pipe,"</".$tag.">");
	}

	function value($p, $value){
		if(trim($value)){
			if($this->valid) fwrite($this->pipe,htmlspecialchars($value));
			elseif(!$this->content) fwrite($this->pipe,htmlspecialchars($value));
			}
	}
}


?>
