<?php
/**
 * The MIME_Viewer_wordperfect class renders out WordPerfect documents in HTML
 * format by using the libwpd package (http://libwpd.sourceforge.net/).
 *
 * $Horde: framework/MIME/MIME/Viewer/wordperfect.php,v 1.1.2.3 2009-01-06 15:23:22 jan Exp $
 *
 * Copyright 2007-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Matt Selsky <selsky@columbia.edu>
 * @since   Horde 3.2
 * @package Horde_MIME_Viewer
 */
class MIME_Viewer_wordperfect extends MIME_Viewer {

    /**
     * Render out the current data using wpd2html.
     *
     * @param array $params  Any parameters the viewer may need.
     *
     * @return string  The rendered contents.
     */
    function render($params = array())
    {
        global $mime_drivers;

        /* Check to make sure the program actually exists. */
        if (!file_exists($mime_drivers['horde']['wordperfect']['location'])) {
            return '<pre>' . sprintf(_("The program used to view this data type (%s) was not found on the system."), $mime_drivers['horde']['wordperfect']['location']) . '</pre>';
        }

        $tmp_wpd = Horde::getTempFile('wpd');
        $tmp_output = Horde::getTempFile('wpd');
        $args = " $tmp_wpd > $tmp_output";

        $fh = fopen($tmp_wpd, 'w');
        fwrite($fh, $this->mime_part->getContents());
        fclose($fh);

        exec($mime_drivers['horde']['wordperfect']['location'] . $args);

        if (!file_exists($tmp_output)) {
            return _("Unable to translate this WordPerfect document");
        }

        return file_get_contents($tmp_output);
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
