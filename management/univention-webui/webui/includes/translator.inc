<?php
  /*
   * Univention Webui
   *  translator.inc
   *
   * Copyright 2004-2010 Univention GmbH
   *
   * http://www.univention.de/
   *
   * All rights reserved.
   *
   * The source code of this program is made available
   * under the terms of the GNU Affero General Public License version 3
   * (GNU AGPL V3) as published by the Free Software Foundation.
   *
   * Binary versions of this program provided by Univention to you as
   * well as other copyrighted, protected or trademarked materials like
   * Logos, graphics, fonts, specific documentations and configurations,
   * cryptographic keys etc. are subject to a license agreement between
   * you and Univention and not subject to the GNU AGPL V3.
   *
   * In the case you use this program under the terms of the GNU AGPL V3,
   * the program is provided in the hope that it will be useful,
   * but WITHOUT ANY WARRANTY; without even the implied warranty of
   * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
   * GNU Affero General Public License for more details.
   *
   * You should have received a copy of the GNU Affero General Public
   * License with the Debian GNU/Linux or Univention distribution in file
   * /usr/share/common-licenses/AGPL-3; if not, see
   * <http://www.gnu.org/licenses/>.
   */
require ("extra.inc");
class webui_translator{

	var $extra;
	var $not_valid;
	var $stack;
	var $conti_ref;
	var $level;
	var $config;
	var $warn;
	var $attribute;
	var $temp;
	
	function webui_translator(&$container, &$config, $attribute=0){
		$this->conti_ref = &$container;
		$this->extra = FALSE;
		$this->level = 1;
		$this->config = &$config;
		$this->warn = FALSE;
		$this->temp = FALSE;
		$this->attribute = &$attribute;
	}


	function start(&$tag, &$attribute, $byteindex){
		$layout_type = "menu";
		if($this->config->layout_type && $this->config->layout_type=='menuless')
		{
			$layout_type = "menuless";
		}

		if($this->extra){
			$this->extra->put_start($tag,$attribute,$byteindex);
		}
		else{
			$this->warn = FALSE;
			if(is_array($attribute))
			  	foreach($attribute as $attrib => $value)
				{
					switch($attrib){
					case 'internal':$this->not_valid = $tag; break;
					case 'colspan':
					case 'rowspan':
					case 'class': $attrib_str.=' '.$attrib.'="'.$value.'"'; break;
					case 'type':$h_size = $value + 1; break;
					case 'wide': if(trim($tag)=='dialog') $this->config->wide=1024; break;
					case 'site_title': if(trim($tag)=='dialog') $this->conti_ref->site_title=$value; break;
					case 'header_img': if(trim($tag)=='dialog') $this->conti_ref->header_img=$value; break;
					case 'refresh': if(trim($tag)=='dialog') $this->config->refresh=$value; break;
					case 'warning': $this->warn = 'warning'; break;
					case 'url': $attrib_str.="src=\"".$value."\""; break;
					case 'size': $size=$value; break;
					case 'nofill': $attrib_str .= "width=\"1\""; break;
					case 'onmouseover': $attrib_str .= "onmouseover=\"".$value."\""; break;
					case 'onmouseout': $attrib_str .= "onmouseout=\"".$value."\""; break;
					}
				}
			if(!$this->not_valid){
				switch($tag){
				case 'title':	$this->conti_ref->set_current("title");
					$tag=""; $close=""; break;
				case 'longtitle':$this->conti_ref->set_current("header");
					$tag="<div class=\"h7\">"; $close="</div>"; break;
				case 'headertext':$this->conti_ref->set_current("headertext");
					$tag=""; $close=""; break;
				case 'icon':	$tag="<img class=\"icon\" $attrib_str align=\"baseline\"></img>"; $close=""; break;
				case 'header':  $tag="<span class=\"h$h_size\">"; $close="</span>"; break;
				case 'paragraph':
				case 'bbreak':  $tag=""; $close="<br><br>"; break;
				case 'break':  $tag=""; $close="<br>"; break;
				case 'space':   $tag=""; $close="<img src=\"style/space.gif\" alt=\"\" width=\"".(5*$size)."\"></img>"; break;
				case 'emphatize':  $tag="<i>"; $close="</i>";  break;
				case 'important':  $tag="<b>"; $close="</b>";  break;
				case 'htmltext':  $tag=""; $close="";  break;
				case 'info':	$tag = "<div class=\"info\">"; 
					$close="</div>"; 
					$this->conti_ref->set_current("info");  
					if ($layout_type == "menuless") 
					{$tag=$tag."<b>";$close="</b>".$close;}; 
					break;
				case 'info2':	$tag = "<div class=\"info\">"; 
					$close="</div>"; 
					$this->conti_ref->set_current("info2"); 
					if ($layout_type == "menuless") 
					{$tag=$tag."<b>";$close="</b>".$close;}; 
					break;
				case 'dialog': $tag = ""; $close=$tag; $this->conti_ref->set_current("content");break;
				case 'menuitem': $tag=""; $close="";
					if($this->config->browser == 'Text') $close="<br />";break;
				case 'menu':	$this->conti_ref->set_current("menu");
					$this->conti_ref->status = "menu";
					if($this->config->is_js){
						$this->conti_ref->status .= (++$this->level);
						$tag = ""; $close = "";
					} else {
						$tag = '<div class="menu" style="z-index:'.$this->level++.';">';
						$close = '</div>';
					}
					break;
				case 'notebook': $this->extra = new notebook($tag, $this->conti_ref, $this->config, $attribute, $this->warn);return;
				case 'categorylist': $this->extra = new categorylist($tag, $this->conti_ref, $this->config, $attribute, $this->warn);return;
				case 'reset':  $this->extra = new reset($tag, $this->conti_ref, $this->config, $attribute, $this->warn);return;
				case 'button':  $this->extra = new button($tag, $this->conti_ref, $this->config, $attribute, $this->warn);return;
				case 'link': $this->extra = new link($tag, $this->conti_ref, $this->config, $attribute, $this->warn);return;
				case 'progressbar': $this->extra = new progressbar($tag, $this->conti_ref, $this->config, $attribute, $this->warn);return;
				case 'question_bool': $this->extra = new question_bool($tag, $this->conti_ref, $this->config, $attribute, $this->warn);return;
				case 'question_secure': $this->extra = new question_secure($tag, $this->conti_ref, $this->config, $attribute, $this->warn);return;
				case 'question_date': $this->extra = new question_dojo_date_widget($tag, $this->conti_ref, $this->config, $attribute, $this->warn);return;
				case 'question_dojo_date_widget': $this->extra = new question_dojo_date_widget($tag, $this->conti_ref, $this->config, $attribute, $this->warn);return;
				case 'question_text': $this->extra = new question_text($tag, $this->conti_ref, $this->config, $attribute, $this->warn);return;
				case 'question_ltext': $this->extra = new question_ltext($tag, $this->conti_ref, $this->config, $attribute, $this->warn);return;
				case 'question_mselect': $this->extra = new question_mselect($tag, $this->conti_ref, $this->config, $attribute, $this->warn);return;
				case 'question_mmselect': $this->extra = new question_mmselect($tag, $this->conti_ref, $this->config, $attribute, $this->warn);return;
				case 'question_select': $this->extra = new question_select($tag, $this->conti_ref, $this->config, $attribute, $this->warn);return;
				case 'question_dojo_select': $this->extra = new question_dojo_select($tag, $this->conti_ref, $this->config, $attribute, $this->warn);return;
				case 'language_dojo_select': $this->extra = new language_dojo_select($tag, $this->conti_ref, $this->config, $attribute, $this->warn);return;
				case 'question_dojo_comboselect': $this->extra = new question_dojo_comboselect($tag, $this->conti_ref, $this->config, $attribute, $this->warn);return;
				case 'question_choice': $this->extra = new question_choice($tag, $this->conti_ref, $this->config, $attribute, $this->warn);return;
				case 'question_group': $this->extra = new question_group($tag, $this->conti_ref, $this->config, $attribute, $this->warn); return;
				case 'question_file': $this->extra = new question_file($tag, $this->conti_ref, $this->config, $attribute, $this->warn); return;
				case 'long_table': $this->extra = new long_table(new dummy_container($this->config,$this->conti_ref->tabindex), $this->config, $attribute); return;
				case 'dynamic_longtable': $this->extra = new dynamic_longtable(new dummy_container($this->config,$this->conti_ref->tabindex), $this->config, $attribute); return;
				case 'table': $this->extra = new table(new dummy_container($this->config,$this->conti_ref->tabindex), $this->config, $attribute); return;
				case 'tgroup': $this->extra = new tgroup(new dummy_container($this->config,$this->conti_ref->tabindex), $this->config, $attribute); return;
				case 'row': 	if(isset($this->attribute["border"]) && !isset($attribute["border"])) $attribute["border"]=$this->attribute["border"];
					$this->extra = new row(new dummy_container($this->config,$this->conti_ref->tabindex), $this->config, $attribute); return;
				case 'col': 	if(isset($this->attribute["border"]) && !isset($attribute["border"])) $attribute["border"]=$this->attribute["border"];
					$this->extra = new col(new dummy_container($this->config,$this->conti_ref->tabindex), $this->config, $attribute); return;
				case 'logout':	if($_SERVER["SERVER_PORT"]=='80') $port="http";
					else $port="https";
					header("Location:$port://".$_SERVER['HTTP_HOST'].dirname($_SERVER['PHP_SELF'])."/index.php?logout=1&session_id=".$this->config->session_id);
					exit();
				default: $tag=""; $close="";
				}
				if($tag)   $this->conti_ref->put("\n".$tag);
				if($close) $this->stack[]=$close."\n";
			}
		}
	}

	function end(&$tag){
		if($this->extra){
			if($this->extra->finish($tag)){
				$this->conti_ref->put($this->extra->show());
				$this->extra=FALSE;
				// if(trim($tag)=='notebook')
				// 	$this->conti_ref->set_current("content");
			}
		}
		else if(!$this->not_valid){
			if(is_array($this->stack))
				$this->conti_ref->put(array_pop($this->stack));
		}
		else if($this->not_valid==$tag)
			$this->not_valid=FALSE;
		if(trim($tag)=='menu' && $this->config->is_js) {$this->conti_ref->status = "menu".(--$this->level);}

		if(trim($tag)=='info' || trim($tag)=='headertext' || trim($tag)=='longtitle' || trim($tag)=='title')
			$this->conti_ref->set_current("content");
		
		if ( trim( $tag ) == 'dialog' )
			$this->conti_ref->set_current("end");
	}

	function value(&$value){
		if($this->extra)
			$this->extra->put_value($value);
		else if(!$this->not_valid){
			$this->conti_ref->put($value);
		}
	}
}
?>
