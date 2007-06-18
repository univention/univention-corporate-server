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
// $Id: Wiki.php,v 1.1.2.1 2005/10/05 14:39:48 steuwer Exp $

require_once 'Text/Wiki/Rule.php';


/**
* 
* This is the "master" class for handling the management and convenience
* functions to transform Wiki-formatted text.
* 
* @author Paul M. Jones <pmjones@ciaweb.net>
* 
* @version 0.8 alpha
* 
*/

class Text_Wiki {
    
    
    /**
    * 
    * The array of rules to apply to the source text, in order.
    *
    * This is an associative array where the key is the token-name
    * to be used for the rule, and the value is the path to the
    * rule class file.
    * 
    * @access public
    * 
    * @var array
    * 
    */
    
    var $rules = array(
    
        // pre-filters
        'prefilter'   => 'Text/Wiki/Rule/prefilter.php',
        'delimiter'   => 'Text/Wiki/Rule/delimiter.php',
        
        // capturing block elements
        'code'        => 'Text/Wiki/Rule/code.php',
        'phpcode'     => 'Text/Wiki/Rule/phpcode.php',
        'html'        => 'Text/Wiki/Rule/html.php',
        
        // non-capturing block elements
        'heading'     => 'Text/Wiki/Rule/heading.php',
        'horiz'       => 'Text/Wiki/Rule/horiz.php',
        'blockquote'  => 'Text/Wiki/Rule/blockquote.php',
        'deflist'     => 'Text/Wiki/Rule/deflist.php',
        'table'       => 'Text/Wiki/Rule/table.php',
        'list'        => 'Text/Wiki/Rule/list.php',
        'toc'         => 'Text/Wiki/Rule/toc.php',
        
        // mark paragraph blocks
        'paragraph'   => 'Text/Wiki/Rule/paragraph.php',
        
        // inline elements
        'raw'         => 'Text/Wiki/Rule/raw.php',
        'phplookup'   => 'Text/Wiki/Rule/phplookup.php',
        'url'         => 'Text/Wiki/Rule/url.php',
        'interwiki'   => 'Text/Wiki/Rule/interwiki.php',
        'freelink'    => 'Text/Wiki/Rule/freelink.php',
        'wikilink'    => 'Text/Wiki/Rule/wikilink.php',
        'strong'      => 'Text/Wiki/Rule/strong.php',
        'bold'        => 'Text/Wiki/Rule/bold.php',
        'emphasis'    => 'Text/Wiki/Rule/emphasis.php',
        'italic'      => 'Text/Wiki/Rule/italic.php',
        'tt'          => 'Text/Wiki/Rule/tt.php',
        'superscript' => 'Text/Wiki/Rule/superscript.php',
        'revise'      => 'Text/Wiki/Rule/revise.php',
        
        // post-filters
        'entities'    => 'Text/Wiki/Rule/entities.php',
        'tighten'     => 'Text/Wiki/Rule/tighten.php'
    ); 
    
    
    /**
    * 
    * An associative array of Interwiki mappings where the key is the
    * Interwiki name as entered on a wiki page, and the value is the
    * replacement URL for the target wiki web.
    * 
    * @access public
    * 
    * @var array
    * 
    */
    
    var $interwiki = array(
        'MeatBall' => 'http://www.usemod.com/cgi-bin/mb.pl?',
        'Advogato' => 'http://advogato.org/',
        'Wiki' => 'http://c2.com/cgi/wiki?'
    );
    
    
    /**
    * 
    * An array of all pages that currently exist in the wiki.  The source
    * of the pages does not matter (database, file system, whatever).  All
    * that Text_Wiki needs to know is what pages are already in the system
    * so that it can decide what kind of link to show when that page name
    * appears in the source text.
    * 
    * @access public
    * 
    * @var array
    * 
    */
    
    var $pages = array(); 
    
    
    /**
    * 
    * The URL used to view an existing page in the wiki; the page name
    * will be appended to this base URL.
    * 
    * @access public
    * 
    * @var string
    * 
    */
    
    var $view_url = 'http://example.com/index.php?page=';
    
    
    /**
    * 
    * The URL used to create a page that does not exist in the wiki; the
    * page name will be appended to this base URL.
    * 
    * @access public
    * 
    * @var string
    * 
    */
    
    var $new_url = 'http://example.com/new.php?page=';
    
    
    /**
    * 
    * When a page does not exist in the wiki, this is the text for the
    * link to the "create" URL. (Typically, the page name itself is not
    * the linked text; instead, a question mark or an inline image is
    * used to indicate the page does not exist.)
    * 
    * @access public
    * 
    * @var string
    * 
    */
    
    var $new_text = '?';
    
    
    /**
    * 
    * The delimiter that surrounds a token number embedded in the source
    * wiki text.
    * 
    * @access public
    * 
    * @var string
    * 
    */
    
    var $delim = "\xFF"; 
    
    
    /**
    * 
    * An array of tokens generated by rules as the source text is
    * parsed.
    * 
    * As Text_Wiki applies rule classes to the source text, it will
    * replace portions of the text with a delimited token number.  This
    * is the array of those tokens, representing the replaced text and
    * any options set by the parser for that replaced text.
    * 
    * The tokens array is seqential; each element is itself a sequential
    * array where element 0 is the name of the rule that generated the
    * token, and element 1 is an associative array where the key is an
    * option name and the value is an option value.
    * 
    * @access private
    * 
    * @var string
    * 
    */
    
    var $_tokens = array();
    
    
    /**
    * 
    * The source text to which rules will be applied.  This text will be
    * transformed in-place, which means that it will change as the rules
    * are applied.
    * 
    * @access private
    * 
    * @var string
    * 
    */
    
    var $_source = '';
    
    
    /**
    * 
    * Text_Wiki creates one instance of every rule that is applied to
    * the source text; this array holds those instances.  The array key
    * is the rule name, and the array value is an instance of the rule
    * class.
    * 
    * @access private
    * 
    * @var string
    * 
    */
    
    var $_rule_obj = array();
    
    
    /**
    * 
    * Constructor.
    * 
    * @access public
    * 
    * @param array $options An associative array of options where the
    * key is the option name and the value is the option value.  Each
    * option key corresponds to a public property of Text_Wiki; e.g.,
    * 'rules', 'interwiki', 'pages', 'rule_dir', and so on.
    *     
    */
    
    function Text_Wiki($options = array())
    {
        if (isset($options) && is_array($options)) {
            foreach ($options as $key => $val) {
            	// don't override private properties
                if (substr($key, 0, 1) != '_') {
                    $this->$key = $val;
                }
            }
        }
    }
    
    
    /**
    * 
    * Transforms the source text in-place.
    * 
    * First, the method parses the source text, applying rules to the
    * text as it goes.  These rules will modify the source text
    * in-place, replacing some text with delimited tokens (and
    * populating the $this->_tokens array as it goes).
    * 
    * Next, the method renders the in-place tokens into the requested
    * output format.
    * 
    * Finally, the method returns the transformed text.  Note that the
    * source text is transformed in place; once it is transformed, it is
    * no longer the same as the original source text.
    * 
    * @access public
    * 
    * @param string $text The source text to which wiki rules should be
    * applied, both for parsing and for rendering.
    * 
    * @param string $format The target output format, typically 'xhtml'.
    *  If a rule does not support a given format, the output from that
    * rule is rule-specific.
    * 
    * @return string The transformed wiki text.
    * 
    */
    
    function transform($text, $format = 'xhtml')
    {
        $this->parse($text);
        return $this->render($format);
    }
    
    
    /**
    * 
    * Sets the $_source text property, then parses it in place and
    * retains tokens in the $_tokens array property.
    * 
    * @access public
    * 
    * @param string $text The source text to which wiki rules should be
    * applied, both for parsing and for rendering.
    * 
    * @return void
    * 
    */
    
    function parse($text)
    {
        // set the object property for the source text
        $this->_source = $text;
        
        // apply the parse() method of each requested rule to the source
        // text.  load each rule class file as we go.
        foreach ($this->rules as $name => $file) {
            $this->_loadRule($name, $file);
            $this->_rule_obj[$name]->parse();
        }
    }
    
    
    /**
    * 
    * Renders tokens back into the source text, based on the requested format.
    * 
    * @access public
    * 
    * @param string $format The target output format, typically 'xhtml'.
    *  If a rule does not support a given format, the output from that
    * rule is rule-specific.
    * 
    * @return string The transformed wiki text.
    * 
    */
    
    function render($format = 'Xhtml')
    {
    	// the rendering method we're going to use from each rule
        $method = "render$format";
        
    	// the eventual output text
        $output = '';
        
        // when passing through the parsed source text, keep track of when
        // we are in a delimited section
        $in_delim = false;
        
        // when in a delimited section, capture the token key number
        $key = '';
        
        // pass through the parsed source text character by character
        $k = strlen($this->_source);
        for ($i = 0; $i < $k; $i++) {
            
            // the current character
            $char = $this->_source{$i};
            
            // are alredy in a delimited section?
            if ($in_delim) {
            
                // yes; are we ending the section?
                if ($char == $this->delim) {
                    
                    // yes, get the replacement text for the delimited
                    // token number and unset the flag.
                    $key = (int)$key;
                    $rule = $this->_tokens[$key][0];
                    $opts = $this->_tokens[$key][1];
                    $output .= $this->_rule_obj[$rule]->$method($opts);
                    $in_delim = false;
                    
                } else {
                
                    // no, add to the dlimited token key number
                    $key .= $char;
                    
                }
                
            } else {
            	
            	// not currently in a delimited section.
            	// are we starting into a delimited section?
                if ($char == $this->delim) {
                	// yes, reset the previous key and
                	// set the flag.
                    $key = '';
                    $in_delim = true;
                } else {
                	// no, add to the output as-is
                    $output .= $char;
                }
            }
        }
        
        // return the rendered source text
        return $output;
    }
    
    
    /**
    * 
    * Returns the parsed source text with delimited token placeholders.
    * 
    * @access public
    * 
    * @return string The parsed source text.
    * 
    */
    
    function getSource()
    {
        return $this->_source;
    }
    
    
    /**
    * 
    * Returns tokens that have been parsed out of the source text.
    * 
    * @access public
    * 
    * @param array $rules If an array of rule names is passed, only return
    * tokens matching these rule names.  If no array is passed, return all
    * tokens.
    * 
    * @return array An array of tokens.
    * 
    */
    
    function getTokens($rules = null)
    {
        if (! is_array($rules)) {
            return $this->_tokens;
        } else {
            $result = array();
            foreach ($this->_tokens as $key => $val) {
                if (in_array($val[0], $rules)) {
                    $result[] = $val;
                }
            }
            return $result;
        }
    }
    
    
    /**
    * 
    * Loads a rule class file and creates an instance of the rule
    * object.
    * 
    * @access private
    * 
    * @param string $name The token name to use for the rule.
    * 
    * @param string $file The file name of the rule class.
    * 
    * @return void
    * 
    */
    
    function _loadRule($name, $file)
    {
        // load the class definition.
        include_once($file);
        
        // dynamically determine the name of the class 
        // we just loaded
        $tmp = get_declared_classes();
        $k = count($tmp) - 1;
        $class = $tmp[$k];
        unset($tmp);
        
        // instantiate the rule object and add to the set
        $this->_rule_obj[$name] =& new $class($this, $name);
    }
}

?>