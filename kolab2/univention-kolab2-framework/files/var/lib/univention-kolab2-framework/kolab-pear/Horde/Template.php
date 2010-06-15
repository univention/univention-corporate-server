<?php
/**
 * Horde_Template::
 *
 * Horde Template system. Adapted from bTemplate, by Brian Lozier
 * <brian@massassi.net>.
 *
 * $Horde: framework/Template/Template.php,v 1.31 2004/02/12 21:01:52 chuck Exp $
 *
 * Copyright 2002-2004 Chuck Hagenbuch <chuck@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 * @package Horde_Template
 */
class Horde_Template {

    /**
     * Option values.
     * @var array $_options
     */
    var $_options = array();

    /**
     * Directory that templates should be read from.
     * @var string $_basepath
     */
    var $_basepath = '';

    /**
     * Reset template variables after parsing?
     * @var boolean $_resetVars
     */
    var $_resetVars = true;

    /**
     * Tag (scalar) values.
     * @var array $_scalars
     */
    var $_scalars = array();

    /**
     * Loop tag values.
     * @var array $_arrays
     */
    var $_arrays = array();

    /**
     * Cloop tag values.
     * @var array $_carrays
     */
    var $_carrays = array();

    /**
     * If tag values.
     * @var array $_ifs
     */
    var $_ifs = array();

    /**
     * Constructor. Can set the template base path and whether or not
     * to drop template variables after a parsing a template.
     *
     * @param string  $basepath  (optional) The directory where templates are read from.
     * @param boolean $resetVars (optional) Drop template vars after parsing a template?
     */
    function Horde_Template($basepath = null, $resetVars = true)
    {
        if (!is_null($basepath)) {
            $this->_basepath = $basepath;
        }
        $this->_resetVars = (bool)$resetVars;
    }

    /**
     * Set an option.
     *
     * @param string $option   The option name.
     * @param mixed  $val      The option's value.
     */
    function setOption($option, $val)
    {
        $this->_options[$option] = $val;
    }

    /**
     * Get an option's value.
     *
     * @param string $option   The option name.
     *
     * @return mixed           The option's value.
     */
    function getOption($option)
    {
        return isset($this->_options[$option]) ? $this->_options[$option] : null;
    }

    /**
     * Set a tag, loop, or if variable.
     *
     * @param string  $tag   The tag name
     * @param mixed   $var   The value to replace the tag with.
     * @param boolean $isIf  (optional) Is this for an <if:> tag? (Default: no).
     */
    function set($tag, $var, $isIf = false)
    {
        if (is_array($tag)) {
            foreach ($tag as $tTag => $tVar) {
                $this->set($tTag, $tVar, $isIf);
            }
        } elseif (is_array($var)) {
            $this->_arrays[$tag] = $var;
            if ($isIf) {
                // Just store the same variable that we stored in
                // $this->_arrays - if we don't modify it, PHP's
                // reference counting ensures we're not using any
                // additional memory here.
                $this->_ifs[$tag] = $var;
            }
        } else {
            $this->_scalars[$tag] = $var;
            if ($isIf) {
                // Just store the same variable that we stored in
                // $this->_scalars - if we don't modify it, PHP's
                // reference counting ensures we're not using any
                // additional memory here.
                $this->_ifs[$tag] = $var;
            }
        }
    }

    /**
     * Set values for a cloop.
     *
     * @param string $tag    The name of the cloop.
     * @param array  $array  The values for the cloop.
     * @param array  $cases  The cases (test values) for the cloops.
     */
    function setCloop($tag, $array, $cases)
    {
        $this->_carrays[$tag] = array(
            'array' => $array,
            'cases' => $cases
        );
    }

    /**
     * Reset the template variables.
     *
     * @param boolean $scalars  Reset scalar (basic tag) variables?
     * @param boolean $arrays   Reset loop variables?
     * @param boolean $carrays  Reset cloop variables?
     * @param boolean $ifs      Reset if variables?
     */
    function resetVars($scalars, $arrays, $carrays, $ifs)
    {
        if ($scalars === true) {
            $this->_scalars = array();
        }
        if ($arrays === true) {
            $this->_arrays = array();
        }
        if ($carrays === true) {
            $this->_carrays = array();
        }
        if ($ifs === true) {
            $this->_ifs = array();
        }
    }

    /**
     * Return full start and end tags for a named tag.
     *
     * @param string $tag
     * @param string $directive  The kind of tag - tag, if, loop, cloop.
     *
     * @return array  'b' => Start tag.
     *                'e' => End tag.
     */
    function getTags($tag, $directive)
    {
        return array('b' => '<' . $directive . ':' . $tag . '>',
                     'e' => '</' . $directive . ':' . $tag . '>');
    }

    /**
     * Format a scalar tag (default format is <tag:name>).
     *
     * @param string $tag  The name of the tag.
     *
     * @return string  The full tag with the current start/end delimiters.
     */
    function getTag($tag)
    {
        return '<tag:' . $tag . ' />';
    }

    /**
     * Extract a portion of a template.
     *
     * @param array   $t         The tag to extract. Hash format is:
     *                             $t['b'] - The start tag
     *                             $t['e'] - The tag
     * @param string &$contents  The template to extract from.
     */
    function getStatement($t, &$contents)
    {
        // Locate the statement.
        $tag_length = String::length($t['b']);
        $pos = String::pos($contents, $t['b']);
        if ($pos === false) {
            return false;
        }

        $fpos = $pos + $tag_length;
        $lpos = String::pos($contents, $t['e']);
        $length = $lpos - $fpos;

        // Extract & return the statement.
        return String::substr($contents, $fpos, $length);
    }

    /**
     * Parse all variables/tags in the template.
     *
     * @param string $contents  The unparsed template.
     *
     * @return string  The parsed template.
     */
    function parse($contents)
    {
        // Process ifs.
        if (!empty($this->_ifs)) {
            foreach ($this->_ifs as $tag => $value) {
                $contents = $this->parseIf($tag, $contents);
            }
        }

        // Process tags.
        $search = array();
        $replace = array();
        foreach ($this->_scalars as $key => $value) {
            $search[] = $this->getTag($key);
            $replace[] = $value;
        }
        if (count($search)) {
            $contents = str_replace($search, $replace, $contents);
        }

        // Process loops and arrays.
        foreach ($this->_arrays as $key => $array) {
            $contents = $this->parseLoop($key, $array, $contents);
        }

        // Process cloops.
        foreach ($this->_carrays as $key => $array) {
            $contents = $this->parseCloop($key, $array, $contents);
        }

        // Parse gettext tags, if the option is enabled.
        if ($this->getOption('gettext')) {
            $contents = $this->parseGettext($contents);
        }

        // Reset template data unless we're supposed to keep it
        // around.
        if ($this->_resetVars) {
            $this->resetVars(false, true, true, false);
        }

        // Return parsed template.
        return $contents;
    }

    /**
     * Parse gettext tags.
     *
     * @param string $contents   The unparsed content of the file.
     *
     * @return string            The parsed contents of the gettext blocks.
     */
    function parseGettext($contents)
    {
        // Get the tags & loop.
        $t = array('b' => '<gettext>',
                   'e' => '</gettext>');
        while ($text = $this->getStatement($t, $contents)) {
            $contents = str_replace($t['b'] . $text . $t['e'], _($text), $contents);
        }
        return $contents;
    }

    /**
     * Parse a given if statement.
     *
     * @param string $tag       The name of the if block to parse.
     * @param string $contents  The unparsed contents of the if block.
     *
     * @return string  The parsed contents of the if block.
     */
    function parseIf($tag, $contents, $key = null)
    {
        // Get the tags & if statement.
        $t = $this->getTags($tag, 'if');
        $et = $this->getTags($tag, 'else');

        // explode the tag, so we have the correct keys for the array
        if (isset($key)) {
            list($tg, $k) = explode('.', $tag);
        }
        while ($if = $this->getStatement($t, $contents)) {
            // Check for else statement.
            if ($else = $this->getStatement($et, $if)) {
                // Process the if statement.
                if ((isset($key) && $this->_ifs[$tg][$key][$k]) ||
                    (isset($this->_ifs[$tag]) && $this->_ifs[$tag])) {
                    $replace = str_replace($et['b'] . $else . $et['e'], '', $if);
                } else {
                    $replace = $else;
                }
            } else {
                // Process the if statement.
                if (isset($key)) {
                    $replace = $this->_ifs[$tg][$key][$k] ? $if : null;
                } else {
                    $replace = $this->_ifs[$tag] ? $if : null;
                }
            }

            // Parse the template.
            $contents = str_replace($t['b'] . $if . $t['e'], $replace,
                                    $contents);
        }

        // Return parsed template.
        return $contents;
    }

    /**
     * Parse the given array for any loops or other uses of the array.
     *
     * @param string $tag       The name of the loop to parse.
     * @param array  $array     The values for the loop.
     * @param string $contents  The unparsed contents of the loop.
     *
     * @return string  The parsed contents of the loop.
     */
    function parseLoop($tag, $array, $contents)
    {
        // Get the tags & loop.
        $t = $this->getTags($tag, 'loop');
        $loop = $this->getStatement($t, $contents);

        // See if we have a divider.
        $l = $this->getTags($tag, 'divider');
        $divider = $this->getStatement($l, $loop);
        $contents = str_replace($l['b'] . $divider . $l['e'], '', $contents);

        // Process the array.
        do {
            $parsed = '';
            $first = true;
            foreach ($array as $key => $value) {
                if (is_numeric($key) && is_array($value)) {
                    $i = $loop;
                    foreach ($value as $key2 => $value2) {
                        if (!is_array($value2)) {
                            // Replace associative array tags.
                            $i = str_replace($this->getTag($tag . '.' . $key2), $value2, $i);
                        } else {
                            // Check to see if it's a nested loop.
                            $i = $this->parseLoop($tag . '.' . $key2, $value2, $i);
                        }
                    }
                } elseif (is_string($key) && !is_array($value)) {
                    $contents = str_replace($this->getTag($tag . '.' . $key), $value, $contents);
                } elseif (!is_array($value)) {
                    $i = str_replace($this->getTag($tag . ''), $value, $loop);
                } else {
                    $i = null;
                }

                // Parse conditions in the array.
                if (!empty($this->_ifs[$tag][$key]) && is_array($this->_ifs[$tag][$key]) && count($this->_ifs[$tag][$key])) {
                    foreach ($this->_ifs[$tag][$key] as $cTag => $cValue) {
                        $i = $this->parseIf($tag . '.' . $cTag, $i, $key);
                    }
                }

                // Add the parsed iteration.
                if (isset($i)) {
                    // If it's not the first time through, prefix the
                    // loop divider, if there is one.
                    if (!$first) {
                        $i = $divider . $i;
                    }
                    $parsed .= rtrim($i);
                }

                // No longer the first time through.
                $first = false;
            }

            // Replace the parsed pieces of the template.
            $contents = str_replace($t['b'] . $loop . $t['e'], $parsed, $contents);
        } while ($loop = $this->getStatement($t, $contents));

        return $contents;
    }

    /**
     * Parse the given case loop (cloop).
     *
     * @param string $tag       The name of the cloop to parse.
     * @param array  $array     The values for the cloop.
     * @param string $contents  The unparsed contents of the cloop.
     *
     * @return string  The parsed contents of the cloop.
     */
    function parseCloop($tag, $array, $contents)
    {
        // Get the tags & cloop.
        $t = $this->getTags($tag, 'cloop');

        while ($loop = $this->getStatement($t, $contents)) {
            // Set up the cases.
            $array['cases'][] = 'default';
            $case_content = array();

            // Get the case strings.
            foreach ($array['cases'] as $case) {
                $ctags[$case] = $this->getTags($case, 'case');
                $case_content[$case] = $this->getStatement($ctags[$case], $loop);
            }

            // Process the cloop.
            $parsed = '';
            foreach ($array['array'] as $key => $value) {
                if (is_numeric($key) && is_array($value)) {
                    // Set up the cases.
                    if (isset($value['case'])) {
                        $current_case = $value['case'];
                    } else {
                        $current_case = 'default';
                    }
                    unset($value['case']);
                    $i = $case_content[$current_case];

                    // Loop through each value.
                    foreach ($value as $key2 => $value2) {
                        if (is_array($value2)) {
                            $i = $this->parseLoop($tag . '.' . $key2, $value2, $i);
                        } else {
                            $i = str_replace($this->getTag($tag . '.' . $key2), $value2, $i);
                        }
                    }
                }

                // Add the parsed iteration.
                $parsed .= rtrim($i);
            }

            // Parse the cloop.
            $contents = str_replace($t['b'] . $loop . $t['e'], $parsed, $contents);
        }

        return $contents;
    }

    /**
     * Fetch a template from the specified file and return the parsed
     * contents.
     *
     * @param string $filename  The file to fetch the template from.
     *
     * @return string  The parsed template.
     */
    function fetch($filename)
    {
        // Prepare the path.
        $file = $this->_basepath . $filename;

        // Open the file.
        $fp = @fopen($file, 'rb');
        if (!$fp) {
            return PEAR::raiseError(sprintf(_("Template '%s' not found."), $file));
        }

        // Read the file.
        $contents = fread($fp, filesize($file));

        // Close the file.
        fclose($fp);

        // Parse and return the contents.
        return $this->parse($contents);
    }

}
