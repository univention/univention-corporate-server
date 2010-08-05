<?php
  /*
   * Univention Webui
   *  extra.inc
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
			if($tag == 'button'){
				$this->update_button = new update_button($tag, $this, $this->config, $warn);
			}
			else{
				$this->current = $tag;
				if(trim($tag)=='content')
					$this->byteindex = $byteindex;
				if(trim($tag)=='active')
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
			if($tag == 'button'){
				$this->update_button = new update_button($tag, $this, $this->config, $warn);
			}
			else{
				$this->current = $tag;
				$this->byteindex = $byteindex;
				if($tag=='choice'){
					$this->area=$tag;
					$this->sub_attribute = $attribute;
				}
				else if ($tag=='var') $this->area=$tag;
				if($this->current == 'content')$this->basket[$this->area][$this->name]['byteindex'] = $this->byteindex;
			}
		}
	}

	function put_value(&$value){
		if($this->update_button){
			$this->update_button->put_value($value);
		}
		else{
			if($this->area){
				if($this->current == 'name') $this->name = $value;
				else{
					$this->basket[$this->area][$this->name][$this->current] .= $value;
					if($this->area == 'choice')
						$this->basket[$this->area][$this->name]['level'] = $this->sub_attribute['level'];
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
				if($tag=='choice') $this->area=FALSE;
				else if ($tag=='var') $this->area=FALSE;
				return FALSE;
			}
		}
	}

}

class question_date extends extra{
	function show(){
		$str .= '<table border="0" cellpadding="0" cellspacing="0" title="'.$this->basket['helptext'].'" ';
		if($this->js && isset($this->basket['update'])) $str .= 'onBlur="sendForm('.$this->update_byteindex.')" ';
		$str .= '><tr><td colspan="6">
<table border="0" cellspadding="0">
<tr><td class="description" height="20" valign="bottom">
';
		if(isset($this->attribute['passive'])) $access = 'disabled';
		$str .= $this->basket['description'].'</td>';
		if($this->warn) $str .= '<td><img src="style/'.$this->warn.'.gif" alt="" class="warn"></img></td>';
		$str .= '</tr>
</table>
</td>
</tr>
<tr><td width="40">
';
		$content = explode('.',$this->basket['content']);
		$class='class="date"';
		if($this->warn)	$class='class="date_warn"';
		$attribs='maxlength="2" '.$class.' '.$access.' type="text" ';
		$str .= '<input tabindex="'.$this->tabindex.'" '.$attribs.'name="usrinput[date#'.$this->byteindex.'][]" value="'.$content[0].'"></input>
</td><td width="8">&nbsp;</td><td width="40">
<input tabindex="'.$this->tabindex.'" '.$attribs.'name="usrinput[date#'.$this->byteindex.'][]" value="'.$content[1].'"></input>
</td><td width="8">&nbsp;</td><td width="40">
<input tabindex="'.$this->tabindex.'" '.$attribs.'name="usrinput[date#'.$this->byteindex.'][]" value="'.$content[2].'"></input>
</td><td>';
		if(isset($this->basket['update'])) $str .= $this->basket['update'];
		$str .= '</td></tr>
</table>';

		return $str;
	}
}

class question_text extends extra{
	function show(){

		$validationbox = false;
		if (isset($this->attribute['validregex'])) {
			$validationbox = true;
			$validregex = $this->attribute['validregex'];
		}

		$isrequired = false;
		if (isset($this->attribute['isrequired'])) {
			$isrequired = true;
			if (! $validationbox) {
				$validationbox = true;
				$validregex = '.*'; # allow all
			}
		}

		$invalidmessage = false;
		if (isset($this->attribute['invalidmessage']))
			$invalidmessage = $this->attribute['invalidmessage'];

# include dojo
		if ($validationbox)
			$str .= '<script type="text/javascript">dojo.require("dijit.form.ValidationTextBox");</script>';
		else
			$str .= '<script type="text/javascript">dojo.require("dijit.form.TextBox");</script>';
	  
		if (isset($this->attribute['passive'])) {
			$access = 'disabled';
		}
		# $str.= '<div class="form-item">';

		if ($this->basket['description'])  {
			$str .=  '<label for="usrinput['.$this->byteindex.']">'.$this->basket['description'].'</label>';
		} else {
			$str .=  '<label for="usrinput['.$this->byteindex.']">&nbsp;</label>';
		}
		$str .= '<input id="usrinput['.$this->byteindex.']" tabindex="'.$this->tabindex.'" type="text" name="usrinput['.$this->byteindex.']" value="'.$this->basket['content'].'" ';
		if ($this->attribute['width']) 
			$str .= 'style="width:'.($this->attribute['width']).'px" ';
		if ($this->js && isset($this->basket['update'])) 
			$str .= 'onChange="sendForm('.$this->update_byteindex.')" ';
		if ($validationbox)
	    {
			# enable as dijit.ValidationTextBox
			$str .= ' dojoType="dijit.form.ValidationTextBox"';
			#add regexp
			$str .= ' regExp="'.$validregex.'"';
			if ($isrequired) # value is required
				$str .= ' required="true"';
			if ($invalidmessage) # user defined message for invalid values
				$str .= ' invalidMessage="'.$invalidmessage.'"';
	    }
		else
			# enable as dijit.TextBox
			if (!isset($this->attribute['puretext'])) 
				$str .= ' dojoType="dijit.form.TextBox"';
		if (isset($this->attribute['focus'])) {
			$str .= ' onclick="this.form.submit()" ';
		}
		if (isset($this->attribute['passive'])) {
			$str .= ' disabled ';
		}
		if ($this->attribute['width']) 
			$str .= 'style="width:'.($this->attribute['width']).'px" ';
		if ($this->warn) 
			$str .= ' class="text_warn" ';
		else 
			$str .= ' class="text" ';
		$str .= ' />';
		if ($this->warn) 
			$str .= '<img src="style/'.$this->warn.'.gif" alt="" class="warn"></img>';
		/* TODO redesign */
				

/*
		$str .= '<table border="0" cellspacing="0" cellpadding="0">';
	  
		if ($this->basket['description']) 
	    {
// <img src="style/blank_spacer.gif" height="2" width="2"></img>
			$str .= '<tr><td class="description">
'.$this->basket['description'];
			if ($this->warn) 
				$str .= '<img src="style/'.$this->warn.'.gif" alt="" class="warn"></img>';
			$str .= '</td></tr>';
	    }
		$str .= '<tr><td>
<input title="'.$this->basket['helptext'].'" tabindex="'.$this->tabindex.'" ';
		if ($this->attribute['width']) 
			$str .= 'style="width:'.($this->attribute['width']).'px" ';
		else
			$str .= 'style="width:300px" '; # width is interpreted by dojo, 300px seems to be the default in the past
		if ($this->js && isset($this->basket['update'])) 
			$str .= 'onChange="sendForm('.$this->update_byteindex.')" ';
		if ($this->warn) 
			$str .= ' class="text_warn" ';
		else 
			$str .= ' class="text" ';
		if ($validationbox)
	    {
# enable as dijit.ValidationTextBox
			$str .= ' dojoType="dijit.form.ValidationTextBox"';
# add regexp
			$str .= ' regExp="'.$validregex.'"';
			if ($isrequired) # value is required
				$str .= ' required="true"';
			if ($invalidmessage) # user defined message for invalid values
				$str .= ' invalidMessage="'.$invalidmessage.'"';
	    }
		else
# enable as dijit.TextBox
			if (!isset($this->attribute['puretext'])) 
				$str .= ' dojoType="dijit.form.TextBox"';
		if (isset($this->attribute['focus'])) {
			$str .= ' onclick="this.form.submit()" ';
		}
		$str .= ' type="text" '.$access.' id="usrinput['.$this->byteindex.']" name="usrinput['.$this->byteindex.']" value="'.$this->basket['content'].'"></input>';
*/
		if (isset($this->basket['update'])) 
			$str .= $this->basket['update'];
		if (isset($this->attribute['focus'])) {
			$str .= '<script type="text/javascript">';
			$str .= 'dojo.addOnLoad(function(setFocus){';
			$str .= 'document.getElementById("usrinput['.$this->byteindex.']").focus();';
			$str .= 'dijit.selectInputText(document.getElementById("usrinput['.$this->byteindex.']")); })';
			$str .= '</script>';
		}
/*
		$str .= '</td></tr>
</table>';
*/
		# $str .= '</div>';
		return $str;
	}
}

class question_dojo_date_widget extends extra {
	function show(){
		if(isset($this->attribute['passive'])) $access = 'disabled';
		$str .= '<script type="text/javascript">dojo.require("unijit.form.DateTextBox");</script>
<table border="0" cellspacing="0" cellpadding="0">
';
		if($this->basket['description']) {
			$str .= '<tr><td class="description">
'.$this->basket['description'];
			if($this->warn)
				$str .= '<img src="style'.$this->warn.'.gif" alt="" class="warn"></img>';
			$str .= '</td></tr>';
		}
		$str .= '<tr><td>
<input title="'.$this->basket['helptext'].'" tabindex="'.$this->tabindex.'" ';
		if($this->attribute['width']) $str .= 'style="width:'.($this->attribute['width']).'px" ';
		if($this->js && isset($this->basket['update'])) $str .= 'onChange="sendForm('.$this->update_byteindex.')" ';
		if($this->warn) $str .= ' class="text_warn" ';
		else $str .= ' class="date_widget" ';
		$str .= ' type="text" '.$access.' name="usrinput['.$this->byteindex.']" value="'.$this->basket['content'].'"
 dojoType="unijit.form.DateTextBox"></input>';
		if(isset($this->basket["update"])) $str .= $this->basket['update'];
		$str .= '</td></tr>
</table>';
		return $str;
	}
}


class question_file extends extra{
	function show(){
		if(isset($this->attribute['passive'])) $access = 'disabled';
		$str .= '<table border="0" cellspacing="0" cellpadding="0">';
		if($this->basket['description']) {
			$str .= '<tr><td class="description">
';
			$str .= $this->basket['description'];
			if($this->warn) $str .= '<img src="style/'.$this->warn.'.gif" alt="" class="warn"></img>';
			$str .= '</td></tr>';
		}
		$str .= '<tr><td>
<input type="hidden" name="file" value="'.$this->byteindex.'"></input>
<input title="'.$this->basket['helptext'].'" tabindex="'.$this->tabindex.'"
';
		if($this->attribute['width']) $str .= '<style="width:'.$this->attribute['width'].'px"';
		if($this->js && isset($this->basket["update"])) $str .= 'onChange="sendForm('.$this->update_byteindex.') "';
		if($this->warn) $str .= ' class="file_warn"';
		else $str .= ' class="file" ';
		$str .= ' type="file" '.$access.' name="userfile"></input>';
		if(isset($this->basket['update'])) $str .= $this->basket['update'];
		$str .= '</td></tr>
</table>';
		return $str;
	}


}

class question_ltext extends extra{
	function show(){
		$str .= '<script type="text/javascript">dojo.require("dijit.form.SimpleTextarea");</script>';
		if (isset($this->attribute['passive'])) 
			$access = 'disabled';
		$str .= '<table border="0" cellspacing="0" cellpadding="0">';
		if ($this->basket['description'])
	    {
			$str .= '<tr><td class="description">'.$this->basket['description'];
			if ($this->warn) 
				$str .= '<img src="style/'.$this->warn.'.gif" alt="" class="warn"></img>';
			$str .= '</td></tr>';
	    }
		$str .= '<tr><td>
<textarea dojoType="dijit.form.SimpleTextarea" '.$access.' title="'.$this->basket['helptext'].'" tabindex="'.$this->tabindex.'" ';
		if ($this->attribute['width'] || $this->attribute['height'])
	    {
			$str .= 'style=" ';
			if ($this->attribute['width']) 
				$str .= 'width:'.($this->attribute['width']).'px; ';
			if ($this->attribute['height']) 
				$str .= 'height:'.($this->attribute['height']).'px';
			$str .= '" ';
			if (isset($this->attribute['readonly'])) 
				$str .= ' readonly="" ';
	    }
		if ($this->js && isset($this->basket["update"])) 
			$str .= 'onChange="sendForm('.$this->update_byteindex.')" ';
		if ($this->warn) 
			$str .= 'class="longtext_warn"';
		else 
			$str .= 'class="longtext"';
		$str .= 'name="usrinput['.$this->byteindex.']">';
		$str .= $this->basket['content'].'</textarea>';
		$str .= '</td></tr>';
		if (isset($this->basket['update'])) 
			$str .= '<tr><td>'.$this->basket['update'].'</td></tr>';
		$str .= '</table>';

		return $str;	  
	}	
}

class question_secure extends extra{
	function show(){
		$str .= '<script type="text/javascript">dojo.require("dijit.form.TextBox");</script>';
		if (isset($this->attribute['passive'])) 
			$access = 'disabled';

		$str .= '<table border="0" cellspacing="0" cellpadding="0">
<tr><td class="description">'.$this->basket['description'];
		if ($this->warn) 
			$str .= '<img src="style/'.$this->warn.'.gif" alt="" class="warn"></img>';
		$str .= '</td></tr>
<tr><td><input title="'.$this->basket['helptext'].'" tabindex="'.$this->tabindex.'"';
		if ($this->attribute['width']) 
			$str .= 'style="width:'.($this->attribute['width']).'px" ';
		if ($this->js && isset($this->basket['update'])) 
			$str .= 'onChange="sendForm('.$this->update_byteindex.')" ';
		if ($this->warn) 
			$str .= ' class="text_warn" ';
		else 
			$str .= ' class="text" ';
		if (isset($this->attribute['puretext'])) 
			$str .= 'type="password"';
		else
			$str .= 'type="password" dojoType="dijit.form.TextBox"';
		$str .= ' '.$access.' name="usrinput['.$this->byteindex.']" value="'.$this->basket['content'].'"></input>';
		if (isset($this->basket['update'])) 
			$str .= $this->basket['update'];
		$str .= '</td></tr>
</table>';
	  
		return $str;
	}
}

class question_bool extends extra{
	function show(){
	  if (isset($this->attribute['passive'])) 
	    $access = 'disabled';
	  if (trim($this->basket['content'])!='') 
	    $is='checked';

	  $str .= '<script type="text/javascript">dojo.require("dijit.form.CheckBox");</script>
<table border="0" cellpadding="0" cellspacing="0"><tr>
<td valign="middle">
<input dojoType="dijit.form.CheckBox" title="'.$this->basket['helptext'].'"
 tabindex="'.$this->tabindex.'" class="bool" type="checkbox" '.$access.' ';
	  if ($this->js && isset($this->basket['update'])) 
	    $str .= 'onChange="sendForm('.$this->update_byteindex.')" ';
	  $str .= 'name="usrinput['.$this->byteindex.']" value="checked" '.$is.'></input></td>';
	  if (trim($this->basket['description']) != '')
	    {
	      $str .= '<td class="description" align="left" valign="middle">
'.$this->basket["description"].'</td>';
	    }
	  $str .= '<td>';
	  if ($this->warn) 
	    $str .= '<img src="style/'.$this->warn.'.gif" alt="" class="warn"></img>';
	  if (isset($this->basket['update'])) 
	    $str .= $this->basket['update'];
	  $str .= '</td></tr></table>';
	  $is='';
	  
	  return $str;
	}
}

class reset extends extra{
	function show(){
		if(isset($this->attribute['passive'])) $access = 'disabled';
		$class=$this->status;
		if($this->warn) $str .= '<img src="style/'.$this->warn.'.gif" alt="" class="warn"></img>';
		$str .=  '<input title="'.$this->basket['helptext'].'" tabindex="'.$this->tabindex.'" id="button'.$this->tabindex.'" ';
		if($this->attribute["width"]) $str .= 'style="width:'.($this->attribute['width']).'px" ';
		$str .= 'class="button'.$class-'" type="reset" name="usrinput['.$this->byteindex.']" '.$access-' value=" '.$this->basket['text'].'" ></input>';

		return $str;
	}
}

class button extends extra{

	function default_button($byteindex)
	{
		$defaultbutton  = '<div style="position:absolute;top:-1000px;left:-1000px;"><input type="submit" name="usrinput['.$byteindex.']" id="defaultbutton"/></div>';
		$defaultbutton .= '<script type="text/javascript">';
		$defaultbutton .= 'dojo.addOnLoad(function(stopReturn){';
		$defaultbutton .= 'submitform = document.getElementById( "component" );';
		$defaultbutton .= 'if ( submitform == undefined) { submitform=document.getElementById( "component-menuless" ); };';
		$defaultbutton .= 'if ( submitform == undefined) { submitform=document.getElementById( "login" ); };';
		$defaultbutton .= 'dojo.connect(submitform, "onkeypress",function(evt) {';

		# check if an element is selected which should get the return key event, for example longtext areas and combobox
		$defaultbutton .= '	var skipEvent = false;';
		$defaultbutton .= '	var foundSearchProperty = false;';
		$defaultbutton .= '	var allElements = document.getElementsByTagName("*");';
		$defaultbutton .= '	for (var i = 0; (element = allElements[i]) != null; i++) {';
		$defaultbutton .= '		var elementClass = element.className;';
		$defaultbutton .= '		if (elementClass && ( (elementClass.indexOf("longtext") != -1 && elementClass.indexOf("dijitTextAreaFocused") != -1) || elementClass.indexOf("dijitComboBoxFocused") != -1) ) {';
		$defaultbutton .= '			skipEvent = true;';
		$defaultbutton .= '			break;';
		$defaultbutton .= '		}';

		# if the focus is set to a userDN and groupDn syntax we overwrite the defaultbutton
		$defaultbutton .= '		if ( elementClass && elementClass.indexOf("search_property") != -1 ) {';
		$defaultbutton .= '			for (var j = 0; (childNode = element.childNodes[j]) != null; j++) {';
		$defaultbutton .= '				var childClass = childNode.className;';
		$defaultbutton .= '				if ( childClass && childClass.indexOf("dijitTextBoxFocused") != -1) {';
		$defaultbutton .= '					skipEvent = true;';
		$defaultbutton .= '					foundSearchProperty = true;';
		$defaultbutton .= '					break;';
		$defaultbutton .= '				}';
		$defaultbutton .= '			}';
		$defaultbutton .= '		}';

		$defaultbutton .= '		if ( elementClass && foundSearchProperty == true && elementClass.indexOf("search_button") != -1 ) {';
		$defaultbutton .= '			button=element.childNodes[0].childNodes[0].childNodes[1].childNodes[0];';
		$defaultbutton .= '			for ( var j = 0; (button=element.childNodes[0].childNodes[0].childNodes[0].childNodes[j]) != null; j++) {';
		$defaultbutton .= '				if (button.className == "button_icon" ) break;';
		$defaultbutton .= '			}';
		$defaultbutton .= '			if ((evt.keyCode == 13 && button != null)) {';
		$defaultbutton .= '	     		dojo.stopEvent(evt);';
		$defaultbutton .= '				button.click();';
		$defaultbutton .= '			}';
		$defaultbutton .= '		}';
		$defaultbutton .= '	}';

		$defaultbutton .= '	if ( skipEvent ==  false ) {';
		$defaultbutton .= '	var b = document.getElementById("defaultbutton");';
		$defaultbutton .= '	var node = (evt.target) ? evt.target : ((evt.srcElement) ? evt.srcElement : null);';
		$defaultbutton .= '	if ((evt.keyCode == 13 && b != null)) {dojo.stopEvent(evt);';
		$defaultbutton .= '		mmselect_objects=document.getElementsByTagName("div");';
		$defaultbutton .= '		for (var i = 0; i < mmselect_objects.length; i++) {';
		$defaultbutton .= '			if (mmselect_objects[i].id=="mmselect") {';
		$defaultbutton .= '				box = mmselect_objects[i].getElementsByTagName("select")[0];';
		$defaultbutton .= '				for (var j = 0; j < box.options.length; j++) {';
		$defaultbutton .= '					box.options[j].selected = true;';
		$defaultbutton .= '				}';
		$defaultbutton .= '			}';
		$defaultbutton .= '		}';
		$defaultbutton .= '		b.click();}}})});';
		$defaultbutton .= '</script>';

		return $defaultbutton;

	}
	function menu2_item($title, $icon, $byteindex, $content)
	{
		$str = '<li style="background-image: url('.$icon.');">';
		$str .= '<input type="hidden" id="'.$byteindex.'" name="usrinput['.$byteindex.']" value="'.$content.'"></input>';
		$str .= '<a title="'.$title.'" onClick="sendForm('.$byteindex.')">'.$title.'</a>';
		$str .= '</li>';

		return $str;
	}
	function menu3_item($title, $icon, $byteindex, $content)
	{
		$str = '<li class="submenu" style="background-image: url('.$icon.');">';
		$str .= '<input type="hidden" id="'.$byteindex.'" name="usrinput['.$byteindex.']" value="'.$content.'"></input>';
		$str .= '<a title="'.$title.'" onClick="sendForm('.$byteindex.')">'.$title.'</a>';
		$str .= '</li>';

		return $str;
	}
	function submit_button($title, $icon, $byteindex, $content, $defaultbutton)
	{
		$str = '<span class="submit">';
		$str .= '<input type="hidden" id="'.$byteindex.'" name="usrinput['.$byteindex.']" value="'.$content.'"></input>';
		if ($defaultbutton) {
			$str .= $this->default_button($byteindex);	
		}
		$str .= '<span>';
		if (isset($this->attribute['link'])) {
			$str .= '<a title="'.$title.'" href="'.$this->attribute['link'].'">'.$title.'</a>';
		} else {
			$str .= '<a title="'.$title.'" onClick="sendForm('.$byteindex.')">'.$title.'</a>';
		}
		$str .= '</span>';
		$str .= '</span>';

		return $str;
	}

	function search_result_button($title, $icon, $byteindex, $content, $defaultbutton)
	{
		$str = '<span class="search_result" style="background-image: url('.$icon.');">';
		$str .= '<input type="hidden" id="'.$byteindex.'" name="usrinput['.$byteindex.']" value="'.$content.'"></input>';
		if ($defaultbutton) {
			$str .= $this->default_button($byteindex);	
		}
		$str .= '<span>';
		if (isset($this->attribute['link'])) {
			$str .= '<a title="'.$title.'" href="'.$this->attribute['link'].'">'.$title.'</a>';
		} else {
			$str .= '<a title="'.$title.'" onClick="sendForm('.$byteindex.')">'.$title.'</a>';
		}
		$str .= '</span>';
		$str .= '</span>';

		return $str;
	}

	function cancel_button($title, $icon, $byteindex, $content, $defaultbutton)
	{
		$str .= '<span class="'.$this->attribute['class'].'">';
		$str .= '<input type="hidden" id="'.$byteindex.'" name="usrinput['.$byteindex.']" value="'.$content.'"></input>';
		if ($defaultbutton) {
			$str .= $this->default_button($byteindex);	
		}
		if (isset($this->attribute['link'])) {
			$str .= '<a title="'.$title.'" href="'.$this->attribute['link'].'">'.$title.'</a>';
		} else {
			$str .= '<a title="'.$title.'" onClick="sendForm('.$byteindex.')">'.$title.'</a>';
		}
		$str .= '</span>';

		return $str;
	}
	function cancel_spacer_button($title, $icon, $byteindex, $content, $defaultbutton)
	{
		$str .= '<span class="cancel spacer">';
		$str .= '<input type="hidden" id="'.$byteindex.'" name="usrinput['.$byteindex.']" value="'.$content.'"></input>';
		if ($defaultbutton) {
			$str .= $this->default_button($byteindex);	
		}
		if (isset($this->attribute['link'])) {
			$str .= '<a title="'.$title.'" href="'.$this->attribute['link'].'">'.$title.'</a>';
		} else {
			$str .= '<a title="'.$title.'" onClick="sendForm('.$byteindex.')">'.$title.'</a>';
		}
		$str .= '</span>';

		return $str;
	}

	function show($csslength=FALSE, $first_tab=FALSE){
		if(isset($this->attribute['passive'])) $access = 'disabled';
		$class=$this->status;
		if(isset($this->attribute['active'])) $class .= '_on';

		if ( $this->attribute['class'] ) {
			$classes = explode( " ", $this->attribute['class'] );
		} else {
			$classes = Array();
		}
		if ( in_array( 'submit', $classes ) ) {
			return $this->submit_button($this->basket['text'], $this->attribute['icon'], $this->byteindex, $this->basket['content'], $this->attribute['defaultbutton']); 
		}
		if ( in_array( 'cancel', $classes ) ) {
			return $this->cancel_button($this->basket['text'], $this->attribute['icon'], $this->byteindex, $this->basket['content'], $this->attribute['defaultbutton']); 
		}
		if ( in_array( 'cancel_spacer', $classes ) ) {
			return $this->cancel_spacer_button($this->basket['text'], $this->attribute['icon'], $this->byteindex, $this->basket['content'], $this->attribute['defaultbutton']); 
		}
		if ( in_array( 'search_result', $classes ) ) {
			return $this->search_result_button($this->basket['text'], $this->attribute['icon'], $this->byteindex, $this->basket['content'], $this->attribute['defaultbutton']); 
		}

		if($this->status == 'content') {
			$onclick = ' onClick="sendForm('.$this->byteindex.')"';
			$onclick_func = "sendForm";
		} else {
			$onclick = ' onClick="sendForm2('.$this->byteindex.')"';
			$onclick_func = "sendForm2";
		}

		if(isset($this->attribute['webui-confirm-title']))
			$onclick = ' onClick="umc_popup_confirm( \''.$this->attribute['webui-confirm-title'].'\', \''.$this->attribute['webui-confirm-question'].'\', \''.$this->attribute['webui-confirm-yes'].'\', \''.$this->attribute['webui-confirm-no'].'\', \''.$onclick_func.'\', '.$this->byteindex.')"';
			
		if( $this->js && $class == 'linkbutton' ){
			// define form-contens
			if(!isset($this->attribute['passive'])){
				$href = '<a class="'.$class.'"';

				$href .= $onclick;	
				$href .= ' title="'.$this->basket['helptext'].'" ';

				if ( isset( $this->attribute[ 'icon' ] ) ) {
					$img = '<input src="'.$this->attribute['icon'].'" tabindex="'.$this->tabindex.'" name="usrinput['.$this->byteindex.']" type="image" value="pressed" class="button_icon" onClick="sendForm('.$this->byteindex.')" title="'.$this->basket['helptext'].'"></input>';
				}

				$link = $href.'>
<span class="'.$this->attribute[ 'type' ].'">'.$this->basket['text'].'</span></a>
';

				$inp = '<input type="hidden" id="'.$this->byteindex.'" name="usrinput['.$this->byteindex.']" value="'.$this->basket['content'].'"></input>';
				if(isset($this->attribute['defaultbutton'])){
					$inp .= '<div style="position:absolute;top:-1000px;left:-1000px;"><input type="submit" name="usrinput['.$this->byteindex.']" id="defaultbutton"></div>';
				//if(isset($this->attribute['nodefault'])){
				$inp .= '<script type="text/javascript">';
				$inp .= 'dojo.addOnLoad(function(stopReturn){';
				$inp .= 'submitform = document.getElementById( "form" );';
				$inp .= 'dojo.connect(submitform, "onkeypress",function(evt) {';
				$inp .= 'var b = document.getElementById("defaultbutton");';
				$inp .= 'var node = (evt.target) ? evt.target : ((evt.srcElement) ? evt.srcElement : null);';
				$inp .= 'if ((evt.keyCode == 13 && b != null)) {dojo.stopEvent(evt);';
				$inp .= 'b.click();}})});';
				$inp .= '</script>';
				//}
				}
			}
			else
		    {
				if ( isset( $this->attribute[ 'icon' ] ) ) {
					$img = '<img class="'.$class.'" src="'.$this->attribute['icon'].'" alt=""></img>';
				}
				$link = '<span class="'.$class.'">'.$this->basket['text'].'</span>';
				$inp = '';
		    }

			if (isset($this->attribute['class'])) {
				$class = $this->attribute['class'];
			} else {
				$class = "button";
			}
					
			$str .= '<table class="'.$class.'"><tr>';
			$text_col = '<td class="button_link">'.$link.'</td>';
		
			$btn_row = '';
			if ( isset( $img ) ) {
				$icon_col = '<td class="button_icon">'.$inp.$img.'</td>';
				$btn_row = $icon_col;
				if(trim($this->basket['text']) != '')
					$btn_row .= $text_col;
			} else {
				$btn_row = $text_col;
			}
			$str .= $btn_row.'</tr>
</table>';
		} elseif ($this->js && $class != 'notebook' && $class != 'categoryitem' && isset($this->attribute['icon'])){

			// define form-contens
			if(!isset($this->attribute['passive'])){
				if($this->status == 'content')
					$href = '<a class="'.$class.'" onClick="sendForm('.$this->byteindex.')"';
				else
					$href = '<a class="'.$class.'" onClick="sendForm2('.$this->byteindex.')"';

				$href .= ' title="'.$this->basket['helptext'].'" ';

				$img = '<input src="'.$this->attribute['icon'].'" tabindex="'.$this->tabindex.'" name="usrinput['.$this->byteindex.']" type="image" value="pressed" class="button_icon" onClick="sendForm('.$this->byteindex.')" title="'.$this->basket['helptext'].'"></input>';

				$link = $href.'>
<span class="'.$class.'">'.$this->basket['text'].'</span></a>
';

				$inp = '<input type="hidden" id="'.$this->byteindex.'" name="usrinput['.$this->byteindex.']" value="'.$this->basket['content'].'"></input>';
				if(isset($this->attribute['defaultbutton'])){
					$inp .= '<div style="position:absolute;top:-1000px;left:-1000px;"><input type="submit" name="usrinput['.$this->byteindex.']" id="defaultbutton"></div>';
				//if(isset($this->attribute['nodefault'])){
				$inp .= '<script type="text/javascript">';
				$inp .= 'dojo.addOnLoad(function(stopReturn){';
				$inp .= 'submitform = document.getElementById( "form" );';
				$inp .= 'dojo.connect(submitform, "onkeypress",function(evt) {';
				$inp .= 'var b = document.getElementById("defaultbutton");';
				$inp .= 'var node = (evt.target) ? evt.target : ((evt.srcElement) ? evt.srcElement : null);';
				$inp .= 'if ((evt.keyCode == 13 && b != null)) {dojo.stopEvent(evt);';
				$inp .= 'b.click();}})});';
				$inp .= '</script>';
				//}
				}
			}
			else
		    {
				$img = '<img class="'.$class.'" src="'.$this->attribute['icon'].'" alt=""></img>';
				$link = '<span class="'.$class.'">'.$this->basket['text'].'</span>';
				$inp = '';
		    }

			// build html
			if ( $class == 'menu2'  ||  $class == 'menu2_on' ) {
				$str .= $this->menu2_item($this->basket['text'], $this->attribute['icon'], $this->byteindex, $this->basket['content']);
			} elseif ($class == 'menu3' || $class == 'menu3_on' ) {
				$str .= $this->menu3_item($this->basket['text'], $this->attribute['icon'], $this->byteindex, $this->basket['content']);
			}
			else //i.e. search result
		    {
				if (isset($this->attribute['class'])) {
					$class = $this->attribute['class'];
				} else {
					$class = "button";
				}
							
				$str .= '<table class="'.$class.'"><tr>';

				$icon_col = '<td class="button_icon">'.$inp.$img.'</td>';
				$text_col = '<td class="button_link">'.$link.'</td>';
				
				$btn_row = '';
				if (isset($this->attribute['icon_side']) && $this->attribute['icon_side'] == 'right') {
					if(trim($this->basket['text']) != '')
						$btn_row = $text_col;
					$btn_row .= $icon_col;
				} else {
					$btn_row = $icon_col;
					if(trim($this->basket['text']) != '')
						$btn_row .= $text_col;
				}
				$str .= $btn_row.'</tr>
</table>';
		    }


			/* no icon */
		}elseif($this->js && isset($this->attribute['link'])){
			if (isset($this->attribute['type'])) {
				$str .= '<a class="'.$this->attribute['type'].'"'.$onclick;
			} elseif ($this->status == 'content') {
				$str .= '<a class="'.$class.'"'.$onclick;
			} else {
				$str .= '<a class="'.$class.'"'.$onclick;
			}
			$str .= ' title="'.$this->basket['helptext'].'">'.$this->basket['text'].'</a>
<input type="hidden" id="'.$this->byteindex.'" name="usrinput['.$this->byteindex.']" value="'.$this->basket['content'].'"></input>';
		}elseif($this->js && strstr($this->status, 'menu')) {
			if($this->basket['active']) $class .= '_on';
			if(isset($this->attribute['passive'])){
				$str .= '<div id="div'.$this->byteindex.'" class="link_passive">'.$this->basket['text'].'</div>';
			} else {
				$str .= '<div id="div'.$this->byteindex.'" class="link'.$class.'" ';
				if(!$this->basket['active']) $str .= 'onMouseOver="setBG(\'div'.$this->byteindex.'\',1)" onMouseOut="setBG(\'div'.$this->byteindex.'\',0)">';
				$str .= '<a class="'.$class.'" onClick="sendForm2('.$this->byteindex.')" title="'.$this->basket['helptext'].'">';
				if(strstr($this->status, '3') && strstr($this->status, 'menu')) $str .= '<img class="sub" src="style/sub_mark.png" align="middle" alt=""></img>';
				$str .= $this->basket['text'];

				$str .= '</a></div>';
				$str .= '<input type="hidden" id="'.$this->byteindex.'" name="usrinput['.$this->byteindex.']" value="'.$this->basket['content'].'"></input>';
			}
		}
		elseif($this->js && $class == 'categoryitem')
		{
		    $cssclass = $class;
		    if ($this->basket[active])
				$cssclass .= 'active';


		    if (isset($this->attribute['closebutton']) && ($this->attribute['closebutton'] == '1'))
			{
				// closebutton -- just an icon
				if ($this->basket[active]) {
					$icon_str = '/icon/close_tab_active.gif';
				} else {
					$icon_str = '/icon/close_tab_inactive.gif';
				}
				$cssclass .= 'closeableend'; // closebuttons are always the last in a closable categoryitem
				$img_str = '<img src="'.$icon_str.'" class="img'.$cssclass.'">';
				$str .= '<a class="'.$cssclass.'" onClick="sendForm('.$this->byteindex.')" title="X">'.$img_str.'</a>
<input type="hidden" id="'.$this->byteindex.'" name="usrinput['.$this->byteindex.']" value="'.$this->basket['content'].'"></input>';
			}
		    else
			{
				$img_str = '';
				$close_str = '';
				if (isset($this->attribute['closeable']) && ($this->attribute['closeable'] == '1')) {
					$cssclass .= 'closeablestart';
				}
				if (isset($this->attribute['icon']))
				{
					$img_str = '<input src="'.$this->attribute['icon'].'" tabindex="'.$this->tabindex.'" name="usrinput['.$this->byteindex.']" type="image" value="pressed" class="button_icon" title="'.$this->basket['helptext'].'"></input>';
				}
				$str .= '<a class="'.$cssclass.'" onClick="sendForm('.$this->byteindex.')"
 title="'.$this->basket['helptext'].'">'.$img_str.$this->basket['text'].'</a>
<input type="hidden" id="'.$this->byteindex.'" name="usrinput['.$this->byteindex.']" value="'.$this->basket['content'].'"></input>';
			}
		}
		elseif($this->js && $class == 'notebook'){
			if ( $first_tab == TRUE ) {
				$tdclass='tab_first';
			} else {
				$tdclass='tab';
			}
			$img = '"style/reiter_grau18x24.gif"';

			$close_icon_str = '/icon/close_page_inactive.gif';
			if($this->basket['active'])
		    {
				$class = 'notebook_on';
				if ( $first_tab == TRUE ) {
					$tdclass = 'tab_on_first';
				} else {
					$tdclass = 'tab_on';
				}
				$img = '"style/reiter_rot18x24.gif"';
				$close_icon_str = '/icon/close_page_active.gif';
		    }
			if(isset($this->attribute['passive']))
		    {
				$str .= '<span id="div'.$this->byteindex.'" class="notebook_passive">'.$this->basket['text'].'</span>';
		    }
			else
		    {
				if (isset($this->attribute['closebutton']) && ($this->attribute['closebutton'] == '1'))
				{
# close button
					$class .= 'closeableend';
					if($this->basket['active'])
						$tdclass = 'tab_on_close';
					else
						$tdclass = 'tab_close';
					$str .= '<td class="'.$tdclass.'" nowrap><a class="'.$class.'" onClick="sendForm('.$this->byteindex.')" title="close">
<img class="'.$class.'" src="'.$close_icon_str.'">
</a><input id="'.$this->byteindex.'" name="usrinput['.$this->byteindex.']" type="hidden" value=""></input>
</td>';
				} 
				else
				{
					if (isset($this->attribute['closeable']) && ($this->attribute['closeable'] == '1')) {
						$class .= 'closeablestart';
					}

					$str .= '<td class="'.$tdclass.'" nowrap>
<a class="'.$class.'" onClick="sendForm('.$this->byteindex.')"';
					if (  isset( $this->attribute[ 'icon' ] ) ) {
						$str .= ' title="'.$this->basket['helptext'].'">
<img class="'.$class.'" src="'.$this->attribute['icon'].'" alt=""></img>';
					} else {
						$str .= ' title="'.$this->basket['helptext'].'">';
					}
					$str .= $this->basket['text'].'</a>';
					if (  isset( $this->attribute[ 'statusicon' ] ) ) {
						$str .= '<img class="'.$class.'" src="'.$this->attribute['statusicon'].'" alt=""></img>';
					}
					$str .= '<input type="hidden" id="'.$this->byteindex.'" name="usrinput['.$this->byteindex.']" value="'.$this->basket['content'].'"></input>';
					$str .= '</td>';
				}
			}
		}
		else
		{
		    if($class == 'notebook' && $this->basket['active']) $class = 'notebook_on';
		    $str .=  '<input tabindex="'.$this->tabindex.'" id="button'.$this->tabindex.'" '.$access.' ';
		    if($this->attribute['width']) $str .= 'style="width:'.($this->attribute['width']).'px" ';
		    $str .= 'class="button'.$class.'" type="submit" name="usrinput['.$this->byteindex.']" value=" '.$this->basket['text'].'"';
		    if($csslength) $str .=  'style="width:'.$csslength.'px;" ';
		    $str .=  'title="'.$this->basket['helptext'].'"></input>';
		}
		return $str;
	}
}

class update_button extends extra{
	function show(){
		if($this->js){
			$str .= '<input type="hidden" id="'.$this->byteindex.'" name="usrinput['.$this->byteindex.']" value="'.$this->basket['content'].'"></input>';
		} else {
			$class=$this->status;
	   		$this->tabindex++;
			$str .= '<input tabindex="'.$this->tabindex.'" id="button'.$this->tabindex.'" class="button'.$class.'" type="submit" name="usrinput['.$this->byteindex.']" value=" ';
			$str .= $this->basket['text'].'" ></input>';
		}
		return $str;
	}
}

class link extends extra{
	function show(){
		$class=$this->modus;
	  	if(stristr($this->basket['dest'],'uniconf_modul')) $this->basket['dest'] .= '&session_id='.$session_id;
		$str .= '<a class="'.$class.'"  tabindex="'.$this->tabindex.'" href="'.$this->basket['dest'].'">'.$this->basket['text'].'</a>';
	  	return $str;
	}
}

class progressbar extends extra{
	function show(){
		$width = '300px';
		if (isset($this->attribute['width']))
			$width = $this->attribute['width'];
		$report_func = '';
		if (isset($this->attribute['label']))
			$report_func = '
jsProgress'.$this->tabindex.'["report"] = function( percent ) {
    return "'.$this->attribute['label'].'";
};';
		$str .= '<script type="text/javascript">dojo.require("dijit.ProgressBar");
dojo.addOnLoad(function(){
'.$report_func.'
jsProgress'.$this->tabindex.'.update({
            maximum: 100,
            progress: '.$this->attribute['percentage'].'
        });
	});
</script>
<div class="umc_progressbar" dojoType="dijit.ProgressBar" style="width:'.$width.'" jsId="jsProgress'.$this->tabindex.'"
id="Progressbar'.$this->tabindex.'">
</div>';
	  	return $str;
	}
}

// single select drop-down
class question_select extends extra_multi{
	function show(){
		$appendstr = '';
		if(isset($this->attribute['passive'])) 
			$access = 'disabled';
		$str .= '<script type="text/javascript">dojo.require("dijit.form.FilteringSelect");</script>';
		if($this->warn) 
			$str .= '<img src="style/'.$this->warn.'.gif" alt="" class="warn"></img>';
		# $str .= '<div class="form-item clear">';
		if(isset($this->basket['description']) and strlen($this->basket['description']) > 0) {
			$str .= '<label for="usrinput[question_select#'.$this->tabindex.'][]">'.$this->basket['description'].'</label>';
		} else {
			$str .= '<label for="usrinput[question_select#'.$this->tabindex.'][]">&nbsp;</label>';
		}
		$str .= '<select dojoType="dijit.form.FilteringSelect" autocomplete="true" '.$access.' title="'.$this->basket['helptext'].'" tabindex="'.$this->tabindex.'"';
    
		if($this->warn) 
			$str .= ' class="text_warn" ';
		else 
			$str .= ' class="text" ';
    
		if($this->attribute['width']) 
			$str .= 'style="width:'.($this->attribute['width']).'px" ';
    
		if($this->js && isset($this->basket['update'])) 
			$str .= 'onChange="sendForm('.$this->update_byteindex.')" ';
    
		if ($access != "disabled")
			$str .= 'name="usrinput[question_select#'.$this->tabindex.'][]"';
		$str .= ">\n";
		if($this->basket['choice'])
			foreach($this->basket['choice'] as $key=>$val) {
				if(trim($this->basket['var'][$key]['content'])!="") {
					$is='selected';
					if ($access == "disabled") {
						$appendstr = '<input type="hidden" name="usrinput[question_select#'.$this->tabindex.'][]"
 value="'.$this->basket['var'][$key]['byteindex'].'"></input>';
					}
				}
				for($x=0; $x < $this->basket['choice'][$key]['level']; $x++) 
					$space .= '&nbsp;';
				$str .= '<option value="'.$this->basket['var'][$key]['byteindex'].'" '.$is.'>';
				$str .= $space.$this->basket['choice'][$key]['description'].'</option>';
				$is = '';
				$space = '';
			}
		$str .='</select>';
		if(isset($this->basket['update'])) 
			$str .= $this->basket['update'];
		$str .= $appendstr;
		# $str .= '</div>';
		return $str;
	}
}

class language_dojo_select extends extra_multi{
	// http://aktuell.de.selfhtml.org/artikel/php/httpsprache/
	function lang_getfrombrowser ($allowed_languages, $default_language, $lang_variable = null, $strict_mode = true) {
		// $_SERVER['HTTP_ACCEPT_LANGUAGE'] verwenden, wenn keine Sprachvariable mitgegeben wurde
		if ($lang_variable === null) {
			$lang_variable = $_SERVER['HTTP_ACCEPT_LANGUAGE'];
		}

		// wurde irgendwelche Information mitgeschickt?
		if (empty($lang_variable)) {
			// Nein? => Standardsprache zurückgeben
			return $default_language;
		}

		// Den Header auftrennen
		$accepted_languages = preg_split('/,\s*/', $lang_variable);

		// Die Standardwerte einstellen
		$current_lang = $default_language;
		$current_q = 0;

		// Nun alle mitgegebenen Sprachen abarbeiten
		foreach ($accepted_languages as $accepted_language) {
			// Alle Infos über diese Sprache rausholen
			$res = preg_match ('/^([a-z]{1,8}(?:-[a-z]{1,8})*)'.
					'(?:;\s*q=(0(?:\.[0-9]{1,3})?|1(?:\.0{1,3})?))?$/i', $accepted_language, $matches);

			// war die Syntax gültig?
			if (!$res) {
				// Nein? Dann ignorieren
				continue;
			}

			// Sprachcode holen und dann sofort in die Einzelteile trennen
			$lang_code = explode ('-', $matches[1]);

			// Wurde eine Qualität mitgegeben?
			if (isset($matches[2])) {
				// die Qualität benutzen
				$lang_quality = (float)$matches[2];
			} else {
				// Kompabilitätsmodus: Qualität 1 annehmen
				$lang_quality = 1.0;
			}

			// Bis der Sprachcode leer ist...
			while (count ($lang_code)) {
				// mal sehen, ob der Sprachcode angeboten wird
				if (in_array (strtolower (join ('-', $lang_code)), $allowed_languages)) {
					// Qualität anschauen
					if ($lang_quality > $current_q) {
						// diese Sprache verwenden
						$current_lang = strtolower (join ('-', $lang_code));
						$current_q = $lang_quality;
						// Hier die innere while-Schleife verlassen
						break;
					}
				}
				// Wenn wir im strengen Modus sind, die Sprache nicht versuchen zu minimalisieren
				if ($strict_mode) {
					// innere While-Schleife aufbrechen
					break;
				}
				// den rechtesten Teil des Sprachcodes abschneiden
				array_pop ($lang_code);
			}
		}

		// die gefundene Sprache zurückgeben
		return $current_lang;
	}

	function show(){
		$appendstr = '';
		if(isset($this->attribute['passive'])) 
			$access = 'disabled';
		$str .= '

<script type="text/javascript">dojo.require("dijit.form.FilteringSelect");</script>
<table border="0" cellpadding="0" cellspacing="0">
<tr><td class="description">'.$this->basket['description'];
		if($this->warn) 
			$str .= '<img src="style/'.$this->warn.'.gif" alt="" class="warn"></img>';
		$str .= '</td></tr>
<tr><td>
<select dojoType="dijit.form.FilteringSelect" autocomplete="true" '.$access.' title="'.$this->basket['helptext'].'" tabindex="'.$this->tabindex.'"';

		if($this->warn) 
			$str .= ' class="select_warn" ';
		else 
			$str .= ' class="select" ';

		if($this->attribute['width']) 
			$str .= 'style="width:'.($this->attribute['width']).'px" ';

		if($this->js && isset($this->basket['update'])) 
			$str .= 'onChange="sendForm('.$this->update_byteindex.')" ';

		if ($access != 'disabled')
			$str .= 'name="usrinput[language_dojo_select#'.$this->tabindex.'][]"';
		$str .= '>';
		if($this->basket['choice']) {
			$allowed_languages = array ();
			$default_language = 'en';
			foreach($this->basket['choice'] as $key=>$val) {
				if(trim($this->basket['var'][$key]['content'])!='') {
					$default_language = $key;
				}
				array_push ($allowed_languages, $key);
			}
			$lang = $this->lang_getfrombrowser ($allowed_languages, $default_language, null, false);
			foreach($this->basket['choice'] as $key=>$val) {
				if($key == $lang) {
					$is='selected';
				}
				if(trim($this->basket['var'][$key]['content'])!='') {
					//$is='selected';
					if ($access == 'disabled') {
						$appendstr = '<input type="hidden" name="usrinput[language_dojo_select#'.$this->tabindex.'][]"
 value="'.$this->basket['var'][$key]['byteindex'].'"></input>';
					}
				}

				for($x=0; $x < $this->basket['choice'][$key]['level']; $x++) 
					$space .= '&nbsp;';
				$str .= '<option value="'.$this->basket['var'][$key]['byteindex'].'" '.$is.'>';
				$str .= $space.$this->basket['choice'][$key]['description'];
				$str .= '</option>';
				$is = '';
				$space = '';
			}
		}
		$str .= '</select>';
		if(isset($this->basket['update'])) 
			$str .= $this->basket['update'];
		$str .= $appendstr;
		$str .= '</td></tr>
</table>';
		return $str;
	}
}

// dojo ComboBoxWidget: allows one of the given options or any other
class question_dojo_comboselect extends extra_multi{
	function show(){
		$appendstr = '';
		if(isset($this->attribute['passive'])) $access = 'disabled';
		$str .= '
<script type="text/javascript">dojo.require("dijit.form.ComboBox");</script>
<table border="0" cellpadding="0" cellspacing="0">
<tr><td class="description">'.$this->basket['description'];
		if($this->warn) $str .= '<img src="style/'.$this->warn.'.gif" alt="" class="warn"></img>';
		$str .= '</td></tr>
<tr><td>
<select dojoType="dijit.form.ComboBox" autocomplete="true" '.$access.' title="'.$this->basket['helptext'].' tabindex="'.$this->tabindex.'"';

		if($this->warn) 
			$str .= ' class="select_warn" ';
		else 
			$str .= ' class="select" ';
	
		if($this->attribute['width']) 
			$str .= 'style="width:'.($this->attribute['width']).'px" ';
	
		if($this->js && isset($this->basket['update'])) 
			$str .= 'onChange="sendForm('.$this->update_byteindex.')" ';

		// - this breaks the whole page if used with dojo_combobox
		//if ($access != 'disabled')
		//  $str .= "name=\"usrinput[multiple#".$this->tabindex."][]\"";

		$str .= '>';
		if($this->basket['choice'])
			foreach($this->basket['choice'] as $key=>$val) {
				if(trim($this->basket['var'][$key]['content'])!='') {
					$is='selected';
					if ($access == 'disabled') {
						$appendstr = '<input type="hidden" name="usrinput[multiple#'.$this->tabindex.'][]"
 value="'.$this->basket['var'][$key]['byteindex'].'"></input>';
					}
				}
				for($x=0; $x < $this->basket['choice'][$key]['level']; $x++) $space .= '&nbsp;';
				$str .= '<option value="'.$this->basket['var'][$key]['byteindex'].'" $is>';
				$str .= $space.$this->basket['choice'][$key]['description'];
				$str .= '</option>';
				$is = '';
				$space = '';
			}
		$str .='</select>';
		if(isset($this->basket['update'])) $str .= $this->basket['update']."\n";
		$str .= $appendstr;
		$str .= '</td></tr></table>';
		return $str;
	}
}


class question_mselect extends extra_multi{
	function show(){
		if (isset($this->attribute['passive'])) 
			$access = 'disabled';

		$str .= '<script type="text/javascript">dojo.require("dijit.form.MultiSelect");</script>
<table border="0" cellspacing="0" cellpadding="0">
<tr><td class="description">'.$this->basket['description'];
		if ($this->warn) 
			$str .= '<img src="style/'.$this->warn.'.gif" alt="" class="warn"></img>';
		$str .= '</td></tr><tr><td>
<select '.$access.' title="'.$this->basket['helptext'].'" tabindex="'.$this->tabindex.'"';
		$str .= " dojoType=\"dijit.form.MultiSelect\"";
		if ($this->warn) 
			$str .= ' class="mselect_warn" ';
		else 
			$str .= ' class="mselect" ';
		if ($this->js && isset($this->basket['update'])) 
			$str .= 'onChange="sendForm('.$this->update_byteindex.')" ';
		if ($this->attribute['width'] || $this->attribute['height'])
	    {
			$str .= 'style=" ';
			if ($this->attribute['width']) 
				$str .= 'width:'.($this->attribute['width']).'px; ';
			if ($this->attribute['height']) 
				$str .= 'height:'.($this->attribute['height']).'px';
			$str .= '" ';
	    }
		$str .= 'name="usrinput[multiple#'.$this->tabindex.'][]" multiple size="5">';
		if ($this->basket['choice'])	    
			foreach($this->basket['choice'] as $key=>$val)
			{
				if (trim($this->basket['var'][$key]['content'])!='') 
					$is='selected';
				$str .= '<option value="'.$this->basket['var'][$key]['byteindex'].'" '.$is.'>';
				$str .= $this->basket['choice'][$key]['description'];
				$str .= '</option>';
				$is = '';
			}
		$str .='</select>
</td></tr></table>';
		if (isset($this->basket['update'])) 
			$str .= $this->basket['update'];
	  
		return $str;
	}
}

/*
 
 * |------------------------------------------|
 * |             |          |                 |
 * |             |----------|                 |
 * |  list       |    >     |      list       |
 * |             |----------|                 |
 * |             |    <     |                 |
 * |------------------------------------------|
 */

class question_mmselect extends extra_multi{
	function show(){
		if (isset($this->attribute['passive'])) 
			$access = 'disabled';

		# the left side and the Dojo code
		$str .= '<tr ><td ><!-- start table of type multi--><table  class="multi"  summary=""><tr class="multi_top"><td  rowspan="3"><script type="text/javascript">dojo.require("dijit.form.MultiSelect");
dojo.addOnLoad(function(){
	dojo.query("select").forEach(function(n){
		if(!dijit.byNode(n)){
			var multiselect = new dijit.form.MultiSelect({ },n);
		}
	});

	/* catch the sendForm event and select all values in the right selectbox */
	var submitform = document.getElementById( "content" );
	dojo.connect(submitform, "onsubmit",function(evt) {
		selectBox=dijit.byId("usrinput[multiple#'.$this->tabindex.'][]");
		// selectBox=dijit.byId("usrinput[multiple#'.$this->tabindex.'][]");
		/* FIXME: the setValue call ist not correct but it was the easiest way ;) */
		selectBox.setValue(1);
		selectBox.invertSelection();
	});

	dojo.query("button.dojo_switchbutton").connect("onclick",function(e) {
		switch(e.target.id.toString()){
			case "left-'.$this->tabindex.'" : dijit.byId("usrinput[multiple#'.$this->tabindex.'][]").addSelected(dijit.byId("field1-'.$this->tabindex.'")); break;
			case "right-'.$this->tabindex.'" : dijit.byId("field1-'.$this->tabindex.'").addSelected(dijit.byId("usrinput[multiple#'.$this->tabindex.'][]")); break;
		}
		dojo.stopEvent(e);
	});
});
';
		$str .= '</script>';
		$str .= '<table border="0" cellspacing="0" cellpadding="0">';
		$str .= '<tr><td class="description">'.$this->basket['caption-left'];
		if ($this->warn) {
			$str .= '<img src="style/'.$this->warn.'.gif" alt="" class="warn"></img>';
		}
		$str .= '</td></tr><tr><td> <select '.$access.' title="'.$this->basket['helptext_left'].'" id="field1-'.$this->tabindex.'" tabindex="'.$this->tabindex.'"';
		if ($this->warn) 
			$str .= ' class="mselect_warn" ';
		else 
			$str .= ' class="mselect" ';

		if ($this->attribute['width'] || $this->attribute['height'])
	    {
			$str .= 'style=" ';
			if ($this->attribute['width']) 
				$str .= 'width:'.($this->attribute['width']).'px; ';
			if ($this->attribute['height']) 
				$str .= 'height:'.($this->attribute['height']).'px';
			$str .= '" ';
	    }
		$str .= " dojoType=\"dijit.form.MultiSelect\"";
		$str .= 'name="field1-'.$this->tabindex.'" multiple size="5">';
		if ($this->basket['choice'])	    
			foreach($this->basket['choice'] as $key=>$val)
			{
				if($this->basket['choice'][$key]['activated'] == '1') {
					continue;
				}
				if (trim($this->basket['var'][$key]['content'])!='') 
					$is='selected';
				$str .= '<option value="'.$this->basket['var'][$key]['byteindex'].'" '.$is.'>';
				$str .= $this->basket['choice'][$key]['description'];
				$str .= '</option>';
				$is = '';
			}
		$str .='</select>
</td></tr></table>';
		
		# the right side
		$str .= '</td><td  class="multi_spacer">';
		$str .= '<div>&nbsp;</div>';
		$str .= '</td><td  rowspan="3"><script type="text/javascript">dojo.require("dijit.form.MultiSelect");</script>';
		$str .= '<table border="0" cellspacing="0" cellpadding="0">';
		$str .= '<tr><td class="description">'.$this->basket['caption-right'];
		if ($this->warn) {
			$str .= '<img src="style/'.$this->warn.'.gif" alt="" class="warn"></img>';
		}
		$str .= '</td></tr><tr><td>
<div id="mmselect"><select '.$access.' title="'.$this->basket['helptext_right'].'" id="usrinput[multiple#'.$this->tabindex.'][]" tabindex="'.$this->tabindex.'"';
		if ($this->warn) 
			$str .= ' class="mselect_warn" ';
		else 
			$str .= ' class="mselect" ';
		if ($this->attribute['width'] || $this->attribute['height'])
	    {
			$str .= 'style=" ';
			if ($this->attribute['width']) 
				$str .= 'width:'.($this->attribute['width']).'px; ';
			if ($this->attribute['height']) 
				$str .= 'height:'.($this->attribute['height']).'px';
			$str .= '" ';
	    }
		$str .= " dojoType=\"dijit.form.MultiSelect\"";
		$str .= 'name="usrinput[multiple#'.$this->tabindex.'][]" multiple size="5">';
		if ($this->basket['choice'])	    
			foreach($this->basket['choice'] as $key=>$val)
			{
				if($this->basket['choice'][$key]['activated'] == 'ascii-null-escape') {
					continue;
				}
				if (trim($this->basket['var'][$key]['content'])!='') 
					$is='selected';
				$str .= '<option value="'.$this->basket['var'][$key]['byteindex'].'" '.$is.'>';
				$str .= $this->basket['choice'][$key]['description'];
				$str .= '</option>';
				$is = '';
			}
		$str .='</select></div>
</td></tr></table>';
		$str .= '</td></tr><tr class="leftright_top"><td  class="leftright_top_fixed"><table class="button"><tr><td class="button_icon_switch">
<button id="left-'.$this->tabindex.'" class="dojo_switchbutton" border="0" title="Add"><img src="/style/right.gif" /></button>
</td></tr>';
		$str .= '</table></td></tr><tr class="leftright_bottom"><td  class="leftright_bottom_fixed"><table class="button"><tr><td class="button_icon_switch">
<button id="right-'.$this->tabindex.'" class="dojo_switchbutton" border="0" title="Remove"><img src="/style/left.gif" /></button>
</td></tr>';
		$str .= '</table></td></tr></table>';

		if (isset($this->basket['update'])) 
			$str .= $this->basket['update'];
	  
		return $str;
	}
}

# FIXME: nowhere used? dijit-forms are not tested...
class question_choice extends extra_multi{
	function show(){
		if (isset($this->attribute['passive'])) 
			$access = 'disabled';
	  
		$str .= '<script type="text/javascript">dojo.require("dijit.form.CheckBox");</script>
<div title="'.$this->basket['helptext'].'" >
';
		if (isset($this->basket['description']) && trim($this->basket['description']) != '')
			$str .= $this->basket['description'].'<br />';
		if ($this->warn) 
			$str .= '<img src="style/'.$this->warn.'.gif" alt="" class="warn"></img>';
		foreach ($this->basket['choice'] as $key=>$val)
	    {
			if (trim($this->basket['var'][$key]['content'])!='') 
				$is = 'checked';
			$str .= '<input tabindex="'.$this->tabindex.'" class="choice" dojoType="dijit.form.RadioButton" ';
			if ($this->js && isset($this->basket['update'])) 
				$str .= 'onClick="sendForm('.$this->update_byteindex.')" ';
			$str .= 'type="radio" name="usrinput[multiple#'.$this->tabindex.'][]"';
			$str .= $access.' value="'.$this->basket['var'][$key]['byteindex'].'" '.$is.'></input>';
			$str .= $this->basket['choice'][$key]['description']."<br />\n";
			$is='';
	    }
		if (isset($this->basket['update'])) 
			$str .= $this->basket['update'];
		$str .= '</div>';
	  
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
		if ($tag=='content') $this->byteindex=$byteindex;
	}
	function put_value($val){
		$this->value .= $val;
	}
	function finish($tag){
		if($tag == 'content')return TRUE;
		else return FALSE;
	}
	function show(){
		return '<input type="hidden" name="session_data['.$this->name.']" value="'.$this->value.'"></input>';
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
		//$close_attribute['closebutton'] = "1";
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
		$str_start = '<!-- start of categorylist--> 
<div id="category">
<table border="0" cellspacing="0" cellpadding="0">
<tr><td nowrap valign="top">
<div id="categorystart">&nbsp;</div>
</td><td width="100%">
<div id="categorycenter">';
		$str_end = '</div>
</td><td nowrap valign="top">
<div id="categoryend">&nbsp;</div>
</td></tr>
</table>
</div>
<!-- end of categorylist-->
';
		$str_buttons = '';
		for($i=1; $i < $this->count+1; $i++) # i is index for button-object-array
		{
			if ( $this->category_buttons[$i]->attribute['closeable'] )
				$cssclass = 'categoryitemactivecloseable';
			else
				$cssclass = "categoryitem-active";
			if( $this->category_buttons[$i]->basket[active] )
			{ // active button
				if(!$this->category_buttons[$i]->attribute['closebutton'] == "1")
					$str_buttons .= '<span class="categoryitem-active">';
			}

			// the button
			$str_buttons .= $this->category_buttons[$i]->show();

			if( $this->category_buttons[$i]->basket[active] )
			{ // active button
				if($this->category_buttons[$i]->attribute['closebutton'] == "1" || !$this->category_buttons[$i]->attribute['closeable'])
					$str_buttons .= '</span>';
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
		for($i=1; $i < $this->count+2; $i++){ # i is index for button-object-array
# we have to check +2, otherwise the last tab on a new line wouldn't be displayed

			$itemlength = $factor*(strlen($this->all_notebook[$i]->basket[text]));
			if ($itemlength < 90)
				$itemlength = 90;
			if ($this->all_notebook[$i]->attribute['closebutton'] == "1") {
				$itemlength = 14; // width of closebutton object
				$spare = 10; // width pixel between
			} else {
				$spare = 20; // width pixel between
			}

			if((($length + $itemlength + $spare) > 800) || $i > $this->count){ # 780 at all - 14 (right) - 2 (left) -> 764 + 14 (otherwise we got an ugly user view)
				if((($length + $itemlength + $spare) > 800)){
# This tab line is full, print this line an than check the next line!
					$one_line=FALSE;
					$end=$i;
				} else if($i == $this->count) {
					$end=$i+1;
					$length += ($itemlength+$spare);
				} else {
# This tab line is full, print this line an than check the next line!
					$one_line=FALSE;
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

					$img = '';
					$img_end = '';
					//if($first==$j){
					//	$img = '';
					//}
					//else
					//{
					//	if ($last_on)
					//	{
					//		$img = 'reiter_rotgrau18x24.gif';
					//	}
					//	elseif ($this->all_notebook[$j]->basket[active]) // this_on
					//	{
					//		$img = 'reiter_graurot18x24.gif';
					//	}
					//	else
					//	{
					//		$img = 'reiter_graugrau18x24.gif';
					//	}
					//}

					if($this->all_notebook[$j]->basket[active])
					{ // active button

						//if($j==$end-1)
						//{
						//	// last in line
						//	$img_end = 'reiter_rot18x24.gif';
						//}
						//$bg='bg_on.gif';
						$last_on=TRUE; // need to know for next button
					}
					else // inactive
					{
						//if($j==$end-1)
						//{
						//	//last in line
						//	$img_end='reiter_grau18x24.gif';
						//}
						//$bg='bg_off.gif';
						$last_on=FALSE; // need to know for next button
					}

					$image = '';

					$image_end='';

					$this->all_notebook[$j]->tabindex++;
					if($this->config->browser=='Text'){$img=''; $img_end='';}
					if($j == $end-1) {
						$width = (490 - $total)+3;
					} else {
						$width = $factor*(strlen($this->all_notebook[$j]->basket[text]));
						if ($this->all_notebook[$j]->attribute['closebutton'] == '1') {
							$width = 14; // width of closebutton object
						}
						$total += $width;
						#$width -= 11;      # Bildbreite
					}
					
					$show_start = TRUE;
					$show_end = TRUE;
					if ($this->all_notebook[$j]->attribute['closebutton'] == '1') {
						$show_start = FALSE;
					}
					if ($this->all_notebook[$j]->attribute['closeable']) {
						$show_end = FALSE;
					}
					#############################################################################################################################
					if($pressed)
					{
						if (($image!='') && $show_start) $str[pressed] .= $image;
						if ($first == $j) {
							$str[pressed] .= $this->all_notebook[$j]->show($width, TRUE);
						} else {
							$str[pressed] .= $this->all_notebook[$j]->show($width);
						}
						if (($img_end != '') && $show_end)  $str[pressed] .= $image_end;
					}
					else
					{
						if (($image!='') && $show_start)  $str[$x] .= $image;
						if ($first == $j) {
							$str[$x] .= $this->all_notebook[$j]->show($width, TRUE);
						} else {
							$str[$x] .= $this->all_notebook[$j]->show($width);
						}
						if (($img_end != '') && $show_end) $str[$x] .= $image_end;
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
				$passive .= '    <tr class="notebook_line"><td class="notebook_line"><table class="tabs" border="0" cellpadding="0" cellspacing="0">
     <tr class="notebook" border="0" cellpadding="0" cellspacing="0">'.$val.'</tr>
    </table></td></tr><tr><td class="notebook_spacer"></td></tr>
';
			}
		}
		return '<table class="tabs" summary="" border="0" cellpadding="0" cellspacing="0">
<tr><td class="notebook_spacer"></td></tr>
'.$passive.'
<tr class="notebook_pressed">
<td class="notebook_pressed">
   <table class="tabs" border="0" cellpadding="0" cellspacing="0"><tr>'.$str[pressed].'</tr>
</table>
</td></tr><tr><td class="notebook_spacer"></td></tr>
</table>
';
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
		if(isset($attribute['warning'])){
			unset($attribute['warning']);
			$this->warn='warning';
		}
		if($this->member){
			$this->member->put_start($tag,$attribute,$byteindex);
		}
		else{
			if(!$this->not_valid){
				$attribute['group']=TRUE;
				switch($tag){
				case 'reset':  $this->member = new reset($tag, $this->conti_ref, $this->config, $attribute);return;
				case 'button':  $this->member = new button($tag, $this->conti_ref, $this->config, $attribute);return;
				case 'link': $this->member = new link($tag, $this->conti_ref, $this->config, $attribute);return;
				case 'question_bool': $this->member = new question_bool($tag, $this->conti_ref, $this->config, $attribute);return;
				case 'question_secure': $this->member = new question_secure($tag, $this->conti_ref, $this->config, $attribute);return;
				case 'question_date': $this->member = new question_dojo_date_widget($tag, $this->conti_ref, $this->config, $attribute);return;
				case 'question_text': $this->member = new question_text($tag, $this->conti_ref, $this->config, $attribute);return;
				case 'question_ltext': $this->member = new question_ltext($tag, $this->conti_ref, $this->config, $attribute);return;
				case 'question_mselect': $this->member = new question_mselect($tag, $this->conti_ref, $this->config, $attribute);return;
				case 'question_mmselect': $this->member = new question_mmselect($tag, $this->conti_ref, $this->config, $attribute);return;
				case 'question_select': $this->member = new question_select($tag, $this->conti_ref, $this->config, $attribute);return;
				case 'question_dojo_select': $this->member = new question_dojo_select($tag, $this->conti_ref, $this->config, $attribute);return;
				case 'language_dojo_select': $this->member = new language_dojo_select($tag, $this->conti_ref, $this->config, $attribute);return;
				case 'question_dojo_comboselect': $this->member = new question_dojo_comboselect($tag, $this->conti_ref, $this->config, $attribute);return;
				case 'question_choice': $this->member = new question_choice($tag, $this->conti_ref, $this->config, $attribute);return;
				case 'question_group': $this->member = new question_group($tag, $this->conti_ref, $this->config, $attribute);return;
				case 'question_dojo_date_widget': $this->member = new question_dojo_date_widget($tag, $this->conti_ref, $this->config, $attribute);return;
				default: $tag=''; $close='';
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
		$group .= '<table class="group">
<tr>';
		if($this->warn) $group .= '<td><img src="style/'.$this->warn.'.gif" alt="" class="warn"></img></td>';
		foreach($this->group as $key => $value)
				$group .= '<td>'.$value.'</td>';
		$group .= '</tr></table>';
		return $group;

	}
}


###########################################
class dynamic_longtable extends webui_translator
{
	var $count_row;
	var $hide;

	function put_start(&$tag, &$attribute, $byteindex)
	{
		if ($tag=='row') 
			$this->conti_ref->next_row();
		$this->start($tag, $attribute, $byteindex);
	}

	function put_value(&$value)
	{
		if(!$this->hide)
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
			if ($tag=='dynamic_longtable')
				return TRUE;
			else
				return FALSE;
		}
	}

	function show() {

		$str = '<!-- start dynamic_longtable of type '.$type.'-->
<script type="text/javascript">dojo.require("dijit.layout.StackContainer");</script>
<script type="text/javascript">dojo.require("dijit.layout.ContentPane");</script>';


# copy & paste from class table
		$space_bottom='';
		if (isset($this->attribute['type']))
		{
			$attrib_str .= ' class="'.$this->attribute['type'].'"';
			$type = $this->attribute['type'];
		}
		else
		{
			$type = 'default';
			$attrib_str .= ' class="table_default"';
		}

		#if ($this->attribute['type'] == 'content_main')
		#{
		#	$space_bottom='<tr><td class="content_spacer">&nbsp;</td></tr>';
		#}

		if($this->attribute['width'])
		{
			if(is_numeric($this->attribute['width']))
			{
				$attrib_str .= 'style="width:'.($this->attribute['width']).'px" ';
			}
			else
			{
				$attrib_str .= 'style="width:'.($this->attribute['width']).'" ';
			}
		}
		# -> end of copy&paste from class table

# config-vars
		$stackNumber = 1;
		$totalrows = 0; # the transfered total is the number of "real" entries, without header etc.
		if (is_numeric($this->attribute['total']))
			$totalrows = $this->attribute['total'];
		$headerrows = 0;
		if (is_numeric($this->attribute['header']))
			$headerrows = $this->attribute['header'];
		$displayedrows = 0;
		$olddisplayedrows = -1;
		$visiblerows = 0;
		if (is_numeric($this->attribute['visible']))
			$visiblerows = $this->attribute['visible'];


		## Buttons
		$button_str = '';
# show buttons only if more than one StackContainer, which means: if total > visible
		if ( $totalrows > $visiblerows ) {
# back button
			$button_str .='<div class="dynlongtable-buttons" id="dynlongtable_buttons" align="center">
<button class="dynlongtable-button" type=button dojoType="dijit.form.Button">
  <img alt="&lt;" style="margin: 4px;" src="style/l_ar_small.gif" />
  <script type="dojo/method" event="onClick" args="evt">
     dijit.byId("longtable").back()
  </script>
</button>';    
    
# direct access buttons
			$button_str .= '<span class="dynlongtable-controller" dojoType="dijit.layout.StackController" containerId="longtable"></span>';

# forward button
			$button_str .= '<button class="dynlongtable-button" type=button dojoType="dijit.form.Button">
  <img alt="&gt;" style="margin: 4px;" src="style/r_ar_small.gif" />
  <script type="dojo/method" event="onClick" args="evt">
     dijit.byId("longtable").forward()
  </script>
</button>
</div>';
			## End Buttons
		}    	  

		$str .= '<div class="dynlongtable-container" id="longtable" dojoType="dijit.layout.StackContainer" dolayout="false"';
#FIXME: define in CSS ?
		$str .= ' style="margin:5px, border:none">'; 
    
# buttons - top # commented out
		# $str .= $button_str;

# if totalrows is not correct we will loop forever, so we check also if displayedrows has been changed
		while ( $totalrows > $displayedrows && $olddisplayedrows != $displayedrows) {
			$olddisplayedrows = $displayedrows;
			$str .= '<div class="dynlongtable-pane" dojoType="dijit.layout.ContentPane" title="'.$stackNumber.'">';
      
# Debug-message
			# $str .= "<h2> Content pane Nr. ".$stackNumber.", shows from element ".$displayedrows." to ".($displayedrows+$visiblerows)."</h2>\n";
      
			$str .= '<table '.$attrib_str.'  summary="">';
					       
			$rowsinthispane = 0;
			$checkedrows = 0;
			foreach ($this->conti_ref->content as $key => $value) {	
# key is a number
				# $this->config->debug_put("key:".$key); 
# value is HTML
				# $this->config->debug_put("value:".$value); 

# detect if header, show
	
				if ($headerrows && $key <= $headerrows)
					$str .= $value;
				else  # show $displayedrows element up to $displayedrows + $visible
				{
					$checkedrows += 1; # rows checked without header
					if ($rowsinthispane < $visiblerows && $checkedrows > $displayedrows)
					{
						$str .= $value;
						$rowsinthispane += 1;
						$displayedrows += 1;
					}	    
            
					else # detect if footer		 
						if ($key > $totalrows + $headerrows + 1)
							$str .= $value;	
				}
			}
      
			$str .= $space_bottom.'</table>';
			$str .= '</div>';

			$stackNumber += 1;
		}
    
# last pane for debug, should be "false"
		if (false) {
			$str .= '<div dojoType="dijit.layout.ContentPane" title="debug">      
<h2> Debug pane </h2>
<br>
visible: '.$this->attribute['visible'].'<br>
total: '.$this->attribute['total'].'<br>
headerrows: '.$headerrows.'<br>
start: '.$this->attribute['start'].'<br>
displayed: '.$displayedrows.'<br>	 
</div>
';
		}

# close longtable div
		$str .= '</div>';

# buttons - foot
		$str .= $button_str;


		$str .= '<!-- finished dynmic_longtable of type '.$type.'-->';
		return $str;
	}

}

class long_table extends webui_translator
{
	var $count_row;
	var $hide;
	function put_start(&$tag, &$attribute, $byteindex)
	{
		if(trim($tag)=='content' && !$this->extra)
		{
			$this->hide=TRUE;
			$this->conti_ref->set_byteindex($byteindex);
		}
		if(!$this->temp)
		{
			$this->conti_ref->set_index();
			$this->temp ='used';
		}
		if($tag=='row')
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
		if($this->hide && $tag=='content')
			$this->hide=FALSE;

		if($tag=='long_table')
			return TRUE;
		else return FALSE;
	}

	function show()
	{
		$this->conti_ref->set_parameter($this->attribute['visible'], $this->attribute['total'], $this->attribute['start']);
		#	$this->count_row
		$wrap_view = $this->conti_ref->wrap_view();
		$table = '<table class="content_list" summary="">'.$this->conti_ref->show().'</table>';
		$tb_index = '<table class="content_sublist" summary="">
<tr><td class="content_wrapview">
'.$wrap_view.'</td></tr>
</table>';
		return $table.$tb_index;
	}
}

class table extends webui_translator
{

	function put_start(&$tag, &$attribute, $byteindex)
	{
		if($tag=='row') $this->conti_ref->next_row();
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
			if ($tag=='table')
				return TRUE;
			else
				return FALSE;
		}
	}

	function show()
	{
		if (isset($this->attribute['border'])) // border is deprecated
		{
			if ($this->attribute['border']=='1')
				$attrib_str .= ' class="content_border"';
			if ($this->attribute['border']=='0')
				$attrib_str .= ' class="content_plain"';
		}

		$space_bottom='';

		if (isset($this->attribute['type']))
		{
			$attrib_str .= ' class="'.$this->attribute['type'].'"';
			$type = $this->attribute['type'];
		}
		else
		{
			$type = 'default';
			$attrib_str .= ' class="table_default"';
		}

		#if ($this->attribute['type'] == 'content_main')
		#{
		#	$space_bottom='<tr><td class="content_spacer">&nbsp;</td></tr>';
		#}
		if(isset($this->attribute['align'])) {
			$attrib_str .= ' align="'.$this->attribute['align'].'"';
		}
		if(isset($this->attribute['webui-id'])) {
			$attrib_str .= ' id="'.$this->attribute['webui-id'].'"';
		}

		if($this->attribute['width'])
		{
			if(is_numeric($this->attribute['width']))
			{
				$attrib_str .= 'style="width:'.($this->attribute['width']).'px" ';
			}
			else
			{
				$attrib_str .= 'style="width:'.($this->attribute['width']).'" ';
			}
		}

		$table = '<!-- start table of type '.$type.'-->';
		$table .= '<table '.$attrib_str.'  summary="">'.$this->conti_ref->show_all().$space_bottom.'</table>';
		$table .= '<!-- finished table of type '.$type.'-->';
		return $table;
	}

} //table

#class dynamic_longtable extends table
#{
#}

class tgroup extends webui_translator{
	function put_start(&$tag, &$attribute, $byteindex){
		$this->conti_ref->next_row();
		$this->start($tag, $attribute, $byteindex);
	}
	function put_value(&$value){$this->value($value);}
	function finish(&$tag){
		if($this->extra){$this->end($tag);}
		else{	if($tag=='tgroup')return TRUE;
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
		else{   if($tag=='row'){
				if(is_array($this->stack))
					foreach( $this->stack as $key => $value)
							$this->value($value);
				return TRUE;
			}
			else return FALSE;
		}
	}
	function show(){
		if(isset($this->attribute['border'])) {
			if($this->attribute['border']=="1")$attrib_str .= ' class="border"';
			if($this->attribute['border']=="0")$attrib_str .= ' class="plain"';
		}
		if(isset($this->attribute['type']))
			$attrib_str = 'class="'.$this->attribute['type'].'"';
		if(isset($this->attribute['webui-id']))
			$attrib_str .= ' id="'.$this->attribute['webui-id'].'"';
		$row='<tr '.$attrib_str.'>'.$this->conti_ref->show_all().'</tr>';
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
			if($tag=='col')
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
		if(isset($this->attribute['type']))
			$attrib_str .= ' class="'.$this->attribute['type'].'"';
		if(isset($this->attribute['colspan']))
			$attrib_str .= ' colspan="'.$this->attribute['colspan'].'"';
		if(isset($this->attribute['rowspan']))
			$attrib_str .= ' rowspan="'.$this->attribute['rowspan'].'"';
		if(isset($this->attribute['align']))
			$attrib_str .= ' align="'.$this->attribute['align'].'"';
		if(isset($this->attribute['valign']))
			$attrib_str .= ' valign="'.$this->attribute['valign'].'"';
		if(isset($this->attribute['width']))
			$attrib_str .= ' width="'.$this->attribute['width'].'"';
		if(isset($this->attribute['nofill']))
			$attrib_str .= ' width="1" ';
		$all=$this->conti_ref->show_all();
		if(trim($all)=='')
			$row='<td '.$attrib_str.'>&nbsp;</td>';
		else
			$row='<td '.$attrib_str.'>'.$all.'</td>';
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
	var $status='content';
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
		$this->status='content';
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
				case 'footer': $footer = $value; break;
				case 'header': $header = $value; break;
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
			$str .= '<table><tr><td>';

			if(!$this->ref_config->is_js)
			{
				$str .= '<!-- script -->';

				if ($first > 1)
					$str .= '<input class="buttoncontent" type="submit" name="long_table['.$this->byteindex.']" value="<<"></input>';
				else
					$str .= '<img class="icon" src="style/no_arrow.gif" style="margin:4px" alt=""></img>';

				$str .= '</td><td>';

				if ($current > 1)
					$str .= '<input class="buttoncontent" type="submit" name="long_table['.$this->byteindex.']" value="<"></input>';
				else
					$str .= '<img class="icon" src="style/no_ar.gif" style="margin:4px" alt=""></img>';

				$str .= '</td><td>';

				for ($y=$first; $y <= $last; $y++)
				{
					if ($y==$current)
						$str .= '<input class="buttoncontent" type="submit" name="long_table['.$this->byteindex.']" value="'.$y.'" disabled></input>';
					else
						$str .= '<input class="buttoncontent" type="submit" name="long_table['.$this->byteindex.']" value="'.$y.'" style="color:#000000"></input>';
				}

				$str .= '</td><td>';

				if ($current < $max)
					$str .= '<input class="buttoncontent" type="submit" name="long_table['.$this->byteindex.']" value=">"></input>';
				else
					$str .= '<img class="icon" src="style/no_ar.gif" style="margin:4px" alt=""></img>';

				$str .= '</td><td>';

				if ($last < $max)
					$str .= '<input class="buttoncontent" type="submit" name="long_table['.$this->byteindex.']" value=">>"></input>';
				else
					$str .= '<img class="icon" src="style/no_arrow.gif" style="margin:4px" alt=""></img>';

			}
			else
			{
				$str .= '<!-- no script -->';
				if($first > 1)
				{
					$str .= '<a class="'.$class.'" onClick="sendForm(\''.$this->byteindex.'\',\'<<\')">
<img class="icon" src="style/l_arrow.gif" style="margin:4px" alt=""></img></a>';
				}
				else
					$str .= '<img class="icon" src="style/no_arrow.gif" style="margin:4px" alt=""></img>';

				$str .= '</td><td>';

				if ($current > 1)
				{
					$str .= '<a class="'.$class.'" onClick="sendForm(\''.$this->byteindex.'\',\''.($current - 1).'\')">
<img class="icon" src="style/l_ar.gif" style="margin:4px" alt=""></img></a>';
				}
				else
					$str .= '<img class="icon" src="style/no_ar.gif" style="margin:4px" alt=""></img>';

				$str .= '</td><td>';

				for ($y=$first; $y <= $last; $y++)
				{
					if ($y==$current )
						$str .= '<b style="vertical-align:middle; font-size:12px; margin:5px; color:#cc0033;"> '.$y.' </b>';
					else
					{
						$str .= '<a class="'.$class.'" onClick="sendForm(\''.$this->byteindex.'\',\''.$y.'\')">
<b style="vertical-align:middle; font-size:12px; margin:5px;"> '.$y.' </b>';
						$str .= '</a>';
					}
				}

				$str .= '</td><td>';

				if ($current < $max)
				{
					$str .= '<a class="'.$class.'" onClick="sendForm(\''.$this->byteindex.'\',\''.($current + 1).'\')">
<img class="icon" src="style/r_ar.gif" style="margin:4px" alt=""></img></a>';
				}
				else
					$str .= '<img class="icon" src="style/no_ar.gif" style="margin:4px" alt=""></img>';

				$str .= '</td><td>';

				if ($last < $max)
				{
					$str .= '<a class="'.$class.'" onClick="sendForm(\''.$this->byteindex.'\',\'>>\')">
<img class="icon" src="style/r_arrow.gif" style="margin:4px" alt=""></img></a>';
				}
				else
					$str .= '<img class="icon" src="style/no_arrow.gif" style="margin:4px" alt=""></img>';

				$str .= '<input type="hidden" id="'.$this->byteindex.'" name="long_table['.$this->byteindex.']" value=""></input>';

			}
			$str .= '</td></tr>
</table>
<input type="hidden" name="current" value="'.$current.'"></input>
<input type="hidden" name="visible" value="'.$this->visible.'"></input>;
<input type="hidden" name="previous" value="'.$first.'"></input>
<input type="hidden" name="next" value="'.$last.'"></input>';
		}
		return $str;
	}
}

###
# old widgets, replaced by dojo/dijit implementations
###

class question_select_old extends extra_multi{
	function show(){
		$appendstr = '';
		if(isset($this->attribute['passive'])) $access = 'disabled';
		$str .= '<table border="0" cellpadding="0" cellspacing="0">
<tr><td class="description">'.$this->basket['description'];
		if($this->warn) $str .= '<img src="style/'.$this->warn.'.gif" alt="" class="warn"></img>';
		$str .= '</td></tr>
<tr><td>;
<select '.$access.' title="'.$this->basket['helptext'].'" tabindex="'.$this->tabindex.'"';
		if($this->warn) $str .= ' class="select_warn" ';
		else $str .= ' class="select" ';
		if($this->attribute['width']) $str .= 'style="width:'.($this->attribute['width']).'px" ';
		if($this->js && isset($this->basket['update'])) $str .= 'onchange="sendForm('.$this->update_byteindex.')" ';
		if ($access != 'disabled')
			$str .= 'name="usrinput[multiple#'.$this->tabindex.'][]"';
		$str .= '>';
		if($this->basket['choice'])
			foreach($this->basket['choice'] as $key=>$val) {
				if(trim($this->basket['var'][$key]['content'])!='') {
					$is='selected';
					if ($access == 'disabled') {
						$appendstr = '<input type="hidden" name="usrinput[multiple#'.$this->tabindex.'][]"
 value="'.$this->basket['var'][$key]['byteindex'].'"></input>';
					}
				}
				for($x=0; $x < $this->basket['choice'][$key]['level']; $x++) $space .= '&nbsp;';
				$str .= "<option value=\"".$this->basket['var'][$key]['byteindex'].'" '.$is.' >';
				$str .= $space.$this->basket['choice'][$key]['description'];
				$str .= '</option>';
				$is = '';
				$space = '';
			}
		$str .='</select>';
		if(isset($this->basket['update'])) $str .= $this->basket['update']."\n";
		$str .= $appendstr;
		$str .= '</td></tr></table>';
		return $str;
	}
}

?>
