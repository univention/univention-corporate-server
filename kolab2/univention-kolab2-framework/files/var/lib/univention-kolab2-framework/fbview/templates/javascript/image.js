/**
 * Horde Image Javascript
 *
 * Provides the javascript to help during the uploading of images in Horde_Form.
 *
 * $Horde: horde/templates/javascript/image.js,v 1.3 2004/01/01 16:17:43 jan Exp $
 *
 * Copyright 2003-2004 Marko Djukic <marko@oblo.com>
 *
 * See the enclosed file COPYING for license information (GPL). If you did not
 * receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author Marko Djukic <marko@oblo.com>
 * @version $Revision: 1.1.2.1 $
 * @package horde
 */

/**
 * Changes the src of an image target, optionally attaching a time value to the
 * URL to make sure that the image does update and not use the browser cache.
 *
 * @param string src              The srouce to inserted into the image element.
 * @param string target           The target element.
 * @param optional bool no_cache  If set to true will append the time.
 *
 * @return bool  False to stop the browser loading anything.
 */
function showImage(src, target, no_cache)
{
    var img = document.getElementById(target);
    if (no_cache == undefined) {
        var no_cache = false;
    }

    if (no_cache) {
        var now = new Date();
        src = src + '<?php echo ini_get('arg_separator.output') ?>' + now.getTime();
    }

    img.src = src;

    return false;
}

/**
 * Adds to the given source the height/width field values for the given target.
 *
 * @param string src           The srouce to append to the resize params.
 * @param string target        The target element.
 * @param optional bool ratio  If set to true will append fix the ratio.
 *
 * @return string  The modified source to include the resize data.
 */
function getResizeSrc(src, target, ratio)
{
    var width = document.getElementById('_w_' + target).value;
    var height = document.getElementById('_h_' + target).value;
    if (ratio == undefined) {
        var ratio = 0;
    }

    src = src + '<?php echo ini_get('arg_separator.output') ?>' + 'v=' + width + '.' + height + '.' + ratio;

    return src;
}
