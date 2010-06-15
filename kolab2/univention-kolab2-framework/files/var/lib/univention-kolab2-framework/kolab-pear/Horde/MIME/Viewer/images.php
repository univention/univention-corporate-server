<?php
/**
 * The MIME_Viewer_images class allows images to be displayed.
 *
 * $Horde: framework/MIME/MIME/Viewer/images.php,v 1.15 2004/04/26 18:21:22 chuck Exp $
 *
 * Copyright 2002-2004 Michael Slusarz <slusarz@bigworm.colorado.edu>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Michael Slusarz <slusarz@bigworm.colorado.edu>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 2.2
 * @package Horde_MIME_Viewer
 */
class MIME_Viewer_images extends MIME_Viewer {

    /**
     * Render out the currently set contents.
     * The $mime_part class variable has the information to render
     * out, encapsulated in a MIME_Part object.
     */
    function render()
    {
        global $browser;

        if ($browser->isViewable($this->getType())) {
            return $this->mime_part->getContents();
        }
    }

    /**
     * Return the content-type.
     *
     * @access public
     *
     * @return string  The content-type of the output.
     */
    function getType()
    {
        global $browser;

        $type = $this->mime_part->getType();
        if ($browser->isBrowser('mozilla') && ($type == 'image/pjpeg')) {
            /* image/jpeg and image/pjpeg *appear* to be the same
             * entity, but Mozilla don't seem to want to accept the
             * latter.  For our purposes, we will treat them the
             * same. */
            return 'image/jpeg';
        } elseif ($type == 'image/x-png') {
            /* image/x-png is equivalent to image/png. */
            return 'image/png';
        } else {
            return $type;
        }
    }

    /**
     * Generate HTML output for a javascript auto-resize view window.
     *
     * @access private
     *
     * @param string $url    The URL which contains the actual image data.
     * @param string $title  The title to use for the page.
     *
     * @return string  The HTML output.
     */
    function _popupImageWindow($url, $title)
    {
        $str = <<<EOD
<html>
<head>
<title>$title</title>
<script language="javascript" type="text/javascript">
function resizeWindow()
{
    window.moveTo(0, 0);
    window.resizeTo(200, 200);

    width_1 = document.disp_image.width;
    width_2 = window.screen.availWidth - 20;
    width = (width_1 > width_2) ? width_2 : width_1;

    height_1 = document.disp_image.height;
    height_2 = window.screen.availTop || (window.screen.height - 20);
    height = (height_1 > height_2) ? height_2 : height_1;

    window.resizeTo(width + (200 - (document.body.clientWidth || window.innerWidth)), height + (200 - (document.body.clientHeight || window.innerHeight)));
    window.focus();
}
</script>
</head>
<body bgcolor="#ffffff" onload="javascript:resizeWindow();" topmargin="0" marginheight="0" leftmargin="0" marginwidth="0">
<img name="disp_image" border="0" src="$url" style="display:block" />
</body>
</html>
EOD;
        return $str;
    }

}
