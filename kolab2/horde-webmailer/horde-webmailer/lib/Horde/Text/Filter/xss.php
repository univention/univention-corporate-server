<?php
/**
 * This filter attempts to make HTML safe for viewing. IT IS NOT PERFECT. If
 * you enable HTML viewing, you are opening a security hole. With the current
 * state of the web, I believe that the best we can do is to make sure that
 * people *KNOW* HTML is a security hole, clean up what we can, and leave it
 * at that.
 *
 * $Horde: framework/Text_Filter/Filter/xss.php,v 1.1.2.19 2009-11-26 00:38:41 slusarz Exp $
 *
 * Copyright 2004-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Jan Schneider <jan@horde.org>
 * @since   Horde 3.1
 * @package Horde_Text
 */
class Text_Filter_xss extends Text_Filter {

    /**
     * Filter parameters.
     *
     * @var array
     */
    var $_params = array('body_only' => true,
                         'replace' => 'XSSCleaned',
                         'strip_styles' => true,
                         'strip_style_attributes' => true);

    /**
     * Returns a hash with replace patterns.
     *
     * @return array  Patterns hash.
     */
    function getPatterns()
    {
        $patterns = array();

        /* Remove all control characters. */
        $patterns['/[\x00-\x08\x0e-\x1f]/'] = '';

        /* Removes HTML comments (including some scripts & styles). */
        if ($this->_params['strip_styles']) {
            $patterns['/<!--.*?-->/s'] = '';
        }

        /* Change space entities to space characters. */
        $patterns['/&#(?:x0*20|0*32);?/i'] = ' ';

        /* If we have a semicolon, it is deterministically detectable and
         * fixable, without introducing collateral damage. */
        $patterns['/&#x?0*(?:[9A-D]|1[0-3]);/i'] = '&nbsp;';

        /* Hex numbers (usually having an x prefix) are also deterministic,
         * even if we don't have the semi. Note that some browsers will treat
         * &#a or &#0a as a hex number even without the x prefix; hence /x?/
         * which will cover those cases in this rule. */
        $patterns['/&#x?0*[9A-D]([^0-9A-F]|$)/i'] = '&nbsp\\1';

        /* Decimal numbers without trailing semicolons. The problem is that
         * some browsers will interpret &#10a as "\na", some as "&#x10a" so we
         * have to clean the &#10 to be safe for the "\na" case at the expense
         * of mangling a valid entity in other cases. (Solution for valid HTML
         * authors: always use the semicolon.) */
        $patterns['/&#0*(?:9|1[0-3])([^0-9]|$)/i'] = '&nbsp\\1';

        /* Remove overly long numeric entities. */
        $patterns['/&#x?0*[0-9A-F]{6,};?/i'] = '&nbsp;';

        /* Remove everything outside of and including the <html> and <body>
         * tags. */
        if ($this->_params['body_only']) {
            $patterns['/^.*<(?:body|html)[^>]*>/si'] = '';
            $patterns['/<\/(?:body|html)>.*$/si'] = '';
        }

        /* Get all attribute="javascript:foo()" tags. This is essentially the
         * regex /(=|url\()("?)[^>]*script:/ but expanded to catch camouflage
         * with spaces and entities. */
        $preg = '/((=|&#0*61;?|&#x0*3D;?)|' .
                '((u|&#0*85;?|&#x0*55;?|&#0*117;?|&#x0*75;?|\\\\0*75)\s*' .
                '(r|&#0*82;?|&#x0*52;?|&#0*114;?|&#x0*72;?|\\\\0*72)\s*' .
                '(l|&#0*76;?|&#x0*4c;?|&#0*108;?|&#x0*6c;?|\\\\0*6c)\s*' .
                '(\(|\\\\0*28)))\s*' .
                '(\'|&#0*34;?|&#x0*22;?|"|&#0*39;?|&#x0*27;?)?' .
                '[^>]*\s*' .
                '(s|&#0*83;?|&#x0*53;?|&#0*115;?|&#x0*73;?|\\\\0*73)\s*' .
                '(c|&#0*67;?|&#x0*43;?|&#0*99;?|&#x0*63;?|\\\\0*63)\s*' .
                '(r|&#0*82;?|&#x0*52;?|&#0*114;?|&#x0*72;?|\\\\0*72)\s*' .
                '(i|&#0*73;?|&#x0*49;?|&#0*105;?|&#x0*69;?|\\\\0*69)\s*' .
                '(p|&#0*80;?|&#x0*50;?|&#0*112;?|&#x0*70;?|\\\\0*70)\s*' .
                '(t|&#0*84;?|&#x0*54;?|&#0*116;?|&#x0*74;?|\\\\0*74)\s*' .
                '(:|&#0*58;?|&#x0*3a;?|\\\\0*3a)/i';
        $patterns[$preg] = '\1\8' . $this->_params['replace'];

        /* Get all on<foo>="bar()". NEVER allow these. */
        $patterns['/([\s"\'\/]+' .
                  '(o|&#0*79;?|&#0*4f;?|&#0*111;?|&#0*6f;?)' .
                  '(n|&#0*78;?|&#0*4e;?|&#0*110;?|&#0*6e;?)' .
                  '\w+)[^=a-z0-9"\'>]*=/i'] = '\1' . $this->_params['replace'] . '=';

        /* Remove all scripts since they might introduce garbage if they are
         * not quoted properly. */
        $patterns['|<script[^>]*>.*?</script>|is'] = '<' . $this->_params['replace'] . '_script />';

        /* Get all tags that might cause trouble - <object>, <embed>,
         * <applet>, <base>, etc. Meta refreshes and iframes, too. */
        $malicious = array(
            '/<([^>a-z]*)' .
            '(?:s|&#0*83;?|&#x0*53;?|&#0*115;?|&#x0*73;?)\s*' .
            '(?:c|&#0*67;?|&#x0*43;?|&#0*99;?|&#x0*63;?)\s*' .
            '(?:r|&#0*82;?|&#x0*52;?|&#0*114;?|&#x0*72;?)\s*' .
            '(?:i|&#0*73;?|&#x0*49;?|&#0*105;?|&#x0*69;?)\s*' .
            '(?:p|&#0*80;?|&#x0*50;?|&#0*112;?|&#x0*70;?)\s*' .
            '(?:t|&#0*84;?|&#x0*54;?|&#0*116;?|&#x0*74;?)(\s*)/i',

            '/<([^>a-z]*)' .
            '(?:e|&#0*69;?|&#0*45;?|&#0*101;?|&#0*65;?)\s*' .
            '(?:m|&#0*77;?|&#0*4d;?|&#0*109;?|&#0*6d;?)\s*' .
            '(?:b|&#0*66;?|&#0*42;?|&#0*98;?|&#0*62;?)\s*' .
            '(?:e|&#0*69;?|&#0*45;?|&#0*101;?|&#0*65;?)\s*' .
            '(?:d|&#0*68;?|&#0*44;?|&#0*100;?|&#0*64;?)(\s*)/i',

            '/<([^>a-z]*)' .
            '(?:x|&#0*88;?|&#0*58;?|&#0*120;?|&#0*78;?)\s*' .
            '(?:m|&#0*77;?|&#0*4d;?|&#0*109;?|&#0*6d;?)\s*' .
            '(?:l|&#0*76;?|&#x0*4c;?|&#0*108;?|&#x0*6c;?)(\s*)/i',

            '/<([^>a-z]*)\?([^>a-z]*)' .
            '(?:i|&#0*73;?|&#x0*49;?|&#0*105;?|&#x0*69;?)\s*' .
            '(?:m|&#0*77;?|&#0*4d;?|&#0*109;?|&#0*6d;?)\s*' .
            '(?:p|&#0*80;?|&#x0*50;?|&#0*112;?|&#x0*70;?)\s*' .
            '(?:o|&#0*79;?|&#0*4f;?|&#0*111;?|&#0*6f;?)\s*' .
            '(?:r|&#0*82;?|&#x0*52;?|&#0*114;?|&#x0*72;?)\s*' .
            '(?:t|&#0*84;?|&#x0*54;?|&#0*116;?|&#x0*74;?)(\s*)/i',

            '/<([^>a-z]*)' .
            '(?:b|&#0*66;?|&#0*42;?|&#0*98;?|&#0*62;?)\s*' .
            '(?:a|&#0*65;?|&#0*41;?|&#0*97;?|&#0*61;?)\s*' .
            '(?:s|&#0*83;?|&#x0*53;?|&#0*115;?|&#x0*73;?)\s*' .
            '(?:e|&#0*69;?|&#0*45;?|&#0*101;?|&#0*65;?)(\s*)' .
            '[^line]/i',

            '/<([^>a-z]*)' .
            '(?:m|&#0*77;?|&#0*4d;?|&#0*109;?|&#0*6d;?)\s*' .
            '(?:e|&#0*69;?|&#0*45;?|&#0*101;?|&#0*65;?)\s*' .
            '(?:t|&#0*84;?|&#x0*54;?|&#0*116;?|&#x0*74;?)\s*' .
            '(?:a|&#0*65;?|&#0*41;?|&#0*97;?|&#0*61;?)(\s*)/i',

            '/<([^>a-z]*)' .
            '(?:j|&#0*74;?|&#0*4a;?|&#0*106;?|&#0*6a;?)\s*' .
            '(?:a|&#0*65;?|&#0*41;?|&#0*97;?|&#0*61;?)\s*' .
            '(?:v|&#0*86;?|&#0*56;?|&#0*118;?|&#0*76;?)\s*' .
            '(?:a|&#0*65;?|&#0*41;?|&#0*97;?|&#0*61;?)(\s*)/i',

            '/<([^>a-z]*)' .
            '(?:o|&#0*79;?|&#0*4f;?|&#0*111;?|&#0*6f;?)\s*' .
            '(?:b|&#0*66;?|&#0*42;?|&#0*98;?|&#0*62;?)\s*' .
            '(?:j|&#0*74;?|&#0*4a;?|&#0*106;?|&#0*6a;?)\s*' .
            '(?:e|&#0*69;?|&#0*45;?|&#0*101;?|&#0*65;?)\s*' .
            '(?:c|&#0*67;?|&#x0*43;?|&#0*99;?|&#x0*63;?)\s*' .
            '(?:t|&#0*84;?|&#x0*54;?|&#0*116;?|&#x0*74;?)(\s*)/i',

            '/<([^>a-z]*)' .
            '(?:a|&#0*65;?|&#0*41;?|&#0*97;?|&#0*61;?)\s*' .
            '(?:p|&#0*80;?|&#x0*50;?|&#0*112;?|&#x0*70;?)\s*' .
            '(?:p|&#0*80;?|&#x0*50;?|&#0*112;?|&#x0*70;?)\s*' .
            '(?:l|&#0*76;?|&#x0*4c;?|&#0*108;?|&#x0*6c;?)\s*' .
            '(?:e|&#0*69;?|&#0*45;?|&#0*101;?|&#0*65;?)\s*' .
            '(?:t|&#0*84;?|&#x0*54;?|&#0*116;?|&#x0*74;?)(\s*)/i',

            '/<([^>a-z]*)' .
            '(?:l|&#0*76;?|&#x0*4c;?|&#0*108;?|&#x0*6c;?)\s*' .
            '(?:a|&#0*65;?|&#0*41;?|&#0*97;?|&#0*61;?)\s*' .
            '(?:y|&#0*89;?|&#0*59;?|&#0*121;?|&#0*79;?)\s*' .
            '(?:e|&#0*69;?|&#0*45;?|&#0*101;?|&#0*65;?)\s*' .
            '(?:r|&#0*82;?|&#x0*52;?|&#0*114;?|&#x0*72;?)(\s*)/i',

            '/<([^>a-z]*)' .
            '(?:i|&#0*73;?|&#x0*49;?|&#0*105;?|&#x0*69;?)?\s*' .
            '(?:f|&#0*70;?|&#0*46;?|&#0*102;?|&#0*66;?)\s*' .
            '(?:r|&#0*82;?|&#x0*52;?|&#0*114;?|&#x0*72;?)\s*' .
            '(?:a|&#0*65;?|&#0*41;?|&#0*97;?|&#0*61;?)\s*' .
            '(?:m|&#0*77;?|&#0*4d;?|&#0*109;?|&#0*6d;?)\s*' .
            '(?:e|&#0*69;?|&#0*45;?|&#0*101;?|&#0*65;?)(\s*)/i');

        foreach ($malicious as $pattern) {
            $patterns[$pattern] = '<$1' . $this->_params['replace'] . '_tag$2';
        }

        /* Strip out data URLs living in an A HREF element (Bug #8715). */
        $malicious = '/<((?:a|&#0*65;?|&#0*41;?|&#0*97;?|&#0*61;?)\b[^>]+?)' .
            '(?:h|&#0*72;?|&#0*48;?|&#0*104;?|&#0*68;?)\s*' .
            '(?:r|&#0*82;?|&#x0*52;?|&#0*114;?|&#x0*72;?)\s*' .
            '(?:e|&#0*69;?|&#0*45;?|&#0*101;?|&#0*65;?)\s*' .
            '(?:f|&#0*70;?|&#0*46;?|&#0*102;?|&#0*66;?)\s*=' .
            '("|\')?\s*data:(?(2)[^"\')>]*|[^\s)>]*)(?(2)\\2)/is';
        $patterns[$malicious] = '<$1';

        /* Comment out style/link tags. */
        if ($this->_params['strip_styles']) {
            if ($this->_params['strip_style_attributes']) {
                $patterns['/(\s+|([\'"]))style\s*=/i'] = '$2 ' . $this->_params['replace'] . '=';
            }
            $patterns['|<style[^>]*>(?:\s*<\!--)*|i'] = '<!--';
            $patterns['|(?:-->\s*)*</style>|i'] = '-->';
            $patterns['|(<link[^>]*>)|i'] = '<!-- $1 -->';
        }

        /* A few other matches. */
        $patterns['|<([^>]*)&{.*}([^>]*)>|'] = '<\1&{;}\2>';
        $patterns['|<([^>]*)mocha:([^>]*)>|i'] = '<\1' . $this->_params['replace'] . ':\2>';
        $patterns['/<(([^>]*)|(style[^>]*>[^<]*))binding:((?(3)[^<]*<\/style)[^>]*)>/i'] = '<\1' . $this->_params['replace'] . ':\4>';

        return array('regexp' => $patterns);
    }

    /**
     * Executes any code necessary before applying the filter patterns.
     *
     * @param string $text  The text before the filtering.
     *
     * @return string  The modified text.
     */
    function preProcess($text)
    {
        // As of PHP 5.2, backtrack limits have been set to an unreasonably
        // low number. The body check will often times trigger backtrack
        // errors so up the backtrack limit if we are doing this match.
        if ($this->_params['body_only'] && ini_get('pcre.backtrack_limit')) {
            ini_set('pcre.backtrack_limit', 5000000);
        }

        return $text;
    }

    /**
     * Executes any code necessary after applying the filter patterns.
     *
     * @param string $text  The text after the filtering.
     *
     * @return string  The modified text.
     */
    function postProcess($text)
    {
        ini_restore('pcre.backtrack_limit');
        return $text;
    }

}
