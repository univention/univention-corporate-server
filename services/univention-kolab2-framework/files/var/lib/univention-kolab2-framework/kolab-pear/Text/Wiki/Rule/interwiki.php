<?php
/* vim: set expandtab tabstop=4 shiftwidth=4: */
// +----------------------------------------------------------------------+
// | PHP version 4                                                        |
// +----------------------------------------------------------------------+
// | Copyright (c) 1997-2003 The PHP Group                                |
// +----------------------------------------------------------------------+
// | This source file is subject to version 2.0 of the PHP license,       |
// | that is bundled with this package in the file LICENSE, and is        |
// | available through the world-wide-web at                              |
// | http://www.php.net/license/2_02.txt.                                 |
// | If you did not receive a copy of the PHP license and are unable to   |
// | obtain it through the world-wide-web, please send a note to          |
// | license@php.net so we can mail you a copy immediately.               |
// +----------------------------------------------------------------------+
// | Authors: Paul M. Jones <pmjones@ciaweb.net>                          |
// +----------------------------------------------------------------------+
//
// $Id: interwiki.php,v 1.1.2.1 2005/10/05 14:39:48 steuwer Exp $


/**
* 
* This class implements a Text_Wiki_Rule to find source text marked as
* an Interwiki link.  See the regex for a detailed explanation of the
* text matching procedure; e.g., "InterWikiName:PageName".
*
* @author Paul M. Jones <pmjones@ciaweb.net>
*
* @package Text_Wiki
*
*/

class Text_Wiki_Rule_interwiki extends Text_Wiki_Rule {
    
    
    /**
    * 
    * Constructor.  We override the Text_Wiki_Rule constructor so we can
    * explicitly comment each part of the $regex property.
    * 
    * @access public
    * 
    * @param object &$obj The calling "parent" Text_Wiki object.
    * 
    * @param string $name The token name to use for this rule.
    * 
    */
    
    function Text_Wiki_Rule_interwiki(&$obj, $name)
    {
        parent::Text_Wiki_Rule($obj, $name);
        $this->regex = '/([A-Za-z0-9]+):([\/=&~#A-Za-z0-9]+)/';
    }
    
    
    /**
    * 
    * Generates a replacement for the matched text.  Token options are:
    * 
    * 'site' => The key name for the Text_Wiki interwiki array map, usually
    * the name of the interwiki site.
    *
    * 'page' => The page on the target interwiki to link to.
    * 
    * @access public
    *
    * @param array &$matches The array of matches from parse().
    *
    * @return A delimited token to be used as a placeholder in
    * the source text, plus any text priot to the match.
    *
    */
    
    function process(&$matches)
    {
        $options = array(
            'site' => $matches[1],
            'page' => $matches[2]
        );
        
        return $this->addToken($options);
    }
    
    
    /**
    * 
    * Renders a token into text matching the requested format.
    * 
    * @access public
    * 
    * @param array $options The "options" portion of the token (second
    * element).
    * 
    * @return string The text rendered from the token options.
    * 
    */
    
    function renderXhtml($options)
    {
        $site = $options['site'];
        $page = $options['page'];
        
        if (isset($this->_wiki->interwiki[$site])) {
            $href = $this->_wiki->interwiki[$site];
        } else {
            $href = '';
        }
        
        if ($href != '') {
            return "<a href=\"$href$page\">$site:$page</a>";
        } else {
            return "$site:$page";
        }
    }
}
?>