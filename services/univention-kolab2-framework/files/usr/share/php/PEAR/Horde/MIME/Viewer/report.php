<?php
/**
 * The MIME_Viewer_report class is a wrapper used to load the appropriate
 * MIME_Viewer for multipart/report data (RFC 3462).
 *
 * $Horde: framework/MIME/MIME/Viewer/report.php,v 1.5 2004/01/01 15:14:21 jan Exp $
 *
 * Copyright 2003-2004 Michael Slusarz <slusarz@bigworm.colorado.edu>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Michael Slusarz <slusarz@bigworm.colorado.edu>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 * @package Horde_MIME_Viewer
 */
class MIME_Viewer_report extends MIME_Viewer {

    /**
     * Stores the MIME_Viewer of the specified protocol.
     *
     * @var object MIME_Viewer $_viewer
     */
    var $_viewer;

    /**
     * Render the multipart/report data. 
     *
     * @access public
     *
     * @param optional array $params  An array of parameters needed.
     *
     * @return string  The rendered data.
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
     * @access public
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
     * Load a MIME_Viewer according to the report-type parameter stored
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
            if (!($type = $this->mime_part->getContentTypeParameter('report-type'))) {
                return false;
            }

            $viewer = &MIME_Viewer::factory($this->mime_part, 'message/' . String::lower($type));
            if (empty($viewer) ||
                (get_class($viewer) == 'mime_viewer_default')) {
                if (!($viewer = &MIME_Viewer::factory($this->mime_part, $this->mime_part->getPrimaryType() . '/*'))) {
                    return false;
                }
            }
            $this->_viewer = $viewer;
        }

        return true;
    }

}
