<?php
/**
 * The MIME_Viewer_richtext class renders out HTML text from text/richtext
 * content tags, (RFC 1896 [7.1.3]).
 *
 * A minimal richtext implementation is one that simply converts "<lt>" to
 * "<", converts CRLFs to SPACE, converts <nl> to a newline according to
 * local newline convention, removes everything between a <comment> command
 * and the next balancing </comment> command, and removes all other
 * formatting commands (all text enclosed in angle brackets).
 *
 * We implement the following tags:
 * <bold>, <italic>, <fixed>, <smaller>, <bigger>, <underline>, <center>,
 * <flushleft>, <flushright>, <indent>, <subscript>, <excerpt>, <paragraph>,
 * <signature>, <comment>, <no-op>, <lt>, <nl>
 *
 * The following tags are implemented differently than described in the RFC
 * (due to limitations in HTML output):
 * <heading> - Output as centered, bold text.
 * <footing> - Output as centered, bold text.
 * <np>      - Output as paragraph break.
 *
 * The following tags are NOT implemented:
 * <indentright>, <outdent>, <outdentright>, <samepage>, <iso-8859-X>,
 * <us-ascii>,
 *
 * $Horde: framework/MIME/MIME/Viewer/richtext.php,v 1.4.10.14 2009-01-06 15:23:21 jan Exp $
 *
 * Copyright 2004-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Michael Slusarz <slusarz@horde.org>
 * @package Horde_MIME_Viewer
 */
class MIME_Viewer_richtext extends MIME_Viewer {

    /**
     * Render out the currently set contents in HTML format.
     *
     * @param array $params  Any parameters the Viewer may need.
     *
     * @return string  The rendered contents.
     */
    function render($params = array())
    {
        if (($text = $this->mime_part->getContents()) === false) {
            return false;
        }

        if (trim($text) == '') {
            return $text;
        }

        /* Use str_ireplace() if using PHP 5.0+. */
        $has_str_ireplace = function_exists('str_ireplace');

        /* We add space at the beginning and end of the string as it will
         * make some regular expression checks later much easier (so we
         * don't have to worry about start/end of line characters). */
        $text = ' ' . $text . ' ';

        /* Remove everything between <comment> tags. */
        $text = preg_replace('/<comment.*>.*<\/comment>/Uis', '', $text);

        /* Remove any unrecognized tags in the text.  We don't need <no-op>
         * in $tags since it doesn't do anything anyway.  All <comment> tags
         * have already been removed. */
        $tags = '<bold><italic><fixed><smaller><bigger><underline><center><flushleft><flushright><indent><subscript><excerpt><paragraph><signature><lt><nl>';
        $text = strip_tags($text, $tags);

        /* <lt> becomes a '<'. CRLF becomes a SPACE. */
        if ($has_str_ireplace) {
            $text = str_ireplace(array('<lt>', "\r\n"), array('&lt;', ' '), $text);
        } else {
            $text = preg_replace(array('/<lt>/i', "/\r\n/"), array('&lt;', ' '), $text);
        }

        /* We try to protect against bad stuff here. */
        $text = @htmlspecialchars($text, ENT_QUOTES, $this->mime_part->getCharset());

        /* <nl> becomes a newline (<br />);
         * <np> becomes a paragraph break (<p />). */
        if ($has_str_ireplace) {
            $text = str_ireplace(array('&lt;nl&gt;', '&lt;np&gt;'), array('<br />', '<p />'), $text);
        } else {
            $text = preg_replace(array('/(?<!&lt;)&lt;nl.*&gt;/Uis', '/(?<!&lt;)&lt;np.*&gt;/Uis'), array('<br />', '<p />'), $text);
        }

        /* Now convert the known tags to html. Try to remove any tag
         * parameters to stop people from trying to pull a fast one. */
        $pattern = array(
            '/(?<!&lt;)&lt;bold.*&gt;(.*)&lt;\/bold&gt;/Uis',
            '/(?<!&lt;)&lt;italic.*&gt;(.*)&lt;\/italic&gt;/Uis',
            '/(?<!&lt;)&lt;fixed.*&gt;(.*)&lt;\/fixed&gt;/Uis',
            '/(?<!&lt;)&lt;smaller.*&gt;(.*)&lt;\/smaller&gt;/Uis',
            '/(?<!&lt;)&lt;bigger.*&gt;(.*)&lt;\/bigger&gt;/Uis',
            '/(?<!&lt;)&lt;underline.*&gt;(.*)&lt;\/underline&gt;/Uis',
            '/(?<!&lt;)&lt;center.*&gt;(.*)&lt;\/center&gt;/Uis',
            '/(?<!&lt;)&lt;flushleft.*&gt;(.*)&lt;\/flushleft&gt;/Uis',
            '/(?<!&lt;)&lt;flushright.*&gt;(.*)&lt;\/flushright&gt;/Uis',
            '/(?<!&lt;)&lt;indent.*&gt;(.*)&lt;\/indent&gt;/Uis',
            '/(?<!&lt;)&lt;excerpt.*&gt;(.*)&lt;\/excerpt&gt;/Uis',
            '/(?<!&lt;)&lt;subscript.*&gt;(.*)&lt;\/subscript&gt;/Uis',
            '/(?<!&lt;)&lt;superscript.*&gt;(.*)&lt;\/superscript&gt;/Uis',
            '/(?<!&lt;)&lt;heading.*&gt;(.*)&lt;\/heading&gt;/Uis',
            '/(?<!&lt;)&lt;footing.*&gt;(.*)&lt;\/footing&gt;/Uis',
            '/(?<!&lt;)&lt;paragraph.*&gt;(.*)&lt;\/paragraph&gt;/Uis',
            '/(?<!&lt;)&lt;signature.*&gt;(.*)&lt;\/signature&gt;/Uis',
        );
        $replace = array(
            '<span style="font-weight: bold">\1</span>',
            '<span style="font-style: italic">\1</span>',
            '<font face="fixed">\1</font>',
            '<span style="font-size: smaller">\1</span>',
            '<span style="font-size: larger">\1</span>',
            '<span style="text-decoration: underline">\1</span>',
            '<div align="center">\1</div>',
            '<div align="left">\1</div>',
            '<div align="right">\1</div>',
            '<blockquote>\1</blockquote>',
            '<cite>\1</cite>',
            '<sub>\1</sub>',
            '<sup>\1</sup>',
            '<br /><div align="center" style="font-weight: bold">\1</div><br />',
            '<br /><div align="center" style="font-weight: bold">\1</div><br />',
            '<p>\1</p>',
            '<address>\1</address>',
        );
        $text = preg_replace($pattern, $replace, $text);

        /* Now we remove the leading/trailing space we added at the start. */
        $text = substr($text, 1, -1);

        /* Wordwrap. */
        $text = str_replace(array("\t", '  ', "\n "), array('        ', ' &nbsp;', "\n&nbsp;"), $text);
        if ($text[0] == ' ') {
            $text = '&nbsp;' . substr($text, 1);
        }

        return '<p class="fixed">' . nl2br($text) . '</p>';
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
