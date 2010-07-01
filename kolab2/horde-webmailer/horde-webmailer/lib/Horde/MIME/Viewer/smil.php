<?php
/**
 * The MIME_Viewer_smil renders SMIL documents to very basic HTML.
 *
 * $Horde: framework/MIME/MIME/Viewer/smil.php,v 1.3.2.3 2009-01-06 15:23:22 jan Exp $
 *
 * Copyright 2006-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Jan Schneider <jan@horde.org>
 * @since   Horde 3.2
 * @package Horde_MIME_Viewer
 */
class MIME_Viewer_smil extends MIME_Viewer {

    /**
     * Handle for the XML parser object.
     *
     * @var resource
     */
    var $_parser;

    /**
     * String buffer to hold the generated content
     *
     * @var string
     */
    var $_content = '';

    /**
     * Renders out the contents.
     *
     * @param array $params  Any parameters the Viewer may need.
     *
     * @return string  The rendered contents.
     */
    function render($params = array())
    {
        /* Create a new parser and set its default properties. */
        $this->_parser = xml_parser_create();
        xml_set_object($this->_parser, $this);
        xml_set_element_handler($this->_parser, '_startElement', '_endElement');
        xml_set_character_data_handler($this->_parser, '_defaultHandler');
        xml_parse($this->_parser, $this->mime_part->getContents(), true);
        return $this->_content;
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
        switch ($name) {
        case 'IMG':
            if (isset($attrs['SRC'])) {
                $this->_content .= '<img src="' . htmlspecialchars($attrs['SRC']) . '" />';
            }
            break;
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
        $data = trim($data);
        if (!empty($data)) {
            $this->_content .= ' ' . htmlspecialchars($data);
        }
    }

    /**
     * Return the MIME content type of the rendered content.
     *
     * @return string  The content type of the output.
     */
    function getType()
    {
        return 'text/html; charset=' . NLS::getCharset();
    }

}
