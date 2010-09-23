<?php
/*
 * Univention Webui
 *  container.inc
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

class webui_container{
	var $content;
	var $reiter;
	var $menu;
	var $info;
	var $info2;
	var $header;
	var $header_img;
	var $site_title;
	var $layout_type;
	var $title;
	var $current;
	var $ref_config;
	var $status;
	var $tabindex;
	var $body_class;

	function webui_container(&$ref_config, &$tabindex){
		$this->ref_config = &$ref_config;
		$this->tabindex = &$tabindex;
				
		if ($_SERVER['SERVER_PORT']=='80')
			$this->port='http';
		else
			$this->port='https';
	}

	function set_current($str){
		$bla = $this->ref_config->session_id;
		switch($str){
		case 'content':
			$this->current = &$this->content;
			break;
		case 'menu':
			$this->current = &$this->menu;
			break;
		case 'info':
			$this->current = &$this->info;
			break;
		case 'info2':
			$this->current = &$this->info2;
			break;
		case 'reiter':
			$this->current = &$this->reiter;
			break;
		case 'header':
			$this->current = &$this->header;
			break;
		case 'headertext':
			$this->current = &$this->headertext;
			break;
		case 'title':
			$this->current = &$this->title;
			break;
		}
		$this->status = $str; 
	}

	function set_body_class($str) {
		$this->body_class=$str;
	}

	function logout($type, $session_id){

		$this->title = 'Logout';

		switch($type){
		case '1':
		  $headertext = _('Session closed');
		  $maincontent = _('Your current session has been closed.');
		  require('config.php');
		  system("rm -r ".$temp_dir.$session_id.'/');
		  header('Location: index.php');
		  break;
		case '2':
		  header('Location: index.php?sessioninvalid=1');
		  break;
		}
	}

	function put($str){
		$this->current .= $str;
	}

	function show_head() {
		echo '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">
<head>
<title>',$this->site_title,'   ',$this->title,'</title>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8"></meta>
<link rel="SHORTCUT ICON" href="/style/favicon.ico"></link>
<link id="themeStyles" rel="stylesheet" href="/univention-dojo/dijit/themes/tundra/tundra.css" type="text/css"></link>
<link rel="stylesheet" href="/style/stylesheet.css" type="text/css" media="screen" title="style.css" charset="utf-8"></link>
<link rel="stylesheet" href="/style/univention-dijit.css" type="text/css"></link>
<script type="text/javascript" src="/style/tip.js"></script>
<script type="text/javascript" src="/univention-dojo/dojo/dojo.js" ></script>
<script type="text/javascript" src="/univention-dojo/unijit/unijit.js"></script>
<script type="text/javascript"> 
<!-- Todo: this should be moved into the univention-dojo package -->
	 var hideLoader = function(){
		 dojo.style("preloader", "display", "none");
		 dojo.fadeOut({
			 node:"preloader",
			 duration:700,
			 onEnd: function(){
				 dojo.style("preloader", "display", "none");
			 }
			 }).play();
	 }
	 dojo.require("dojo.parser");
	 dojo.addOnLoad(function(){
		 dojo.parser.parse();
		 hideLoader();
});
</script>
<script type="text/javascript">
<!--
dojo.require("dojo.cookie");
function umc_hide_show( itemId, minus, plus ) {
	if (document.getElementById) {
		table = document.getElementById( itemId );
		icon = document.getElementById( itemId + ".button" );
		if ( table ) {
			if (table.className == "umc_visible") {
				table.className = "umc_hidden";
				icon.src = plus;
			} else {
				table.className = "umc_visible";		
				icon.src = minus;
			}
			dojo.cookie( "univention.umc." + itemId, table.className );
		}
	}
}
function umc_restore( tree_items, minus, plus, default_class ) {
	if (document.getElementById) {
        default_class = default_class || "umc_visible";
		// IE 8 does not support for each; variable may not be named "item"
		for ( var i = 0; i < tree_items.length; i++ ) {
			itemId = tree_items[ i ];
			itema = document.getElementById( itemId );
			icon = document.getElementById( itemId + ".button" );
			if ( itema == null ) continue;
			class_name = dojo.cookie( "univention.umc." + itemId );
			if ( class_name == null ) {
				class_name = default_class;
			}
			itema.className = class_name;
			if ( class_name == "umc_hidden" ) {
				icon.src = plus;
			} else {
				icon.src = minus;
			}
		}
	}
}
var confirmDlg;
function umc_popup_confirm( title, question, yes, no, send, byteindex ) {
	dojo.require("dijit.Dialog");
	// variable named "content" can not be used as it does not work with IE8
	mycontent = "<p>" + question + "</p>";
	mycontent += "<br/><p class=\"umc_dialog_button\">";
	mycontent += "<button dojoType=\"dijit.form.Button\" onClick=\"" + send + "(" + byteindex + ")\">" + yes + "</button>&nbsp;";
	mycontent += "<button dojoType=\"dijit.form.Button\" onClick=\"confirmDlg.hide();\">" + no + "</button></p>";
	confirmDlg = new dijit.Dialog({
		title: title,
		content: mycontent,
		style: "width: 400px"
	});
	confirmDlg.show();
}
var infoDialog;
function umc_info_dialog( title, message ) {
	dojo.require("dijit.Dialog");
	// variable named "content" can not be used as it does not work with IE8
	mycontent = "<p>" + message + "</p>";
	mycontent += "<br/><p class=\"umc_dialog_button\">";
	mycontent += "<button dojoType=\"dijit.form.Button\" onClick=\"infoDialog.hide();\">OK</button></p>";
	infoDialog = new dijit.Dialog({
		title: title,
		content: mycontent,
		style: "width: 400px"
	});
	infoDialog.show();
}
//-->
function umc_checkbox_toggle( ids, value ) {
    for ( var i = 0; i < ids.length; i++ ) {
		dijit_item = dijit.byId( ids[ i ] );
        if ( value === undefined ) {
     		if ( dijit_item.checked )
     			dijit_item.setValue( false );
     		else
     			dijit_item.setValue( true );
        } else {
            dijit_item.setValue( value );
        }
	}
}
</script>
</head>
';

		if($this->ref_config->refresh) {
			echo '<body class="'.$this->body_class.' tundra" onload="doRefresh(',($this->ref_config->refresh),'); clear_cached(); ">';
		} else {
			echo '<body class="'.$this->body_class.' tundra" onload="clear_cached()">';
		}
		echo "<div id=\"preloader\"></div> \n";
		$this->ref_config->debug_show();
	}

	function show_headertext() {
		echo '<form name="content" id="'.$this->body_class.'" method="post" enctype="multipart/form-data" action="'.$this->port.'://'.$_SERVER['HTTP_HOST'].dirname($_SERVER['PHP_SELF']).'/index.php">';
		echo '
		<div id="wrapper">
';
	}

	function show_info() {
		if($this->ref_config->layout_type && $this->ref_config->layout_type=='menuless') {
		    echo '';
		  }
		else
		  {
		    echo ' 
	
	<div id=menu>
	<ul>
	'.$this->menu.'
	</ul>
	</div>
';
		  }
	}

	function show_header() {
/*
		if($this->ref_config->layout_type && $this->ref_config->layout_type=='menuless')
		  {
		    echo '    <tr><td colspan="4" valign="top">
    <table class="global_content_menuless" cellpadding="0" cellspacing="0">
';
		  }
		else
		  {
		    echo '    <td colspan="3" valign="top">
    <table class="global_content" cellpadding="0" cellspacing="0">
'; // table2
		  }
		echo '      <tr>
		<td class="gc_small_spacer"></td>
		<td class="gc_wide_spacer"></td>
		<td class="gc_small_spacer"></td>
	  </tr>

	  <tr><td></td>
	  <td colspan="2" valign="top">
<!-- ####### pre-content ####### -->
';
*/
		$this->header=trim($this->header);

		if($this->header)
			echo "<div class=\"header\">",$this->header,"</div>\n";

		/*echo "<form name=\"content\" method=\"post\" enctype=\"multipart/form-data\" action=\"",$this->port,"://",$_SERVER['HTTP_HOST'].dirname($_SERVER['PHP_SELF']),"/index.php\">\n";*/
/*
		if($this->ref_config->layout_type && $this->ref_config->layout_type=='menuless') {
		    echo "    <table class=\"global\"><tr><td width=\"20\" height=\"100\"></td><td>\n";
		}
*/
	}

	function show_content() {
		echo '
<!-- ####### content ####### -->
',$this->content,'
<!-- ####### end of content ####### -->

<br class="clear" />
</div>
<!-- @end wrapper -->
';

	}

	function show_end() {
/*
		if($this->ref_config->layout_type && $this->ref_config->layout_type=='menuless') {
		    echo "\n    </td></tr></table>\n";
		}
*/

		echo '<input type="hidden" name="session_id" value="',$this->ref_config->number,'_',$this->ref_config->session_id,'"></input>
<input type="hidden" name="is_js" value="',$this->ref_config->is_js,'"></input>
<!-- @end content-wrapper -->
</form>

<form name="redirectsignon" target="_blank" id="redirectsignon" method="post" enctype="multipart/form-data" action="/">
  <input type="hidden" name="usrinput[0]" value="" />
  <input type="hidden" name="session_id" value="" />
  <input type="hidden" name="is_js" value="1" />
</form>


<!-- ####### cache-control ####### -->

<form name="cache" method="post" action="">
<input type="hidden" value="" name="cache"></input>
</form>
<!-- ####### end of cache-control ####### -->
</div>
</body>
</html>
';
	}

	function show(){
		$this->ref_config->debug_put('HTML: '.(strlen($this->menu)+strlen($this->content)+strlen($this->info)).' Byte');
		$this->show_head();
		$this->show_headertext();
		if ($this->body_class != 'login') {
			$this->show_info();
		}
		$this->show_header();
		$this->show_content();
		$this->show_end();
	}
}

?>
