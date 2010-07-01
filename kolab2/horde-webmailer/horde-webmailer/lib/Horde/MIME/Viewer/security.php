<?php
/**
 * The MIME_Viewer_security class is a wrapper used to load the appropriate
 * MIME_Viewer for secure multipart messages (defined by RFC 1847). This
 * class handles multipart/signed and multipart/encrypted data.
 *
 * $Horde: framework/MIME/MIME/Viewer/security.php,v 1.6.10.9 2009-01-06 15:23:21 jan Exp $
 *
 * Copyright 2002-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Michael Slusarz <slusarz@horde.org>
 * @since   Horde 3.0
 * @package Horde_MIME_Viewer
 */
class MIME_Viewer_security extends MIME_Viewer {

    /**
     * Stores the MIME_Viewer of the specified security protocol.
     *
     * @var MIME_Viewer
     */
    var $_viewer;

    /**
     * The $mime_part class variable has the information to render
     * out, encapsulated in a MIME_Part object.
     *
     * @param $params mixed  The parameters (if any) to pass to the underlying
     *                       MIME_Viewer.
     *
     * @return string  Rendering of the content.
     */
    function render($params = array())
    {
        /* Get the appropriate MIME_Viewer for the protocol specified. */
        if (!($this->_resolveViewer())) {
            return;
        }

        /* Render using the loaded MIME_Viewer object. */
        return $this->_viewer->render($params);
    }

    /**
     * Returns the content-type of the Viewer used to view the part.
     *
     * @return string  A content-type string.
     */
    function getType()
    {
        /* Get the appropriate MIME_Viewer for the protocol specified. */
        if (!($this->_resolveViewer())) {
            return 'application/octet-stream';
        } else {
            return $this->_viewer->getType();
        }
    }

    /**
     * Load a MIME_Viewer according to the protocol parameter stored
     * in the MIME_Part to render. If unsuccessful, try to load a generic
     * multipart MIME_Viewer.
     *
     * @access private
     *
     * @return boolean  True on success, false on failure.
     */
    function _resolveViewer()
    {
        $viewer = null;

        if (empty($this->_viewer)) {
            $protocol = $this->mime_part->getContentTypeParameter('protocol');
            if (empty($protocol)) {
                return false;
            }
            $viewer = &MIME_Viewer::factory($this->mime_part, $protocol);
            if (empty($viewer) ||
                (String::lower(get_class($viewer)) == 'mime_viewer_default')) {
                $viewer = &MIME_Viewer::factory($this->mime_part, $this->mime_part->getPrimaryType() . '/*');
                if (empty($viewer)) {
                    return false;
                }
            }
            $this->_viewer = $viewer;
        }

        return true;
    }

}
