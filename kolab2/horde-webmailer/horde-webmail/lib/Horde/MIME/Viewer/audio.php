<?php
/**
 * The MIME_Viewer_audio class sends audio parts to the browser for
 * handling by the browser, a plugin, or a helper application.
 *
 * $Horde: framework/MIME/MIME/Viewer/audio.php,v 1.3.2.3 2009-01-06 15:23:21 jan Exp $
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
class MIME_Viewer_audio extends MIME_Viewer {

    /**
     * Return the content-type.
     *
     * @return string  The content-type of the output.
     */
    function getType()
    {
        return $this->mime_part->getType();
    }

}
