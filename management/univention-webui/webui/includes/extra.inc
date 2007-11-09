<?php
/*
 * Univention Webui
 *  extra.inc
 *
 * Copyright (C) 2004, 2005, 2006 Univention GmbH
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

class extra{

	var $tag;
	var $current;
	var $byteindex;
	var $update_byteindex;
	var $status;
	var $tabindex;
	var $basket;
	var $update_button;
	var $js;
	var $attribute;
	var $config;
	var $warn;

	function extra($tag, &$container, $config, $attribute, $warn=FALSE){
		$this->config = &$config;
		$this->attribute = $attribute;
		$this->js = $this->config->is_js;
		$this->tag = $tag;
		$this->tabindex = &$container->tabindex;
		$this->tabindex++;
		$this->status = $container->status;
		$this->update_button = FALSE;
		$this->update_byteindex = FALSE;
		$this->warn = $warn;
		}
	function put_start(&$tag, &$attribute, $byteindex){
		if($this->update_button){
			$this->update_button->put_start($tag,$attribute,$byteindex);
		}
		else{
			if($tag == "button"){
				$this->update_button = new update_button($tag, $this, $this->config, $warn);
			}
			else{
				$this->current = $tag;
				if(trim($tag)=="content")
					$this->byteindex = $byteindex;
				if(trim($tag)=="active")
					$this->basket[$this->current] = '1';
			}
		}
	}
	function put_value(&$value){
		if($this->update_button){
			$this->update_button->put_value($value);
		}
		else
			$this->basket[$this->current] .= $value;
	}

	function finish(&$tag){
		if($this->update_button){
			if($this->update_button->finish($tag)){
				$this->update_byteindex = $this->update_button->byteindex;
				$this->basket["update"] = $this->update_button->show();
				$this->update_button = FALSE;
			}
		}
		else{
			if($this->tag == $tag)
				return TRUE;
			else
				return FALSE;
		}
	}
	function show(){}
}

class extra_multi extends extra{
	var $area;
	var $name;
	var $sub_attribute;

	function put_start(&$tag, &$attribute, $byteindex){
		if($this->update_button){
			$this->update_button->put_start($tag,$attribute,$byteindex);
		}
		else{
			if($tag == "button"){
				$this->update_button = new update_button($tag, $this, $this->config, $warn);
			}
			else{
				$this->current = $tag;
				$this->byteindex = $byteindex;
				if($tag=="choice"){
					$this->area=$tag;
					$this->sub_attribute = $attribute;
					}
				else if ($tag=="var") $this->area=$tag;
				if($this->current == "content")$this->basket[$this->area][$this->name]["byteindex"] = $this->byteindex;
			}
		}
	}

	function put_value(&$value){
		if($this->update_button){
			$this->update_button->put_value($value);
		}
		else{
			if($this->area){
				if($this->current == "name") $this->name = $value;
				else{
				$this->basket[$this->area][$this->name][$this->current] .= $value;
				if($this->area == "choice")
					$this->basket[$this->area][$this->name]["level"] = $this->sub_attribute["level"];
				}
			}
			else
			$this->basket[$this->current] .= $value;

		}
	}
	function finish(&$tag){
		if($this->update_button){
			if($this->update_button->finish($tag)){
				$this->update_byteindex = $this->update_button->byteindex;
				$this->basket["update"] = $this->update_button->show();
				$this->update_button = FALSE;
			}
		}
		else{
			if($this->tag == $tag)
				return TRUE;
			else{
				if($tag=="choice") $this->area=FALSE;
				else if ($tag=="var") $this->area=FALSE;
				return FALSE;
			}
		}
	}

}

class question_date extends extra{
	function show(){
      		$str .= "<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\" title=\"".$this->basket["helptext"]."\" ";
		if($this->js && isset($this->basket["update"])) $str .=  "onBlur=\"sendForm(".$this->update_byteindex.")\" ";
		$str .= ">\n";
		$str .= "<tr><td colspan=\"6\">\n<table border=\"0\" cellspadding=\"0\">\n";
		$str .= "<tr><td class=\"description\" height=\"20\" valign=\"bottom\">\n";
		$str .= "<img src=\"style/blank_spacer.gif\" width=\"2\" height=\"2\"></img>\n";
		if(isset($this->attribute["passive"])) $access = "disabled";
		$str .= $this->basket["description"]."\n</td>\n";
		if($this->warn) $str .= "<td><img src=\"style/".$this->warn.".gif\" alt=\"\" class=\"warn\"></img></td>\n";
		$str .= "</tr>\n</table>\n</td>\n";
		$str .= "</tr>\n<tr><td width=\"40\">\n";
		$content = explode('.',$this->basket["content"]);
		$class="class=\"date\"";
		if($this->warn)	$class="class=\"date_warn\"";
		$attribs="maxlength=\"2\" $class $access type=\"text\" ";
		$str .= "<input tabindex=\"".$this->tabindex."\" ".$attribs;
		$str .= "name=\"usrinput[date#".$this->byteindex."][]\" value=\"".$content[0]."\"></input>\n";
		$str .= "</td><td width=\"8\">&nbsp;</td><td width=\"40\">\n";
		$str .= "<input tabindex=\"".$this->tabindex."\" ".$attribs;
		$str .= "name=\"usrinput[date#".$this->byteindex."][]\" value=\"".$content[1]."\"></input>\n";
		$str .= "</td><td width=\"8\">&nbsp;</td><td width=\"40\">\n";
		$str .= "<input tabindex=\"".$this->tabindex."\" ".$attribs;
		$str .= "name=\"usrinput[date#".$this->byteindex."][]\" value=\"".$content[2]."\"></input>\n";
		$str .= "</td><td>\n";
		if(isset($this->basket["update"])) $str .= $this->basket["update"];
		$str .= "</td></tr>\n";
		$str .= "</table>\n";
		return $str;
	}
}

class question_text extends extra{
	function show(){

		if(isset($this->attribute["passive"])) $access = "disabled";
		$str .= "<table border=\"0\" cellspacing=\"0\" cellpadding=\"0\">\n";
		if($this->basket["description"]) {
			$str .= "<tr><td class=\"description\">\n<img src=\"style/blank_spacer.gif\" height=\"2\" width=\"2\"></img>\n";
			$str .= $this->basket["description"];
			if($this->warn) $str .= "<img src=\"style/".$this->warn.".gif\" alt=\"\" class=\"warn\"></img>\n";
			$str .= "</td></tr>\n";
			}
		$str .= "<tr><td>\n";
		$str .= "<input title=\"".$this->basket["helptext"]."\" tabindex=\"".$this->tabindex."\" ";
		if($this->attribute["width"]) $str .= "style=\"width:".($this->attribute["width"])."px\" ";
		if($this->js && isset($this->basket["update"])) $str .= "onChange=\"sendForm(".$this->update_byteindex.")\" ";
		if($this->warn) $str .= " class=\"text_warn\" ";
		else $str .= " class=\"text\" ";
		$str .= " type=\"text\" $access name=\"usrinput[".$this->byteindex."]\" value=\"".$this->basket["content"]."\"></input>\n";
		if(isset($this->basket["update"])) $str .= $this->basket["update"]."\n";
		$str .= "</td></tr>\n</table>\n";
		return $str;
	}


}

class question_file extends extra{
	function show(){
		if(isset($this->attribute["passive"])) $access = "disabled";
		$str .= "<table border=\"0\" cellspacing=\"0\" cellpadding=\"0\">\n";
		if($this->basket["description"]) {
			$str .= "<tr><td class=\"description\">\n<img src=\"style/blank_spacer.gif\" height=\"2\" width=\"2\"></img>\n";
			$str .= $this->basket["description"];
			if($this->warn) $str .= "<img src=\"style/".$this->warn.".gif\" alt=\"\" class=\"warn\"></img>\n";
			$str .= "</td></tr>\n";
			}
		$str .= "<tr><td>\n";
		$str .= "<input type=\"hidden\" name=\"file\" value=\"".$this->byteindex."\"></input>\n";
		$str .= "<input title=\"".$this->basket["helptext"]."\" tabindex=\"".$this->tabindex."\" \n";
		if($this->attribute["width"]) $str .= "style=\"width:".($this->attribute["width"])."px\" \n";
		if($this->js && isset($this->basket["update"])) $str .= "onChange=\"sendForm(".$this->update_byteindex.")\" \n";
		if($this->warn) $str .= " class=\"file_warn\" \n";
		else $str .= " class=\"file\" ";
		$str .= " type=\"file\" $access name=\"userfile\"></input>\n";
		if(isset($this->basket["update"])) $str .= $this->basket["update"]."\n";
		$str .= "</td></tr>\n</table>\n";
		return $str;
	}


}

class question_ltext extends extra{
	function show(){
		if(isset($this->attribute["passive"])) $access = "disabled";
		$str .= "<table border=\"0\" cellspacing=\"0\" cellpadding=\"0\">\n";
		if($this->basket["description"]){
			$str .= "<tr><td class=\"description\"><img src=\"style/blank_spacer.gif\" height=\"2\" width=\"2\"></img>\n".$this->basket["description"];
			if($this->warn) $str .= "<img src=\"style/".$this->warn.".gif\" alt=\"\" class=\"warn\"></img>\n";
			$str .= "</td></tr>\n";
			}
		$str .= "<tr><td>\n";
		$str .= "<textarea $access title=\"".$this->basket["helptext"]."\" tabindex=\"".$this->tabindex."\" ";
		if($this->attribute["width"] || $this->attribute["height"]){
			$str .= "style=\" ";
			if($this->attribute["width"]) $str .= "width:".($this->attribute["width"])."px; ";
			if($this->attribute["height"]) $str .= "height:".($this->attribute["height"])."px";
			$str .= "\" ";
			if(isset($this->attribute["readonly"])) $str .= " readonly=\"\" ";
			}
		if($this->js && isset($this->basket["update"])) $str .= "onChange=\"sendForm(".$this->update_byteindex.")\" ";
		if($this->warn) $str .= "class=\"longtext_warn\"";
		else $str .= "class=\"longtext\"";
		$str .= "name=\"usrinput[".$this->byteindex."]\">\n";
		$str .= $this->basket["content"]."</textarea>\n";
		$str .= "</td></tr>\n";
		if(isset($this->basket["update"])) $str .= "<tr><td>\n".$this->basket["update"]."</td></tr>\n";
		$str .= "</table>\n";
		return $str;

	}

}

class question_secure extends extra{
	function show(){
		if(isset($this->attribute["passive"])) $access = "disabled";
    		$str .= "<table border=\"0\" cellspacing=\"0\" cellpadding=\"0\">\n";
		$str .= "<tr><td class=\"description\"><img src=\"style/blank_spacer.gif\" width=\"2\" height=\"2\"></img>\n".$this->basket["description"];
		if($this->warn) $str .= "<img src=\"style/".$this->warn.".gif\" alt=\"\" class=\"warn\"></img>\n";
		$str .= "</td></tr>\n";
		$str .= "<tr><td><input title=\"".$this->basket["helptext"]."\" tabindex=\"".$this->tabindex."\"";
		if($this->attribute["width"]) $str .= "style=\"width:".($this->attribute["width"])."px\" ";
		if($this->js && isset($this->basket["update"])) $str .= "onChange=\"sendForm(".$this->update_byteindex.")\" ";
		if($this->warn) $str .= " class=\"text_warn\" ";
		else $str .= " class=\"text\" ";
		$str .= "type=\"password\" $access name=\"usrinput[".$this->byteindex."]\" value=\"".$this->basket["content"]."\"></input>\n";
		if(isset($this->basket["update"])) $str .= $this->basket["update"]."\n";
		$str .= "</td></tr>\n</table>\n";
		return $str;
	}

}

class question_bool extends extra{
	function show(){
		if(isset($this->attribute["passive"])) $access = "disabled";
		if(trim($this->basket["content"])!="") $is='checked';
		$str .= "<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\"><tr>\n";
		$str .= "<td valign=\"middle\">\n";
		$str .= "<input title=\"".$this->basket["helptext"]."\" tabindex=\"".$this->tabindex."\" class=\"bool\" type=\"checkbox\" $access ";
		if($this->js && isset($this->basket["update"])) $str .= "onChange=\"sendForm(".$this->update_byteindex.")\" ";
		$str .= "name=\"usrinput[".$this->byteindex."]\" value=\"checked\" $is></input></td>\n";
		if(trim($this->basket["description"]) != ''){
			$str .= "<td class=\"description\" align=\"left\" valign=\"middle\">\n";
			$str .= "<img src=\"style/blank_spacer.gif\" width=\"2\" height=\"2\"></img>\n";
			$str .= $this->basket["description"]."\n";
			$str .= "</td>\n";
			}
		$str .= "<td>\n";
		if($this->warn) $str .= "<img src=\"style/".$this->warn.".gif\" alt=\"\" class=\"warn\"></img>\n";
		if(isset($this->basket["update"])) $str .= $this->basket["update"];
		$str .= "</td></tr>\n</table>\n";
		$is='';
		return $str;
	}
}

class reset extends extra{
	function show(){
		if(isset($this->attribute["passive"])) $access = "disabled";
		$class=$this->status;
		if($this->warn) $str .= "<img src=\"style/".$this->warn.".gif\" alt=\"\" class=\"warn\"></img>\n";
      		$str .=  "<input title=\"".$this->basket["helptext"]."\" tabindex=\"".$this->tabindex."\" id=\"button".$this->tabindex."\" ";
		if($this->attribute["width"]) $str .= "style=\"width:".($this->attribute["width"])."px\" ";
		$str .= "class=\"button$class\" type=\"reset\" name=\"usrinput[".$this->byteindex."]\" $access value=\" ".$this->basket["text"]."\" ></input>\n";
		return $str;
	}

}

class button extends extra{
	function show($csslength=FALSE){
		if(isset($this->attribute["passive"])) $access = "disabled";
		$class=$this->status;
		if(isset($this->attribute["active"])) $class .= "_on";

		if($this->js && $class != 'notebook' && $class != 'categoryitem' && isset($this->attribute["icon"])){

		  // define form-contens
		  if(!isset($this->attribute["passive"])){
		    if($this->status == "content")
		      $href= "<a class=\"$class\" onClick=\"sendForm(".$this->byteindex.")\"";
		    else
		      $href = "<a class=\"$class\" onClick=\"sendForm2(".$this->byteindex.")\"";

		    $href .= " title=\"".$this->basket["helptext"]."\" ";

		    $img = "<input src=\"".$this->attribute["icon"]."\" tabindex=\"".$this->tabindex."\" name=\"usrinput[".$this->byteindex."]\" type=\"image\" value=\"pressed\" class=\"button_icon\" title=\"".$this->basket["helptext"]."\"></input>\n";

		    $link = $href.">\n";
		    $link .= "<span class=\"$class\">".$this->basket["text"]."</span></a>\n";


		    $inp = "<input type=\"hidden\" id=\"".$this->byteindex."\" name=\"usrinput[".$this->byteindex."]\" value=\"".$this->basket["content"]."\"></input>\n";
		  }
		  else
		    {
		      $img = "<img class=\"$class\" src=\"".$this->attribute["icon"]."\" alt=\"\"></img>\n";
		      $link = "<span class=\"$class\">".$this->basket["text"]."</span>\n";
		      $inp = "";
		    }

		  // build html
		  if ($class == "menu3" || $class == "menu3_on" || $class == "menu2" || $class == "menu2_on") { //menu
		    $str .= "          <tr>\n";
		    if ($class == "menu3" || $class == "menu3_on") //submenu
		      {
			$str .= "           <td></td>\n";
			$str .= "           <td colspan=\"2\">\n";
			$str .= "           <table class=\"submenu\">\n";
			$str .= "            <tr>\n";
			$str .= "             <td class=\"submenu_icon\"> \n";
			$str .= "             ".$inp;
			$str .= "             ".$img;
			$str .= "             </td>\n";
			$str .= "             <td class=\"submenu_spacer\">&nbsp;</td>\n";
			$str .= "             <td class=\"submenu_link\">\n";
			$str .= "             ".$link;
			$str .= "             </td>\n";
			$str .= "            </tr>\n";
			$str .= "           </table>\n";
		      }
		    else //main menu
		      {
			$str .= "           <td class=\"submenu_icon\"> \n";
			$str .= "           ".$inp;
			$str .= "           ".$img;
			$str .= "           </td>\n";
			$str .= "           <td class=\"submenu_spacer\">&nbsp;</td><td>\n";
			$str .= "           ".$link."\n";
		      }

		    $str .= "           </td>\n";
		    $str .= "          </tr>\n";
		    $str .= "          <tr>\n";
		    $str .= "            <td height=\"10\"></td>\n";
		    $str .= "            <td></td>\n";
		    $str .= "            <td></td>\n";
		    $str .= "          </tr>\n";

		  }
		  else //i.e. search result
		    {
		      $str .= "<table class=\"button\"><tr><td class=\"button_icon\">".$inp.$img;
		      if(trim($this->basket["text"]) != "")
		        $str .= "</td><td class=\"button_link\">".$link."</td><td>&nbsp;\n";
		      $str .= "</td></tr>\n</table>\n";
		    }


		  /* no icon */
		}elseif($this->js && isset($this->attribute["link"])){
			if (isset($this->attribute["type"])) $str .= "<a class=\"".$this->attribute["type"]."\" onClick=\"sendForm(".$this->byteindex.")\"";
			elseif($this->status == 'content') $str .= "<a class=\"$class\" onClick=\"sendForm(".$this->byteindex.")\"";
			else	$str .= "<a class=\"$class\" onClick=\"sendForm2(".$this->byteindex.")\"";
			$str .= " title=\"".$this->basket["helptext"]."\">\n";
			$str .= $this->basket["text"]."</a>\n";
			$str .= "<input type=\"hidden\" id=\"".$this->byteindex."\" name=\"usrinput[".$this->byteindex."]\" value=\"".$this->basket["content"]."\"></input>\n";
		}elseif($this->js && strstr($this->status, 'menu')) {
			if($this->basket["active"]) $class .= "_on";
			if(isset($this->attribute["passive"])){
				$str .= "<div id=\"div".$this->byteindex."\" class=\"link_passive\">".$this->basket["text"]."</div>\n";
				}
			else{
				$str .= "<div id=\"div".$this->byteindex."\" class=\"link$class\" ";
				if(!$this->basket["active"]) $str .= "onMouseOver=\"setBG('div".$this->byteindex."',1)\" onMouseOut=\"setBG('div".$this->byteindex."',0)\">\n";
				$str .= "<a class=\"$class\" onClick=\"sendForm2(".$this->byteindex.")\" title=\"".$this->basket["helptext"]."\">\n";
				if(strstr($this->status, '3') && strstr($this->status, 'menu')) $str .= "<img class=\"sub\" src=\"style/sub_mark.png\" align=\"middle\" alt=\"\"></img>\n";
				$str .= $this->basket["text"];

				$str .= "</a></div>\n";
				$str .= "<input type=\"hidden\" id=\"".$this->byteindex."\" name=\"usrinput[".$this->byteindex."]\" value=\"".$this->basket["content"]."\"></input>\n";
				}
		}
		elseif($this->js && $class == 'categoryitem')
		  {
		    $cssclass = $class;
		    if ($this->basket[active])
      		       $cssclass .= "active";


		    if (isset($this->attribute["closebutton"]) && ($this->attribute["closebutton"] == "1"))
 		     {
		       // closebutton -- just an icon
		      if ($this->basket[active]) {
			  	$icon_str = "/icon/close_tab_active.gif";
			  } else {
			  	$icon_str = "/icon/close_tab_inactive.gif";
			  }
		      $cssclass .= "closeableend"; // closebuttons are always the last in a closable categoryitem
		      $img_str = "<img src=\"".$icon_str."\" class=\"img$cssclass\">";
		      $str .= "<a class=\"$cssclass\" onClick=\"sendForm(".$this->byteindex.")\" title=\"X\">".$img_str."</a>";
		      $str .= "<input type=\"hidden\" id=\"".$this->byteindex."\" name=\"usrinput[".$this->byteindex."]\" value=\"".$this->basket["content"]."\"></input>\n";
		     }
		    else
		     {
		      $img_str = "";
		      $close_str = "";
		      if (isset($this->attribute["closeable"]) && ($this->attribute["closeable"] == "1")) {
		        $cssclass .= "closeablestart";
			  }
		      if (isset($this->attribute["icon"]))
		       {
		         $img_str = "<input src=\"".$this->attribute["icon"]."\" tabindex=\"".$this->tabindex."\" name=\"usrinput[".$this->byteindex."]\" type=\"image\" value=\"pressed\" class=\"button_icon\" title=\"".$this->basket["helptext"]."\"></input>\n";
		       }
		      $str .= "<a class=\"$cssclass\" onClick=\"sendForm(".$this->byteindex.")\"";
		      $str .= " title=\"".$this->basket["helptext"]."\">".$img_str."&nbsp;";
		      $str .= $this->basket["text"];
		      $str .= "</a>\n";
		      $str .= "<input type=\"hidden\" id=\"".$this->byteindex."\" name=\"usrinput[".$this->byteindex."]\" value=\"".$this->basket["content"]."\"></input>\n";
		     }
		  }
		elseif($this->js && $class == 'notebook'){
		  $tdclass="tab";
		  $img="\"style/reiter_grau18x24.gif\"";

		  $close_icon_str = "/icon/close_page_inactive.gif";
		  if($this->basket['active'])
		    {
		      $class = 'notebook_on';
		      $tdclass = "tab_on";
		      $img="\"style/reiter_rot18x24.gif\"";
			  $close_icon_str = "/icon/close_page_active.gif";
		    }
		  if(isset($this->attribute["passive"]))
		    {
		      $str .= "<span id=\"div".$this->byteindex."\" class=\"notebook_passive\">".$this->basket["text"]."</span>\n";
		    }
		  else
		    {
			  if (isset($this->attribute["closebutton"]) && ($this->attribute["closebutton"] == "1"))
			  {
                # close button
				$class .= "closeableend";
				$str .= "<td class=\"$tdclass\" nowrap><a class=\"$class\" onClick=\"sendForm(".$this->byteindex.")\"";
				$str .= " title=\"close\">";
				$str .= "<img class=\"$class\" src=\"".$close_icon_str."\">\n";
				$str .= "</a>";
				$str .= "<input id=\"". $this->byteindex ."\" name=\"usrinput[".$this->byteindex."]\" type=\"hidden\" value=\"\"></input>\n";
				$str .= "</td>";
			  } 
			  else
			  {
				if (isset($this->attribute["closeable"]) && ($this->attribute["closeable"] == "1")) {
				  $class .= "closeablestart";
				}

				$str .= "<td class=\"$tdclass\" nowrap>\n";
				$str .= "<table style=\"padding: 0px;\"><tr>";
				$str .= "<td><a class=\"$class\" onClick=\"sendForm(".$this->byteindex.")\"";
				if (  isset( $this->attribute[ "icon" ] ) ) {
				  $str .= " title=\"".$this->basket["helptext"]."\">";
				  $str .= "<img class=\"$class\" src=\"".$this->attribute["icon"]."\" alt=\"\"></img>";
				} else {
				  $str .= " title=\"".$this->basket["helptext"]."\">";
				}
				$str .= "&nbsp;";
				$str .= $this->basket["text"];
				$str .= "</a></td>\n";
				if (  isset( $this->attribute[ "statusicon" ] ) ) {
				  $str .= "<td><img class=\"$class\" src=\"".$this->attribute["statusicon"]."\" alt=\"\"></img></td>";
				}
				$str .= "<input type=\"hidden\" id=\"".$this->byteindex."\" name=\"usrinput[".$this->byteindex."]\" value=\"".$this->basket["content"]."\"></input>\n";
				$str .= "</tr></table></td>\n";
			  }
		    }
		}
		else
		  {
		    if($class == 'notebook' && $this->basket['active']) $class = 'notebook_on';
		    $str .=  "<input tabindex=\"".$this->tabindex."\" id=\"button".$this->tabindex."\" $access ";
		    if($this->attribute["width"]) $str .= "style=\"width:".($this->attribute["width"])."px\" ";
		    $str .= "class=\"button$class\" type=\"submit\" name=\"usrinput[".$this->byteindex."]\" value=\" ".$this->basket["text"]."\"";
		    if($csslength) $str .=  " style=\"width:".$csslength."px;\" ";
		    $str .=  " title=\"".$this->basket["helptext"]."\"></input>\n";
		  }
		return $str;
	}
}

class update_button extends extra{
	function show(){
		if($this->js){
			$str .=  "<input type=\"hidden\" id=\"".$this->byteindex."\" name=\"usrinput[".$this->byteindex."]\" value=\"".$this->basket["content"]."\"></input>\n";
			}
	  	else{	$class=$this->status;
	   		$this->tabindex++;
        		$str .=  "<input tabindex=\"".$this->tabindex."\" id=\"button".$this->tabindex."\"";
			$str .=  " class=\"button$class\" type=\"submit\" name=\"usrinput[".$this->byteindex."]\" value=\" ";
			$str .=  $this->basket["text"]."\" ></input>\n";
			}
		return $str;
	}
}

class link extends extra{
	function show(){
		$class=$this->modus;
	  	if(stristr($this->basket["dest"],"uniconf_modul")) $this->basket["dest"] .= "&sesion_id=$session_id";
        	$str .=  "<a class=\"$class\"  tabindex=\"".$this->tabindex."\" href=\"".$this->basket["dest"]."\">\n";
		$str .= "&nbsp;".$this->basket["text"]."\n";
		$str .= "</a>\n";
	  	return $str;
	}
}

class question_select extends extra_multi{
	function show(){
		$appendstr = "";
		if(isset($this->attribute["passive"])) $access = "disabled";
		$str .= "<table border=\"0\" cellpadding=\"0\" cellspacing=\"0\">\n";
		$str .= "<tr><td class=\"description\"><img src=\"style/blank_spacer.gif\" width=\"2\" height=\"2\"></img>".$this->basket["description"]."\n";
		if($this->warn) $str .= "<img src=\"style/".$this->warn.".gif\" alt=\"\" class=\"warn\"></img>\n";
		$str .= "</td></tr>\n<tr><td>\n";
        	$str .= "<select $access title=\"".$this->basket["helptext"]."\" tabindex=\"".$this->tabindex."\"";
		if($this->warn) $str .= " class=\"select_warn\" ";
		else $str .= " class=\"select\" ";
		if($this->attribute["width"]) $str .= "style=\"width:".($this->attribute["width"])."px\" ";
		if($this->js && isset($this->basket["update"])) $str .= "onchange=\"sendForm(".$this->update_byteindex.")\" ";
		if ($access != "disabled")
			$str .= "name=\"usrinput[multiple#".$this->tabindex."][]\"";
		$str .= ">\n";
		if($this->basket["choice"])
			foreach($this->basket["choice"] as $key=>$val) {
	        		if(trim($this->basket["var"][$key]["content"])!="") {
					$is='selected';
					if ($access == "disabled") {
						$appendstr = "<input type=\"hidden\" name=\"usrinput[multiple#".$this->tabindex."][]\"";
						$appendstr .= " value=\"".$this->basket["var"][$key]["byteindex"]."\"></input>\n";
					}
				}
				for($x=0; $x < $this->basket["choice"][$key]["level"]; $x++) $space .= "&nbsp;";
        			$str .= "<option value=\"".$this->basket["var"][$key]["byteindex"]."\" $is >\n";
				$str .= $space.$this->basket["choice"][$key]["description"];
				$str .= "</option>\n";
	        		$is = '';
				$space = '';
			}
        	$str .="</select>\n";
   		if(isset($this->basket["update"])) $str .= $this->basket["update"]."\n";
		$str .= $appendstr;
		$str .= "</td></tr>\n</table>\n";
		return $str;
	}
}

class question_mselect extends extra_multi{
	function show(){
		if(isset($this->attribute["passive"])) $access = "disabled";
		$str .= "<table border=\"0\" cellspacing=\"0\" cellpadding=\"0\">\n";
		$str .= "<tr><td class=\"description\"><img src=\"style/blank_spacer.gif\" width=\"2\" height=\"2\"></img>".$this->basket["description"]."\n";
		if($this->warn) $str .= "<img src=\"style/".$this->warn.".gif\" alt=\"\" class=\"warn\"></img>\n";
		$str .= "</td></tr><tr><td>\n";
        	$str .= "<select $access title=\"".$this->basket["helptext"]."\" tabindex=\"".$this->tabindex."\"";
		if($this->warn) $str .= " class=\"mselect_warn\" ";
		else $str .= " class=\"mselect\" ";
		if($this->js && isset($this->basket["update"])) $str .= "onChange=\"sendForm(".$this->update_byteindex.")\" ";
		if($this->attribute["width"] || $this->attribute["height"]){
			$str .= "style=\" ";
			if($this->attribute["width"]) $str .= "width:".($this->attribute["width"])."px; ";
			if($this->attribute["height"]) $str .= "height:".($this->attribute["height"])."px";
			$str .= "\" ";
			}
		$str .= "name=\"usrinput[multiple#".$this->tabindex."][]\" multiple size=\"5\">\n";
        	if($this->basket["choice"])
			foreach($this->basket["choice"] as $key=>$val)
		      		{
				if(trim($this->basket["var"][$key]["content"])!="") $is='selected';
	 	       		$str .= "<option value=\"".$this->basket["var"][$key]["byteindex"]."\" $is>\n";
				$str .= $this->basket["choice"][$key]["description"];
				$str .= "</option>\n";
        			$is = '';
        			}
        	$str .="</select>\n";
		$str .= "</td></tr>\n</table>\n";
   		if(isset($this->basket["update"])) $str .= $this->basket["update"]."\n";
		return $str;
	}

}

class question_choice extends extra_multi{
	function show(){
		if(isset($this->attribute["passive"])) $access = "disabled";
		$str .= "<div title=\"".$this->basket["helptext"]."\" >\n";
		if (isset($this->basket["description"]) && trim($this->basket["description"]) != "")
			$str .= $this->basket["description"]."<br />\n";
		if($this->warn) $str .= "<img src=\"style/".$this->warn.".gif\" alt=\"\" class=\"warn\"></img>\n";
        	 foreach($this->basket["choice"] as $key=>$val)
        		{
        		if(trim($this->basket["var"][$key]["content"])!="")$is='checked';
      			$str .= "<input tabindex=\"".$this->tabindex."\" class=\"choice\" ";
			if($this->js && isset($this->basket["update"])) $str .= "onClick=\"sendForm(".$this->update_byteindex.")\" ";
			$str .= "type=\"radio\" name=\"usrinput[multiple#".$this->tabindex."][]\" $access value=\"".$this->basket["var"][$key]["byteindex"]."\" $is></input>\n";
        		$str .= $this->basket["choice"][$key]["description"]."<br />\n";
        		$is='';
        		}
        	if(isset($this->basket["update"])) $str .= $this->basket["update"]."\n";
		$str.="</div>\n";
		return $str;
	}
}

class session_data{
	var $name;
	var $value;
	var $byteindex;

	function session_data($name){
	$this->name = $name;
	}
	function put_start($tag,$atrib,$byteindex){
	if ($tag=="content") $this->byteindex=$byteindex;
	}
	function put_value($val){
	$this->value .= $val;
	}
	function finish($tag){
	if($tag == "content")return TRUE;
	else return FALSE;
	}
	function show(){
	return "<input type=\"hidden\" name=\"session_data[".$this->name."]\" value=\"".$this->value."\"></input>\n";
	}

}

class categorylist{

  var $category_buttons;
  var $category_close_buttons;
  var $tag;
  var $container;
  var $unsort;
  var $count;
  var $attribute;
  var $config;
  var $warn;

  function categorylist($tag, &$container, $config, $attribute, $warn=FALSE){
    $this->attribute = $attribute;
    $this->config = &$config;
    $this->tag = $tag;
    $this->count = 0;
    $this->container = &$container;
    $this->container->status = 'categoryitem';
    $this->warn = $warn;
  }

  function put_start(&$tag, &$attribute, $byteindex)
  {
    $close_attribute = $attribute;
    //$close_attribute["closebutton"] = "1";
    if(trim($tag) == 'button')
     {
      $this->category_buttons[++$this->count] = new button($tag, $this->container, $this->config, $attribute, $this->warn);
      //$this->category_close_buttons[$this->count] = new button($tag, $this->container, $this->config, $close_attribute, $this->warn);
     }
    elseif(is_object($this->category_buttons[$this->count]))
    {
      $this->category_buttons[$this->count]->put_start($tag, $attribute, $byteindex);
      //$this->category_close_buttons[$this->count]->put_start($tag, $attribute, $byteindex+1); # wouldn't call this a clean "byteindex"...
     }
  }

  function put_value(&$value)
  {
    if(is_object($this->category_close_buttons[$this->count]))
      {
      $this->category_buttons[$this->count]->basket['closed'] = $this->category_close_buttons[$this->count]->basket['pressed'];
      }
    if(is_object($this->category_buttons[$this->count]))
      $this->category_buttons[$this->count]->put_value($value);
  }

  function finish(&$tag)
  {
    if($this->tag == $tag)
      return TRUE;
    else
      return FALSE;
  }

  function show()
  {
    $str_start = "\n\n<!-- start of categorylist--> \n<div id=\"category\">\n<table border=\"0\" cellspacing=\"0\" cellpadding=\"0\">\n";
    $str_start .= "<tr><td nowrap valign=\"top\">\n<div id=\"categorystart\">&nbsp;</div>\n</td><td width=\"100%\">\n<div id=\"categorycenter\">\n";
    $str_end = "</div>\n</td><td nowrap valign=\"top\">\n<div id=\"categoryend\">&nbsp;</div>\n</td></tr>\n</table>\n</div>\n<!-- end of categorylist-->\n\n";
    $str_buttons = "";
    for($i=1; $i < $this->count+1; $i++) # i is index for button-object-array
      {
        if ( $this->category_buttons[$i]->attribute["closeable"] )
	  $cssclass = "categoryitemactivecloseable";
	else
	  $cssclass = "categoryitem-active";
	if( $this->category_buttons[$i]->basket[active] )
	  { // active button
	  if(!$this->category_buttons[$i]->attribute["closebutton"] == "1")
	    $str_buttons .= "<span class=\"categoryitem-active\">\n";
	  }

	// the button
	$str_buttons .= $this->category_buttons[$i]->show();

	if( $this->category_buttons[$i]->basket[active] )
	   { // active button
	     if($this->category_buttons[$i]->attribute["closebutton"] == "1" || !$this->category_buttons[$i]->attribute["closeable"])
	       $str_buttons .= "</span>\n";
	   }
	}

    return $str_start.$str_buttons.$str_end;
  }
}

class notebook{

	var $all_notebook;
	var $tag;
	var $container;
	var $unsort;
	var $count;
	var $attribute;
	var $config;
	var $warn;

	function notebook($tag, &$container, $config, $attribute, $warn=FALSE){
		$this->attribute = $attribute;
		$this->config = &$config;
		$this->tag = $tag;
		$this->count = 0;
		$this->container = &$container;
		$this->container->status = 'notebook';
		$this->warn = $warn;
	}
	function put_start(&$tag, &$attribute, $byteindex){
		if(trim($tag) == 'button')
			$this->all_notebook[++$this->count] = new button($tag, $this->container, $this->config, $attribute, $this->warn);
		elseif(is_object($this->all_notebook[$this->count]))
			$this->all_notebook[$this->count]->put_start($tag, $attribute, $byteindex);
	}
	function put_value(&$value){
		if(is_object($this->all_notebook[$this->count]))
			$this->all_notebook[$this->count]->put_value($value);
	}
	function finish(&$tag){
		if($this->tag == $tag)
			return TRUE;
		else
			return FALSE;
		}
	function show(){
		$j = 1;
		$length = 0;
		$pressed = FALSE;
		$factor = 7; // pixel per letter
		$one_line=TRUE;
		for($i=1; $i < $this->count+1; $i++){ # i is index for button-object-array

  		    $itemlength = $factor*(strlen($this->all_notebook[$i]->basket[text]));
			if ($this->all_notebook[$i]->attribute["closebutton"] == "1") {
			  $itemlength = 14; // width of closebutton object
			  $spare = 10; // width pixel between
			} else {
			  $spare = 20; // width pixel between
			}

			if((($length + $itemlength) > 764) || $i == $this->count){ # 780 at all - 14 (right) - 2 (left) -> 764
				if($i == $this->count){
					$end=$i+1;
					$length += ($itemlength+$spare);
					}
				else {	$one_line=FALSE;
					$end=$i;
					}
				$all = $end-$j;
				$first=$j;
				$space = 0; #round((580-$length*$factor) / ($end-$j));
				$x++;
				for($j; $j < $end; $j++){ # j is index for one line - end is end of line
					$sub='';
					$img='';
					$img_end='';
					$bg='';
					if(!$one_line){
						if(isset($str) && !array_key_exists('1',$str) && $x != 2 && $x != 1)
							$sub='_sub';
						elseif($pressed && $x == 1)
							$sub='_sub';
						elseif(isset($str) && array_key_exists('1',$str) && $x != 1)
							$sub='_sub';
						}

					if($first==$j){
					  $img = "";
					}
					else
					  {
					    if ($last_on)
					      {
						$img = "reiter_rotgrau18x24.gif";
					      }
					    elseif ($this->all_notebook[$j]->basket[active]) // this_on
					      {
						$img = "reiter_graurot18x24.gif";
					      }
					    else
					      {
						$img = "reiter_graugrau18x24.gif";
					      }
					  }

					if($this->all_notebook[$j]->basket[active])
					  { // active button

					    if($j==$end-1)
						  {
						    // last in line
						    $img_end = "reiter_rot18x24.gif";
						  }
					    //$bg='bg_on.gif';
					    $last_on=TRUE; // need to know for next button
					  }
					else // inactive
					  {
					    if($j==$end-1)
					      {
						//last in line
						$img_end="reiter_grau18x24.gif";
					      }
					    //$bg='bg_off.gif';
					    $last_on=FALSE; // need to know for next button
					  }

					if($img != '') $image = '<img class="note" src="style/'.$img.'" alt=""></img>';
					else $image = '';

					if($img_end != '') $image_end='<img class="note" src="style/'.$img_end.'" alt=""></img>';
					else $image_end='';

					$this->all_notebook[$j]->tabindex++;
					if($this->config->browser=="Text"){$img=""; $img_end="";}
					if($j == $end-1) {
					  $width = (490 - $total)+3;
					} else {
					  $width = $factor*(strlen($this->all_notebook[$j]->basket[text]));
					  if ($this->all_notebook[$j]->attribute["closebutton"] == "1") {
						$width = 14; // width of closebutton object
					  }
					  $total += $width;
					  #$width -= 11;      # Bildbreite
					}
					
					$show_start = TRUE;
					$show_end = TRUE;
					if ($this->all_notebook[$j]->attribute["closebutton"] == "1") {
					  $show_start = FALSE;
					}
					if ($this->all_notebook[$j]->attribute["closeable"]) {
					  $show_end = FALSE;
					}
#############################################################################################################################
					if($pressed)
					  {
					    if (($image!="") && $show_start) $str[pressed] .= '<td class="tab">'.$image."</td>\n";
					    $str[pressed] .= $this->all_notebook[$j]->show($width);
					    if (($img_end != '') && $show_end)  $str[pressed] .= '<td class="tab">'.$image_end."</td>\n";
					  }
					else
					  {
					    if (($image!="") && $show_start)  $str[$x] .= '<td class="tab">'.$image."</td>\n";
					    $str[$x] .= $this->all_notebook[$j]->show($width);
					    if (($img_end != '') && $show_end) $str[$x] .= '<td class="tab">'.$image_end."</td>\n";
					  }
##############################################################################################################################
					} #end of for
				$pressed = FALSE;
				$length = 0;
				$total = 0;
			}
			$length += $itemlength+$spare;
			if($this->all_notebook[$i]->basket[active]) {$pressed = TRUE;}

		} # end of for

		$this->container->status = 'content';
		foreach($str as $key=>$val)
		  {
		    if($key != 'pressed')
		      {
			$passive .= "    <tr class=\"notebook_line\"><td class=\"notebook_line\"><table class=\"tabs\" border=\"0\" cellpadding=\"0\" cellspacing=\"0\">\n";
			$passive .= "     <tr class=\"notebook\" border=\"0\" cellpadding=\"0\" cellspacing=\"0\">".$val."</tr>\n";
			$passive .= "    </table></td></tr><tr><td class=\"notebook_spacer\"></td></tr>\n";
		      }
		  }
		return "<table class=\"tabs\" summary=\"\" border=\"0\" cellpadding=\"0\" cellspacing=\"0\">\n<tr><td class=\"notebook_spacer\"></td></tr>\n".$passive."\n<tr class=\"notebook_pressed\">\n<td class=\"notebook_pressed\">\n   <table class=\"tabs\" border=\"0\" cellpadding=\"0\" cellspacing=\"0\"><tr>".$str[pressed]."</tr>\n</table>\n</td></tr><tr><td class=\"notebook_spacer\"></td></tr>\n</table>\n";
	}
}

class question_group{
	var $group;
	var $member;
	var $tag;
	var $conti_ref;
	var $attribute;
	var $config;
	var $warn;

	function question_group($tag, &$container, $config, $attribute, $warn=FALSE){
		$this->member = FALSE;
		$this->attribute = $attribute;
		$this->config = &$config;
		$this->tag = $tag;
		$this->conti_ref = &$container;
		$this->warn = $warn;
	}
	function put_start(&$tag, &$attribute, $byteindex){
		if(isset($attribute["warning"])){
			unset($attribute["warning"]);
			$this->warn='warning';
			}
		if($this->member){
			$this->member->put_start($tag,$attribute,$byteindex);
		}
		else{
		if(!$this->not_valid){
			$attribute["group"]=TRUE;
			switch($tag){
				case 'reset':  $this->member = new reset($tag, $this->conti_ref, $this->config, $attribute);return;
				case 'button':  $this->member = new button($tag, $this->conti_ref, $this->config, $attribute);return;
				case 'link': $this->member = new link($tag, $this->conti_ref, $this->config, $attribute);return;
				case 'question_bool': $this->member = new question_bool($tag, $this->conti_ref, $this->config, $attribute);return;
				case 'question_secure': $this->member = new question_secure($tag, $this->conti_ref, $this->config, $attribute);return;
				case 'question_date': $this->member = new question_date($tag, $this->conti_ref, $this->config, $attribute);return;
				case 'question_text': $this->member = new question_text($tag, $this->conti_ref, $this->config, $attribute);return;
				case 'question_ltext': $this->member = new question_ltext($tag, $this->conti_ref, $this->config, $attribute);return;
				case 'question_mselect': $this->member = new question_mselect($tag, $this->conti_ref, $this->config, $attribute);return;
				case 'question_select': $this->member = new question_select($tag, $this->conti_ref, $this->config, $attribute);return;
				case 'question_choice': $this->member = new question_choice($tag, $this->conti_ref, $this->config, $attribute);return;
				case 'question_group': $this->member = new question_group($tag, $this->conti_ref, $this->config, $attribute);return;
				default: $tag=""; $close="";
				}
			}
		}
	}
	function put_value(&$value){
		if($this->member) $this->member->put_value($value);
	}
	function finish(&$tag){
		if($this->member)
			if($this->member->finish($tag)){
				$this->group[]=$this->member->show();
				$this->member=FALSE;
				return FALSE;
			}
		if($tag == $this->tag){
			return TRUE;
			}

	}
	function show(){
		$group .= "<table class=\"group\">\n<tr>\n";
		if($this->warn) $group .= "<td>\n<img src=\"style/".$this->warn.".gif\" alt=\"\" class=\"warn\"></img>\n</td>\n";
		foreach($this->group as $key => $value)
			$group .= "<td>\n".$value."\n</td>\n";
		$group .= "</tr>\n</table>\n";
	return $group;

	}
}


###########################################
class long_table extends webui_translator
{
  var $count_row;
  var $hide;
  function put_start(&$tag, &$attribute, $byteindex)
  {
    if(trim($tag)=="content" && !$this->extra)
      {
	$this->hide=TRUE;
	$this->conti_ref->set_byteindex($byteindex);
      }
    if(!$this->temp)
      {
	$this->conti_ref->set_index();
	$this->temp ="used";
      }
    if($tag=="row")
      {
	$this->conti_ref->next_row($attribute['type']);
	if(!$attribute['type'] == 'header' || !$attribute['type'] == 'footer')
	  $this->count_row++;
      }
    $this->start($tag, $attribute, $byteindex);
  }

  function put_value(&$value)
  {
    if(!$this->hide)
      $this->value($value);
  }

  function finish(&$tag)
  {
    $this->end($tag);
    if($this->hide && $tag=="content")
      $this->hide=FALSE;

    if($tag=="long_table")
      return TRUE;
    else return FALSE;
  }

  function show()
  {
    $this->conti_ref->set_parameter($this->attribute['visible'], $this->attribute['total'], $this->attribute['start']);
#	$this->count_row
    $wrap_view = $this->conti_ref->wrap_view();
    $table = "\n<!-- start longtable -->\n";
    $table="<table class=\"content_list\" summary=\"\">\n".$this->conti_ref->show()."</table>\n";
    $table .= "<!-- finished longtable -->\n\n";
    $tb_index="<table class=\"content_sublist\" summary=\"\">\n<tr><td class=\"content_wrapview\">\n".$wrap_view."</td></tr>\n</table>\n";
    return $table.$tb_index;
  }
}

class table extends webui_translator
{

  function put_start(&$tag, &$attribute, $byteindex)
  {
    if($tag=="row") $this->conti_ref->next_row();
    $this->start($tag, $attribute, $byteindex);
  }

  function put_value(&$value)
  {
    $this->value($value);
  }

  function finish(&$tag)
  {
	if ($this->extra)
	  {
	    $this->end($tag);
	  }
	else
	  {
	    if ($tag=="table")
	      return TRUE;
	    else
	      return FALSE;
	  }
  }

  function show()
  {

    if (isset($this->attribute["border"])) // border is deprecated
      {
	if ($this->attribute["border"]=="1")
	  $attrib_str .= " class=\"content_border\"";
	if ($this->attribute["border"]=="0")
	  $attrib_str .= " class=\"content_plain\"";
      }

    $space_bottom="";

    if (isset($this->attribute["type"]))
      {
	$attrib_str .= " class=\"".$this->attribute["type"]."\"";
	$type = $this->attribute["type"];
      }
    else
      {
	$type = "default";
	$attrib_str .= " class=\"table_default\"";
      }

    if ($this->attribute["type"] == 'content_main')
      {
	$space_bottom="<tr><td class=\"content_spacer\">&nbsp;</td></tr>\n";
      }

    $table = "\n<!-- start table of type ".$type."-->\n";
    $table .= "<table $attrib_str  summary=\"\">\n".$this->conti_ref->show_all().$space_bottom."</table>\n";
    $table .= "<!-- finished table of type ".$type."-->\n\n";
    return $table;
  }

} //table

class tgroup extends webui_translator{
function put_start(&$tag, &$attribute, $byteindex){
	$this->conti_ref->next_row();
	$this->start($tag, $attribute, $byteindex);
	}
function put_value(&$value){$this->value($value);}
function finish(&$tag){
	if($this->extra){$this->end($tag);}
	else{	if($tag=="tgroup")return TRUE;
		else return FALSE;
		}
	}
function show(){
	$group=$this->conti_ref->show_all();
	return $group;
	}
}
class row extends webui_translator{
function put_start(&$tag, &$attribute, $byteindex){
	$this->conti_ref->next_row($this->attribute['type']);
	$this->start($tag, $attribute, $byteindex);
	}
function put_value(&$value){$this->value($value);}
function finish(&$tag){
	if($this->extra){$this->end($tag);}
	else{   if($tag=="row"){
			if(is_array($this->stack))
			foreach( $this->stack as $key => $value)
				$this->value($value);
			return TRUE;
			}
		else return FALSE;
		}
	}
function show(){
	if(isset($this->attribute["border"])) {
		if($this->attribute["border"]=="1")$attrib_str .= " class=\"border\"";
		if($this->attribute["border"]=="0")$attrib_str .= " class=\"plain\"";
		}
    	if(isset($this->attribute["type"]))
		$attrib_str = "class=\"".$this->attribute["type"]."\"";
	$row="<tr $attrib_str>".$this->conti_ref->show_all()."</tr>\n";
	return $row;
	}
}
class col extends webui_translator
{
  function put_start(&$tag, &$attribute, $byteindex)
  {
    $this->start($tag, $attribute, $byteindex);
  }

  function put_value(&$value)
  {
    if($this->extra)
      {
	$this->value($value);
      }
    else
      {
	if(is_array($this->stack))
	  $str=array_pop($this->stack);
	$str=$this->conti_ref->pop().$value.$str;
	$this->value($str);
      }
  }

  function finish(&$tag)
  {
    if($this->extra)
      {
	$this->end($tag);
      }
    else
      {
	if($tag=="col")
	  {
	    if(is_array($this->stack))
	      foreach( $this->stack as $key => $value)
		$this->value($value);
	    return TRUE;
	  }
	else return FALSE;
      }
  }

  function show()
  {
    if(isset($this->attribute["type"]))
      $attrib_str .= " class=\"".$this->attribute["type"]."\"";
    if(isset($this->attribute["colspan"]))
      $attrib_str .= " colspan=\"".$this->attribute["colspan"]."\"";
    if(isset($this->attribute["rowspan"]))
      $attrib_str .= " rowspan=\"".$this->attribute["rowspan"]."\"";
    if(isset($this->attribute["align"]))
      $attrib_str .= " align=\"".$this->attribute["align"]."\"";
    if(isset($this->attribute["nofill"]))
      $attrib_str .= " width=\"1\" ";
    $all=$this->conti_ref->show_all();
    if(trim($all)=="")
      $row="<td $attrib_str>&nbsp;</td>\n";
    else
      $row="<td $attrib_str>".$all."</td>\n";
    return $row;
  }
}

class dummy_container extends webui_container{
var $index;
var $position;
var $total;
var $visible;
var $start;
var $byteindex;
var $status="content";
var $temp;

function set_parameter($visible, $total, $start){
	$this->visible = $visible;
	$this->total = $total;
	$this->start = $start;
	if(!$this->ref_config->position) $this->position = $this->start;
	else $this->position = (($this->ref_config->position - 1) * $this->visible);
	}

function set_index(){$this->index = 0;}

function set_byteindex($byteindex){$this->byteindex = $byteindex;}

function next_row($type=FALSE){
	if($type){
	  $this->temp = $this->index;
	  $this->index = $type;
	  }
	elseif($this->index == 'header' || $this->index == 'footer' ){
	  $this->index = $this->temp;
	  $this->temp = FALSE;
	  }
	else{
	  $this->index++;
	  }
	$this->current = &$this->content;
	$this->status="content";
	}

function put($str){
	$this->content[$this->index] .= $str;
	}

function pop(){
	if(is_array($this->content))
	return array_pop($this->content);}

function show_all(){
	foreach($this->content as $key => $value){
		$str .= $value;
		}
	unset($this->content);
	return $str;
	}

function show(){
	foreach($this->content as $key => $value){
		if(!is_int($key))
		  switch($key){
		    case "footer": $footer = $value; break;
		    case "header": $header = $value; break;
		    }
		else $str = $value;
		}
	unset($this->content);
	return $header.$str.$footer;
	}

function wrap_view(){
	$current = ceil(($this->start+$this->visible) / $this->visible);
	$max = ceil($this->total / $this->visible);
	$first = $current - ($current % 10);
	$last = $first + 9;
	if ($first == 0)
	  $first++;
	if ($last > $max)
	  $last = $max;

	if($first != $last || $current > 1)
	  {
	    $str .= "<table>\n<tr><td>\n";

	    if(!$this->ref_config->is_js)
	      {
		$str .= "<!-- script -->\n";

		if ($first > 1)
		  $str .= "<input class=\"buttoncontent\" type=\"submit\" name=\"long_table[".$this->byteindex."]\" value=\"<<\"></input>\n";
		else
		  $str .= "<img class=\"icon\" src=\"style/no_arrow.gif\" style=\"margin:4px\" alt=\"\"></img>\n";

		$str .= "</td><td>\n";

		if ($current > 1)
		  $str .= "<input class=\"buttoncontent\" type=\"submit\" name=\"long_table[".$this->byteindex."]\" value=\"<\"></input>\n";
		else
		  $str .= "<img class=\"icon\" src=\"style/no_ar.gif\" style=\"margin:4px\" alt=\"\"></img>\n";

		$str .= "</td><td>\n";

		for ($y=$first; $y <= $last; $y++)
		  {
		    if ($y==$current)
		      $str .= "<input class=\"buttoncontent\" type=\"submit\" name=\"long_table[".$this->byteindex."]\" value=\"$y\" disabled></input>\n";
		    else
		      $str .= "<input class=\"buttoncontent\" type=\"submit\" name=\"long_table[".$this->byteindex."]\" value=\"$y\" style=\"color:#000000\"></input>\n";
		  }

		$str .= "</td><td>\n";

		if ($current < $max)
		  $str .= "<input class=\"buttoncontent\" type=\"submit\" name=\"long_table[".$this->byteindex."]\" value=\">\"></input>\n";
		else
		  $str .= "<img class=\"icon\" src=\"style/no_ar.gif\" style=\"margin:4px\" alt=\"\"></img>\n";

		$str .= "</td><td>\n";

		if ($last < $max)
		  $str .= "<input class=\"buttoncontent\" type=\"submit\" name=\"long_table[".$this->byteindex."]\" value=\">>\"></input>\n";
		else
		  $str .= "<img class=\"icon\" src=\"style/no_arrow.gif\" style=\"margin:4px\" alt=\"\"></img>\n";

	      }
	    else
	      {
		$str .= "<!-- no script -->\n";
		if($first > 1)
		  {
		    $str .= "<a class=\"$class\" onClick=\"sendForm('".$this->byteindex."','<<')\">\n";
		    $str .= "<img class=\"icon\" src=\"style/l_arrow.gif\" style=\"margin:4px\" alt=\"\"></img></a>\n";
		  }
		else
		  $str .= "<img class=\"icon\" src=\"style/no_arrow.gif\" style=\"margin:4px\" alt=\"\"></img>\n";

		$str .= "</td><td>\n";

		if ($current > 1)
		  {
		    $str .= "<a class=\"$class\" onClick=\"sendForm('".$this->byteindex."','".($current - 1)."')\">\n";
		    $str .= "<img class=\"icon\" src=\"style/l_ar.gif\" style=\"margin:4px\" alt=\"\"></img></a>\n";
		  }
		else
		  $str .= "<img class=\"icon\" src=\"style/no_ar.gif\" style=\"margin:4px\" alt=\"\"></img>\n";

		$str .= "</td><td>\n";

		for ($y=$first; $y <= $last; $y++)
		  {
		    if ($y==$current )
		      $str .= "<b style=\"vertical-align:middle; font-size:12px; margin:5px; color:#cc0033;\"> $y </b>\n";
		    else
		      {
			$str .= "<a class=\"$class\" onClick=\"sendForm('".$this->byteindex."','$y')\">\n";
			$str .= "<b style=\"vertical-align:middle; font-size:12px; margin:5px;\"> $y </b>\n";
			$str .= "</a>\n";
		      }
		  }

		$str .= "</td><td>\n";

		if ($current < $max)
		  {
		    $str .= "<a class=\"$class\" onClick=\"sendForm('".$this->byteindex."','".($current + 1)."')\">\n";
		    $str .= "<img class=\"icon\" src=\"style/r_ar.gif\" style=\"margin:4px\" alt=\"\"></img></a>\n";
		  }
		else
		  $str .= "<img class=\"icon\" src=\"style/no_ar.gif\" style=\"margin:4px\" alt=\"\"></img>\n";

		$str .= "</td><td>\n";

		if ($last < $max)
		  {
		    $str .= "<a class=\"$class\" onClick=\"sendForm('".$this->byteindex."','>>')\">\n";
		    $str .= "<img class=\"icon\" src=\"style/r_arrow.gif\" style=\"margin:4px\" alt=\"\"></img></a>\n";
		  }
		else
		  $str .= "<img class=\"icon\" src=\"style/no_arrow.gif\" style=\"margin:4px\" alt=\"\"></img>\n";

		$str .= "<input type=\"hidden\" id=\"".$this->byteindex."\" name=\"long_table[".$this->byteindex."]\" value=\"\"></input>\n";

	      }
	    $str .= "</td></tr>\n</table>\n";

	    $str .= "<input type=\"hidden\" name=\"current\" value=\"".$current."\"></input>\n";
	    $str .= "<input type=\"hidden\" name=\"visible\" value=\"".$this->visible."\"></input>\n";
	    $str .= "<input type=\"hidden\" name=\"previous\" value=\"".$first."\"></input>\n";
	    $str .= "<input type=\"hidden\" name=\"next\" value=\"".$last."\"></input>\n";
	  }
	return $str;
}
}

?>
