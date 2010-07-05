<?php
/**
 * @package Horde_Framework
 *
 * $Horde: framework/Horde/Horde/Help.php,v 1.68.8.22 2009-01-06 15:23:10 jan Exp $
 */

/**
 * Raw help in the string.
 */
define('HELP_SOURCE_RAW', 0);

/**
 * Help text is in a file.
 */
define('HELP_SOURCE_FILE', 1);

/**
 * The Help:: class provides an interface to the online help subsystem.
 *
 * Copyright 1999-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Jon Parise <jon@horde.org>
 * @since   Horde 1.3
 * @package Horde_Framework
 */
class Help {

    /**
     * Handle for the XML parser object.
     *
     * @var resource
     */
    var $_parser = 0;

    /**
     * String buffer to hold the XML help source.
     *
     * @var string
     */
    var $_buffer = '';

    /**
     * String containing the ID of the requested help entry.
     *
     * @var string
     */
    var $_reqEntry = '';

    /**
     * String containing the ID of the current help entry.
     *
     * @var string
     */
    var $_curEntry = '';

    /**
     * String containing the formatted output.
     *
     * @var string
     */
    var $_output = '';

    /**
     * Boolean indicating whether we're inside a <help> block.
     *
     * @var boolean
     */
    var $_inHelp = false;

    /**
     * Boolean indicating whether we're inside the requested block.
     *
     * @var boolean
     */
    var $_inBlock = false;

    /**
     * Boolean indicating whether we're inside a <title> block.
     *
     * @var boolean
     */
    var $_inTitle = false;

    /**
     * Boolean indicating whether we're inside a heading block.
     *
     * @var boolean
     */
    var $_inHeading = false;

    /**
     * Hash containing an index of all of the help entries.
     *
     * @var array
     */
    var $_entries = array();

    /**
     * String containing the charset of the XML data source.
     *
     * @var string
     */
    var $_charset = 'iso-8859-1';

    /**
     * Hash of user-defined function handlers for the XML elements.
     *
     * @var array
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
        'pre'      =>  '_preHandler',
        'tip'      =>  '_tipHandler',
        'warn'     =>  '_warnHandler'
    );

    /**
     * Hash containing an index of all of the search results.
     *
     * @var array
     */
    var $_search = array();

    /**
     * String containing the keyword for the search.
     *
     * @var string
     */
    var $_keyword = "";

    /**
     * Constructor
     *
     * @param integer $source  The source of the XML help data, based on the
     *                         HELP_SOURCE_* constants.
     * @param string $arg      Source-dependent argument for this Help
     *                         instance.
     */
    function Help($source, $arg = null)
    {
        global $language, $nls;

        $this->_charset = isset($nls['charsets'][$language]) ? $nls['charsets'][$language] : 'ISO-8859-1';

        /* Populate $this->_buffer based on $source. */
        switch ($source) {
        case HELP_SOURCE_RAW:
            $this->_buffer = $arg;
            break;

        case HELP_SOURCE_FILE:
            if (file_exists($arg[0]) && filesize($arg[0])) {
                $this->_buffer = file_get_contents($arg[0]);
            } elseif (file_exists($arg[1]) && filesize($arg[1])) {
                $this->_buffer = file_get_contents($arg[1]);
            } else {
                $this->_buffer = '';
            }
            break;

        default:
            $this->_buffer = '';
            break;
        }
    }

    /**
     * Generates the HTML link that will pop up a help window for the
     * requested topic.
     *
     * @param string $module  The name of the current Horde module.
     * @param string $topic   The help topic to be displayed.
     *
     * @return string  The HTML to create the help link.
     */
    function link($module, $topic)
    {
        global $conf, $registry, $browser;

        if (!Horde::showService('help')) {
            return '&nbsp;';
        }

        if ($browser->hasFeature('javascript')) {
            Horde::addScriptFile('popup.js', 'horde');
        }

        $url = Horde::url($registry->get('webroot', 'horde') . '/services/help/', true);
        $url = Util::addParameter($url, array('module' => $module,
                                              'topic' => $topic));

        return Horde::link($url, _("Help"), 'helplink', 'hordehelpwin', 'popup(this.href); return false;') .
            Horde::img('help.png', _("Help"), 'width="16" height="16"', $registry->getImageDir('horde')) . '</a>';
    }

    /**
     * Looks up the requested entry in the XML help buffer.
     *
     * @param string $entry  String containing the entry ID.
     */
    function lookup($entry)
    {
        $this->_output = '';
        $this->_reqEntry = String::upper($entry);
        $this->_init();
        xml_parse($this->_parser, $this->_buffer, true);
    }

    /**
     * Returns a hash of all of the topics in this help buffer
     * containing the keyword specified.
     *
     * @return array  Hash of all of the search results.
     */
    function search($keyword)
    {
        $this->_init();
        $this->_keyword = $keyword;
        xml_parse($this->_parser, $this->_buffer, true);

        return $this->_search;
    }

    /**
     * Returns a hash of all of the topics in this help buffer.
     *
     * @return array  Hash of all of the topics in this buffer.
     */
    function topics()
    {
        $this->_init();
        xml_parse($this->_parser, $this->_buffer, true);

        return $this->_entries;
    }

    /**
     * Display the contents of the formatted output buffer.
     */
    function display()
    {
        echo $this->_output;
    }

    /**
     * Initializes the XML parser.
     *
     * @access private
     *
     * @return boolean  Returns true on success, false on failure.
     */
    function _init()
    {
        if (!$this->_parser) {
            if (!Util::extensionExists('xml')) {
                Horde::fatal(PEAR::raiseError('The XML functions are not available. Rebuild PHP with --with-xml.'), __FILE__, __LINE__, false);
            }

            /* Create a new parser and set its default properties. */
            $this->_parser = xml_parser_create();
            xml_set_object($this->_parser, $this);
            xml_parser_set_option($this->_parser, XML_OPTION_CASE_FOLDING, false);
            xml_set_element_handler($this->_parser, '_startElement', '_endElement');
            xml_set_character_data_handler($this->_parser, '_defaultHandler');
        }

        return ($this->_parser != 0);
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
        $data = String::convertCharset($data, version_compare(zend_version(), '2', '<') ? $this->_charset : 'UTF-8');
        if ($this->_inTitle) {
            $this->_entries[$this->_curEntry] .= $data;
        }

        if ($this->_inHelp && $this->_inBlock) {
            $this->_output .= htmlspecialchars($data);
        }

        if ($this->_keyword) {
            if (stristr($data, $this->_keyword) !== false) {
                $this->_search[$this->_curEntry] = $this->_entries[$this->_curEntry];
            }
        }
    }

    /**
     * XML element handler for the <help> tag.
     *
     * @access private
     *
     * @param boolean $startTag  Boolean indicating whether this instance is a
     *                           start tag.
     * @param array $attrs       Additional element attributes (Not used).
     */
    function _helpHandler($startTag, $attrs = array())
    {
        $this->_inHelp = $startTag ?  true : false;
    }

    /**
     * XML element handler for the <entry> tag.
     * Attributes: id
     *
     * @access private
     *
     * @param boolean $startTag  Boolean indicating whether this instance is a
     *                           start tag.
     * @param array $attrs       Additional element attributes.
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
     * @param boolean $startTag  Boolean indicating whether this instance is a
     *                           start tag.
     * @param array $attrs       Additional element attributes (Not used).
     */
    function _titleHandler($startTag, $attrs = array())
    {
        $this->_inTitle = $startTag;
        if ($this->_inHelp && $this->_inBlock) {
            $this->_output .= $startTag ? '<h1>' : '</h1>';
        }
    }

    /**
     * XML element handler for the <heading> tag.
     *
     * @access private
     *
     * @param boolean $startTag  Boolean indicating whether this instance is a
     *                           start tag.
     * @param  array $attrs      Additional element attributes (Not used).
     */
    function _headingHandler($startTag, $attrs = array())
    {
        $this->_inHeading = $startTag;
        if ($this->_inHelp && $this->_inBlock) {
            $this->_output .= $startTag ? '<h2>' : '</h2>';
        }
    }

    /**
     * XML element handler for the <para> tag.
     *
     * @access private
     *
     * @param boolean $startTag  Boolean indicating whether this instance is a
     *                           start tag.
     * @param array $attrs       Additional element attributes (Not used).
     */
    function _paraHandler($startTag, $attrs = array())
    {
        if ($this->_inHelp && $this->_inBlock) {
            $this->_output .= $startTag ? '<p>' : '</p>';
        }
    }

    /**
     * XML element handler for the <ref> tag.
     * Required attributes: ENTRY, MODULE
     *
     * @access private
     *
     * @param boolean $startTag  Boolean indicating whether this instance is a
     *                           start tag.
     * @param array $attrs       Additional element attributes.
     */
    function _refHandler($startTag, $attrs = array())
    {
        if ($this->_inHelp && $this->_inBlock) {
            if ($startTag && isset($attrs['module']) && isset($attrs['entry'])) {
                $url = Util::addParameter(Horde::selfUrl(),
                                          array('show' => 'entry',
                                                'module' => $attrs['module'],
                                                'topic'  => $attrs['entry']));
                $this->_output .= Horde::link($url);
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
     * @param boolean $startTag  Boolean indicating whether this instance is a
     *                           start tag.
     * @param array $attrs       Additional element attributes.
     */
    function _erefHandler($startTag, $attrs = array())
    {
        if ($this->_inHelp && $this->_inBlock) {
            if ($startTag) {
                $this->_output .= Horde::link($attrs['url'], null, '', '_blank');
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
     * @param boolean $startTag  Boolean indicating whether this instance is a
     *                           start tag.
     * @param array $attrs       Additional element attributes.
     */
    function _hrefHandler($startTag, $attrs = array())
    {
        if ($this->_inHelp && $this->_inBlock) {
            if ($startTag) {
                global $registry;
                $url = Horde::url($registry->get('webroot', $attrs['app']) . '/' . $attrs['url']);
                $this->_output .= Horde::link($url, null, '', '_blank');
            } else {
                $this->_output .= '</a>';
            }
        }
    }

    /**
     * XML element handler for the &lt;b&gt; tag.
     *
     * @access private
     *
     * @param boolean $startTag  Boolean indicating whether this instance is a
     *                           start tag.
     * @param array $attrs       Additional element attributes (Not used).
     */
    function _bHandler($startTag, $attrs = array())
    {
        if ($this->_inHelp && $this->_inBlock) {
            $this->_output .= $startTag ? '<strong>' : '</strong>';
        }
    }

    /**
     * XML element handler for the &lt;i&gt; tag.
     *
     * @access private
     *
     * @param boolean $startTag  Boolean indicating whether this instance is a
     *                           start tag.
     * @param array $attrs       Additional element attributes.
     */
    function _iHandler($startTag, $attrs = array())
    {
        if ($this->_inHelp && $this->_inBlock) {
            $this->_output .= $startTag ? '<em>' : '</em>';
        }
    }

    /**
     * XML element handler for the &lt;pre&gt; tag.
     *
     * @access private
     *
     * @param boolean $startTag  Boolean indicating whether this instance is a
     *                           start tag.
     * @param array $attrs       Additional element attributes.
     */
    function _preHandler($startTag, $attrs = array())
    {
        if ($this->_inHelp && $this->_inBlock) {
            $this->_output .= $startTag ? '<pre>' : '</pre>';
        }
    }

    /**
     * XML element handler for the <tip> tag.
     *
     * @access private
     *
     * @param boolean $startTag  Boolean indicating whether this instance is a
     *                           start tag.
     * @param array $attrs       Additional element attributes.
     */
    function _tipHandler($startTag, $attrs = array())
    {
        if ($this->_inHelp && $this->_inBlock) {
            $this->_output .= $startTag ? '<em class="helpTip">' : '</em>';
        }
    }

    /**
     * XML element handler for the <warn> tag.
     *
     * @access private
     *
     * @param boolean $startTag  Boolean indicating whether this instance is a
     *                           start tag.
     * @param array $attrs       Additional element attributes.
     */
    function _warnHandler($startTag, $attrs = array())
    {
        if ($this->_inHelp && $this->_inBlock) {
            $this->_output .= $startTag ? '<em class="helpWarn">' : '</em>';
        }
    }

}
