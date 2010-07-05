<?php
/**
 * Horde Template system. Adapted from bTemplate by Brian Lozier
 * <brian@massassi.net>.
 *
 * Horde_Template provides a basic template engine with tags, loops,
 * and if conditions. However, it is also a simple interface with
 * several essential functions: set(), fetch(), and
 * parse(). Subclasses or decorators can implement (or delegate) these
 * three methods, plus the options api, and easily implement other
 * template engines (PHP code, XSLT, etc.) without requiring usage
 * changes.
 *
 * Compilation code adapted from code written by Bruno Pedro <bpedro@ptm.pt>.
 *
 * $Horde: ingo/lib/Template.php,v 1.6.2.3 2009-01-06 15:24:35 jan Exp $
 *
 * Copyright 2002-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @author  Michael Slusarz <slusarz@horde.org>
 * @since   Horde 3.0
 * @package Horde_Template
 */

/** The identifier to use for memory-only templates. */
define('INGO_TEMPLATE_STRING', '**string');

class Ingo_Template {

    /**
     * The Horde_Cache object to use.
     *
     * @var Horde_Cache
     */
    var $_cache;

    /**
     * Option values.
     *
     * @var array
     */
    var $_options = array();

    /**
     * Directory that templates should be read from.
     *
     * @var string
     */
    var $_basepath = '';

    /**
     * Tag (scalar) values.
     *
     * @var array
     */
    var $_scalars = array();

    /**
     * Loop tag values.
     *
     * @var array
     */
    var $_arrays = array();

    /**
     * Path to template source.
     *
     * @var string
     */
    var $_templateFile = null;

    /**
     * Template source.
     *
     * @var string
     */
    var $_template = null;

    /**
     * Foreach variable mappings.
     *
     * @var array
     */
    var $_foreachMap = array();

    /**
     * Foreach variable incrementor.
     *
     * @var integer
     */
    var $_foreachVar = 0;

    /**
     * preg_match() cache.
     *
     * @var array
     */
    var $_pregcache = array();

    /**
     * Constructor.
     *
     * @param string $basepath  The directory where templates are read from.
     */
    function Ingo_Template($basepath = null)
    {
        if (!is_null($basepath)) {
            $this->_basepath = $basepath;
        }

        if (!empty($GLOBALS['conf']['cache']['driver'])) {
            require_once 'Horde/Cache.php';
            $this->_cache = &Horde_Cache::singleton($GLOBALS['conf']['cache']['driver'], Horde::getDriverConfig('cache', $GLOBALS['conf']['cache']['driver']));
        }

        // DEBUGGING
        $this->setOption('forcecompile', true);
    }

    /**
     * Sets an option.
     * Currently available options are:
     * <pre>
     * 'debug' - Output debugging information to screen
     * 'forcecompile' - Force a compilation on every page load
     * 'gettext' - Activate gettext detection
     * <pre>
     *
     * @param string $option  The option name.
     * @param mixed $val      The option's value.
     */
    function setOption($option, $val)
    {
        $this->_options[$option] = $val;
    }

    /**
     * Set the template contents to a string.
     *
     * @param string $template  The template text.
     */
    function setTemplate($template)
    {
        $this->_template = $template;
        $this->_parse();
        $this->_templateFile = INGO_TEMPLATE_STRING;
    }

    /**
     * Returns an option's value.
     *
     * @param string $option  The option name.
     *
     * @return mixed  The option's value.
     */
    function getOption($option)
    {
        return isset($this->_options[$option]) ? $this->_options[$option] : null;
    }

    /**
     * Sets a tag, loop, or if variable.
     *
     * @param string|array $tag   Either the tag name or a hash with tag names
     *                            as keys and tag values as values.
     * @param mixed        $var   The value to replace the tag with.
     */
    function set($tag, $var)
    {
        if (is_array($tag)) {
            foreach ($tag as $tTag => $tVar) {
                $this->set($tTag, $tVar);
            }
        } elseif (is_array($var) || is_object($var)) {
            $this->_arrays[$tag] = $var;
        } else {
            $this->_scalars[$tag] = $var;
        }
    }

    /**
     * Returns the value of a tag or loop.
     *
     * @param string $tag  The tag name.
     *
     * @return mixed  The tag value or null if the tag hasn't been set yet.
     */
    function get($tag)
    {
        if (isset($this->_arrays[$tag])) {
            return $this->_arrays[$tag];
        }
        if (isset($this->_scalars[$tag])) {
            return $this->_scalars[$tag];
        }
        return null;
    }

    /**
     * Fetches a template from the specified file and return the parsed
     * contents.
     *
     * @param string $filename  The file to fetch the template from.
     *
     * @return string  The parsed template.
     */
    function fetch($filename = null)
    {
        $file = $this->_basepath . $filename;
        $force = $this->getOption('forcecompile');

        if (!is_null($filename) && ($file != $this->_templateFile)) {
            $this->_template = $this->_templateFile = null;
        }

        /* First, check for a cached compiled version. */
        if (!$force && is_null($this->_template) && isset($this->_cache)) {
            $cacheid = 'horde_template|' . filemtime($file) . '|' . $file;
            $this->_template = $this->_cache->get($cacheid, 0);
            if ($this->_template === false) {
                $this->_template = null;
            }
        }

        /* Parse and compile the template. */
        if ($force || is_null($this->_template)) {
            $this->_template = str_replace("\n", " \n", file_get_contents($file));
            $this->_parse();
            if (isset($cacheid) &&
                !$this->_cache->set($cacheid, $this->_template)) {
                Horde::logMessage(sprintf(_("Could not save the compiled template file '%s'."), $file), __FILE__, __LINE__, PEAR_LOG_ERR);
            }
        }

        $this->_templateFile = $file;

        /* Template debugging. */
        if ($this->getOption('debug')) {
            echo '<pre>' . htmlspecialchars($this->_template) . '</pre>';
        }

        return $this->parse();
    }

    /**
     * Parses all variables/tags in the template.
     *
     * @param string $contents  The unparsed template.
     *
     * @return string  The parsed template.
     */
    function parse($contents = null)
    {
        if (!is_null($contents)) {
            $this->setTemplate(str_replace("\n", " \n", $contents));
        }

        /* Evaluate the compiled template and return the output. */
        ob_start();
        eval('?>' . $this->_template);
        return str_replace(" \n", "\n", ob_get_clean());
    }

    /**
     * Parses all variables/tags in the template.
     */
    function _parse()
    {
        // Escape XML instructions.
        $this->_template = preg_replace('/\?>|<\?/',
                                        '<?php echo \'$0\' ?>',
                                        $this->_template);

        // Parse gettext tags, if the option is enabled.
        if ($this->getOption('gettext')) {
            $this->_parseGettext();
        }

        // Process ifs.
        $this->_parseIf();

        // Process loops and arrays.
        $this->_parseLoop();

        // Process base scalar tags.  Needs to be after _parseLoop() as we
        // rely on _foreachMap().
        $this->_parseTags();

        // Finally, process any associative array scalar tags.
        $this->_parseAssociativeTags();
    }

    /**
     * Parses gettext tags.
     *
     * @access private
     */
    function _parseGettext()
    {
        if (preg_match_all("/<gettext>(.+?)<\/gettext>/s", $this->_template, $matches, PREG_SET_ORDER)) {
            $replace = array();
            foreach ($matches as $val) {
                $replace[$val[0]] = '<?php echo _(\'' . str_replace("'", "\\'", $val[1]) . '\'); ?>';
            }
            $this->_doReplace($replace);
        }
    }

    /**
     * Parses 'if' statements.
     *
     * @access private
     *
     * @param string $key  The key prefix to parse.
     */
    function _parseIf($key = null)
    {
        $replace = array();

        foreach ($this->_doSearch('if', $key) as $val) {
            $replace[$val[0]] = '<?php if (!empty(' . $this->_generatePHPVar('scalars', $val[1]) . ') || !empty(' . $this->_generatePHPVar('arrays', $val[1]) . ')): ?>';
            $replace[$val[2]] = '<?php endif; ?>';

            // Check for else statement.
            foreach ($this->_doSearch('else', $key) as $val2) {
                $replace[$val2[0]] = '<?php else: ?>';
                $replace[$val2[2]] = '';
            }
        }

        $this->_doReplace($replace);
    }

    /**
     * Parses the given array for any loops or other uses of the array.
     *
     * @access private
     *
     * @param string $key  The key prefix to parse.
     */
    function _parseLoop($key = null)
    {
        $replace = array();

        foreach ($this->_doSearch('loop', $key) as $val) {
            $divider = null;

            // See if we have a divider.
            if (preg_match("/<divider:" . $val[1] . ">(.*)<\/divider:" . $val[1] . ">/sU", $this->_template, $m)) {
                $divider = $m[1];
                $replace[$m[0]] = '';
            }

            if (!isset($this->_foreachMap[$val[1]])) {
                $this->_foreachMap[$val[1]] = ++$this->_foreachVar;
            }
            $varId = $this->_foreachMap[$val[1]];
            $var = $this->_generatePHPVar('arrays', $val[1]);

            $replace[$val[0]] = '<?php ' .
                (($divider) ? '$i' . $varId . ' = count(' . $var . '); ' : '') .
                'foreach (' . $this->_generatePHPVar('arrays', $val[1]) . ' as $k' . $varId . ' => $v' . $varId . '): ?>';
            $replace[$val[2]] = '<?php ' .
                (($divider) ? 'if (--$i' . $varId . ' != 0) { echo \'' . $divider . '\'; }; ' : '') .
                'endforeach; ?>';

            // Parse ifs.
            $this->_parseIf($val[1]);

            // Parse interior loops.
            $this->_parseLoop($val[1]);

            // Replace scalars.
            $this->_parseTags($val[1]);
        }

        $this->_doReplace($replace);
    }

    /**
     * Replaces 'tag' tags with their PHP equivalents.
     *
     * @access private
     *
     * @param string $key  The key prefix to parse.
     */
    function _parseTags($key = null)
    {
        $replace = array();

        foreach ($this->_doSearch('tag', $key, true) as $val) {
            $replace_text = '<?php ';
            if (isset($this->_foreachMap[$val[1]])) {
                $var = $this->_foreachMap[$val[1]];
                $replace_text .= 'if (isset($v' . $var . ')) { echo is_array($v' . $var . ') ? $k' . $var . ' : $v' . $var . '; } else';
            }
            $var = $this->_generatePHPVar('scalars', $val[1]);
            $replace[$val[0]] = $replace_text . 'if (isset(' . $var . ')) { echo ' . $var . '; } ?>';
        }

        $this->_doReplace($replace);
    }

    /**
     * Parse associative tags (i.e. <tag:foo.bar />).
     *
     * @access private
     */
    function _parseAssociativeTags()
    {
        $replace = array();

        foreach ($this->_pregcache['tag'] as $key => $val) {
            $parts = explode('.', $val[1]);
            $var = '$this->_arrays[\'' . $parts[0] . '\'][\'' . $parts[1] . '\']';
            $replace[$val[0]] = '<?php if (isset(' . $var . ')) { echo ' . $var . '; } ?>';
            unset($this->_pregcache['tag'][$key]);
        }

        $this->_doReplace($replace);
    }

    /**
     * Output the correct PHP variable string for use in template space.
     *
     * @access private
     */
    function _generatePHPVar($tag, $key)
    {
        $out = '';

        $a = explode('.', $key);
        $a_count = count($a);

        if ($a_count == 1) {
            switch ($tag) {
            case 'arrays':
                $out = '$this->_arrays';
                break;

            case 'scalars':
                $out = '$this->_scalars';
                break;
            }
        } else {
            $out = '$v' . $this->_foreachMap[implode('.', array_slice($a, 0, -1))];
        }

        return $out . '[\'' . end($a) . '\']';
    }

    /**
     * TODO
     *
     * @access private
     */
    function _doSearch($tag, $key, $noclose = false)
    {
        $out = array();
        $level = (is_null($key)) ? 0 : substr_count($key, '.') + 1;

        if (!isset($this->_pregcache[$key])) {
            $regex = ($noclose) ?
                "/<" . $tag . ":(.+?)\s\/>/" :
                "/<" . $tag . ":([^>]+)>/";
            preg_match_all($regex, $this->_template, $this->_pregcache[$tag], PREG_SET_ORDER);
        }

        foreach ($this->_pregcache[$tag] as $pkey => $val) {
            $val_level = substr_count($val[1], '.');
            $add = false;
            if (is_null($key)) {
                $add = !$val_level;
            } else {
                $add = (($val_level == $level) &&
                        (strpos($val[1], $key . '.') === 0));
            }
            if ($add) {
                if (!$noclose) {
                    $val[2] = '</' . $tag . ':' . $val[1] . '>';
                }
                $out[] = $val;
                unset($this->_pregcache[$tag][$pkey]);
            }
        }

        return $out;
    }

    /**
     * TODO
     *
     * @access private
     */
    function _doReplace($replace)
    {
        if (empty($replace)) {
            return;
        }

        $search = array();

        foreach (array_keys($replace) as $val) {
            $search[] = '/' . preg_quote($val, '/') . '/';
        }

        $this->_template = preg_replace($search, array_values($replace), $this->_template);
    }

}
