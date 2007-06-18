<?php

/** @constant HELP_SOURCE_RAW Raw help in the string. */
define('HELP_SOURCE_RAW', 0);

/** @constant HELP_SOURCE_FILE Help text is in a file. */
define('HELP_SOURCE_FILE', 1);

/** @constant HELP_SOURCE_DB Help comes from a database. */
define('HELP_SOURCE_DB', 2);

/**
 * The Help:: class provides an interface to the online help subsystem.
 *
 * $Horde: framework/Horde/Horde/Help.php,v 1.57 2004/04/07 14:43:08 chuck Exp $
 *
 * Copyright 1999-2004 Jon Parise <jon@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Jon Parise <jon@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 1.3
 * @package Horde_Framework
 */
class Help {

    /**
     * Handle for the XML parser object.
     *
     * @var object $_parser
     */
    var $_parser = 0;

    /**
     * String buffer to hold the XML help source.
     *
     * @var string $_buffer
     */
    var $_buffer = '';

    /**
     * String containing the ID of the requested help entry.
     *
     * @var string $_reqEntry
     */
    var $_reqEntry = '';

    /**
     * String containing the ID of the current help entry.
     *
     * @var string $_curEntry
     */
    var $_curEntry = '';

    /**
     * String containing the formatted output.
     *
     * @var string $_output
     */
    var $_output = '';

    /**
     * Boolean indicating whether we're inside a <help> block.
     *
     * @var boolean $_inHelp
     */
    var $_inHelp = false;

    /**
     * Boolean indicating whether we're inside the requested block.
     *
     * @var boolean $_inBlock
     */
    var $_inBlock = false;

    /**
     * Boolean indicating whether we're inside a <title> block.
     *
     * @var boolean $_inTitle
     */
    var $_inTitle = false;

    /**
     * Hash containing an index of all of the help entries.
     *
     * @var array $_entries
     */
    var $_entries = array();

    /**
     * String containing the charset of the XML data source.
     *
     * @var string $_charset
     */
    var $_charset = 'iso-8859-1';

    /**
     * Hash of user-defined function handlers for the XML elements.
     *
     * @var array $_handlers
     */
    var $_handlers = array(
        'help'     =>  '_helpHandler',
        'entry'    =>  '_entryHandler',
        'title'    =>  '_titleHandler',
        'heading'  =>  '_headingHandler',
        'para'     =>  '_paraHandler',
        'ref'      =>  '_refHandler',
        'eref'     =>  '_erefHandler',
        'href'     =>  '_hrefHandler',
        'b'        =>  '_bHandler',
        'i'        =>  '_iHandler',
    );


    /**
     * Constructor
     *
     * @access public
     *
     * @param integer $source       The source of the XML help data, based
     *                              on the HELP_SOURCE_* constants.
     * @param optional string $arg  Source-dependent argument for this Help
     *                              instance.
     */
    function Help($source, $arg = null)
    {
        global $language, $nls;

        if (!Util::extensionExists('xml')) {
            Horde::fatal(PEAR::raiseError('The XML functions are not available. Rebuild PHP with --with-xml.'), __FILE__, __LINE__, false);
        }

        $this->_charset = array_key_exists($language, $nls['charsets']) ? $nls['charsets'][$language] : $nls['defaults']['charset'];

        /* Populate $this->_buffer based on $source. */
        switch ($source) {
        case HELP_SOURCE_RAW:
            $this->_buffer = $arg;
            break;

        case HELP_SOURCE_FILE:
            if (!(@file_exists($arg[0]) && ($fp = @fopen($arg[0], 'r')) && ($fs = @filesize($arg[0])) ||
                 @file_exists($arg[1]) && ($fp = @fopen($arg[1], 'r')) && ($fs = @filesize($arg[1])))) {
                $this->_buffer = '';
            } else {
                $this->_buffer = fread($fp, $fs);
                fclose($fp);
            }
            break;

        default:
            $this->_buffer = '';
            break;
        }
    }

    /**
     * Initialzes the XML parser.
     *
     * @access private
     *
     * @return boolean  Returns true on success, false on failure.
     */
    function _init()
    {
        /* Create a new parser and set its default properties. */
        $this->_parser = xml_parser_create();
        xml_set_object($this->_parser, $this);
        xml_parser_set_option($this->_parser, XML_OPTION_CASE_FOLDING, false);
        xml_set_element_handler($this->_parser, '_startElement', '_endElement');
        xml_set_character_data_handler($this->_parser, '_defaultHandler');

        return ($this->_parser != 0);
    }

    /**
     * Cleans up the Help class resources.
     *
     * @access public
     *
     * @return boolean  Returns true on success, false on failure.
     */
    function cleanup()
    {
        $this->_buffer = '';
        return xml_parser_free($this->_parser);
    }

    /**
     * Looks up the requested entry in the XML help buffer.
     *
     * @access public
     *
     * @param string $entry  String containing the entry ID.
     */
    function lookup($entry)
    {
        $this->_output = '';
        $this->_reqEntry = String::upper($entry);
        if (!$this->_parser) {
            $this->_init();
        }
        xml_parse($this->_parser, $this->_buffer, true);
    }

    /**
     * Returns a hash of all of the topics in this help buffer.
     *
     * @access public
     *
     * @return array  Hash of all of the topics in this buffer.
     */
    function topics()
    {
        if (!$this->_parser) {
            $this->_init();
        }
        xml_parse($this->_parser, $this->_buffer, true);

        return $this->_entries;
    }

    /**
     * Display the contents of the formatted output buffer.
     *
     * @access public
     */
    function display()
    {
        echo $this->_output;
    }

    /**
     * User-defined function callback for start elements.
     *
     * @access private
     *
     * @param object $parser  Handle to the parser instance.
     * @param string $name    The name of this XML element.
     * @param array $attrs    List of this element's attributes.
     */
    function _startElement($parser, $name, $attrs)
    {
        /* Call the assigned handler for this element, if one is
         * available. */
        if (in_array($name, array_keys($this->_handlers))) {
            call_user_func(array(&$this, $this->_handlers[$name]), true, $attrs);
        }
    }

    /**
     * User-defined function callback for end elements.
     *
     * @access private
     *
     * @param object $parser  Handle to the parser instance.
     * @param string $name    The name of this XML element.
     */
    function _endElement($parser, $name)
    {
        /* Call the assigned handler for this element, if one is available. */
        if (in_array($name, array_keys($this->_handlers))) {
            call_user_func(array(&$this, $this->_handlers[$name]), false);
        }
    }

    /**
     * User-defined function callback for character data.
     *
     * @access private
     *
     * @param object $parser  Handle to the parser instance.
     * @param string $data    String of character data.
     */
    function _defaultHandler($parser, $data)
    {
        $data = String::convertCharset($data, $this->_charset);
        if ($this->_inTitle) {
            $this->_entries[$this->_curEntry] .= $data;
        }
        if ($this->_inHelp && $this->_inBlock) {
            $this->_output .= htmlspecialchars($data);
        }
    }

    /**
     * XML element handler for the <help> tag.
     *
     * @access private
     *
     * @param boolean $startTag      Boolean indicating whether this instance
     *                               is a start tag.
     * @param optional array $attrs  Additional element attributes (Not used).
     */
    function _helpHandler($startTag, $attrs = array())
    {
        $this->_inHelp = ($startTag) ? true : false;
    }

    /**
     * XML element handler for the <entry> tag.
     * Attributes: id
     *
     * @access private
     *
     * @param boolean $startTag      Boolean indicating whether this instance
     *                               is a start tag.
     * @param optional array $attrs  Additional element attributes.
     */
    function _entryHandler($startTag, $attrs = array())
    {
        if (!$startTag) {
            $this->_inBlock = false;
        } else {
            $id = String::upper($attrs['id']);
            $this->_curEntry = $id;
            $this->_entries[$id] = '';
            $this->_inBlock = ($id == $this->_reqEntry);
        }
    }

    /**
     * XML element handler for the <title> tag.
     *
     * @access private
     *
     * @param boolean $startTag      Boolean indicating whether this instance
     *                               is a start tag.
     * @param optional array $attrs  Additional element attributes (Not used).
     */
    function _titleHandler($startTag, $attrs = array())
    {
        $this->_inTitle = $startTag;
        if ($this->_inHelp && $this->_inBlock) {
            $this->_output .= ($startTag) ? '<h3>' : '</h3>';
        }
    }

    /**
     * XML element handler for the <heading> tag.
     *
     * @access private
     *
     * @param boolean $startTag      Boolean indicating whether this instance
     *                               is a start tag.
     * @param optional array $attrs  Additional element attributes (Not used).
     */
    function _headingHandler($startTag, $attrs = array())
    {
        if ($this->_inHelp && $this->_inBlock) {
            $this->_output .= ($startTag) ? '<h4>' : '</h4>';
        }
    }

    /**
     * XML element handler for the <para> tag.
     *
     * @access private
     *
     * @param boolean $startTag      Boolean indicating whether this instance
     *                               is a start tag.
     * @param optional array $attrs  Additional element attributes (Not used).
     */
    function _paraHandler($startTag, $attrs = array())
    {
        if ($this->_inHelp && $this->_inBlock) {
            $this->_output .= ($startTag) ? '<p>' : '</p>';
        }
    }

    /**
     * XML element handler for the <ref> tag.
     * Required attributes: ENTRY, MODULE
     *
     * @access private
     *
     * @param boolean $startTag      Boolean indicating whether this instance
     *                               is a start tag.
     * @param optional array $attrs  Additional element attributes.
     */
    function _refHandler($startTag, $attrs = array())
    {
        if ($this->_inHelp && $this->_inBlock) {
            if ($startTag) {
                $url = Util::addParameter(Horde::selfURL(), 'show', 'entry');
                $url = Util::addParameter($url, 'module', $attrs['MODULE']);
                $url = Util::addParameter($url, 'topic',  $attrs['ENTRY']);
                $this->_output .= Horde::link($url, null, 'helplink');
            } else {
                $this->_output .= '</a>';
            }
        }
    }

    /**
     * XML element handler for the <eref> tag.
     * Required elements: URL
     *
     * @access private
     *
     * @param boolean $startTag      Boolean indicating whether this instance
     *                               is a start tag.
     * @param optional array $attrs  Additional element attributes.
     */
    function _erefHandler($startTag, $attrs = array())
    {
        if ($this->_inHelp && $this->_inBlock) {
            if ($startTag) {
                $this->_output .= Horde::link($attrs['URL'], null, 'helplink', '_blank');
            } else {
                $this->_output .= '</a>';
            }
        }
    }

    /**
     * XML element handler for the <href> tag.
     * Required elements: url, app.
     *
     * @access private
     *
     * @param boolean $startTag      Boolean indicating whether this instance
     *                               is a start tag.
     * @param optional array $attrs  Additional element attributes.
     */
    function _hrefHandler($startTag, $attrs = array())
    {
        if ($this->_inHelp && $this->_inBlock) {
            if ($startTag) {
                global $registry;
                $url = Horde::url($registry->getParam('webroot', $attrs['app']) . '/' . $attrs['url']);
                $this->_output .= Horde::link($url, null, 'helplink', '_blank');
            } else {
                $this->_output .= '</a>';
            }
        }
    }

    /**
     * XML element handler for the <b> tag.
     *
     * @access private
     *
     * @param boolean $startTag      Boolean indicating whether this instance
     *                               is a start tag.
     * @param optional array $attrs  Additional element attributes (Not used).
     */
    function _bHandler($startTag, $attrs = array())
    {
        if ($this->_inHelp && $this->_inBlock) {
            $this->_output .= ($startTag) ? '<b>' : '</b>';
        }
    }

    /**
     * XML element handler for the <i> tag.
     *
     * @access private
     *
     * @param boolean $startTag      Boolean indicating whether this instance
     *                               is a start tag.
     * @param optional array $attrs  Additional element attributes (Not used).
     */
    function _iHandler($startTag, $attrs = array())
    {
        if ($this->_inHelp && $this->_inBlock) {
            $this->_output .= ($startTag) ? '<i>' : '</i>';
        }
    }

    /**
     * Includes the JavaScript necessary to create a new pop-up help
     * window.
     *
     * @access public
     */
    function javascript()
    {
        global $conf, $registry;

        if ($conf['user']['online_help'] && Help::_useJS()) {
            Horde::addScriptFile('open_help_win.js', 'horde');
        }
    }

    /**
     * Generates the HTML link that will pop up a help window for the
     * requested topic.
     *
     * @access public
     *
     * @param string $module  The name of the current Horde module.
     * @param string $topic   The help topic to be displayed.
     *
     * @return string  The HTML to create the help link.
     */
    function link($module, $topic)
    {
        global $conf, $registry;

        if (!$conf['user']['online_help']) {
            return '&nbsp;';
        }

        if (Help::_useJS()) {
            $html = Horde::link('', _("Help"), '', '', "open_help_win('$module', '$topic'); return false;");
        } else {
            $url = Horde::url($registry->getParam('webroot', 'horde') . '/services/help/', true);
            $url = Util::addParameter($url, 'module', $module);
            $url = Util::addParameter($url, 'topic', $topic);
            $html = Horde::link($url, '', '', '_hordehelpwin');
        }
        $html .= Horde::img('help.gif', _("Help"), 'width="16" height="16" align="middle"', $registry->getParam('graphics', 'horde')) . '</a>';

        return $html;
    }

    /**
     * Should we use javascript for the popup help windows?
     *
     * @access private
     *
     * @return boolean  True if javascript can be used for the help windows.
     */
    function _useJS()
    {
        static $use_js;

        if (!isset($use_js)) {
            require_once 'Horde/Browser.php';
            $browser = &Browser::singleton();
            $use_js = $browser->hasFeature('javascript');
        }

        return $use_js;
    }

    /**
     * Generates the URL that will pop up a help window for the list
     * of topics.
     *
     * @access public
     *
     * @param string $module  The name of the current Horde module.
     *
     * @return string  The HTML to create the help link.
     */
    function listLink($module)
    {
        global $conf;

        if (!$conf['user']['online_help']) {
            return false;
        } elseif (Help::_useJS()) {
            return "javascript:open_help_win('$module');";
        } else {
            global $registry;
            $url = Horde::url($registry->getParam('webroot', 'horde') . '/services/help/', true);
            $url = Util::addParameter($url, 'module', $module);
            $url = Util::addParameter($url, 'show', 'topics');
            return $url;
        }
    }

}
