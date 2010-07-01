<?php
/**
 * @category Horde
 * @package  Horde_Text_Textile
 */

/**
 * References:
 *   http://www.textism.com/tools/textile/
 *   http://en.wikipedia.org/wiki/Textile_(markup_language)
 *   http://hobix.com/textile/
 *   http://whytheluckystiff.net/ruby/redcloth/
 *   http://redcloth.rubyforge.org/rdoc/
 *   http://code.whytheluckystiff.net/redcloth/browser/trunk/test/textism.yml
 *
 * Example: get XHTML from a given Textile-markup string ($string)
 *   $textile = new Horde_Text_Textile;
 *   echo $textile->toHtml($string);
 *
 * @category Horde
 * @package  Horde_Text_Textile
 */
class Horde_Text_Textile {

    /**
     * A_HLGN
     */
    const REGEX_A_HLGN = '(?:\<(?!>)|(?<!<)\>|\<\>|\=|[()]+(?! ))';

    /**
     * A_VLGN
     */
    const REGEX_A_VLGN = '[\-^~]';

    /**
     * '(?:' . A_HLGN . '|' . A_VLGN . ')*'
     */
    const REGEX_A = '(?:(?:\<(?!>)|(?<!<)\>|\<\>|\=|[()]+(?! ))|[\-^~])*';

    /**
     * '(?:' . S_CSPN . '|' . S_RSPN . ')*'
     */
    const REGEX_S = '(?:(?:\\\\\d+)|(?:\/\d+))*';

    /**
     * '(?:' . C_CLAS . '|' . C_STYL . '|' . C_LNGE . '|' . A_HLGN . ')*'
     */
    const REGEX_C = '(?:(?:\([^)]+\))|(?:\{[^}]+\})|(?:\[[^]]+\])|(?:\<(?!>)|(?<!<)\>|\<\>|\=|[()]+(?! )))*';

    /**
     * PUNCT
     */
    const REGEX_PUNCT = '\!"#\$%&\'\*\+,-\.\/\:;\=\?@\\\^_`\|~';

    /**
     * LINK_RE
     */
    const REGEX_URL = '[\w"$\-_.+!*\'(),";\/?:@=&%#{}|\\^~\[\]`]';

    /**
     * Block tags
     */
    const REGEX_BLOCK_TAGS = 'bq|bc|notextile|pre|h[1-6]|fn\d+|p';

    /**
     * Glyphs. Can be overridden if you want to substitute different
     * entities.
     */
    public static $GLYPH_QUOTE_SINGLE_OPEN = '&#8216;';
    public static $GLYPH_QUOTE_SINGLE_CLOSE = '&#8217;';
    public static $GLYPH_QUOTE_DOUBLE_OPEN = '&#8220;';
    public static $GLYPH_QUOTE_DOUBLE_CLOSE = '&#8221;';
    public static $GLYPH_APOSTROPHE = '&#8217;';
    public static $GLYPH_PRIME = '&#8242;';
    public static $GLYPH_PRIME_DOUBLE = '&#8243;';
    public static $GLYPH_ELLIPSIS = '&#8230;';
    public static $GLYPH_EMDASH = '&#8212;';
    public static $GLYPH_ENDASH = '&#8211;';
    public static $GLYPH_DIMENSION = '&#215;';
    public static $GLYPH_TRADEMARK = '&#8482;';
    public static $GLYPH_REGISTERED = '&#174;';
    public static $GLYPH_COPYRIGHT = '&#169;';
    public static $GLYPH_RETURN_ARROW = '&#8617;';

    /**
     * Show images? On by default.
     *
     * @var boolean
     */
    public $images = true;

    /**
     * Rel attribute for links (ex: nofollow).
     *
     * @var string
     */
    public $rel = '';

    /**
     * Shelf of values being processed.
     *
     * @var array
     */
    protected $_shelf = array();

    public function transform($text, $rel = '')
    {
        if ($rel) {
            $this->rel = ' rel="' . $rel . '" ';
        }

        $text = $this->cleanWhiteSpace($text);
        $text = $this->getRefs($text);
        $text = $this->block($text);

        return $this->retrieve($text);
    }

    /**
     * parse block attributes
     * @ignore
     */
    public function parseBlockAttributes($in, $element = '')
    {
        $style = '';
        $class = '';
        $lang = '';
        $colspan = '';
        $rowspan = '';
        $id = '';
        $atts = '';

        if (!empty($in)) {
            $matched = $in;
            if ($element == 'td') {
                if (preg_match("/\\\\(\d+)/", $matched, $csp)) $colspan = $csp[1];
                if (preg_match("/\/(\d+)/", $matched, $rsp)) $rowspan = $rsp[1];
            }

            if ($element == 'td' || $element == 'tr') {
                if (preg_match('/(' . self::REGEX_A_VLGN . ')/', $matched, $vert))
                    $style[] = 'vertical-align:' . $this->vAlign($vert[1]) . ';';
            }

            if (preg_match('/\{([^}]*)\}/', $matched, $sty)) {
                $style[] = rtrim($sty[1], ';') . ';';
                $matched = str_replace($sty[0], '', $matched);
            }

            if (preg_match('/\[([^]]+)\]/U', $matched, $lng)) {
                $lang = $lng[1];
                $matched = str_replace($lng[0], '', $matched);
            }

            if (preg_match('/\(([^()]+)\)/U', $matched, $cls)) {
                $class = $cls[1];
                $matched = str_replace($cls[0], '', $matched);
            }

            if (preg_match('/([(]+)/', $matched, $pl)) {
                $style[] = 'padding-left:' . strlen($pl[1]) . 'em;';
                $matched = str_replace($pl[0], '', $matched);
            }

            if (preg_match('/([)]+)/', $matched, $pr)) {
                $style[] = 'padding-right:' . strlen($pr[1]) . 'em;';
                $matched = str_replace($pr[0], '', $matched);
            }

            if (preg_match('/(' . self::REGEX_A_HLGN . ')/', $matched, $horiz)) {
                $style[] = 'text-align:' . $this->hAlign($horiz[1]) . ';';
            }

            if (preg_match('/^(.*)#(.*)$/', $class, $ids)) {
                $id = $ids[2];
                $class = $ids[1];
            }

            return
                ($style     ? ' style="'   . implode('', $style) . '"' : '')
                . ($class   ? ' class="'   . $class              . '"' : '')
                . ($lang    ? ' lang="'    . $lang               . '"' : '')
                . ($id      ? ' id="'      . $id                 . '"' : '')
                . ($colspan ? ' colspan="' . $colspan            . '"' : '')
                . ($rowspan ? ' rowspan="' . $rowspan            . '"' : '');
        }

        return '';
    }

    /**
     * @ignore
     */
    public function hasRawText($text)
    {
        // Checks whether the text has text not already enclosed by a
        // block tag.
        $r = trim(preg_replace('@<(p|blockquote|div|form|table|ul|ol|pre|h\d)[^>]*?>.*</\1>@s', '', trim($text)));
        $r = trim(preg_replace('@<\/?(p|blockquote|div|form|table|ul|ol|pre|h\d)[^>]*?\/?>@s', '', $r));
        $r = trim(preg_replace('@<(hr|br)[^>]*?/>@', '', $r));
        return '' != $r;
    }

    /**
     * @ignore
     */
    public function table($text)
    {
        $text = $text . "\n\n";
        return preg_replace_callback("/^(?:table(_?" . self::REGEX_S . self::REGEX_A . self::REGEX_C . ")\. ?\n)?^(" . self::REGEX_A . self::REGEX_C . "\.? ?\|.*\|)\n\n/smU",
                                     array($this, 'fTable'), $text);
    }

    /**
     * @ignore
     */
    public function fTable($matches)
    {
        $tatts = $this->parseBlockAttributes($matches[1], 'table');

        foreach (preg_split("/\|$/m", $matches[2], -1, PREG_SPLIT_NO_EMPTY) as $row) {
            if (preg_match("/^(" . self::REGEX_A . self::REGEX_C . "\. )(.*)/m", ltrim($row), $rmtch)) {
                $ratts = $this->parseBlockAttributes($rmtch[1], 'tr');
                $row = $rmtch[2];
            } else {
                $ratts = '';
            }
            $cells = array();
            foreach (explode('|', $row) as $cell) {
                $ctyp = 'd';
                if (preg_match("/^_/", $cell)) {
                    $ctyp = 'h';
                }
                if (preg_match("/^(_?" . self::REGEX_S . self::REGEX_A . self::REGEX_C . "\. )(.*)/", $cell, $cmtch)) {
                    $catts = $this->parseBlockAttributes($cmtch[1], 'td');
                    $cell = $cmtch[2];
                } else {
                    $catts = '';
                }

                $cell = $this->paragraph($this->span($cell));
                if (trim($cell) != '') {
                    $cells[] = "\t\t\t<t$ctyp$catts>$cell</t$ctyp>";
                }
            }
            $rows[] = "\t\t<tr$ratts>\n" . implode("\n", $cells) . ($cells ? "\n" : '') . "\t\t</tr>";
            unset($cells, $catts);
        }
        return "\t<table$tatts>\n" . implode("\n", $rows) . "\n\t</table>\n\n";
    }

    /**
     * @ignore
     */
    public function lists($text)
    {
        return preg_replace_callback("/^([#*]+" . self::REGEX_C . ".*)$(?![^#*])/smU", array($this, 'fList'), $text);
    }

    /**
     * @ignore
     */
    public function fList($m)
    {
        $out = array();
        $lines = explode("\n", $m[0]);
        for ($i = 0, $i_max = count($lines); $i < $i_max; $i++) {
            $line = $lines[$i];
            $nextline = isset($lines[$i + 1]) ? $lines[$i + 1] : false;

            if (preg_match("/^([#*]+)(" . self::REGEX_A . self::REGEX_C . ") (.*)$/s", $line, $m)) {
                list(, $tl, $atts, $content) = $m;
                $nl = '';
                if (preg_match("/^([#*]+)\s.*/", $nextline, $nm)) {
                    $nl = $nm[1];
                }
                $level = strlen($tl);
                if (!isset($lists[$tl])) {
                    $lists[$tl] = true;
                    $atts = $this->parseBlockAttributes($atts);
                    $line = str_repeat("\t", $level) . '<' . $this->lT($tl) . "l$atts>\n" . str_repeat("\t", $level + 1) . '<li>' . $this->paragraph($content);
                } else {
                    $line = str_repeat("\t", $level + 1) . '<li>' . $this->paragraph($content);
                }

                if (strlen($nl) <= strlen($tl)) {
                    $line .= '</li>';
                }
                foreach (array_reverse($lists) as $k => $v) {
                    if (strlen($k) > strlen($nl)) {
                        $line .= "\n" . str_repeat("\t", $level--) . '</' . $this->lT($k) . 'l>';
                        if (strlen($k) > 1) {
                            $line .= '</li>';
                        }
                        unset($lists[$k]);
                    }
                }
            }

            $out[] = $line;
        }

        return implode("\n", $out);
    }

    /**
     * @ignore
     */
    public function lT($in)
    {
        return substr($in, 0, 1) == '#' ? 'o' : 'u';
    }

    /**
     * @ignore
     */
    public function doPBr($in)
    {
        return preg_replace_callback('@<(p)([^>]*?)>(.*)(</\1>)@s', array($this, 'doBr'), $in);
    }

    /**
     * @ignore
     */
    public function doBr($m)
    {
        $content = preg_replace("@(.+)(?<!<br>|<br />)\n(?![#*\s|])@", "\$1<br />\n", $m[3]);
        return '<' . $m[1] . $m[2] . '>' . $content . $m[4];
    }

    /**
     * @ignore
     */
    public function block($text)
    {
        $tag = 'p';
        $atts = $cite = $graf = $ext = '';

        $text = explode("\n\n", $text);
        foreach ($text as $line) {
            $anon = 0;
            if (preg_match('/^(' . self::REGEX_BLOCK_TAGS . ')(' . self::REGEX_A . self::REGEX_C . ')\.(\.?)(?::(\S+))? (.*)$/s', $line, $m)) {
                if ($ext) {
                    // last block was extended, so close it
                    $out[count($out) - 1] .= $c1;
                }
                // new block
                list(, $tag, $atts, $ext, $cite, $graf) = $m;
                list($o1, $o2, $content, $c2, $c1) = $this->fBlock(array(0, $tag, $atts, $ext, $cite, $graf));

                // leave off c1 if this block is extended, we'll close
                // it at the start of the next block
                if ($ext) {
                    $line = $o1 . $o2 . $content . $c2;
                } else {
                    $line = $o1 . $o2 . $content . $c2 . $c1;
                }
            } else {
                // anonymous block
                $anon = 1;
                if ($ext || !preg_match('/^ /', $line)) {
                    list($o1, $o2, $content, $c2, $c1) = $this->fBlock(array(0, $tag, $atts, $ext, $cite, $line));
                    // skip $o1/$c1 because this is part of a
                    // continuing extended block
                    if ($tag == 'p' && !$this->hasRawText($content)) {
                        $line = $content;
                    } else {
                        $line = $o2 . $content . $c2;
                    }
                } else {
                   $line = $this->paragraph($line);
                }
            }

            $line = preg_replace('/<br>/', '<br />', $this->doPBr($line));

            if ($ext && $anon) {
                $out[count($out) - 1] .= "\n" . $line;
            } else {
                $out[] = $line;
            }

            if (!$ext) {
                $tag = 'p';
                $atts = '';
                $cite = '';
                $graf = '';
            }
        }
        if ($ext) {
            $out[count($out) - 1] .= $c1;
        }
        return implode("\n\n", $out);
    }

    /**
     * @ignore
     */
    public function fBlock($m)
    {
        list(, $tag, $atts, $ext, $cite, $content) = $m;
        $atts = $this->parseBlockAttributes($atts);

        $o1 = $o2 = $c2 = $c1 = '';

        if (preg_match('/fn(\d+)/', $tag, $fns)) {
            $tag = 'p';
            $fnid = $fns[1];
            $atts .= ' id="fn' . $fnid . '"';
            $content = '<sup>' . $fns[1] . '</sup> ' . $content . ' <a href="#fnr' . $fnid . '">' . self::$GLYPH_RETURN_ARROW . '</a>';
        }

        if ($tag == 'bq') {
            $cite = $this->checkRefs($cite);
            $cite = ($cite != '') ? ' cite="' . $cite . '"' : '';
            $o1 = '<blockquote' . $cite . $atts . ">\n";
            $o2 = "<p$atts>";
            $c2 = '</p>';
            $c1 = "\n</blockquote>";
        } elseif ($tag == 'bc') {
            $o1 = "<pre$atts>";
            $o2 = "<code$atts>";
            $c2 = '</code>';
            $c1 = '</pre>';
            $content = $this->shelve($this->encodeHtml(rtrim($content, "\n") . "\n"));
        } elseif ($tag == 'notextile') {
            $content = $this->shelve($content);
            $o1 = $o2 = '';
            $c1 = $c2 = '';
        } elseif ($tag == 'pre') {
            $content = $this->shelve($this->encodeHtml(rtrim($content, "\n") . "\n"));
            $o1 = "<pre$atts>";
            $o2 = $c2 = '';
            $c1 = '</pre>';
        } else {
            $o2 = "<$tag$atts>";
            $c2 = "</$tag>";
        }

        return array($o1, $o2, $this->paragraph($content), $c2, $c1);
    }

    /**
     * Handle normal paragraph text.
     * @ignore
     */
    public function paragraph($text)
    {
        $text = $this->code($this->noTextile($text));
        $text = $this->links($text);
        if ($this->images) {
            $text = $this->image($text);
        }

        $text = $this->table($this->lists($text));
        $text = $this->glyphs($this->footnoteRef($this->span($text)));
        return rtrim($text, "\n");
    }

    /**
     * @ignore
     */
    public function span($text)
    {
        $qtags = array('\*\*', '\*', '\?\?', '-', '__', '_', '%', '\+', '~', '\^');
        $pnct = ".,\"'?!;:";

        foreach ($qtags as $f) {
            $text = preg_replace_callback("/
                (?:^|(?<=[\s>$pnct])|([{[]))
                ($f)(?!$f)
                (" . self::REGEX_C . ")
                (?::(\S+))?
                ([^\s$f]+|\S[^$f\n]*[^\s$f\n])
                ([$pnct]*)
                $f
                (?:$|([\]}])|(?=[[:punct:]]{1,2}|\s))
            /x", array($this, 'fSpan'), $text);
        }
        return $text;
    }

    /**
     * @ignore
     */
    public function fSpan($m)
    {
        $qtags = array(
            '*'  => 'strong',
            '**' => 'b',
            '??' => 'cite',
            '_'  => 'em',
            '__' => 'i',
            '-'  => 'del',
            '%'  => 'span',
            '+'  => 'ins',
            '~'  => 'sub',
            '^'  => 'sup',
        );

        list(, , $tag, $atts, $cite, $content, $end) = $m;
        $tag = $qtags[$tag];
        $atts = $this->parseBlockAttributes($atts)
            . ($cite ? 'cite="' . $cite . '"' : '');

        return "<$tag$atts>$content$end</$tag>";
    }

    /**
     * @ignore
     */
    public function links($text)
    {
        $punct = preg_quote('!"#$%&\'*+,-./:;=?@\\^_`|~', '/');
        return preg_replace_callback('/
            (^|(?<=[\s>.' . self::REGEX_PUNCT . '\(])|([{[]))  # $pre
            "                                                  # $start
            (' . self::REGEX_C . ')                            # $atts
            ([^"]+)                                            # $text
            \s?
            (?:\(([^)]+)\)(?="))?                              # $title
            ":
            (' . self::REGEX_URL . '+)                         # $url
            (\/)?                                              # $slash
            ([^\w\/;]*)                                        # $post
            (?:([\]}])|(?=\s|$|\)))
        /Ux', array($this, 'fLink'), $text);
    }

    /**
     * @ignore
     */
    public function fLink($m)
    {
        list(, $pre, $start, $atts, $text, $title, $url, $slash, $post) = $m;

        $atts = $this->parseBlockAttributes($atts)
            . ($title != '') ? ' title="' . $this->encodeHtml($title) . '"' : '';

        if ($this->images) {
            $text = $this->image($text);
        }
        $text = $this->glyphs($this->span($text));

        $url = $this->checkRefs($url);

        return $this->shelve('<a href="'
                             . $this->encodeHtml($url . $slash)
                             . '"' . $atts . ($this->rel ? ' rel="' . $this->rel . '" ' : '') . '>'
                             . $text . '</a>' . $post);
    }

    /**
     * @ignore
     */
    public function getRefs($text)
    {
        return preg_replace_callback("/(?<=^|\s)\[(.+)\]((?:http:\/\/|\/)\S+)(?=\s|$)/U",
            array($this, 'refs'), $text);
    }

    /**
     * @ignore
     */
    public function refs($m)
    {
        list(, $flag, $url) = $m;
        $this->urlrefs[$flag] = $url;
        return '';
    }

    /**
     * @ignore
     */
    public function checkRefs($text)
    {
        return isset($this->urlrefs[$text]) ? $this->urlrefs[$text] : $text;
    }

    /**
     * @ignore
     */
    public function image($text)
    {
        return preg_replace_callback("/
            (?:[[{])?               # pre
            \!                      # opening !
            (\<|\=|\>)??            # optional alignment attributes
            (" . self::REGEX_C . ") # optional style, class attributes
            (?:\. )?                # optional dot-space
            ([^\s(!]+)              # presume this is the src
            \s?                     # optional space
            (?:\(([^\)]+)\))?       # optional title
            \!                      # closing
            (?::(\S+))?             # optional href
            (?:[\]}]|(?=\s|$))      # lookahead: space or end of string
        /Ux", array($this, 'fImage'), $text);
    }

    /**
     * @ignore
     */
    public function fImage($m)
    {
        list(, $algn, $atts, $url) = $m;
        $title = isset($m[4]) ? $m[4] : '';
        $atts = $this->parseBlockAttributes($atts)
            . ($algn != '' ? ' align="' . $this->iAlign($algn) . '"' : '')
            . ($title ? ' title="' . $title . '"' : '')
            . ' alt="'   . $title . '"';

        $href = isset($m[5]) ? $this->checkRefs($m[5]) : '';
        $url = $this->checkRefs($url);

        return ($href ? '<a href="' . $href . '">' : '')
            . '<img src="' . $url . '"' . $atts . ' />'
            . ($href ? '</a>' : '');
    }

    /**
     * @ignore
     */
    public function code($text)
    {
        $text = $this->doSpecial($text, '<code>', '</code>', 'fCode');
        $text = $this->doSpecial($text, '@', '@', 'fCode');
        $text = $this->doSpecial($text, '<pre>', '</pre>', 'fPre');
        return $text;
    }

    /**
     * @ignore
     */
    public function fCode($m)
    {
        @list(, $before, $text, $after) = $m;
        return $before . $this->shelve('<code>' . $this->encodeHtml($text, false) . '</code>') . $after;
    }

    /**
     * @ignore
     */
    public function fPre($m)
    {
        @list(, $before, $text, $after) = $m;
        return $before . '<pre>' . $this->shelve($this->encodeHtml($text, false)) . '</pre>' . $after;
    }

    /**
     * @ignore
     */
    public function shelve($val)
    {
        $i = uniqid(mt_rand());
        $this->_shelf[$i] = $val;
        return $i;
    }

    /**
     * @ignore
     */
    public function retrieve($text)
    {
        if (is_array($this->_shelf)) {
            do {
                $old = $text;
                $text = strtr($text, $this->_shelf);
            } while ($text != $old);
        }
        return $text;
    }

    /**
     * @ignore
     */
    public function cleanWhiteSpace($text)
    {
        return preg_replace(array("/\r\n/", "/\n{3,}/", "/\n *\n/"),
                            array("\n",     "\n\n",     "\n\n"),
                            $text);
    }

    /**
     * @ignore
     */
    public function doSpecial($text, $start, $end, $method = 'fSpecial')
    {
        return preg_replace_callback('/(^|\s|[[({>])' . preg_quote($start, '/') . '(.*?)' . preg_quote($end, '/') . '(\s|$|[\])}])?/ms',
                                     array($this, $method), $text);
    }

    /**
     * @ignore
     */
    public function fSpecial($m)
    {
        // A special block like notextile or code
        @list(, $before, $text, $after) = $m;
        return $before . $this->shelve($this->encodeHtml($text)) . $after;
    }

    /**
     * @ignore
     */
    public function noTextile($text)
    {
         $text = $this->doSpecial($text, '<notextile>', '</notextile>', 'fTextile');
         return $this->doSpecial($text, '==', '==', 'fTextile');
    }

    /**
     * @ignore
     */
    public function fTextile($m)
    {
        @list(, $before, $notextile, $after) = $m;
        return $before . $this->shelve($notextile) . $after;
    }

    /**
     * @ignore
     */
    public function footnoteRef($text)
    {
        return preg_replace('/\b\[([0-9]+)\](\s)?/U',
                            '<sup><a id="fnr$1" href="#fn$1">$1</a></sup>$2',
                            $text);
    }

    /**
     * @ignore
     */
    public function glyphs($text)
    {
        $glyph_search = array(
            '/(\w)\'(\w)/',                                           // apostrophe's
            '/(\s)\'(\d+\w?)\b(?!\')/',                               // back in '88
            '/(\S)\'(?=\s|[[:punct:]]|<|$)/',                         // single closing
            '/\'/',                                                   // single opening
            '/(\S)\"(?=\s|[[:punct:]]|<|$)/',                         // double closing
            '/"/',                                                    // double opening
            '/\b([A-Z][A-Z0-9]{2,})\b(?:[(]([^)]*)[)])/',             // 3+ uppercase acronym
            '/\b([A-Z][A-Z\'\-]+[A-Z])(?=[\s.,\)>])/',                // 3+ uppercase
            '/\b( )?\.{3}/',                                          // ellipsis
            '/(\s?)--(\s?)/',                                         // em dash
            '/\s-(?:\s|$)/',                                          // en dash
            '/(\d+)( ?)x( ?)(?=\d+)/',                                // dimension sign
            '/\b ?[([]TM[])]/i',                                      // trademark
            '/\b ?[([]R[])]/i',                                       // registered
            '/\b ?[([]C[])]/i',                                       // copyright
        );

        $glyph_replace = array(
            '$1' . self::$GLYPH_APOSTROPHE . '$2',      // apostrophes
            '$1' . self::$GLYPH_APOSTROPHE . '$2',      // back in '88
            '$1' . self::$GLYPH_QUOTE_SINGLE_CLOSE,     // single closing
            self::$GLYPH_QUOTE_SINGLE_OPEN,             // single opening
            '$1' . self::$GLYPH_QUOTE_DOUBLE_CLOSE,     // double closing
            self::$GLYPH_QUOTE_DOUBLE_OPEN,             // double opening
            '<acronym title="$2">$1</acronym>',                       // 3+ uppercase acronym
            '<span class="caps">$1</span>',                           // 3+ uppercase
            '$1' . self::$GLYPH_ELLIPSIS,               // ellipsis
            self::$GLYPH_EMDASH,                        // em dash
            ' ' . self::$GLYPH_ENDASH . ' ',            // en dash
            '$1' . self::$GLYPH_DIMENSION,              // dimension sign
            self::$GLYPH_TRADEMARK,                     // trademark
            self::$GLYPH_REGISTERED,                    // registered
            self::$GLYPH_COPYRIGHT,                     // copyright
        );

        $text = preg_split('/(<.*>)/U', $text, -1, PREG_SPLIT_DELIM_CAPTURE);
        foreach ($text as $line) {
            if (!preg_match('/<.*>/', $line)) {
                $line = preg_replace($glyph_search, $glyph_replace, $line);
            }
            $glyph_out[] = $line;
        }

        return implode('', $glyph_out);
    }

    /**
     * @ignore
     */
    public function iAlign($in)
    {
        $vals = array(
            '<' => 'left',
            '=' => 'center',
            '>' => 'right');
        return isset($vals[$in]) ? $vals[$in] : '';
    }

    /**
     * @ignore
     */
    public function hAlign($in)
    {
        $vals = array(
            '<'  => 'left',
            '='  => 'center',
            '>'  => 'right',
            '<>' => 'justify');
        return isset($vals[$in]) ? $vals[$in] : '';
    }

    /**
     * @ignore
     */
    public function vAlign($in)
    {
        $vals = array(
            '^' => 'top',
            '-' => 'middle',
            '~' => 'bottom');
        return isset($vals[$in]) ? $vals[$in] : '';
    }

    /**
     * @ignore
     */
    public function encodeHtml($str, $quotes = true)
    {
        $a = array(
            '&' => '&amp;',
            '<' => '&lt;',
            '>' => '&gt;',
        );
        if ($quotes) {
            $a = $a + array(
                "'" => '&#39;',
                '"' => '&#34;',
            );
        }

        return strtr($str, $a);
    }

}
