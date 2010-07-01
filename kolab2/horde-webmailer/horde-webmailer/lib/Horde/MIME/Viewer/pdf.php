<?php
/**
 * The MIME_Viewer_pdf class simply outputs the PDF file with the content-type
 * 'application/pdf' enabling web browsers with a PDF viewer plugin to view
 * the PDF file inside the browser.
 *
 * $Horde: framework/MIME/MIME/Viewer/pdf.php,v 1.3.12.10 2009-01-06 15:23:21 jan Exp $
 *
 * Copyright 2003-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Michael Slusarz <slusarz@horde.org>
 * @package Horde_MIME_Viewer
 */
class MIME_Viewer_pdf extends MIME_Viewer {

    /**
     * Return the content-type.
     *
     * @return string  The content-type of the output.
     */
    function getType()
    {
        return 'application/pdf';
    }

}
