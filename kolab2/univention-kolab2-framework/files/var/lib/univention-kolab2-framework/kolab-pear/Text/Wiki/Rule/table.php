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
// $Id: table.php,v 1.1.2.1 2005/10/05 14:39:48 steuwer Exp $


/**
* 
* This class implements a Text_Wiki_Rule to find source text marked as a
* set of table rows, where a line start and ends with double-pipes (||)
* and uses double-pipes to separate table cells.  The rows must be on
* sequential lines (no blank lines between them) -- a blank line
* indicates the beginning of a new table.
*
* @author Paul M. Jones <pmjones@ciaweb.net>
*
* @package Text_Wiki
*
*/

class Text_Wiki_Rule_table extends Text_Wiki_Rule {
    
    
    /**
    * 
    * The regular expression used to parse the source text and find
    * matches conforming to this rule.  Used by the parse() method.
    * 
    * @access public
    * 
    * @var string
    * 
    * @see parse()
    * 
    */
    
    var $regex = '/\n((\|\|).*)(\n)(?!(\|\|))/Us';
    
    
    /**
    * 
    * Generates a replacement for the matched text.  Token options are:
    * 
    * 'type' =>
    *     'table_start' : the start of a bullet list
    *     'table_end'   : the end of a bullet list
    *     'row_start' : the start of a number list
    *     'row_end'   : the end of a number list
    *     'cell_start'   : the start of item text (bullet or number)
    *     'cell_end'     : the end of item text (bullet or number)
    * 
    * 'colspan' => column span (for a cell)
    * 
    * @access public
    *
    * @param array &$matches The array of matches from parse().
    *
    * @return A series of text and delimited tokens marking the different
    * table elements and cell text.
    *
    */
    
    function process(&$matches)
    {
        // out eventual return value
        $return = '';
        
        // start a new table
        $return .= $this->addToken(array('type' => 'table_start'));
        
        // rows are separated by newlines in the matched text
        $rows = explode("\n", $matches[1]);
        
        // loop through each row
        foreach ($rows as $row) {
            
            // start a new row
            $return .= $this->addToken(array('type' => 'row_start'));
            
            // cells are separated by double-pipes
            $cell = explode("||", $row);
            
            // get the last cell number
            $last = count($cell) - 1;
            
            // by default, cells span only one column (their own)
            $span = 1;
            
            // ignore cell zero, and ignore the "last" cell; cell zero
            // is before the first double-pipe, and the "last" cell is
            // after the last double-pipe. both are always empty.
            for ($i = 1; $i < $last; $i ++) {
                
                // if there is no content at all, then it's an instance
                // of two sets of || next to each other, indicating a
                // colspan.
                if ($cell[$i] == '') {
                    
                    // add to the span and loop to the next cell
                    $span += 1;
                    continue;
                    
                } else {
                    
                    // this cell has content.
                    // start a new cell...
                    $return .= $this->addToken(
                        array (
                            'type' => 'cell_start',
                            'colspan' => $span
                        )
                    );
                    
                    // ...add the content...
                    $return .= trim($cell[$i]);
                    
                    // ...and end the cell.
                    $return .= $this->addToken(
                        array (
                            'type' => 'cell_end',
                            'colspan' => $span
                        )
                    );
                    
                    // reset the colspan.
                    $span = 1;
                }
                    
            }
            
            // end the row
            $return .= $this->addToken(array('type' => 'row_end'));
            
        }
        
        // end the table
        $return .= $this->addToken(array('type' => 'table_end'));
        
        // we're done!
        return "\n$return";
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
        // make nice variable names (type, colspan)
        extract($options);
        
        $pad = '    ';
        
        switch ($type) {
        
        case 'table_start':
            return "<table border=\"1\" cellspacing=\"0\" cellpadding=\"4\">\n";
            break;
        
        case 'table_end':
            return "</table>\n";
            break;
        
        case 'row_start':
            return "$pad<tr>\n";
            break;
        
        case 'row_end':
            return "$pad</tr>\n";
            break;
        
        case 'cell_start':
            if ($colspan > 1) {
                return "$pad$pad<td colspan=\"$colspan\">";
            } else {
                return "$pad$pad<td>";
            }
            break;
        
        case 'cell_end':
            return "</td>\n";
            break;
        
        default:
            return '';
        
        }
    }
}
?>