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
// $Id: paragraph.php,v 1.1.2.1 2005/10/05 14:39:48 steuwer Exp $


/**
* 
* This class implements a Text_Wiki rule to find sections of the source
* text that are paragraphs.  A para is any line not starting with a token
* delimiter, followed by two newlines.
*
* @author Paul M. Jones <pmjones@ciaweb.net>
*
* @package Text_Wiki
*
*/

class Text_Wiki_Rule_paragraph extends Text_Wiki_Rule {
    
    
    /**
    * 
    * The regular expression used to find source text matching this
    * rule.
    * 
    * @access public
    * 
    * @var string
    * 
    */
    
    function Text_Wiki_Rule_paragraph(&$obj, $name)
    {
        parent::Text_Wiki_Rule($obj, $name);
        $this->regex = "/^(?!{$this->_wiki->delim}).*?\n\n/m";
    }
    
    /**
    * 
    * Generates a token entry for the matched text.  Token options are:
    * 
    * 'text' => The full matched text.
    * 
    * @access public
    *
    * @param array &$matches The array of matches from parse().
    *
    * @return A delimited token number to be used as a placeholder in
    * the source text.
    *
    */
    
    function process(&$matches)
    {
        if (trim($matches[0]) == '') {
            return $matches[0];
        } else {
            $start = $this->addToken(array('type' => 'start'));
            $end = $this->addToken(array('type' => 'end'));
            return $start . trim($matches[0]) . $end;
        }
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
        extract($options); //type
        
        if ($type == 'start') {
            return '<p>';
        }
        
        if ($type == 'end') {
            return "</p>\n\n";
        }
    }
}
?>