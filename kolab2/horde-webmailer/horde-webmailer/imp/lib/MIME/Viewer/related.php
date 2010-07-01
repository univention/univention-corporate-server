<?php
/**
 * The IMP_MIME_Viewer_related class handles multipart/related messages
 * as defined by RFC 2387.
 *
 * $Horde: imp/lib/MIME/Viewer/related.php,v 1.21.10.15 2009-01-06 15:24:09 jan Exp $
 *
 * Copyright 2002-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author  Michael Slusarz <slusarz@horde.org>
 * @package Horde_MIME_Viewer
 */
class IMP_MIME_Viewer_related extends MIME_Viewer {

    /**
     * The character set of the rendered HTML part.
     *
     * @var string
     */
    var $_charset = null;

    /**
     * The mime type of the message part that has been chosen to be displayed.
     *
     * @var string
     */
    var $_viewerType = 'text/html';

    /**
     * Render out the currently set contents.
     *
     * @param array $params  An array with a reference to a MIME_Contents
     *                       object.
     *
     * @return string  The rendered text in HTML.
     */
    function render($params)
    {
        $contents = &$params[0];

        /* Look at the 'start' parameter to determine which part to start
           with. If no 'start' parameter, use the first part.
           RFC 2387 [3.1] */
        if ($this->mime_part->getContentTypeParameter('start') &&
            ($key = array_search($this->mime_part->getContentTypeParameter('start'), $this->mime_part->getCIDList()))) {
            if (($pos = strrpos($key, '.'))) {
                $id = substr($key, $pos + 1);
            } else {
                $id = $key;
            }
        } else {
            $id = 1;
        }
        $start = $this->mime_part->getPart($this->mime_part->getRelativeMimeID($id));

        /* Only display if the start part (normally text/html) can be displayed
           inline -OR- we are viewing this part as an attachment. */
        if ($contents->canDisplayInline($start) ||
            $contents->viewAsAttachment()) {
            $text = $contents->renderMIMEPart($start);
            $this->_viewerType = $contents->getMIMEViewerType($start);
            $this->_charset = $start->getCharset();
        } else {
            $text = '';
        }

        return $text;
     }

    /**
     * Render out attachment information.
     *
     * @param array $params  An array with a reference to a MIME_Contents
     *                       object.
     *
     * @return string  The rendered text in HTML.
     */
    function renderAttachmentInfo($params)
    {
        $contents = &$params[0];

        $msg = sprintf(_("Click %s to view this multipart/related part in a separate window."), $contents->linkViewJS($this->mime_part, 'view_attach', _("HERE"), _("View content in a separate window")));
        return $contents->formatStatusMsg($msg, Horde::img('mime/html.png', _("HTML")), false);
    }

    /**
     * Return the content-type.
     *
     * @return string  The content-type of the message.
     */
    function getType()
    {
        return $this->_viewerType . '; charset=' . $this->getCharset();
    }

    /**
     * Returns the character set used for the Viewer.
     *
     * @return string  The character set used by this Viewer.
     */
    function getCharset()
    {
        return ($this->_charset === null) ? NLS::getCharset() : $this->_charset;
    }

}
