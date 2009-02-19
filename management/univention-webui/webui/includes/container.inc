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
	}

	function set_current($str){
		switch($str){
		case 'content': $this->current = &$this->content; $this->status = $str; break;
		case 'menu': 	$this->current = &$this->menu; $this->status = $str; break;
		case 'info': 	$this->current = &$this->info; $this->status = $str; break;
		case 'info2': 	$this->current = &$this->info2; $this->status = $str; break;
		case 'reiter': 	$this->current = &$this->reiter; $this->status = $str; break;
		case 'header': 	$this->current = &$this->header; $this->status = $str; break;
		case 'headertext': $this->current = &$this->headertext; $this->status = $str; break;
		case 'title': 	$this->current = &$this->title; $this->status = $str; break;
		}
	}

	function logout($type, $session_id){

		$this->title = "Logout";

		switch($type){
		case '1':
		  $headertext = _("Session closed");
		  $maincontent = _("Your current session has been closed.");
		  require("config.php");
		  system("rm -r ".$temp_dir.$session_id.'/');
		  header("Location: index.php");
		  break;
		case '2':
		  header("Location: index.php?sessioninvalid=1");
		  break;
		}
	}

	function put($str){
	$this->current .= $str;
	}

	function show(){
		if($_SERVER["SERVER_PORT"]=='80') $port="http";
		else $port="https";


		$this->ref_config->debug_put("HTML: ".(strlen($this->menu)+strlen($this->content)+strlen($this->info))." Byte");
		#echo "<!DOCTYPE html PUBLIC \"-//W3C//DTD XHTML 1.1//EN\" \"http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd\">\n";
		echo "<!DOCTYPE html PUBLIC \"-//W3C//DTD XHTML 1.1 Transitional//EN\" \"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd\">\n";
		echo "<html xmlns=\"http://www.w3.org/1999/xhtml\" xml:lang=\"en\">\n\n";
		echo "<head>\n";

		echo "<title>".$this->site_title."   ".$this->title."</title>\n";
		echo "<meta http-equiv=\"Content-Type\" content=\"text/html; charset=utf-8\"></meta>\n";
		echo "<link rel=\"SHORTCUT ICON\" href=\"/style/favicon.ico\"></link>\n";
		echo "<style type=\"text/css\">\n";
		echo "@import \"/univention-dojo/dojo/resources/dojo.css\";\n";
		echo "\n</style>\n";
		echo "<link id=\"themeStyles\" rel=\"stylesheet\" href=\"/univention-dojo/dijit/themes/tundra/tundra.css\" type=\"text/css\"></link>\n";
		echo "<link rel=\"stylesheet\" href=\"/style/stylesheet.css\" type=\"text/css\"></link>\n";
		echo "<link rel=\"stylesheet\" href=\"/style/univention-dijit.css\" type=\"text/css\"></link>\n";
		echo "<script type=\"text/javascript\" src=\"/style/tip.js\"></script>\n";
		echo "<script type=\"text/javascript\" src=\"/univention-dojo/dojo/dojo.js\" ></script>\n";
		echo "<script type=\"text/javascript\" src=\"/univention-dojo/unijit/unijit.js\"></script>\n";
		echo "<script type=\"text/javascript\"> \n";
		# Todo: this should be moved into the univention-dojo package
		echo "\t var hideLoader = function(){ \n";
		echo "\t\t dojo.style(\"preloader\", \"display\", \"none\"); \n";
		echo "\t\t dojo.fadeOut({ \n";
		echo "\t\t\t node:\"preloader\", \n";
		echo "\t\t\t duration:700, \n";
		echo "\t\t\t onEnd: function(){ \n";
		echo "\t\t\t\t dojo.style(\"preloader\", \"display\", \"none\"); \n";
		echo "\t\t\t } \n";
		echo "\t\t\t }).play(); \n";
		echo "\t }\n";
		echo "\t dojo.require(\"dojo.parser\"); \n";
		echo "\t dojo.addOnLoad(function(){ \n";
		echo "\t\t dojo.parser.parse(); \n";
		echo "\t\t hideLoader(); \n";
		echo "}); \n";

		# // import all potetial dijit-elements here?
#		echo "\t dojo.require(\"unijit.form.ComboBox\"); \n";
#		echo "\t dojo.require(\"unijit.form.FilteringSelect\"); \n";
		echo "</script>\n";

		echo "</head>\n\n";
		if($this->ref_config->refresh)
			echo"<body class=\"tundra\" onload=\"doRefresh(".($this->ref_config->refresh)."); clear_cached(); \">\n";
		else
			echo"<body class=\"tundra\" onload=\"clear_cached()\">\n";
		$this->ref_config->debug_show();

		echo "<div id=\"preloader\"></div> \n";

		echo "<table class=\"global\" cellspacing=\"0\" cellpadding=\"0\">\n";// table1
		echo "  <tr class=\"global_head\">\n"; //line 1
		echo "    <td class=\"global_head_spacer\" colspan=\"4\"></td>\n";
		echo "  </tr>\n";
		echo "  <tr class=\"global_head\">\n"; //line 2
		echo "    <td height=\"33\"><img src=\"style/logo_univention.gif\" alt=\"".$this->site_title."\" width=\"180\" height=\"33\" border=\"0\"></img>\n";
		echo "	</td>\n";

		echo "    <td width=\"15\" height=\"33\"></td>\n";
		echo "    <td width=\"100\" height=\"33\">\n";
		if (isset($this->header_img) && ($this->header_img != "")) {
			echo "     <img src=\"".$this->header_img."\" alt=\"\" height=\"33\" border=\"0\"></td>\n";
		}
		echo "    <td width=\"722\"><span class=\"Stil2\">".$this->headertext."</span></td>\n";
		echo "  </tr>\n";

		if($this->ref_config->layout_type && $this->ref_config->layout_type=='menuless')
		  {
		    echo "  <tr>\n"; //line 3
		    echo "   <td colspan=\"4\">\n";
		    echo "   <!-- layout is menuless -->\n";
		    echo "    <table width=\"98%\" class=\"global_menu\" cellspacing=\"0\" cellpadding=\"0\">\n"; // table2
		    echo "      <tr class=\"global_menu\">\n";
		    echo "        <td class=\"global_menu_slogan\" align=\"top\">\n";
		    echo "          <img src=\"style/slogan_whitebg.gif\" alt=\"linux for your business\" width=\"180\" height=\"29\" border=\"0\"></img>\n";
		    echo "        </td>\n";
		    echo "        <td align=\"right\">\n";
		    echo "\n\n<!-- ####### info2 ####### -->\n\n";
		    if ($this->info2 && $this->info2 != "")
		       echo $this->info2;
		    else
		       echo "        &nbsp;&nbsp;\n";
		    echo "\n\n<!-- ####### end of info2 ####### -->\n\n";
		    echo "\n\n<!-- ####### info ####### -->\n\n";
		    if ($this->info && $this->info != "")
		       echo $this->info;
		    else
		       echo "        &nbsp;&nbsp;";
		    echo "\n\n<!-- ####### end of info ####### -->\n\n";
		    # include menu-form which is called by several javascripts
		    echo "      <form class=\"menu\" name=\"menu\" method=\"post\" action=\"$port://".$_SERVER['HTTP_HOST'].dirname($_SERVER['PHP_SELF'])."/index.php\">\n";
		    echo "      <input type=\"hidden\" name=\"session_id\" value=\"".$this->ref_config->number."_".$this->ref_config->session_id."\"></input>\n";
		    echo "      <input type=\"hidden\" name=\"is_js\" value=\"".$this->ref_config->is_js."\"></input>\n";
		    echo "      </form>\n";
		    echo "          </td>\n";
		    echo "        </tr>\n";
		    echo "      </table>\n"; // table2
		    echo "     </td>\n";
		    echo "    </tr>\n";
		  }
		else
		  {
		    echo "  <tr>\n"; //line 3
		    echo "    <td class=\"global_left\" >\n";
		    echo "      <table class=\"global_menu\" cellspacing=\"0\" cellpadding=\"0\">\n"; // table2
		    echo "      <tr class=\"global_menu\">\n";
		    echo "        <td colspan=\"2\" class=\"global_menu_slogan\"><img src=\"style/slogan.gif\" alt=\"linux for your business\" width=\"180\" height=\"29\" border=\"0\"></img></td>\n";
		    echo "        </tr>\n";
		    echo "      <tr>\n";
		    echo "        <td width=\"35\" height=\"25\" class=\"global_menu\">&nbsp;</td>\n";
		    echo "        <td width=\"145\" class=\"global_menu\">&nbsp;</td>\n";
		    echo "      </tr>\n";
		    echo "      <tr>\n";
		    echo "        <td height=\"20\" class=\"global_menu\"></td>\n";
		    echo "        <td class=\"global_menu\"></td>\n";
		    echo "      </tr>\n";
		    echo "      <tr>\n";
		    echo "        <td class=\"global_menu_left\"></td>\n";
		    echo "        <td class=\"global_menu_right\">\n";

		    echo "\n\n<!-- ####### menu ####### --> \n\n";
		    echo "      <form class=\"menu\" name=\"menu\" method=\"post\" action=\"$port://".$_SERVER['HTTP_HOST'].dirname($_SERVER['PHP_SELF'])."/index.php\">\n";
		    echo "      <table class=\"menu\" cellspacing=\"0\" cellpadding=\"0\">\n"; //table3

		    echo $this->menu;
		    echo "\n\n<!-- ####### end of menu ####### -->\n\n";

		    echo "        <tr><td colspan=\"3\">\n";
		    echo "\n\n<!-- ####### info ####### -->\n\n";
		    echo "        <br><br>\n";
		    echo $this->info;
		    echo "\n\n<!-- ####### end of info ####### -->\n\n";
		    echo "\n\n<!-- ####### info2 ####### -->\n\n";
		    echo "        <br><br>\n";
		    echo $this->info2;
		    echo "\n\n<!-- ####### end of info2 ####### -->\n\n";
		    echo "        </td></tr>\n";
		    echo "        <tr><td colspan=\"3\" class=\"menu_spacer\">\n";
		    echo "        </td></tr>";

		    echo "        </table>\n"; // table3
		    echo "      <input type=\"hidden\" name=\"session_id\" value=\"".$this->ref_config->number."_".$this->ref_config->session_id."\"></input>\n";
		    echo "      <input type=\"hidden\" name=\"is_js\" value=\"".$this->ref_config->is_js."\"></input>\n";
		    echo "      </form>\n";
		    echo "      </td></tr>\n";
		    echo "      <tr><td colspan=\"3\" class=\"menu_foot\">&nbsp;</td></tr>";
		    echo "      </table>\n"; // table2
		    echo "	</td>\n";
		  }

		if($this->ref_config->layout_type && $this->ref_config->layout_type=='menuless')
		  {
		    echo "    <tr><td colspan=\"4\" valign=\"top\">\n";
		    echo "    <table class=\"global_content_menuless\" cellpadding=\"0\" cellspacing=\"0\">\n"; // table2
		  }
		else
		  {
		    echo "    <td colspan=\"3\" valign=\"top\">\n";
		    echo "    <table class=\"global_content\" cellpadding=\"0\" cellspacing=\"0\">\n"; // table2
		  }
		echo "      <tr>\n";
		echo "        <td class=\"gc_small_spacer\"></td>\n";
		echo "        <td class=\"gc_wide_spacer\"></td>\n";
		echo "        <td class=\"gc_small_spacer\"></td>\n";
		echo "      </tr>\n";

		echo "      <tr><td></td>\n";
		echo "      <td colspan=\"2\" valign=\"top\">\n";
		echo"\n\n<!-- ####### pre-content ####### -->\n\n";
		$this->header=trim($this->header);

		if($this->header)
		  echo "<div class=\"header\">".$this->header."</div>\n";

		echo"<form class=\"content\" name=\"content\" method=\"post\" enctype=\"multipart/form-data\" action=\"$port://".$_SERVER['HTTP_HOST'].dirname($_SERVER['PHP_SELF'])."/index.php\">\n";
		if($this->ref_config->layout_type && $this->ref_config->layout_type=='menuless')
		  {
		    echo "    <table class=\"global\"><tr><td width=\"20\" height=\"100\"></td><td>\n";
		  }

		echo"\n\n<!-- ####### content ####### -->\n\n";
		echo $this->content;
		echo"\n\n<!-- ####### end of content ####### -->\n\n";

		if($this->ref_config->layout_type && $this->ref_config->layout_type=='menuless')
		  {
		    echo "\n    </td></tr></table>\n";
		  }

		echo"<input type=\"hidden\" name=\"session_id\" value=\"".$this->ref_config->number."_".$this->ref_config->session_id."\"></input>\n";
		echo"<input type=\"hidden\" name=\"is_js\" value=\"".$this->ref_config->is_js."\"></input>\n";
		echo"</form>\n";

		echo "      </td></tr>\n";
		echo "     </table>\n"; // table2
		echo "   </td></tr>\n"; //end line 3
		echo "\n";
		echo "</table>\n"; // table1

                echo"\n\n<!-- ####### cache-control ####### -->\n\n ";
                echo"<form name=\"cache\" method=\"post\" action=\"\">";
                echo"<input type=\"hidden\" value=\"\" name=\"cache\"></input>";
                echo"</form>";
                echo"\n\n<!-- ####### end of cache-control ####### -->\n\n ";

		echo "<p>&nbsp;</p>\n";
		echo "<p>&nbsp;</p>\n";
		echo "</body>\n";
		echo "</html>\n";

	}
}

?>
