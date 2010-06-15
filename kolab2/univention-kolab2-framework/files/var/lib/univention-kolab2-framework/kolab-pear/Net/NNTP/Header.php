<?php
// +-----------------------------------------------------------------------+
// |                                                                       |
// | Copyright © 2003 Heino H. Gehlsen. All Rights Reserved.               |
// |                  http://www.heino.gehlsen.dk/software/license         |
// |                                                                       |
// +-----------------------------------------------------------------------+
// |                                                                       |
// | This work (including software, documents, or other related items) is  |
// | being provided by the copyright holders under the following license.  |
// | By obtaining, using and/or copying this work, you (the licensee)      |
// | agree that you have read, understood, and will comply with the        |
// | following terms and conditions:                                       |
// |                                                                       |
// | Permission to use, copy, modify, and distribute this software and     |
// | its documentation, with or without modification, for any purpose and  |
// | without fee or royalty is hereby granted, provided that you include   |
// | the following on ALL copies of the software and documentation or      |
// | portions thereof, including modifications, that you make:             |
// |                                                                       |
// | 1. The full text of this NOTICE in a location viewable to users of    |
// |    the redistributed or derivative work.                              |
// |                                                                       |
// | 2. Any pre-existing intellectual property disclaimers, notices, or    |
// |    terms and conditions. If none exist, a short notice of the         |
// |    following form (hypertext is preferred, text is permitted) should  |
// |    be used within the body of any redistributed or derivative code:   |
// |    "Copyright © 2003 Heino H. Gehlsen. All Rights Reserved.           |
// |     http://www.heino.gehlsen.dk/software/license"                     |
// |                                                                       |
// | 3. Notice of any changes or modifications to the files, including     |
// |    the date changes were made. (We recommend you provide URIs to      |
// |    the location from which the code is derived.)                      |
// |                                                                       |
// | THIS SOFTWARE AND DOCUMENTATION IS PROVIDED "AS IS," AND COPYRIGHT    |
// | HOLDERS MAKE NO REPRESENTATIONS OR WARRANTIES, EXPRESS OR IMPLIED,    |
// | INCLUDING BUT NOT LIMITED TO, WARRANTIES OF MERCHANTABILITY OR        |
// | FITNESS FOR ANY PARTICULAR PURPOSE OR THAT THE USE OF THE SOFTWARE    |
// | OR DOCUMENTATION WILL NOT INFRINGE ANY THIRD PARTY PATENTS,           |
// | COPYRIGHTS, TRADEMARKS OR OTHER RIGHTS.                               |
// |                                                                       |
// | COPYRIGHT HOLDERS WILL NOT BE LIABLE FOR ANY DIRECT, INDIRECT,        |
// | SPECIAL OR CONSEQUENTIAL DAMAGES ARISING OUT OF ANY USE OF THE        |
// | SOFTWARE OR DOCUMENTATION.                                            |
// |                                                                       |
// | The name and trademarks of copyright holders may NOT be used in       |
// | advertising or publicity pertaining to the software without specific, |
// | written prior permission. Title to copyright in this software and any |
// | associated documentation will at all times remain with copyright      |
// | holders.                                                              |
// |                                                                       |
// +-----------------------------------------------------------------------+
// |                                                                       |
// | This license is based on the "W3C® SOFTWARE NOTICE AND LICENSE".      |
// | No changes have been made to the "W3C® SOFTWARE NOTICE AND LICENSE",  |
// | except for the references to the copyright holder, which has either   |
// | been changes or removed.                                              |
// |                                                                       |
// +-----------------------------------------------------------------------+
// $Id: Header.php,v 1.1.2.1 2005/10/05 14:39:47 steuwer Exp $

require_once 'PEAR.php';


define('NET_NNTP_HEADER_SET_UNFOLD', 1);
define('NET_NNTP_HEADER_SET_DECODE', 2);
define('NET_NNTP_HEADER_SET_CLEAN', 4);
define('NET_NNTP_HEADER_SET_KEEPCASE', 8);
define('NET_NNTP_HEADER_SET_DEFAULT', NET_NNTP_HEADER_SET_CLEAN | NET_NNTP_HEADER_SET_UNFOLD | NET_NNTP_HEADER_SET_DECODE);

define('NET_NNTP_HEADER_GET_FOLD', 1);
define('NET_NNTP_HEADER_GET_ENCODE', 2);
define('NET_NNTP_HEADER_GET_DEFAULT', NET_NNTP_HEADER_GET_ENCODE | NET_NNTP_HEADER_GET_FOLD);


/**
 * The Net_NNTP_Header class
 *
 * @version $Revision: 1.1.2.1 $
 * @package Net_NNTP
 *
 * @author Heino H. Gehlsen <heino@gehlsen.dk>
 */
class Net_NNTP_Header
{
    // {{{ properties

    /**
     * Container for the header fields
     *
     * @var    array
     * @access public
     */
    var $fields;

    // }}}
    // {{{ constructor

    /**
     * Constructor
     *
     * @access public
     * @since 0.1
     */
    function Net_NNTP_Header()
    {
	// Reset object
	$this->reset();
    }

    // }}}
    // {{{ reset()
    
    /**
     * Reset the field container
     * 
     * @access public
     * @since 0.1
     */
    function reset()
    {
	$this->fields = array();
    }

    // }}}
    // {{{ create()
    
    /**
     * Create a new instance of Net_NNTP_Header
     *
     * @param optional mixed $input Can be any of the following:
     * 	   	                    (string) RFC2822 style header lines (CRLF included)
     *                              (array)  RFC2822 style header lines (CRLF not included)
     *                              (object) Net_NNTP_Header object
     *                              (object) Net_NNTP_Message object
     * 
     * @return object Net_NNTP_Header object
     * @access public
     * @since 0.1
     */
    function & create($input = null)
    {
	switch (true) {

	    // Null
	    case is_null($input);
		$Object = new Net_NNTP_Header();
	        return $Object;
		break;

	    // Object
	    case is_object($input);
		switch (true) {
		    
		    // Header
		    case is_a($input, 'net_nntp_header'):
			return $input;
			break;
			
		    // Message
		    case is_a($input, 'net_nntp_message'):
			return $input->getHeader();
			break;
			
		    // Unknown object/class
		    default:
			return PEAR::throwError('Unsupported object/class: '.get_class($input), null);
		}
		break;

	    // String & Array
	    case is_string($input);
	    case is_array($input);
	        $Object = new Net_NNTP_Header();
		$R = $Object->setFields($input);
		if (PEAR::isError($R)) {
		    return $R;
		}
		return $Object;
		break;

	    // Unknown type
	    default:
		return PEAR::throwError('Unsupported object/class: '.get_class($input), null);
	}
    }

    // }}}
    // {{{ add()
    
    /**
     * Add a new field
     * 
     * @param string $tag
     * @param string $value
     * @param optional int $index
     * 
     * @access public
     * @since 0.1
     */
    function add($tag, $value, $index = null)
    {
	// Add header to $return array
    	if (isset($this->fields[$tag]) && is_array($this->fields[$tag])) {
	    // The header name has already been used at least two times.
            $this->fields[$tag][] = $value;
        } elseif (isset($this->fields[$tag])) {
	    // The header name has already been used one time -> change to nedted values.
            $this->fields[$tag] = array($this->fields[$tag], $value);
        } else {
	    // The header name has not used until now.
	    $this->fields[$tag] = $value;
        }
    }

    // }}}
    // {{{ replace()
    
    /**
     * Replace a field's value
     * 
     * @param string $tag
     * @param string $value
     * @param optional int $index
     * 
     * @access public
     * @since 0.1
     */
    function replace($tag, $value, $index = null)
    {
	if (isset($this->fields[$tag])) {
	    if ($index === null) {
		$this->fields[$tag] = $value;
	    } else {
		if (is_array($this->fields[$tag])) {
		    $this->fields[$tag][$index] = $value;
		} else {
//TODO: Currently ignores $index, and just replaces the value
		    $this->fields[$tag] = $value;
		}
	    }
	} else {
	    $this->fields[$tag] = $value;
	}
    }

    // }}}
    // {{{ delete()
    
    /**
     * Delete a field
     * 
     * @param string $tag
     * @param optional int $index
     * 
     * @access public
     * @since 0.1
     */
    function delete($tag, $index = null)
    {
	if (isset($this->fields[$tag])) {
	    if ($index == null) {
		unset($this->fields[$tag]);
	    } else {
		if (is_array($this->fields[$tag])) {
		    unset($this->fields[$tag][$index]);
		} else {
		    unset($this->fields[$tag]);
		}
	    }
	} else {
	    // Do nothing...
	}
    }

    // }}}
    // {{{ get()
    
    /**
     * Gets the value of a header field
     * 
     * @param string $tag
     * @param optional int $index (defaults to 0)
     * 
     * @return string
     * @access public
     * @since 0.1
     */
    function get($tag, $index = 0)
    {
	if (!isset($this->fields[$tag])) {
	    return null;
	}

	if (is_array($this->fields[$tag])) {
	    return $this->fields[$tag][$index];
	} else {
	    if ($index == 0) {
		return $this->fields[$tag];
	    } else {
	        return null;
	    }
	}
    }

    // }}}
    // {{{ getAll()
    
    /**
     * Gets the values of a all occurences of a field
     * 
     * @param string $tag
     * @param optional int $index
     * 
     * @return array
     * @access public
     * @since 0.1
     */
    function getAll($tag)
    {
	if (!isset($this->fields[$tag])) {
	    array();
	}

	if (is_array($this->fields[$tag])) {
	    return $this->fields[$tag];
	} else {
// TODO: What to do, when not array but index is set...
	    return array($this->fields[$tag]);
	}
    }

    // }}}
    // {{{ count()
    
    /**
     * Returns the number of times the given field tag appears in the header.
     * 
     * @param string $tag
     * 
     * @return int
     * @access public
     * @since 0.1
     */
    function count($tag)
    {
	if (!isset($this->fields[$tag])) {
	    return 0;
	}

	if (is_array($this->fields[$tag])) {
	    return count($this->fields[$tag]);
	} else {
	    return 1;
	}
    }

    // }}}
    // {{{ tags()
    
    /**
     * Returns an array of all the tags that exist in the header.
     * Each tag will only appear in the list once.
     * 
     * @return array
     * @access public
     * @since 0.1
     */
    function tags()
    {
	return array_keys($this->fields);
    }

    // }}}
    // {{{ clean()
    
    /**
     * Remove any header field that only contains whitespace.
     * 
     * @access public
     * @since 0.1
     */
    function clean()
    {
	foreach (array_keys($this->fields) as $tag) {
	    if (is_array($this->fields[$tag])) {
		foreach (array_keys($this->fields[$tag]) as $i) {
		    if (trim($this->fields[$tag][$i]) == '') {
			unset($this->fields[$tag][$i]);
		    }
		}
	    } else {
		if (trim($this->fields[$tag]) == '') {
		    unset($this->fields[$tag]);
		}
	    }
	}
    }

    // }}}
    // {{{ setFields()
    
    /**
     * Import RFC2822 style header lines given in $input into the object
     * 
     * @param mixed $input Can be any of the following:
     * 	 	           (string) RFC2822 style header lines (CRLF included)
     *                     (array)  RFC2822 style header lines (CRLF not included)
     *                     (object) Net_NNTP_Header object
     *                     (object) Net_NNTP_Message object
     * @param optional $flags
     * 
     * @access public
     * @since 0.1
     */
    function setFields(&$input, $flags = NET_NNTP_HEADER_SET_DEFAULT)
    {
	switch (true) {

	    // Object
	    case is_object($input):
		switch (true) {
		    case is_a($input, 'net_nntp_header'):
			$this =& $input;
			break;
		    
		    case is_a($input, 'net_nntp_message'):
			$this =& $input->getHeader();
			break;
		    
		    // Unknown type
		    default:
			return PEAR::throwError('Unsupported object/class: '.get_class($input), null);
		}
		break;

	    // String
	    case is_string($input):
		$this->fields = $this->_parseString($input, $flags);
		break;

	    // Array
	    case is_array($input):
		$this->fields = $this->_parseArray($input, $flags);
		break;

	    // Unknown type
	    default:
		return PEAR::throwError('Unsupported type: '.gettype($input), null);
	}
    }

    // }}}
    // {{{ getFields()

    /**
     * Get the array of header fields.
     * 
     * @param optional $flags
     *
     * @return array
     * @access public
     * @since 0.1
     */
    function getFields()
    {
	return $this->fields;
    }

    // }}}
    // {{{ getFieldsString()

    /**
     * Export a string of RFC2822 style header style lines from the object.
     * 
     * @param optional $flags
     *
     * @return string RFC2822 style header lines (CRLF included)
     * @access public
     * @since 0.1
     */
    function getFieldsString($flags = NET_NNTP_HEADER_GET_DEFAULT)
    {
	return $this->_regenerateString($this->fields, $flags);
    }

    // }}}
    // {{{ getFieldsArray()

    /**
     * Export an array of RFC2822 style header style lines from the object.
     *
     * @param optional $flags
     *
     * @return array RFC2822 style header lines (CRLF not included)
     * @access public
     * @since 0.1
     */
    function getFieldsArray($flags = NET_NNTP_HEADER_GET_DEFAULT)
    {
	return $this->_regenerateArray($this->fields, $flags);
    }

    // }}}
    // {{{ _parseString()
    
    /**
     * Parse a string of RFC2822 style header lines into a 'header array' with the header names as keys.
     * 
     * @param string $string RFC2822 style header lines (CRLF included)
     * @param optional $flags
     * 
     * @return array 'header array' with the header names as keys, values may be nested.
     * @access private
     * @since 0.1
     */
    function _parseString($string, $flags)
    {
    	// Clean the header lines
	if (($flags & NET_NNTP_HEADER_SET_CLEAN) == NET_NNTP_HEADER_SET_CLEAN) {
	    $string = $this->cleanString($string);
	}

    	// Unfold the header lines
	if (($flags & NET_NNTP_HEADER_SET_UNFOLD) == NET_NNTP_HEADER_SET_UNFOLD) {
	    $string = $this->unfoldString($string);
	}

	// Convert to array
	$array = explode("\r\n", $string);

	// Remove body if present
	$i = array_search('', $array);
	if ($i != null) {
	    array_splice($array, $i, (count($array))-$i);
	}

	// Forward to _parse()
	return $this->_parse($array, $flags);
    }

    // }}}
    // {{{ _parseArray()

    /**
     * Parse an array of RFC2822 style header lines into a 'header array' with the header names as keys.
     * 
     * @param array $array RFC2822 style header lines (CRLF not included)
     * @param optional $flags
     *
     * @return array 'header array' with the header names as keys, values may be nested.
     * @access private
     * @since 0.1
     */
    function _parseArray($array, $flags)
    {
    	// Clean the header lines
	if (($flags & NET_NNTP_HEADER_SET_CLEAN) == NET_NNTP_HEADER_SET_CLEAN) {
	    $array = $this->cleanArray($array);
	}

    	// Unfold the header lines
	if (($flags & NET_NNTP_HEADER_SET_UNFOLD) == NET_NNTP_HEADER_SET_UNFOLD) {
	    $array = $this->unfoldArray($array);
	}

	// Remove body if present
	$i = array_search('', $array);
	if ($i != null) {
	    array_splice($array, $i, count($array)-$i);
	}

	// Forward to _parse()
	return $this->_parse($array, $flags);
    }

    // }}}
    // {{{ _parse()

    /**
     * Parse a cleaned and unfolded array of RFC2822 style header lines into a 'header array' with the header names as keys.
     * When header names a'pear more the once, the resulting array will have the values nested in the order of a'pear'ence.
     * 
     * @param array $array RFC2822 style header lines (CRLF not included)
     * @param optional $flags
     *
     * @return array 'header array' with the header names as keys, values may be nested.
     * @access private
     * @since 0.1
     */
    function _parse($array, $flags)
    {
	// Init return variable
	$return = array();

	// Loop through all headers
        foreach ($array as $field) {
	    // Separate header name and value
	    if (!preg_match('/([\S]+)\:\s*(.*)\s*/', $field, $matches)) {
		// Fail...
	    }
	    $name = $matches[1];
	    $value = $matches[2];
	    unset($matches);

	    // Change header name to lower case
	    if (($flags & NET_NNTP_HEADER_SET_KEEPCASE) != NET_NNTP_HEADER_SET_KEEPCASE) {
 		$name = strtolower($name);
	    }
	    
	    // Decode header value acording to RFC 2047
	    if (($flags & NET_NNTP_HEADER_SET_DECODE) == NET_NNTP_HEADER_SET_UNFOLD) {
		$value = $this->decodeString($value);
	    }
	    
	    // Add header to $return array
    	    if (isset($return[$name]) AND is_array($return[$name])) {
		// The header name has already been used at least two times.
            	$return[$name][] = $value;
            } elseif (isset($return[$name])) {
		// The header name has already been used one time -> change to nedted values.
            	$return[$name] = array($return[$name], $value);
            } else {
		// The header name has not used until now.
        	$return[$name] = $value;
            }
        }

        return $return;
    }

    // }}}
    // {{{ _regenerateString()
    
    /**
     * Generate a string of RFC2822 style header lines from the 'header array' given in $array.
     * 
     * @param array $array RFC2822 style header lines
     * @param optional $flags
     *
     * @return string RFC822 style header lines (CRLF included).
     * @access private
     * @since 0.1
     */
    function _regenerateString($array, $flags)
    {
	// ( Forward to _regenerateArray() and then convert to string )
	return implode("\r\n", $this->_regenerateArray($array, $flags));
    }

    // }}}
    // {{{ _regenerateArray()

    /**
     * Generate an array of RFC2822 style header lines from the array given in $array.
     *
     * @param array $array 'header field array'
     * @param optional $flags
     *
     * @return array RFC822 style header lines (CRLF not included).
     * @access private
     * @since 0.1
     */
    function _regenerateArray($array, $flags)
    {
	// Init return variable
	$return = array();

	// Loop through headers
        foreach ($array as $name => $value) {
	    // Encode header values acording to RFC 2047
	    if (($flags & NET_NNTP_HEADER_GET_ENCODE) == NET_NNTP_HEADER_GET_ENCODE) {
		if (is_array($value)) {
		    foreach(array_keys($value) as $key) {
			$value[$key] = $this->encodeString($value[$key]);
		    }
		} else {
		    $value = $this->encodeString($value);
		}
	    }

	    if (is_array($value)) {
    		foreach ($value as $sub_value) {
        	    $return[] = $name.': '.$sub_value;
		}
	    } else {
        	$return[] = $name.': '.$value;
	    }
        }

	// Fold headers
	if (($flags & NET_NNTP_HEADER_GET_FOLD) == NET_NNTP_HEADER_GET_FOLD) {
	    $return = $this->foldArray($return);
	}

        return $return;
    }

    // }}}
    // {{{ unfoldString()

    /**
     * Do the (RFC822 3.1.1) header unfolding to a string of RFC2822 header lines.
     * 
     * @param string $string RFC2822 header lines to unfolded (CRLF included)
     *
     * @return string Unfolded RFC2822 header lines (CRLF included)
     * @access public
     * @since 0.1
     */
    function unfoldString($string)
    {
	// Correct \r to \r\n
    	$string = preg_replace("/\r?\n/", "\r\n", $string);

	// Unfold multiline headers
    	$string = preg_replace("/\r\n(\t| )+/", ' ', $string);

	return $string;
    }

    // }}}
    // {{{ unfoldArray()

    /**
     * Do the (RFC822 3.1.1) header unfolding to an array of RFC2822 header lines.
     *
     * @param array $array RFC2822 header lines to unfolded (CRLF not included)
     *
     * @return array Unfolded RFC2822 header lines (CRLF not included)
     * @access public
     * @since 0.1
     */
    function unfoldArray($array)
    {
	// Unfold multiline headers
	for ($i = count($array)-1; $i>0; $i--) {

	    // Check for leading whitespace
	    if (preg_match('/^(\x09|\x20)/', $array[$i])) {
		    
	        // Remove folding \r\n
    	        if (substr($array[$i-1], -2) == "\r\n") {
	            $array[$i-1] = substr($array[$i-1], 0, -2);
    	        }
			
	        // Append folded line to prev line
	        $array[$i-1] = $array[$i-1].' '.ltrim($array[$i], " \t");
			
	        // Remove folded line
		array_splice($array, $i, 1);
	    }
	}

	return $array;
    }

    // }}}
    // {{{ foldArray()

    /**
     * Folds an array of RFC2822 style header lines.
     *
     * @param array $array
     * @param optional int $maxlen
     *
     * @return array 
     * @access public
     * @since 0.1
     */
    function foldArray($array, $maxlen = 78)
    {
	$return = array();

	foreach (array_keys($array) as $key) {
	    $tmp = $this->_foldExplode($array[$key], $maxlen);
	    $prepend = '';
	    foreach (array_keys($tmp) as $key2) {
		$return[] = $prepend.$tmp[$key2];
		$prepend = "\t";
	    }
	}

	return $return;	
    }

    // }}}
    // {{{ foldString()

    /**
     * Folds a string by inserting CRLF's and TAB's where allowed
     *
     * @param string $string
     * @param optional int $maxlen
     *
     * @return string 
     * @access public
     * @since 0.1
     */
    function foldString($string, $maxlen = 78)
    {
	$array = $this->_foldExplode($string, $maxlen);
	$return = implode("\r\n\t", $array);
	return $return;
    }

    // }}}
    // {{{ _foldExplode()

    /**
     * Unfold $string, and return a 'folded' array
     *
     * The current implementation is still experimental, and is NOT expected to comply with RFC2822 !!!
     *
     * @param string $string
     * @param optional int $maxlen
     *
     * @return array
     * @access private
     * @since 0.1
     */
    function _foldExplode($string, $maxlen = 78)
//TODO:
    {
	if ($maxlen < 20) {
	    $maxlen = 20;
	}

	if ($maxlen > 998) {
	    $maxlen = 998;
	}

	if (strlen($string) <= $maxlen) {
	    return array($string);
    	}
      
	$min = (int) ($maxlen * (2/5)) - 4;
        $max = $maxlen - 5;                   // 4 for leading spcs + 1 for [\,\;]

	// try splitting at ',' or ';'   >2/5 along the line
        // Split the line up
	// next split a whitespace
	// else we are looking at a single word and probably don't want to split
	$exp = array();
        $exp[] = "[^\"]\{$min,$max}?[\,\;]\s";
        $exp[] = "[^\"]\{1,$max}\s";
        $exp[] = "[^\s\"]*(?:\"[^\"]*\"[^\s\"]*)+\s";
	$exp[] = "[^\s\"]+\s";

	$exp ="/^\s*(".implode('|', $exp).")(.*)\$/x";
	$tmp = $string;
	$return = array();

	while ((strlen($tmp) > $max) && (preg_match($exp, $tmp, $match))) {
	    $return[] = $match[1];
	    $tmp = $match[2];
	}

	$return[] = $tmp;
	
	return $return;
    }

    // }}}
    // {{{ decodeString()

    /**
     * Given a header/string, this function will decode it according to RFC2047.
     * Probably not *exactly* conformant, but it does pass all the given
     * examples (in RFC2047).
     * 
     * @param string $input Input header value to decode
     *
     * @return string Decoded header value
     * @access public
     * @since 0.1
     */
    function decodeString($input)
    {
        // Remove white space between encoded-words
        $input = preg_replace('/(=\?[^?]+\?(q|b)\?[^?]*\?=)(\s)+=\?/i', '\1=?', $input);

        // For each encoded-word...
        while (preg_match('/(=\?([^?]+)\?(q|b)\?([^?]*)\?=)/i', $input, $matches)) {

            $encoded  = $matches[1];
            $charset  = $matches[2];
            $encoding = $matches[3];
            $text     = $matches[4];

            switch (strtolower($encoding)) {

                case 'b': // RFC2047 4.1
                    $text = base64_decode($text);
                    break;

                case 'q': // RFC2047 4.2
                    $text = str_replace('_', ' ', $text);
                    preg_match_all('/=([a-f0-9]{2})/i', $text, $matches);
                    foreach($matches[1] as $value)
                        $text = str_replace('='.$value, chr(hexdec($value)), $text);
                    break;
            }

            $input = str_replace($encoded, $text, $header);
        }

        return $input;
    }

    // }}}
    // {{{ encodeString()

    /**
     * Encodes the string given in $string as per RFC2047
     * 
     * @param string $string The string to encode
     *
     * @return string Encoded string
     * @access public
     * @since 0.1
     */
    function encodeString($string)
    {
	// TODO: could be better! (Look into CPAN's Encode::MIME::Header)
	
	$charset = 'iso-8859-1';
	
        preg_match_all('/(\w*[\x80-\xFF]+\w*)/', $string, $matches);
	foreach ($matches[1] as $value) {
            $replacement = preg_replace('/([\x80-\xFF])/e', '"=" . strtoupper(dechex(ord("\1")))', $value);
            $string = str_replace($value, '=?' . $charset . '?Q?' . $replacement . '?=', $string);
        }
            
        return $string;
    }

    // }}}
    // {{{ cleanString()

    /**
     * Removes CRLF and misplaced empty lines before and after actual headerlines.
     * 
     * @param string $string.
     *
     * @return string 
     * @access public
     * @since 0.1
     */
    function cleanString($string)
    {
	// Correct missing CR's before LF's
        $string = preg_replace("!\r?\n!", "\r\n", $string);

	// Remove empty lines from start and end.
	// TODO: This should be done better...
	$string = trim($string, "\r\n");

        return $string;
    }

    // }}}
    // {{{ cleanArray()

    /**
     * Removes CRLF and misplaced empty lines before and after actual headerlines.
     * 
     * @param array $input 
     *
     * @return array
     * @access public
     * @since 0.1
     */
    function cleanArray($input)
    {
	// Remove empty lines from the start
	while (reset($input) == "\r\n") {
	    array_shift($input);
	}
	// Remove empty lines from the end
	while (end($input) == "\r\n") {
	    array_pop($input);
	}

	// Run backwards through all lines
	for ($i = count($input)-1; $i > 0; $i--) {

	    // Remove \r\n from the end
	    $input = preg_replace("/\r?\n$/", '', $input);
	}

        return $input;
    }

    // }}}

}

?>
