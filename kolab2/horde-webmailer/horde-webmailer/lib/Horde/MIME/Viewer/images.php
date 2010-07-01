<?php
/**
 * The MIME_Viewer_images class allows images to be displayed.
 *
 * $Horde: framework/MIME/MIME/Viewer/images.php,v 1.18.8.14 2009-01-06 15:23:21 jan Exp $
 *
 * Copyright 2002-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Michael Slusarz <slusarz@horde.org>
 * @package Horde_MIME_Viewer
 */
class MIME_Viewer_images extends MIME_Viewer {

    /**
     * Return the content-type.
     *
     * @return string  The content-type of the output.
     */
    function getType()
    {
        $type = $this->mime_part->getType();
        if ($GLOBALS['browser']->isBrowser('mozilla') &&
            ($type == 'image/pjpeg')) {
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
        global $browser;

        $str = <<<EOD
<html>
<head>
<title>$title</title>
<style type="text/css"><!-- body { margin:0px; padding:0px; } --></style>
EOD;

        /* Only use javascript if we are using a DOM capable browser. */
        if ($browser->getFeature('dom')) {
            /* Translate '&amp' entities to '&' for JS URL links. */
            $url = str_replace('&amp;', '&', $url);

            /* Javascript display. */
            $loading = _("Loading...");
            $str .= <<<EOD
<script type="text/javascript">
function resizeWindow()
{

    var h, img = document.getElementById('disp_image'), w;
    document.getElementById('splash').style.display = 'none';
    img.style.display = 'block';
    window.moveTo(0, 0);
    h = img.height - (window.innerHeight ? window.innerHeight : (document.documentElement.clientHeight ? document.documentElement.clientHeight : document.body.clientHeight));
    w = img.width - (window.innerWidth ? window.innerWidth : (document.documentElement.clientWidth ? document.documentElement.clientWidth : document.body.clientWidth));
    window.resizeBy(w, h);
    self.focus();
}
</script></head>
<body onload="resizeWindow();"><span id="splash" style="color:gray;font-family:sans-serif;padding:2px;">$loading</span><img id="disp_image" style="display:none;" src="$url" /></body></html>
EOD;
        } else {
            /* Non-javascript display. */
            $img_txt = _("Image");
            $str .= <<<EOD
</head>
<body bgcolor="#ffffff" topmargin="0" marginheight="0" leftmargin="0" marginwidth="0">
<img border="0" src="$url" alt="$img_txt" />
</body>
</html>
EOD;
        }

        return $str;
    }

}
