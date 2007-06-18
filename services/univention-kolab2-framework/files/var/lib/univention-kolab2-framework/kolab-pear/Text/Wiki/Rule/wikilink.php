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
// $Id: wikilink.php,v 1.1.2.1 2005/10/05 14:39:48 steuwer Exp $


/**
* 
* This class implements a Text_Wiki_Rule to find source text marked as a
* wiki page name and automatically create a link to that page.
*
* Wiki page names are typically in StudlyCapsStyle made of
* WordsSmashedTogether.
*
* @author Paul M. Jones <pmjones@ciaweb.net>
*
* @package Text_Wiki
*
*/

class Text_Wiki_Rule_wikilink extends Text_Wiki_Rule {
    
    
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
    
    function Text_Wiki_Rule_wikilink(&$obj, $name)
    {
        parent::Text_Wiki_Rule($obj, $name);
        
        $this->regex =
            "/" .                  // START regex
            "(^|[^A-Za-z])" .      //
            "(!?" .                // START WikiPage pattern
            "[A-Z\xc0-\xde]" .     // 1 upper
            "[A-Za-z\xc0-\xfe]*" . // 0 or more alpha
            "[a-z\xdf-\xfe]+" .    // 1 or more lower
            "[A-Z\xc0-\xde]" .     // 1 upper
            "[A-Za-z\xc0-\xfe]*" . // 0 or more alpha
            '(\\/' .               // start subpattern
            "[A-Z\xc0-\xde]" .     // 1 upper
            "[A-Za-z\xc0-\xfe]*" . // 0 or more alpha
            ')?' .                 // end subpattern 0 or 1
            ")" .                  // END WikiPage pattern
            "((\#" .               // START Anchor pattern
            "[A-Za-z]" .           // 1 alpha
            "(" .                  // start sub pattern
            "[-A-Za-z0-9_:.]*" .   // 0+ dash, alpha, digit, underscore
            "[-A-Za-z0-9_]" .      // 1 dash, alpha, digit, or underscore
            ")?" .                 // end subpattern 0 or 1
            ")?)" .                // END Anchor pattern
            "(\"\")?" .            //
            "/";                   // END regex
    }
    
    
    /**
    * 
    * Generates a replacement for the matched text.  Token options are:
    * 
    * 'page' => the wiki page name (e.g., HomePage).
    * 
    * 'anchor' => a named anchor on the target wiki page
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
        // when prefixed with !, it's explicitly not a wiki link.
        // return everything as it was.
        if ($matches[2]{0} == '!') {
            return $matches[1] . substr($matches[2], 1) .
                $matches[3] . $matches[4];
        }
        
        // set the options
        $options = array(
            'page' => $matches[2],
            'anchor' => substr($matches[4], 1)
        );
        
        // create and return the replacement token and preceding text
        return $matches[1] . $this->addToken($options);
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
        // make nice variable names (page, anchor)
        extract($options);
        
        // does the page exist?
        if (in_array($page, $this->_wiki->pages)) {
            // yes, link to the page view
            $href = $this->_wiki->view_url . $page . "#" . $anchor;
            return "<a href=\"$href\">$page</a>";
        } else {
            // no, link to a create-page url
            $href = $this->_wiki->new_url;
            return $page . "<a href=\"$href$page\">{$this->_wiki->new_text}</a>";
        }
    }
}
?>