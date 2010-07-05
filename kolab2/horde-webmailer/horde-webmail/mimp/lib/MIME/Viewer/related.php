<?php
/**
 * The MIMP_MIME_Viewer_related class handles multipart/related messages
 * as defined by RFC 2112.
 *
 * $Horde: mimp/lib/MIME/Viewer/related.php,v 1.14.2.4 2009-01-06 15:24:54 jan Exp $
 *
 * Copyright 2002-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author  Michael Slusarz <slusarz@horde.org>
 * @package Horde_MIME_Viewer
 */
class MIMP_MIME_Viewer_related extends MIME_Viewer {

    /**
     * Render out the currently set contents.
     *
     * The $mime_part class variable has the information to render
     * out, encapsulated in a MIME_Part object.
     */
    function render($params)
    {
        $contents = &$params[0];

        $text = '';

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
           inline. */
        if ($contents->canDisplayInline($start)) {
            $text = $contents->renderMIMEPart($start);
            $contents->removeIndex($start->getMIMEId());
        }

        return $text;
     }

    /**
     * Return the content-type.
     *
     * @return string  The content-type of the message.
     */
    function getType()
    {
        return 'text/html';
    }

}
