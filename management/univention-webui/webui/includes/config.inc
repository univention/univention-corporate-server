<?php
/*
 * Univention Webui
 *  config.inc
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

class webui_config{
	var $temp_age;
	var $temp_dir;
	var $session_dir;
	var $temp_mode;
	var $run;
	var $encoding;
	var $debugger;
	var $debug_text;
	var $session_id;
	var $number;
	var $browser;
	var $is_js;
	var $wide;
	var $position;
	var $language;
	var $refresh;
	var $layout_type;

	function webui_config($browser, $session_id = FALSE){
		require("config.php");

		if(preg_match("/MSIE/i",$browser)) $this->browser = "IE";
		elseif(preg_match("/Gecko/i",$browser)) $this->browser = "Gecko";
		elseif(preg_match("/Konqueror/i",$browser)) $this->browser = "Gecko";
		elseif(preg_match("/Lynx/i",$browser) || preg_match("/W3M/i",$browser)) $this->browser = "Text";
		$this->debugger = $debugger;
		$this->language = $language;
		$this->temp_age = $temp_age;
		$this->debug_put("max. Tempfile-Alter: ".$this->temp_age." sec");
		$this->temp_dir = $temp_dir;
		$this->debug_put("Temp-Dir: ".$this->temp_dir);
		$this->temp_mode = $temp_mode;
		$this->debug_put("File-Mode: ".$this->temp_mode);
		$this->encoding = $encoding;
		$this->debug_put("Encoding: ".$this->encoding);
		$this->check_temp_dir();
		$this->wide=860;
		$this->position=FALSE;
		$this->refresh=FALSE;
		$this->layout_type=$layout_type;
		
		if($session_id){
			$sess=split("_",$session_id);
			$this->session_id = $sess[1];
			$this->session_dir = $this->temp_dir.$this->session_id."/";
			$this->number = $sess[0]+1;
			@touch($this->session_dir);
			$socket_filename_file = $this->session_dir."socket_filename";
			$fp=@fopen($socket_filename_file, "r");
			if(!$fp){
				$this->debug_put("Datei ".$socket_filename_file." kann nicht gelesen werden!");
			} else {
				$this->socket_filename = fread($fp, 1024);
				fclose($fp);
			}
		}
		else $this->mk_session();
		$this->debug_put("Session-ID: ".$this->session_id);
		$this->debug_put("current filenumber: ".$this->number);
		$this->run = $run; # For orig. Python Backend;
	}
	
	function set_js($is_js=FALSE){
		if($this->browser=="Text") $this->is_js = FALSE;
		else $this->is_js = TRUE;
	}
	
	function set_layout_type($layout_type=''){
		$this->layout_type = $layout_type;
	}
	
	function check_temp_dir(){
		if(!is_dir($this->temp_dir))
		  if(!mkdir($this->temp_dir,$this->temp_mode)){
		        $this->debug_put("Verzeichnis ".$this->temp_dir." kann nicht erstellt werden!");
		 	exit();
		  }
	
	}

	function mk_rand_id(){
		list($usec, $sec) = explode(' ', microtime());
		mt_srand((float) $sec + ((float) $usec * 100000));
		return md5(time().mt_rand(0,100000000));
	}

	function mk_session(){
		$this->session_id=$this->mk_rand_id();
		$this->socket_filename=$this->temp_dir.$this->mk_rand_id().".socket";
		$this->number = "0";
		$this->session_dir = $this->temp_dir.$this->session_id."/";
		if(!mkdir($this->session_dir,$this->temp_mode)){
			$this->debug_put("Verzeichnis ".$this->session_dir." kann nicht erstellt werden!");
		 	exit();
		}
		$socket_filename_file = $this->session_dir."socket_filename";
		if(!($fp=fopen($socket_filename_file, "w"))){
			$this->debug_put("Datei ".$socket_filename_file." kann nicht erstellt werden!");
			exit();
		}
		fwrite($fp, $this->socket_filename);
		if (!fclose($fp)){
			$this->debug_put("Datei ".$socket_filename_file." kann nicht geschlossen werden!");
			exit();
		}
	}
	
	function debug_put($str){
		if($this->debugger=="on")$this->debug_text[] = "<b>".$str."</b>";
	}
	
	function debug_show(){
		if($this->debugger=="on"){
			echo"\n\n<!-- ####### debugger ####### -->\n\n";
			echo"<br>\n<table border=\"1\" cellspacing=\"0\" width=\"785\">\n";	
			echo"<tr>\n<th bgcolor=\"#FF9900\">Debugger</th>\n</tr>\n";	
			echo"<tr>\n<td><b>Browser - Typ: ".$this->browser."</b></td>\n</tr>\n";
			foreach($this->debug_text as $val){
		   		echo"<tr>\n<td>".$val."</td>\n</tr>\n";
			}
			echo"<tr>\n<td><b>Ausgabe...</b></td>\n</tr>\n";
			echo"</table>\n<br><br>\n";
			echo"\n\n<!-- ####### end of debugger ####### -->\n\n";
		}
	}
	
	function del_old(){
	$old;
	$dir_handle=opendir($this->temp_dir);
	while($entry = readdir($dir_handle)){
		if(is_dir($this->temp_dir.$entry) && ((time() - filemtime($this->temp_dir.$entry)) > $this->temp_age) && ($entry != "..") && ($entry != ".")){
			system("rm -r ".$this->temp_dir.$entry.'/');
			$this->debug_put("Verzeichnis ".$this->temp_dir.$entry."/ geloescht !!!");
			}
		}	
	closedir($dir_handle);
	}
	
	function recycle(){
		$this->number--;
	}
	
  function set_position($long_table)
  {
    $this->position = $long_table;
  }
}
?>
