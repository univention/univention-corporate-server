<?php
/**
 * The MIME_Viewer_simple class renders out plain text without any
 * modifications.
 *
 * $Horde: framework/MIME/MIME/Viewer/simple.php,v 1.1.6.10 2009-05-29 06:09:03 slusarz Exp $
 *
 * Copyright 2004-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Michael Slusarz <slusarz@horde.org>
 * @since   Horde 3.0
 * @package Horde_MIME_Viewer
 */
class MIME_Viewer_simple extends MIME_Viewer {

    /**
     * Renders out the contents.
     *
     * @param array $params  Any parameters the Viewer may need.
     *
     * @return string  The rendered contents.
     */
    function render($params = array())
    {
        // Bug #8311: Unknown text parts should not be rendered inline.
        return MIME_Contents::viewAsAttachment()
            ? parent::render($params)
            : _("Can not display contents of text part inline.");
    }

    /**
     * Return the MIME type of the rendered content.
     *
     * @return string  MIME-type of the output content.
     */
    function getType()
    {
        return 'text/plain';
    }

}
