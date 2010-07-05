<?php
/**
 * The MIME_Viewer_plain class renders out plain text with URLs made
 * into hyperlinks (if viewing inline).
 *
 * $Horde: framework/MIME/MIME/Viewer/plain.php,v 1.18.6.15 2009-01-06 15:23:21 jan Exp $
 *
 * Copyright 1999-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Anil Madhavapeddy <anil@recoil.org>
 * @author  Michael Slusarz <slusarz@horde.org>
 * @package Horde_MIME_Viewer
 */
class MIME_Viewer_plain extends MIME_Viewer {

    /**
     * Render out the contents.
     *
     * @param array $params  Any parameters the Viewer may need.
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
            require_once 'Horde/Text/Filter.php';
            return Text_Filter::filter($text, 'text2html', array('parselevel' => TEXT_HTML_MICRO, 'charset' => null, 'class' => null));
        }
    }

    /**
     * Return the MIME content type of the rendered content.
     *
     * @return string  The content type of the output.
     */
    function getType()
    {
        require_once 'Horde/MIME/Contents.php';
        return (MIME_Contents::viewAsAttachment()) ? $this->mime_part->getType(true) : 'text/html; charset=' . NLS::getCharset();
    }

    /**
     * Format flowed text for HTML output.
     *
     * @param string $text    The text to format.
     * @param integer $opt    The optimal length to wrap.
     * @param integer $max    The maximum length to wrap. 0 means don't wrap.
     * @param boolean $delsp  Was text created with DelSp formatting?
     *
     * @return string  The formatted text.
     */
    function _formatFlowed($text, $opt = null, $max = null, $delsp = null)
    {
        require_once 'Text/Flowed.php';
        $flowed = &new Text_Flowed($this->mime_part->replaceEOL($text, "\n"), $this->mime_part->getCharset());
        if (!is_null($opt)) {
            $flowed->setOptLength($opt);
        }
        if (!is_null($max)) {
            $flowed->setMaxLength($max);
        }
        if (!is_null($delsp)) {
            $flowed->setDelSp($delsp);
        }
        return $flowed->toFixed();
    }

}
