<?php
/**
 * The MIME_Viewer_text class renders out plain text with URLs made
 * into hyperlinks (if viewing inline).
 *
 * $Horde: framework/MIME/MIME/Viewer/plain.php,v 1.15 2004/04/14 12:38:38 jan Exp $
 *
 * Copyright 1999-2004 Anil Madhavapeddy <anil@recoil.org>
 * Copyright 2002-2004 Michael Slusarz <slusarz@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Anil Madhavapeddy <anil@recoil.org>
 * @author  Michael Slusarz <slusarz@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 1.3
 * @package Horde_MIME_Viewer
 */
class MIME_Viewer_plain extends MIME_Viewer {

    /**
     * Render out the contents.
     *
     * @access public
     *
     * @param optional array $params  Any parameters the Viewer may need.
     *
     * @return string  The rendered contents.
     */
    function render($params = array())
    {
        require_once 'Horde/MIME/Contents.php';

        $text = $this->mime_part->getContents();

        /* Check for 'flowed' text data. */
        $flowed = ($this->mime_part->getContentTypeParameter('format') == 'flowed');
        if ($flowed) {
            $text = $this->_formatFlowed($text);
        }

        /* If calling as an attachment from view.php, we do not want
           to alter the text in any way with HTML. */
        if (MIME_Contents::viewAsAttachment()) {
            return $text;
        } else {
            require_once 'Horde/Text.php';
            return Text::toHTML($text, TEXT_HTML_MICRO, null, null);
        }
    }

    /**
     * Return the MIME content type of the rendered content.
     *
     * @access public
     *
     * @return string  The content type of the output. 
     */
    function getType()
    {
        require_once 'Horde/MIME/Contents.php';
        return (MIME_Contents::viewAsAttachment()) ? $this->mime_part->getType(true) : 'text/html';
    }

    /**
     * Format flowed text for HTML output.
     *
     * @access public
     *
     * @param string $text  The text to format.
     *
     * @return string  The formatted text.
     */
    function _formatFlowed($text)
    {
        require_once 'Horde/Text/Flowed.php';
        $flowed = &new Text_Flowed($this->mime_part->replaceEOL($text, "\n"));
        $flowed->setOptLength(90);
        return $flowed->toFixed();
    }

}
