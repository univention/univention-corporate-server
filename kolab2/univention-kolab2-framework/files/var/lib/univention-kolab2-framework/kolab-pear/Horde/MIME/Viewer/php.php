<?php

require_once dirname(__FILE__) . '/source.php';

/**
 * The MIME_Viewer_php class renders out syntax-highlighted PHP code
 * in HTML format.
 *
 * $Horde: framework/MIME/MIME/Viewer/php.php,v 1.21 2004/05/22 03:06:23 chuck Exp $
 *
 * Copyright 1999-2004 Chuck Hagenbuch <chuck@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 1.3
 * @package Horde_MIME_Viewer
 */
class MIME_Viewer_php extends MIME_Viewer_source {

    /**
     * Renders out the contents.
     *
     * @access public
     *
     * @param optional array $params  Any parameters the Viewer may need.
     *
     * @return string  The rendered contents.
     */
    function render($params = array())
    {
        return $this->lineNumber(trim(str_replace(array("\n", '<br />'), array('', "\n"),
                                                  highlight_string($this->mime_part->getContents(), true))));
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
        return 'text/html';
    }

}
