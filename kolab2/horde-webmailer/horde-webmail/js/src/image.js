/**
 * Horde Image Javascript
 *
 * Provides the javascript to help during the uploading of images in Horde_Form.
 *
 * $Horde: horde/js/src/image.js,v 1.5.2.4 2009-01-06 15:24:43 jan Exp $
 *
 * Copyright 2003-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
*
* @author Marko Djukic <marko@oblo.com>
 */

/**
 * Changes the src of an image target, optionally attaching a time value to the
 * URL to make sure that the image does update and not use the browser cache.
 *
 * @param string src              The source to insert into the image element.
 * @param string target           The target element.
 * @param optional bool no_cache  If set to true will append the time.
 *
 * @return bool  False to stop the browser loading anything.
 */
function showImage(src, target, no_cache)
{
    var img = document.getElementById(target);
    if (typeof no_cache == 'undefined') {
        no_cache = false;
    }

    if (no_cache) {
        var now = new Date();
        src = src + '&' + now.getTime();
    }

    img.src = src;

    return false;
}

/**
 * Adds to the given source the height/width field values for the given target.
 *
 * @param string src           The source to append the resize params to.
 * @param string target        The target element.
 * @param optional bool ratio  If set to true will append fix the ratio.
 *
 * @return string  The modified source to include the resize data.
 */
function getResizeSrc(src, target, ratio)
{
    var width = document.getElementById('_w_' + target).value;
    var height = document.getElementById('_h_' + target).value;
    if (typeof ratio == 'undefined') {
        ratio = 0;
    }

    src = src + '&' + 'v=' + width + '.' + height + '.' + ratio;

    return src;
}
