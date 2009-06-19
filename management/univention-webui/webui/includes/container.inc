<?php
/*
 * Univention Webui
 *  container.inc
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
		echo '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">
<head>
<title>',$this->site_title,'   ',$this->title,'</title>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8"></meta>
<link rel="SHORTCUT ICON" href="/style/favicon.ico"></link>
<style type="text/css">
@import "/univention-dojo/dojo/resources/dojo.css";
</style>
<link id="themeStyles" rel="stylesheet" href="/univention-dojo/dijit/themes/tundra/tundra.css" type="text/css"></link>
<link rel="stylesheet" href="/style/stylesheet.css" type="text/css"></link>
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

</head>
';
		if($this->ref_config->refresh)
			echo '<body class="tundra" onload="doRefresh(',($this->ref_config->refresh),'); clear_cached(); ">';
		else
			echo '<body class="tundra" onload="clear_cached()">';
		$this->ref_config->debug_show();
	}

	function show_headertext() {
		echo '
<div id="preloader"></div>
<table class="global" cellspacing="0" cellpadding="0">
  <tr class="global_head">
	<td class="global_head_spacer" colspan="4"></td>
  </tr>
  <tr class="global_head">
	<td height="33"><img src="style/logo_univention.gif" alt="',$this->site_title,'" width="180" height="33" border="0"></img></td>
    <td width="15" height="33"></td>
    <td width="100" height="33">
';
		if (isset($this->header_img) && ($this->header_img != '')) {
			echo '     <img src="',$this->header_img,'" alt="" height="33" border="0"></td>
';
		}
		echo '    <td width="722"><span class="Stil2">',$this->headertext,'</span></td>
  </tr>
';
	}

	function show_info() {
		if($this->ref_config->layout_type && $this->ref_config->layout_type=='menuless') {
		    echo '  <tr>
   <td colspan="4">
   <!-- layout is menuless -->
	<table width="98%" class="global_menu" cellspacing="0" cellpadding="0">
	  <tr class="global_menu">
		<td class="global_menu_slogan" align="top">
		  <img src="style/slogan_whitebg.gif" alt="linux for your business" width="180" height="29" border="0"></img>
		</td>
		<td align="right">

<!-- ####### info2 ####### -->
';
		    if ($this->info2 && $this->info2 != '') {
		       echo $this->info2;
		    } else {
		       echo "        &nbsp;&nbsp;\n";
			}
		    echo '
<!-- ####### end of info2 ####### -->
<!-- ####### info ####### -->
';
		    if ($this->info && $this->info != '')
		       echo $this->info;
		    else
		       echo '        &nbsp;&nbsp;';
		    # include menu-form which is called by several javascripts
		    echo '
<!-- ####### end of info ####### -->
	  <form class="menu" name="menu" method="post" action="',$this->port,'://',$_SERVER['HTTP_HOST'].dirname($_SERVER['PHP_SELF']),'/index.php">
	  <input type="hidden" name="session_id" value="',$this->ref_config->number,'_',$this->ref_config->session_id,'"></input>
	  <input type="hidden" name="is_js" value="',$this->ref_config->is_js,'"></input>
	  </form>
		  </td>
		</tr>
	  </table>
	 </td>
	</tr>
';
		  }
		else
		  {
		    echo '  <tr>
	<td class="global_left" >
	  <table class="global_menu" cellspacing="0" cellpadding="0">
	  <tr class="global_menu">
		<td colspan="2" class="global_menu_slogan"><img src="style/slogan.gif" alt="linux for your business" width="180" height="29" border="0"></img></td>
		</tr>
	  <tr>
		<td width="35" height="25" class="global_menu">&nbsp;</td>
		<td width="145" class="global_menu">&nbsp;</td>
	  </tr>
	  <tr>
		<td height="20" class="global_menu"></td>
		<td class="global_menu"></td>
	  </tr>
	  <tr>
		<td class="global_menu_left"></td>
		<td class="global_menu_right">

<!-- ####### menu ####### -->

	  <form class="menu" name="menu" method="post" action="',$this->port,'://',$_SERVER['HTTP_HOST'].dirname($_SERVER['PHP_SELF']),'/index.php">
	  <table class="menu" cellspacing="0" cellpadding="0">
',$this->menu,'

<!-- ####### end of menu ####### -->

		<tr><td colspan="3">

<!-- ####### info ####### -->
		<br><br>',$this->info,'

<!-- ####### end of info ####### -->

<!-- ####### info2 ####### -->
		<br><br>',$this->info2,'
<!-- ####### end of info2 ####### -->
		</td></tr>
		<tr><td colspan="3" class="menu_spacer">
		</td></tr>

	</table>
    <input type="hidden" name="session_id" value="',$this->ref_config->number,'_',$this->ref_config->session_id,'"></input>
	<input type="hidden" name="is_js" value="',$this->ref_config->is_js,'"></input>
	</form>
	</td></tr>
	<tr><td colspan="3" class="menu_foot">&nbsp;</td></tr>
	</table>
	</td>
';
		  }
	}

	function show_header() {
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
		$this->header=trim($this->header);

		if($this->header)
			echo "<div class=\"header\">",$this->header,"</div>\n";

		echo "<form class=\"content\" name=\"content\" method=\"post\" enctype=\"multipart/form-data\" action=\"",$this->port,"://",$_SERVER['HTTP_HOST'].dirname($_SERVER['PHP_SELF']),"/index.php\">\n";
		if($this->ref_config->layout_type && $this->ref_config->layout_type=='menuless') {
		    echo "    <table class=\"global\"><tr><td width=\"20\" height=\"100\"></td><td>\n";
		}
	}

	function show_content() {
		echo '
<!-- ####### content ####### -->
',$this->content,'
<!-- ####### end of content ####### -->
';

	}

	function show_end() {
		if($this->ref_config->layout_type && $this->ref_config->layout_type=='menuless') {
		    echo "\n    </td></tr></table>\n";
		}

		echo '<input type="hidden" name="session_id" value="',$this->ref_config->number,'_',$this->ref_config->session_id,'"></input>
<input type="hidden" name="is_js" value="',$this->ref_config->is_js,'"></input>
</form>

	  </td></tr>
	 </table>
   </td></tr>

</table>

<!-- ####### cache-control ####### -->

<form name="cache" method="post" action="">
<input type="hidden" value="" name="cache"></input>
</form>
<!-- ####### end of cache-control ####### -->

<p>&nbsp;</p>
<p>&nbsp;</p>
</body>
</html>
';
	}

	function show(){
		$this->ref_config->debug_put('HTML: '.(strlen($this->menu)+strlen($this->content)+strlen($this->info)).' Byte');
		$this->show_head();
		$this->show_headertext();
		$this->show_info();
		$this->show_header();
		$this->show_content();
		$this->show_end();
	}
}

?>
