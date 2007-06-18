<?php
/**
 * The MIME_Viewer_html class renders out HTML text with an effort to
 * remove potentially malicious code.
 *
 * $Horde: framework/MIME/MIME/Viewer/html.php,v 1.5 2004/04/24 13:55:11 jan Exp $
 *
 * Copyright 1999-2004 Anil Madhavapeddy <anil@recoil.org>
 * Copyright 1999-2004 Jon Parise <jon@horde.org>
 * Copyright 2002-2004 Michael Slusarz <slusarz@horde.org>
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author  Anil Madhavapeddy <anil@recoil.org>
 * @author  Jon Parise <jon@horde.org>
 * @author  Michael Slusarz <slusarz@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 * @package Horde_Mime_Viewer
 */
class MIME_Viewer_html extends MIME_Viewer {

    /**
     * Render out the currently set contents.
     *
     * @access public
     *
     * @param optional array $params  Any parameters the viewer may need.
     *
     * @return string  The rendered text.
     */
    function render($params = null)
    {
        return $this->_cleanHTML($this->mime_part->getContents());
    }

    /**
     * These regular expressions attempt to make HTML safe for
     * viewing. THEY ARE NOT PERFECT. If you enable HTML viewing,
     * you are opening a security hole. With the current state of
     * the web, I believe that the best we can do is to make sure
     * that people *KNOW* HTML is a security hole, clean up what
     * we can, and leave it at that.
     *
     * @access private
     *
     * @param string $data  The HTML data.
     *
     * @return string  The cleaned HTML data.
     */
    function _cleanHTML($data)
    {
        global $browser, $prefs;

        require_once 'Horde/MIME/Contents.php';
        $attachment = MIME_Contents::viewAsAttachment();

        /* Deal with <base> tags in the HTML, since they will screw up our
           own relative paths. */
        if (($i = stristr($data, '<base ')) && ($i = stristr($i, 'http')) &&
            ($j = strchr($i, '>'))) {
            $base = substr($i, 0, strlen($i) - strlen($j));
            $base = preg_replace('|(http.*://[^/]*/?).*|i', '\1', $base);

            if ($base[strlen($base) - 1] != '/') {
                $base .= '/';
            }
        }

        /* Change space entities to space characters. */
        $data = preg_replace('/&#(x0*20|0*32);?/i', ' ', $data);

        /* Nuke non-printable characters (a play in three acts). */

        /* Rule #1: If we have a semicolon, it is deterministically
         * detectable and fixable, without introducing collateral damage. */
        $data = preg_replace('/&#x?0*([9A-D]|1[0-3]);/i', '&nbsp;', $data);

        /* Rule #2: Hex numbers (usually having an x prefix) are also
         * deterministic, even if we don't have the semi. Note that
         * some browsers will treat &#a or &#0a as a hex number even
         * without the x prefix; hence /x?/ which will cover those
         * cases in this rule. */
        $data = preg_replace('/&#x?0*[9A-D]([^0-9A-F]|$)/i', '&nbsp\\1', $data);

        /* Rule #3: Decimal numbers without semi. The problem is that
         * some browsers will interpret &#10a as "\na", some as
         * "&#x10a" so we have to clean the &#10 to be safe for the
         * "\na" case at the expense of mangling a valid entity in
         * other cases. (Solution for valid HTML authors: always use
         * the semicolon.) */
        $data = preg_replace('/&#0*(9|1[0-3])([^0-9]|$)/i', '&nbsp\\2', $data);

        /* Remove overly long numeric entities. */
        $data = preg_replace('/&#x?0*[0-9A-F]{6,};?/i', '&nbsp;', $data);

        /* Remove everything outside of and including the <body> tag if
         * displaying inline. */
        if (!$attachment) {
            $data = preg_replace('/.*<body[^>]*>/si', '', $data);
            $data = preg_replace('/<\/body>.*/si', '', $data);
        }

        /* Get all attribute="javascript:foo()" tags. This is essentially
         * the regex /(=|url\()("?)[^>]*script:/ but expanded to catch
         * camouflage with spaces and entities. */
        $preg = '/((&#0*61;?|&#x0*3D;?|=)|' .
                '((u|&#0*85;?|&#x0*55;?|&#0*117;?|&#x0*75;?)\s*' .
                '(r|&#0*82;?|&#x0*52;?|&#0*114;?|&#x0*72;?)\s*' .
                '(l|&#0*76;?|&#x0*4c;?|&#0*108;?|&#x0*6c;?)\s*' .
                '(\()))\s*' .
                '(&#0*34;?|&#x0*22;?|"|&#0*39;?|&#x0*27;?|\')?' .
                '[^>]*\s*' .
                '(s|&#0*83;?|&#x0*53;?|&#0*115;?|&#x0*73;?)\s*' .
                '(c|&#0*67;?|&#x0*43;?|&#0*99;?|&#x0*63;?)\s*' .
                '(r|&#0*82;?|&#x0*52;?|&#0*114;?|&#x0*72;?)\s*' .
                '(i|&#0*73;?|&#x0*49;?|&#0*105;?|&#x0*69;?)\s*' .
                '(p|&#0*80;?|&#x0*50;?|&#0*112;?|&#x0*70;?)\s*' .
                '(t|&#0*84;?|&#x0*54;?|&#0*116;?|&#x0*74;?)\s*' .
                '(:|&#0*58;?|&#x0*3a;?)/i';
        $data = preg_replace($preg, '\1\8HordeCleaned', $data);

        /* Get all on<foo>="bar()". NEVER allow these. */
        $data = preg_replace('/(\s+[Oo][Nn]\w+)\s*=/', '\1HordeCleaned=', $data);

        /* Get all tags that might cause trouble - <object>, <embed>,
         * <base>, etc. Meta refreshes and iframes, too. */
        $malicious = array('|<([^>]*)s\s*c\s*r\s*i\s*p\s*t|i',
                           '|<([^>]*)embed|i',
                           '|<([^>]*)base[^line]|i',
                           '|<([^>]*)meta|i',
                           '|<([^>]*)j\sa\sv\sa|i',
                           '|<([^>]*)object|i',
                           '|<([^>]*)iframe|i');
        $data = preg_replace($malicious, '<HordeCleaned_tag', $data);

        /* Comment out style/link tags, only if we are viewing inline.
           NEVER show style tags to Netscape 4.x users since 1) the output
           will really, really suck and 2) there might be security issues. */
        if (!$attachment || 
            ($GLOBALS['browser']->isBrowser('mozilla') &&
             ($GLOBALS['browser']->getMajor() == 4))) {
            $orig_data = $data;
            $data = preg_replace('/\s+style\s*=/i', ' HordeCleaned=', $data);
            $data = preg_replace('|<style[^>]*>(?:\s*<\!--)*|i', '<!--', $data);
            $data = preg_replace('|(?:-->\s*)*</style>|i', '-->', $data);
            $data = preg_replace('|(<link[^>]*>)|i', '<!-- $1 -->', $data);
        }

        /* A few other matches. */
        $data = preg_replace('|<([^>]*)&{.*}([^>]*)>|', '<&{;}\3>', $data);
        $data = preg_replace('|<([^>]*)mocha:([^>]*)>|i', '<HordeCleaned\2>', $data);

        /* Attempt to fix paths that were relying on a <base> tag. */
        if (!empty($base)) {
            $data = preg_replace('|src="/|i', 'src="' . $base, $data);
            $data = preg_replace('|src=\'/|i', 'src=\'' . $base, $data);
            $data = preg_replace('|src=[^\'"]/|i', 'src=' . $base, $data);

            $data = preg_replace('|href= *"/|i', 'href="' . $base, $data);
            $data = preg_replace('|href= *\'/|i', 'href=\'' . $base, $data);
            $data = preg_replace('|href= *[^\'"]/|i', 'href=' . $base, $data);
        }

        return $data;
    }

    /**
     * Return the content-type of the rendered text.
     *
     * @access public
     *
     * @return string  The MIME Content-Type.
     */
    function getType()
    {
        require_once 'Horde/MIME/Contents.php';
        return (MIME_Contents::viewAsAttachment()) ? $this->mime_part->getType(true) : 'text/html';
    }

}
