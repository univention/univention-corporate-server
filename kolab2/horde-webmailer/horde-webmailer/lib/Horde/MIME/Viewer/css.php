<?php

require_once dirname(__FILE__) . '/source.php';

/**
 * The MIME_Viewer_css class renders CSS source as HTML with an effort
 * to remove potentially malicious code.
 *
 * $Horde: framework/MIME/MIME/Viewer/css.php,v 1.1.10.12 2009-01-06 15:23:21 jan Exp $
 *
 * Copyright 2004-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @since   Horde 3.0
 * @package Horde_MIME_Viewer
 */
class MIME_Viewer_css extends MIME_Viewer_source {

    /**
     * Render out the currently set contents.
     *
     * @param array $params  Any parameters the viewer may need.
     *
     * @return string  The rendered text.
     */
    function render($params = null)
    {
        $css = htmlspecialchars($this->mime_part->getContents(), ENT_NOQUOTES);
        $css = preg_replace_callback('!(}|\*/).*?({|/\*)!s', array($this, '_handles'), $css);
        $css = preg_replace_callback('!{[^}]*}!s', array($this, '_attributes'), $css);
        $css = preg_replace_callback('!/\*.*?\*/!s', array($this, '_comments'), $css);
        $css = trim($css);

        // Educated Guess at whether we are inline or not.
        if (headers_sent() || ob_get_length()) {
            return $this->lineNumber($css);
        } else {
            return Util::bufferOutput('require', $GLOBALS['registry']->get('templates', 'horde') . '/common-header.inc') .
                $this->lineNumber($css) .
                Util::bufferOutput('require', $GLOBALS['registry']->get('templates', 'horde') . '/common-footer.inc');
        }
    }

    function _comments($matches)
    {
        $patterns[] = '!(http://[/\w-.]+)!s';
        $replaces[] = '<a href="\\1">\\1</a>';

        $comments = preg_replace($patterns, $replaces, $matches[0]);

        return '<span class="comment">' . $comments . '</span>';
    }

    function _attributes($matches)
    {
        // Attributes.
        $patterns[] = '!([-\w]+\s*):!s';
        $replaces[] = '<span class="attr"">\\1</span>:';

        // Values.
        $patterns[] = '!:(\s*)(.+?)(\s*;)!s';
        $replaces[] = ':\\1<span class="value">\\2</span><span class="eol">\\3</span>';

        // URLs.
        $patterns[] = '!(url\([\'"]?)(.*?)([\'"]?\))!s';
        $replaces[] = '<span class="url">\\1<span class="file">\\2</span>\\3</span>';

        // Colors.
        $patterns[] = '!(#[[:xdigit:]]{3,6})!s';
        $replaces[] = '<span class="color">\\1</span>';

        // Parentheses.
        $patterns[] = '!({|})!s';
        $replaces[] = '<span class="parentheses">\\1</span>';

        // Unity.
        $patterns[] = '!(em|px|%)\b!s';
        $replaces[] = '<em>\\1</em>';

        return preg_replace($patterns, $replaces, $matches[0]);
    }

    function _handles($matches)
    {
        // HTML Tags.
        $patterns[] = '!\b(body|h\d|a|span|div|acronym|small|strong|em|pre|ul|ol|li|p)\b!s';
        $replaces[] = '<span class="htag">\\1</span>\\2';

        // IDs.
        $patterns[] = '!(#[-\w]+)!s';
        $replaces[] = '<span class="id">\\1</span>';

        // Class.
        $patterns[] = '!(\.[-\w]+)\b!s';
        $replaces[] = '<span class="class">\\1</span>';

        // METAs.
        $patterns[] = '!(:link|:visited|:hover|:active|:first-letter)!s';
        $replaces[] = '<span class="metac">\\1</span>';

        return preg_replace($patterns, $replaces, $matches[0]);
    }

}
