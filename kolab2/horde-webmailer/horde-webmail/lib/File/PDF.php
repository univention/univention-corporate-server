<?php
/**
 * The File_PDF class provides a PHP-only implementation of a PDF library. No
 * external libs or PHP extensions are required.
 *
 * Based on the FPDF class by Olivier Plathey (http://www.fpdf.org/).
 *
 * $Horde: framework/File_PDF/PDF.php,v 1.18.10.21 2009-01-06 15:23:05 jan Exp $
 *
 * Copyright 2001-2003 Olivier Plathey <olivier@fpdf.org>
 * Copyright 2003-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author   Olivier Plathey <olivier@fpdf.org>
 * @author   Marko Djukic <marko@oblo.com>
 * @author   Jan Schneider <jan@horde.org>
 * @package  File_PDF
 * @category Fileformats
 */

/**
 * This hack works around Horde bug #4094
 * (http://bugs.horde.org/ticket/?id=4094)
 *
 * Once this package does not need to support PHP < 4.3.10 anymore the
 * following definiton can be removed and the ugly code can be removed
 * using
 *
 * sed -i -e 's/\' \. FILE_PDF_FLOAT \. \'/F/g' PDF.php
 */
if (version_compare(PHP_VERSION, '4.3.10', '>=')) {
    define('FILE_PDF_FLOAT', 'F');
} else {
    define('FILE_PDF_FLOAT', 'f');
}

class File_PDF {

    /**
     * Current page number.
     *
     * @var integer
     */
    var $_page = 0;

    /**
     * Current object number.
     *
     * @var integer
     */
    var $_n = 2;

    /**
     * Array of object offsets.
     *
     * @var array
     */
    var $_offsets = array();

    /**
     * Buffer holding in-memory PDF.
     *
     * @var string
     */
    var $_buffer = '';

    /**
     * Buffer length, including already flushed content.
     *
     * @var integer
     */
    var $_buflen = 0;

    /**
     * Whether the buffer has been flushed already.
     *
     * @var boolean
     */
    var $_flushed = false;

    /**
     * Array containing the pages.
     *
     * @var array
     */
    var $_pages = array();

    /**
     * Current document state.<pre>
     *   0 - initial state
     *   1 - document opened
     *   2 - page opened
     *   3 - document closed
     * </pre>
     *
     * @var integer
     */
    var $_state = 0;

    /**
     * Flag indicating if PDF file is to be compressed or not.
     *
     * @var boolean
     */
    var $_compress;

    /**
     * The default page orientation.
     *
     * @var string
     */
    var $_default_orientation;

    /**
     * The current page orientation.
     *
     * @var string
     */
    var $_current_orientation;

    /**
     * Array indicating orientation changes.
     *
     * @var array
     */
    var $_orientation_changes = array();

    /**
     * Current width of page format in points.
     *
     * @var float
     */
    var $fwPt;

    /**
     * Current height of page format in points.
     *
     * @var float
     */
    var $fhPt;

    /**
     * Current width of page format in user units.
     *
     * @var float
     */
    var $fw;

    /**
     * Current height of page format in user units.
     *
     * @var float
     */
    var $fh;

    /**
     * Current width of page in points.
     *
     * @var float
     */
    var $wPt;

    /**
     * Current height of page in points.
     *
     * @var float
     */
    var $hPt;

    /**
     * Current width of page in user units
     *
     * @var float
     */
    var $w;

    /**
     * Current height of page in user units
     *
     * @var float
     */
    var $h;

    /**
     * Scale factor (number of points in user units).
     *
     * @var float
     */
    var $_scale;

    /**
     * Left page margin size.
     *
     * @var float
     */
    var $_left_margin;

    /**
     * Top page margin size.
     *
     * @var float
     */
    var $_top_margin;

    /**
     * Right page margin size.
     *
     * @var float
     */
    var $_right_margin;

    /**
     * Break page margin size, the bottom margin which triggers a page break.
     *
     * @var float
     */
    var $_break_margin;

    /**
     * Cell margin size.
     *
     * @var float
     */
    var $_cell_margin;

    /**
     * The current horizontal position for cell positioning.
     * Value is set in user units and is calculated from the top left corner
     * as origin.
     *
     * @var float
     */
    var $x;

    /**
     * The current vertical position for cell positioning.
     * Value is set in user units and is calculated from the top left corner
     * as origin.
     *
     * @var float
     */
    var $y;

    /**
     * The height of the last cell printed.
     *
     * @var float
     */
    var $_last_height;

    /**
     * Line width in user units.
     *
     * @var float
     */
    var $_line_width;

    /**
     * An array of standard font names.
     *
     * @var array
     */
    var $_core_fonts = array('courier'      => 'Courier',
                             'courierB'     => 'Courier-Bold',
                             'courierI'     => 'Courier-Oblique',
                             'courierBI'    => 'Courier-BoldOblique',
                             'helvetica'    => 'Helvetica',
                             'helveticaB'   => 'Helvetica-Bold',
                             'helveticaI'   => 'Helvetica-Oblique',
                             'helveticaBI'  => 'Helvetica-BoldOblique',
                             'times'        => 'Times-Roman',
                             'timesB'       => 'Times-Bold',
                             'timesI'       => 'Times-Italic',
                             'timesBI'      => 'Times-BoldItalic',
                             'symbol'       => 'Symbol',
                             'zapfdingbats' => 'ZapfDingbats');

    /**
     * An array of used fonts.
     *
     * @var array
     */
    var $_fonts = array();

    /**
     * An array of font files.
     *
     * @var array
     */
    var $_font_files = array();

    /**
     * An array of encoding differences.
     *
     * @var array
     */
    var $_diffs = array();

    /**
     * An array of used images.
     *
     * @var array
     */
    var $_images = array();

    /**
     * An array of links in pages.
     *
     * @var array
     */
    var $_page_links;

    /**
     * An array of internal links.
     *
     * @var array
     */
    var $_links = array();

    /**
     * Current font family.
     *
     * @var string
     */
    var $_font_family = '';

    /**
     * Current font style.
     *
     * @var string
     */
    var $_font_style = '';

    /**
     * Underlining flag.
     *
     * @var boolean
     */
    var $_underline = false;

    /**
     * An array containing current font info.
     *
     * @var array
     */
    var $_current_font;

    /**
     * Current font size in points.
     *
     * @var float
     */
    var $_font_size_pt = 12;

    /**
     * Current font size in user units.
     *
     * @var float
     */
    var $_font_size = 12;

    /**
     * Commands for filling color.
     *
     * @var string
     */
    var $_fill_color = '0 g';

    /**
     * Commands for text color.
     *
     * @var string
     */
    var $_text_color = '0 g';

    /**
     * Whether text color is different from fill color.
     *
     * @var boolean
     */
    var $_color_flag = false;

    /**
     * Commands for drawing color.
     *
     * @var string
     */
    var $_draw_color = '0 G';

    /**
     * Word spacing.
     *
     * @var integer
     */
    var $_word_spacing = 0;

    /**
     * Automatic page breaking.
     *
     * @var boolean
     */
    var $_auto_page_break;

    /**
     * Threshold used to trigger page breaks.
     *
     * @var float
     */
    var $_page_break_trigger;

    /**
     * Flag set when processing footer.
     *
     * @var boolean
     */
    var $_in_footer = false;

    /**
     * Zoom display mode.
     *
     * @var string
     */
    var $_zoom_mode;

    /**
     * Layout display mode.
     *
     * @var string
     */
    var $_layout_mode;

    /**
     * An array containing the document info, consisting of:
     *   - title
     *   - subject
     *   - author
     *   - keywords
     *   - creator
     *
     * @var array
     */
    var $_info = array();

    /**
     * Alias for total number of pages.
     *
     * @var string
     */
    var $_alias_nb_pages = '{nb}';

    /**
     * Attempts to return a conrete PDF instance.
     *
     * It allows to set up the page format, the orientation and the units of
     * measurement used in all the methods (except for the font sizes).
     *
     * Example:
     * <code>
     * $pdf = File_PDF::factory(array('orientation' => 'P',
     *                                'unit' => 'mm',
     *                                'format' => 'A4'));
     * </code>
     *
     * @param array $params  A hash with parameters for the created PDF object.
     *                       Possible parameters are:
     *                       - orientation - Default page orientation. Possible
     *                         values are (case insensitive):
     *                         - P or Portrait (default)
     *                         - L or Landscape
     *                       - unit - User measure units. Possible values
     *                         values are:
     *                         - pt: point
     *                         - mm: millimeter (default)
     *                         - cm: centimeter
     *                         - in: inch
     *                         A point equals 1/72 of inch, that is to say
     *                         about 0.35 mm (an inch being 2.54 cm). This is a
     *                         very common unit in typography; font sizes are
     *                         expressed in that unit.
     *                       - format - The format used for pages. It can be
     *                         either one of the following values (case
     *                         insensitive):
     *                         - A3
     *                         - A4 (default)
     *                         - A5
     *                         - Letter
     *                         - Legal
     *                         or a custom format in the form of a two-element
     *                         array containing the width and the height
     *                         (expressed in the unit given by the unit
     *                         parameter).
     * @param string $class  The concrete class name to return an instance of.
     *                       Defaults to File_PDF.
     */
    function &factory($params = array(), $class = 'File_PDF')
    {
        /* Default parameters. */
        $defaults = array('orientation' => 'P',
                          'unit' => 'mm',
                          'format' => 'A4');

        /* Backward compatibility with old method signature. */
        /* Should be removed a few versions later. */
        if (!is_array($params)) {
            $class = 'File_PDF';
            $params = $defaults;
            $names = array_keys($defaults);
            for ($i = 0; $i < func_num_args(); $i++) {
                $params[$names[$i]] = func_get_arg($i);
            }
        } else {
            $params = array_merge($defaults, $params);
        }

        /* Create the PDF object. */
        $pdf = new $class($params);

        /* Scale factor. */
        if ($params['unit'] == 'pt') {
            $pdf->_scale = 1;
        } elseif ($params['unit'] == 'mm') {
            $pdf->_scale = 72 / 25.4;
        } elseif ($params['unit'] == 'cm') {
            $pdf->_scale = 72 / 2.54;
        } elseif ($params['unit'] == 'in') {
            $pdf->_scale = 72;
        } else {
            $error = File_PDF::raiseError(sprintf('Incorrect units: %s', $params['unit']));
            return $error;
        }
        /* Page format. */
        if (is_string($params['format'])) {
            $params['format'] = strtolower($params['format']);
            if ($params['format'] == 'a3') {
                $params['format'] = array(841.89, 1190.55);
            } elseif ($params['format'] == 'a4') {
                $params['format'] = array(595.28, 841.89);
            } elseif ($params['format'] == 'a5') {
                $params['format'] = array(420.94, 595.28);
            } elseif ($params['format'] == 'letter') {
                $params['format'] = array(612, 792);
            } elseif ($params['format'] == 'legal') {
                $params['format'] = array(612, 1008);
            } else {
                $error = File_PDF::raiseError(sprintf('Unknown page format: %s', $params['format']));
                return $error;
            }
            $pdf->fwPt = $params['format'][0];
            $pdf->fhPt = $params['format'][1];
        } else {
            $pdf->fwPt = $params['format'][0] * $pdf->_scale;
            $pdf->fhPt = $params['format'][1] * $pdf->_scale;
        }
        $pdf->fw = $pdf->fwPt / $pdf->_scale;
        $pdf->fh = $pdf->fhPt / $pdf->_scale;

        /* Page orientation. */
        $params['orientation'] = strtolower($params['orientation']);
        if ($params['orientation'] == 'p' || $params['orientation'] == 'portrait') {
            $pdf->_default_orientation = 'P';
            $pdf->wPt = $pdf->fwPt;
            $pdf->hPt = $pdf->fhPt;
        } elseif ($params['orientation'] == 'l' || $params['orientation'] == 'landscape') {
            $pdf->_default_orientation = 'L';
            $pdf->wPt = $pdf->fhPt;
            $pdf->hPt = $pdf->fwPt;
        } else {
            $error = File_PDF::raiseError(sprintf('Incorrect orientation: %s', $params['orientation']));
            return $error;
        }
        $pdf->_current_orientation = $pdf->_default_orientation;
        $pdf->w = $pdf->wPt / $pdf->_scale;
        $pdf->h = $pdf->hPt / $pdf->_scale;

        /* Page margins (1 cm) */
        $margin = 28.35 / $pdf->_scale;
        $pdf->setMargins($margin, $margin);

        /* Interior cell margin (1 mm) */
        $pdf->_cell_margin = $margin / 10;

        /* Line width (0.2 mm) */
        $pdf->_line_width = .567 / $pdf->_scale;

        /* Automatic page break */
        $pdf->setAutoPageBreak(true, 2 * $margin);

        /* Full width display mode */
        $pdf->setDisplayMode('fullwidth');

        /* Compression */
        $pdf->setCompression(true);

        return $pdf;
    }

    /**
     * Returns a PEAR_Error object.
     *
     * Wraps around PEAR::raiseError() to avoid having to include PEAR.php
     * unless an error occurs.
     *
     * @param mixed $error  The error message.
     *
     * @return object PEAR_Error
     */
    function raiseError($error)
    {
        require_once 'PEAR.php';
        return PEAR::raiseError($error);
    }

    /**
     * Defines the left, top and right margins.
     *
     * By default, they equal 1 cm. Call this method to change them.
     *
     * @param float $left   Left margin.
     * @param float $top    Top margin.
     * @param float $right  Right margin. If not specified default to the value
     *                      of the left one.
     *
     * @see setAutoPageBreak()
     * @see setLeftMargin()
     * @see setRightMargin()
     * @see setTopMargin()
     */
    function setMargins($left, $top, $right = null)
    {
        /* Set left and top margins. */
        $this->_left_margin  = $left;
        $this->_top_margin   = $top;
        /* If no right margin set default to same as left. */
        $this->_right_margin = (is_null($right) ? $left : $right);
    }

    /**
     * Defines the left margin.
     *
     * The method can be called before creating the first page.  If the
     * current abscissa gets out of page, it is brought back to the margin.
     *
     * @param float $margin  The margin.
     *
     * @see setAutoPageBreak()
     * @see setMargins()
     * @see setRightMargin()
     * @see setTopMargin()
     */
    function setLeftMargin($margin)
    {
        $this->_left_margin = $margin;
        /* If there is a current page and the current X position is less than
         * margin set the X position to the margin value. */
        if ($this->_page > 0 && $this->x < $margin) {
            $this->x = $margin;
        }
    }

    /**
     * Defines the top margin.
     *
     * The method can be called before creating the first page.
     *
     * @param float $margin  The margin.
     */
    function setTopMargin($margin)
    {
        $this->_top_margin = $margin;
    }

    /**
     * Defines the right margin.
     *
     * The method can be called before creating the first page.
     *
     * @param float $margin  The margin.
     */
    function setRightMargin($margin)
    {
        $this->_right_margin = $margin;
    }

    /**
     * Returns the actual page width.
     *
     * @since File_PDF 0.2.0
     * @since Horde 3.2
     *
     * @return float  The page width.
     */
    function getPageWidth()
    {
        return ($this->w - $this->_right_margin - $this->_left_margin);
    }

    /**
     * Returns the actual page height.
     *
     * @since File_PDF 0.2.0
     * @since Horde 3.2
     *
     * @return float  The page height.
     */
    function getPageHeight()
    {
        return ($this->h - $this->_top_margin - $this->_break_margin);
    }

    /**
     * Enables or disables the automatic page breaking mode.
     *
     * When enabling, the second parameter is the distance from the bottom of
     * the page that defines the triggering limit. By default, the mode is on
     * and the margin is 2 cm.
     *
     * @param boolean $auto  Boolean indicating if mode should be on or off.
     * @param float $margin  Distance from the bottom of the page.
     */
    function setAutoPageBreak($auto, $margin = 0)
    {
        $this->_auto_page_break    = $auto;
        $this->_break_margin       = $margin;
        $this->_page_break_trigger = $this->h - $margin;
    }

    /**
     * Defines the way the document is to be displayed by the viewer.
     *
     * The zoom level can be set: pages can be displayed entirely on screen,
     * occupy the full width of the window, use real size, be scaled by a
     * specific zooming factor or use viewer default (configured in the
     * Preferences menu of Acrobat). The page layout can be specified too:
     * single at once, continuous display, two columns or viewer default.  By
     * default, documents use the full width mode with continuous display.
     *
     * @param mixed $zoom    The zoom to use. It can be one of the following
     *                       string values:
     *                         - fullpage: entire page on screen
     *                         - fullwidth: maximum width of window
     *                         - real: uses real size (100% zoom)
     *                         - default: uses viewer default mode
     *                       or a number indicating the zooming factor.
     * @param string layout  The page layout. Possible values are:
     *                         - single: one page at once
     *                         - continuous: pages in continuously
     *                         - two: two pages on two columns
     *                         - default: uses viewer default mode
     *                       Default value is continuous.
     */
    function setDisplayMode($zoom, $layout = 'continuous')
    {
        $zoom = strtolower($zoom);
        if ($zoom == 'fullpage' || $zoom == 'fullwidth' || $zoom == 'real'
            || $zoom == 'default' || !is_string($zoom)) {
            $this->_zoom_mode = $zoom;
        } elseif ($zoom == 'zoom') {
            $this->_zoom_mode = $layout;
        } else {
            return $this->raiseError(sprintf('Incorrect zoom display mode: %s', $zoom));
        }

        $layout = strtolower($layout);
        if ($layout == 'single' || $layout == 'continuous' || $layout == 'two'
            || $layout == 'default') {
            $this->_layout_mode = $layout;
        } elseif ($zoom != 'zoom') {
            return $this->raiseError(sprintf('Incorrect layout display mode: %s', $layout));
        }
    }

    /**
     * Activates or deactivates page compression.
     *
     * When activated, the internal representation of each page is compressed,
     * which leads to a compression ratio of about 2 for the resulting
     * document. Compression is on by default.
     *
     * Note: the {@link http://www.php.net/zlib/ zlib extension} is required
     * for this feature. If not present, compression will be turned off.
     *
     * @param boolean $compress  Boolean indicating if compression must be
     *                           enabled or not.
     */
    function setCompression($compress)
    {
        /* If no gzcompress function is available then default to false. */
        $this->_compress = (function_exists('gzcompress') ? $compress : false);
    }

    /**
     * Set the info to a document.
     *
     * Possible info settings are:
     *   - title
     *   - subject
     *   - author
     *   - keywords
     *   - creator
     *
     * @param array|string $info  If passed as an array then the complete hash
     *                            containing the info to be inserted into the
     *                            document. Otherwise the name of setting to be
     *                            set.
     * @param string $value       The value of the setting.
     */
    function setInfo($info, $value = '')
    {
        if (is_array($info)) {
            $this->_info = $info;
        } else {
            $this->_info[$info] = $value;
        }
    }

    /**
     * Defines an alias for the total number of pages.
     *
     * It will be substituted as the document is closed.
     *
     * Example:
     * <code>
     * class My_File_PDF extends File_PDF {
     *     function footer()
     *     {
     *         // Go to 1.5 cm from bottom
     *         $this->setY(-15);
     *         // Select Arial italic 8
     *         $this->setFont('Arial', 'I', 8);
     *         // Print current and total page numbers
     *         $this->cell(0, 10, 'Page ' . $this->getPageNo() . '/{nb}', 0,
     *                     0, 'C');
     *     }
     * }
     * $pdf = My_File_PDF::factory();
     * $pdf->aliasNbPages();
     * </code>
     *
     * @param string $alias  The alias.
     *
     * @see getPageNo()
     * @see footer()
     */
    function aliasNbPages($alias = '{nb}')
    {
        $this->_alias_nb_pages = $alias;
    }

    /**
     * This method begins the generation of the PDF document; it must be
     * called before any output commands.
     *
     * No page is created by this method, therefore it is necessary to call
     * {@link addPage()}.
     *
     * @see addPage()
     * @see close()
     */
    function open()
    {
        $this->_beginDoc();
    }

    /**
     * Terminates the PDF document. It is not necessary to call this method
     * explicitly because {@link output()} does it automatically.
     *
     * If the document contains no page, {@link addPage()} is called to
     * prevent from getting an invalid document.
     *
     * @see open()
     * @see output()
     */
    function close()
    {
        /* Terminate document */
        if ($this->_page == 0) {
            $result = $this->addPage();
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }
        /* Page footer */
        $this->_in_footer = true;
        $this->x = $this->_left_margin;
        $this->footer();
        $this->_in_footer = false;
        /* Close page */
        $this->_endPage();
        /* Close document */
        $this->_endDoc();
    }

    /**
     * Adds a new page to the document.
     *
     * If a page is already present, the {@link footer()} method is called
     * first to output the footer. Then the page is added, the current
     * position set to the top-left corner according to the left and top
     * margins, and {@link header()} is called to display the header.
     *
     * The font which was set before calling is automatically restored. There
     * is no need to call {@link setFont()} again if you want to continue with
     * the same font. The same is true for colors and line width.  The origin
     * of the coordinate system is at the top-left corner and increasing
     * ordinates go downwards.
     *
     * @param string $orientation  Page orientation. Possible values
     *                             are (case insensitive):
     *                               - P or Portrait
     *                               - L or Landscape
     *                             The default value is the one passed to the
     *                             constructor.
     *
     * @see header()
     * @see footer()
     * @see setMargins()
     */
    function addPage($orientation = '')
    {
        /* For good measure make sure this is called. */
        $this->_beginDoc();

        /* Save style settings so that they are not overridden by footer() or
         * header(). */
        $lw = $this->_line_width;
        $dc = $this->_draw_color;
        $fc = $this->_fill_color;
        $tc = $this->_text_color;
        $cf = $this->_color_flag;
        $font_family = $this->_font_family;
        $font_style = $this->_font_style . ($this->_underline ? 'U' : '');
        $font_size  = $this->_font_size_pt;

        /* Close old page. */
        if ($this->_page > 0) {
            /* Page footer. */
            $this->_in_footer = true;
            $this->x = $this->_left_margin;
            $this->footer();
            $this->_in_footer = false;

            /* Close page. */
            $this->_endPage();
        }

        /* Start new page. */
        $this->_beginPage($orientation);
        /* Set line cap style to square. */
        $this->_out('2 J');
        /* Set line width. */
        $this->_line_width = $lw;
        $this->_out(sprintf('%.2' . FILE_PDF_FLOAT . ' w', $lw * $this->_scale));

        /* Force the setting of the font. Each new page requires a new
         * call. */
        if ($font_family) {
            $result = $this->setFont($font_family, $font_style, $font_size, true);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }

        /* Restore styles. */
        if ($this->_fill_color != $fc) {
            $this->_fill_color = $fc;
            $this->_out($this->_fill_color);
        }
        if ($this->_draw_color != $dc) {
            $this->_draw_color = $dc;
            $this->_out($this->_draw_color);
        }
        $this->_text_color = $tc;
        $this->_color_flag = $cf;

        /* Page header. */
        $this->header();

        /* Restore styles. */
        if ($this->_line_width != $lw) {
            $this->_line_width = $lw;
            $this->_out(sprintf('%.2' . FILE_PDF_FLOAT . ' w', $lw * $this->_scale));
        }
        $result = $this->setFont($font_family, $font_style, $font_size);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }
        if ($this->_fill_color != $fc) {
            $this->_fill_color = $fc;
            $this->_out($this->_fill_color);
        }
        if ($this->_draw_color != $dc) {
            $this->_draw_color = $dc;
            $this->_out($this->_draw_color);
        }
        $this->_text_color = $tc;
        $this->_color_flag = $cf;
    }

    /**
     * This method is used to render the page header.
     *
     * It is automatically called by {@link addPage()} and should not be
     * called directly by the application. The implementation in File_PDF:: is
     * empty, so you have to subclass it and override the method if you want a
     * specific processing.
     *
     * Example:
     * <code>
     * class My_File_PDF extends File_PDF {
     *     function header()
     *     {
     *         // Select Arial bold 15
     *         $this->setFont('Arial', 'B', 15);
     *         // Move to the right
     *         $this->cell(80);
     *         // Framed title
     *         $this->cell(30, 10, 'Title', 1, 0, 'C');
     *         // Line break
     *         $this->newLine(20);
     *     }
     * }
     * </code>
     *
     * @see footer()
     */
    function header()
    {
        /* To be implemented in your own inherited class. */
    }

    /**
     * This method is used to render the page footer.
     *
     * It is automatically called by {@link addPage()} and {@link close()} and
     * should not be called directly by the application. The implementation in
     * File_PDF:: is empty, so you have to subclass it and override the method
     * if you want a specific processing.
     *
     * Example:
     * <code>
     * class My_File_PDF extends File_PDF {
     *    function footer()
     *    {
     *        // Go to 1.5 cm from bottom
     *        $this->setY(-15);
     *        // Select Arial italic 8
     *        $this->setFont('Arial', 'I', 8);
     *        // Print centered page number
     *        $this->cell(0, 10, 'Page ' . $this->getPageNo(), 0, 0, 'C');
     *    }
     * }
     * </code>
     *
     * @see header()
     */
    function footer()
    {
        /* To be implemented in your own inherited class. */
    }

    /**
     * Returns the current page number.
     *
     * @return integer
     *
     * @see aliasNbPages()
     */
    function getPageNo()
    {
        return $this->_page;
    }

    /**
     * Sets the fill color.
     *
     * Depending on the colorspace called, the number of color component
     * parameters required can be either 1, 3 or 4. The method can be called
     * before the first page is created and the color is retained from page to
     * page.
     *
     * @param string $cs  Indicates the colorspace which can be either 'rgb',
     *                    'cmyk' or 'gray'. Defaults to 'rgb'.
     * @param float $c1   First color component, floating point value between 0
     *                    and 1. Required for gray, rgb and cmyk.
     * @param float $c2   Second color component, floating point value
     *                    between 0 and 1. Required for rgb and cmyk.
     * @param float $c3   Third color component, floating point value between 0
     *                    and 1. Required for rgb and cmyk.
     * @param float $c4   Fourth color component, floating point value
     *                    between 0 and 1. Required for cmyk.
     *
     * @see setTextColor()
     * @see setDrawColor()
     * @see rect()
     * @see cell()
     * @see multiCell()
     */
    function setFillColor($cs = 'rgb', $c1, $c2 = 0, $c3 = 0, $c4 = 0)
    {
        $cs = strtolower($cs);
        if ($cs == 'rgb') {
            $this->_fill_color = sprintf('%.3' . FILE_PDF_FLOAT . ' %.3' . FILE_PDF_FLOAT . ' %.3' . FILE_PDF_FLOAT . ' rg', $c1, $c2, $c3);
        } elseif ($cs == 'cmyk') {
            $this->_fill_color = sprintf('%.3' . FILE_PDF_FLOAT . ' %.3' . FILE_PDF_FLOAT . ' %.3' . FILE_PDF_FLOAT . ' %.3' . FILE_PDF_FLOAT . ' k', $c1, $c2, $c3, $c4);
        } else {
            $this->_fill_color = sprintf('%.3' . FILE_PDF_FLOAT . ' g', $c1);
        }
        if ($this->_page > 0) {
            $this->_out($this->_fill_color);
        }
        $this->_color_flag = $this->_fill_color != $this->_text_color;
    }

    /**
     * Sets the text color.
     *
     * Depending on the colorspace called, the number of color component
     * parameters required can be either 1, 3 or 4. The method can be called
     * before the first page is created and the color is retained from page to
     * page.
     *
     * @param string $cs  Indicates the colorspace which can be either 'rgb',
     *                    'cmyk' or 'gray'. Defaults to 'rgb'.
     * @param float $c1   First color component, floating point value between 0
     *                    and 1. Required for gray, rgb and cmyk.
     * @param float $c2   Second color component, floating point value
     *                    between 0 and 1. Required for rgb and cmyk.
     * @param float $c3   Third color component, floating point value between 0
     *                    and 1. Required for rgb and cmyk.
     * @param float $c4   Fourth color component, floating point value
     *                    between 0 and 1. Required for cmyk.
     *
     * @since File_PDF 0.2.0
     * @since Horde 3.2
     * @see setFillColor()
     * @see setDrawColor()
     * @see rect()
     * @see cell()
     * @see multiCell()
     */
    function setTextColor($cs, $c1, $c2 = 0, $c3 = 0, $c4 = 0)
    {
        $cs = strtolower($cs);
        if ($cs == 'rgb') {
            $this->_text_color = sprintf('%.3' . FILE_PDF_FLOAT . ' %.3' . FILE_PDF_FLOAT . ' %.3' . FILE_PDF_FLOAT . ' rg', $c1, $c2, $c3);
        } elseif ($cs == 'cmyk') {
            $this->_text_color = sprintf('%.3' . FILE_PDF_FLOAT . ' %.3' . FILE_PDF_FLOAT . ' %.3' . FILE_PDF_FLOAT . ' %.3' . FILE_PDF_FLOAT . ' k', $c1, $c2, $c3, $c4);
        } else {
            $this->_text_color = sprintf('%.3' . FILE_PDF_FLOAT . ' g', $c1);
        }
        $this->_color_flag = $this->_fill_color != $this->_text_color;
    }

    /**
     * Sets the draw color, used when drawing lines.
     *
     * Depending on the colorspace called, the number of color component
     * parameters required can be either 1, 3 or 4. The method can be called
     * before the first page is created and the color is retained from page to
     * page.
     *
     * @param string $cs  Indicates the colorspace which can be either 'rgb',
     *                    'cmyk' or 'gray'. Defaults to 'rgb'.
     * @param float $c1   First color component, floating point value between 0
     *                    and 1. Required for gray, rgb and cmyk.
     * @param float $c2   Second color component, floating point value
     *                    between 0 and 1. Required for rgb and cmyk.
     * @param float $c3   Third color component, floating point value between 0
     *                    and 1. Required for rgb and cmyk.
     * @param float $c4   Fourth color component, floating point value
     *                    between 0 and 1. Required for cmyk.
     *
     * @see setFillColor()
     * @see line()
     * @see rect()
     * @see cell()
     * @see multiCell()
     */
    function setDrawColor($cs = 'rgb', $c1, $c2 = 0, $c3 = 0, $c4 = 0)
    {
        $cs = strtolower($cs);
        if ($cs == 'rgb') {
            $this->_draw_color = sprintf('%.3' . FILE_PDF_FLOAT . ' %.3' . FILE_PDF_FLOAT . ' %.3' . FILE_PDF_FLOAT . ' RG', $c1, $c2, $c3);
        } elseif ($cs == 'cmyk') {
            $this->_draw_color = sprintf('%.3' . FILE_PDF_FLOAT . ' %.3' . FILE_PDF_FLOAT . ' %.3' . FILE_PDF_FLOAT . ' %.3' . FILE_PDF_FLOAT . ' K', $c1, $c2, $c3, $c4);
        } else {
            $this->_draw_color = sprintf('%.3' . FILE_PDF_FLOAT . ' G', $c1);
        }
        if ($this->_page > 0) {
            $this->_out($this->_draw_color);
        }
    }

    /**
     * Returns the length of a text string. A font must be selected.
     *
     * @param string $text  The text whose length is to be computed.
     * @param boolean $pt   Whether the width should be returned in points or
     *                      user units.
     *
     * @return float
     */
    function getStringWidth($text, $pt = false)
    {
        $text = (string)$text;
        $width = 0;
        $length = strlen($text);
        for ($i = 0; $i < $length; $i++) {
            $width += $this->_current_font['cw'][$text{$i}];
        }

        /* Adjust for word spacing. */
        $width += $this->_word_spacing * substr_count($text, ' ') * $this->_current_font['cw'][' '];

        if ($pt) {
            return $width * $this->_font_size_pt / 1000;
        } else {
            return $width * $this->_font_size / 1000;
        }
    }

    /**
     * Defines the line width.
     *
     * By default, the value equals 0.2 mm. The method can be called before
     * the first page is created and the value is retained from page to page.
     *
     * @param float $width  The width.
     *
     * @see line()
     * @see rect()
     * @see cell()
     * @see multiCell()
     */
    function setLineWidth($width)
    {
        $this->_line_width = $width;
        if ($this->_page > 0) {
            $this->_out(sprintf('%.2' . FILE_PDF_FLOAT . ' w', $width * $this->_scale));
        }
    }

    /**
     * Draws a line between two points.
     *
     * All coordinates can be negative to provide values from the right or
     * bottom edge of the page (since File_PDF 0.2.0, Horde 3.2).
     *
     * @param float $x1  Abscissa of first point.
     * @param float $y1  Ordinate of first point.
     * @param float $x2  Abscissa of second point.
     * @param float $y2  Ordinate of second point.
     *
     * @see setLineWidth()
     * @see setDrawColor()
     */
    function line($x1, $y1, $x2, $y2)
    {
        if ($x1 < 0) {
            $x1 += $this->w;
        }
        if ($y1 < 0) {
            $y1 += $this->h;
        }
        if ($x2 < 0) {
            $x2 += $this->w;
        }
        if ($y2 < 0) {
            $y2 += $this->h;
        }

        $this->_out(sprintf('%.2' . FILE_PDF_FLOAT . ' %.2' . FILE_PDF_FLOAT . ' m %.2' . FILE_PDF_FLOAT . ' %.2' . FILE_PDF_FLOAT . ' l S', $x1 * $this->_scale, ($this->h - $y1) * $this->_scale, $x2 * $this->_scale, ($this->h - $y2) * $this->_scale));
    }

    /**
     * Outputs a rectangle.
     *
     * It can be drawn (border only), filled (with no border) or both.
     *
     * All coordinates can be negative to provide values from the right or
     * bottom edge of the page (since File_PDF 0.2.0, Horde 3.2).
     *
     * @param float $x       Abscissa of upper-left corner.
     * @param float $y       Ordinate of upper-left corner.
     * @param float $width   Width.
     * @param float $height  Height.
     * @param float $style   Style of rendering. Possible values are:
     *                         - D or empty string: draw (default)
     *                         - F: fill
     *                         - DF or FD: draw and fill
     *
     * @see setLineWidth()
     * @see setDrawColor()
     * @see setFillColor()
     */
    function rect($x, $y, $width, $height, $style = '')
    {
        if ($x < 0) {
            $x += $this->w;
        }
        if ($y < 0) {
            $y += $this->h;
        }

        $style = strtoupper($style);
        if ($style == 'F') {
            $op = 'f';
        } elseif ($style == 'FD' || $style == 'DF') {
            $op = 'B';
        } else {
            $op = 'S';
        }

        $x      = $this->_toPt($x);
        $y      = $this->_toPt($y);
        $width  = $this->_toPt($width);
        $height = $this->_toPt($height);

        $this->_out(sprintf('%.2' . FILE_PDF_FLOAT . ' %.2' . FILE_PDF_FLOAT . ' %.2' . FILE_PDF_FLOAT . ' %.2' . FILE_PDF_FLOAT . ' re %s', $x, $this->hPt - $y, $width, -$height, $op));
    }

    /**
     * Outputs a circle. It can be drawn (border only), filled (with no
     * border) or both.
     *
     * All coordinates can be negative to provide values from the right or
     * bottom edge of the page (since File_PDF 0.2.0, Horde 3.2).
     *
     * @param float $x       Abscissa of the center of the circle.
     * @param float $y       Ordinate of the center of the circle.
     * @param float $r       Circle radius.
     * @param string $style  Style of rendering. Possible values are:
     *                         - D or empty string: draw (default)
     *                         - F: fill
     *                         - DF or FD: draw and fill
     */
    function circle($x, $y, $r, $style = '')
    {
        if ($x < 0) {
            $x += $this->w;
        }
        if ($y < 0) {
            $y += $this->h;
        }

        $style = strtolower($style);
        if ($style == 'f') {
            $op = 'f';      // Style is fill only.
        } elseif ($style == 'fd' || $style == 'df') {
            $op = 'B';      // Style is fill and stroke.
        } else {
            $op = 'S';      // Style is stroke only.
        }

        $x = $this->_toPt($x);
        $y = $this->_toPt($y);
        $r = $this->_toPt($r);

        /* Invert the y scale. */
        $y = $this->hPt - $y;
        /* Length of the Bezier control. */
        $b = $r * 0.552;

        /* Move from the given origin and set the current point
         * to the start of the first Bezier curve. */
        $c = sprintf('%.2' . FILE_PDF_FLOAT . ' %.2' . FILE_PDF_FLOAT . ' m', $x - $r, $y);
        $x = $x - $r;
        /* First circle quarter. */
        $c .= sprintf(' %.2' . FILE_PDF_FLOAT . ' %.2' . FILE_PDF_FLOAT . ' %.2' . FILE_PDF_FLOAT . ' %.2' . FILE_PDF_FLOAT . ' %.2' . FILE_PDF_FLOAT . ' %.2' . FILE_PDF_FLOAT . ' c',
                      $x, $y + $b,           // First control point.
                      $x + $r - $b, $y + $r, // Second control point.
                      $x + $r, $y + $r);     // Final point.
        /* Set x/y to the final point. */
        $x = $x + $r;
        $y = $y + $r;
        /* Second circle quarter. */
        $c .= sprintf(' %.2' . FILE_PDF_FLOAT . ' %.2' . FILE_PDF_FLOAT . ' %.2' . FILE_PDF_FLOAT . ' %.2' . FILE_PDF_FLOAT . ' %.2' . FILE_PDF_FLOAT . ' %.2' . FILE_PDF_FLOAT . ' c',
                      $x + $b, $y,
                      $x + $r, $y - $r + $b,
                      $x + $r, $y - $r);
        /* Set x/y to the final point. */
        $x = $x + $r;
        $y = $y - $r;
        /* Third circle quarter. */
        $c .= sprintf(' %.2' . FILE_PDF_FLOAT . ' %.2' . FILE_PDF_FLOAT . ' %.2' . FILE_PDF_FLOAT . ' %.2' . FILE_PDF_FLOAT . ' %.2' . FILE_PDF_FLOAT . ' %.2' . FILE_PDF_FLOAT . ' c',
                      $x, $y - $b,
                      $x - $r + $b, $y - $r,
                      $x - $r, $y - $r);
        /* Set x/y to the final point. */
        $x = $x - $r;
        $y = $y - $r;
        /* Fourth circle quarter. */
        $c .= sprintf(' %.2' . FILE_PDF_FLOAT . ' %.2' . FILE_PDF_FLOAT . ' %.2' . FILE_PDF_FLOAT . ' %.2' . FILE_PDF_FLOAT . ' %.2' . FILE_PDF_FLOAT . ' %.2' . FILE_PDF_FLOAT . ' c %s',
                      $x - $b, $y,
                      $x - $r, $y + $r - $b,
                      $x - $r, $y + $r,
                      $op);
        /* Output the whole string. */
        $this->_out($c);
    }

    /**
     * Imports a TrueType or Type1 font and makes it available. It is
     * necessary to generate a font definition file first with the
     * makefont.php utility.
     * The location of the definition file (and the font file itself when
     * embedding) must be found at the full path name included.
     *
     * Example:
     * <code>
     * $pdf->addFont('Comic', 'I');
     * is equivalent to:
     * $pdf->addFont('Comic', 'I', 'comici.php');
     * </code>
     *
     * @param string $family  Font family. The name can be chosen arbitrarily.
     *                        If it is a standard family name, it will
     *                        override the corresponding font.
     * @param string $style   Font style. Possible values are (case
     *                        insensitive):
     *                          - empty string: regular (default)
     *                          - B: bold
     *                          - I: italic
     *                          - BI or IB: bold italic
     * @param string $file    The font definition file. By default, the name is
     *                        built from the family and style, in lower case
     *                        with no space.
     *
     * @see setFont()
     */
    function addFont($family, $style = '', $file = '')
    {
        $family = strtolower($family);
        if ($family == 'arial') {
            $family = 'helvetica';
        }

        $style = strtoupper($style);
        if ($style == 'IB') {
            $style = 'BI';
        }
        if (isset($this->_fonts[$family . $style])) {
            return $this->raiseError(sprintf('Font already added: %s %s', $family, $style));
        }
        if ($file == '') {
            $file = str_replace(' ', '', $family) . strtolower($style) . '.php';
        }
        include($file);
        if (!isset($name)) {
            return $this->raiseError('Could not include font definition file');
        }
        $i = count($this->_fonts) + 1;
        $this->_fonts[$family . $style] = array('i' => $i, 'type' => $type, 'name' => $name, 'desc' => $desc, 'up' => $up, 'ut' => $ut, 'cw' => $cw, 'enc' => $enc, 'file' => $file);
        if ($diff) {
            /* Search existing encodings. */
            $d = 0;
            $nb = count($this->_diffs);
            for ($i = 1; $i <= $nb; $i++) {
                if ($this->_diffs[$i] == $diff) {
                    $d = $i;
                    break;
                }
            }
            if ($d == 0) {
                $d = $nb + 1;
                $this->_diffs[$d] = $diff;
            }
            $this->_fonts[$family . $style]['diff'] = $d;
        }
        if ($file) {
            if ($type == 'TrueType') {
                $this->_font_files[$file] = array('length1' => $originalsize);
            } else {
                $this->_font_files[$file] = array('length1' => $size1, 'length2' => $size2);
            }
        }
    }

    /**
     * Sets the font used to print character strings.
     *
     * It is mandatory to call this method at least once before printing text
     * or the resulting document would not be valid. The font can be either a
     * standard one or a font added via the {@link addFont()} method. Standard
     * fonts use Windows encoding cp1252 (Western Europe).
     *
     * The method can be called before the first page is created and the font
     * is retained from page to page.
     *
     * If you just wish to change the current font size, it is simpler to call
     * {@link setFontSize()}.
     *
     * @param string $family  Family font. It can be either a name defined by
     *                        {@link addFont()} or one of the standard families
     *                        (case insensitive):
     *                          - Courier (fixed-width)
     *                          - Helvetica or Arial (sans serif)
     *                          - Times (serif)
     *                          - Symbol (symbolic)
     *                          - ZapfDingbats (symbolic)
     *                        It is also possible to pass an empty string. In
     *                        that case, the current family is retained.
     * @param string $style   Font style. Possible values are (case
     *                        insensitive):
     *                          - empty string: regular
     *                          - B: bold
     *                          - I: italic
     *                          - U: underline
     *                        or any combination. Bold and italic styles do not
     *                        apply to Symbol and ZapfDingbats.
     * @param integer $size   Font size in points. The default value is the
     *                        current size. If no size has been specified since
     *                        the beginning of the document, the value taken
     *                        is 12.
     * @param boolean $force  Force the setting of the font. Each new page will
     *                        require a new call to {@link setFont()} and
     *                        settings this to true will make sure that the
     *                        checks for same font calls will be skipped.
     *
     * @see addFont()
     * @see setFontSize()
     * @see cell()
     * @see multiCell()
     * @see write()
     */
    function setFont($family, $style = '', $size = null, $force = false)
    {
        $family = strtolower($family);
        if (empty($family)) {
            $family = $this->_font_family;
        }
        if ($family == 'arial') {
            /* Use helvetica instead of arial. */
            $family = 'helvetica';
        } elseif ($family == 'symbol' || $family == 'zapfdingbats') {
            /* These two fonts do not have styles available. */
            $style = '';
        }

        $style = strtoupper($style);

        /* Underline is handled separately, if specified in the style var
         * remove it from the style and set the underline flag. */
        if (strpos($style, 'U') !== false) {
            $this->_underline = true;
            $style = str_replace('U', '', $style);
        } else {
            $this->_underline = false;
        }

        if ($style == 'IB') {
            $style = 'BI';
        }

        /* If no size specified, use current size. */
        if (is_null($size)) {
            $size = $this->_font_size_pt;
        }

        /* If font requested is already the current font and no force setting
         * of the font is requested (eg. when adding a new page) don't bother
         * with the rest of the function and simply return. */
        if ($this->_font_family == $family && $this->_font_style == $style &&
            $this->_font_size_pt == $size && !$force) {
            return;
        }

        /* Set the font key. */
        $fontkey = $family . $style;

        /* Test if already cached. */
        if (!isset($this->_fonts[$fontkey])) {
            /* Get the character width definition file. */
            $font_widths = File_PDF::_getFontFile($fontkey);
            if (is_a($font_widths, 'PEAR_Error')) {
                return $font_widths;
            }

            $i = count($this->_fonts) + 1;
            $this->_fonts[$fontkey] = array(
                'i'    => $i,
                'type' => 'core',
                'name' => $this->_core_fonts[$fontkey],
                'up'   => -100,
                'ut'   => 50,
                'cw'   => $font_widths[$fontkey]);
        }

        /* Store font information as current font. */
        $this->_font_family  = $family;
        $this->_font_style   = $style;
        $this->_font_size_pt = $size;
        $this->_font_size    = $size / $this->_scale;
        $this->_current_font = &$this->_fonts[$fontkey];

        /* Output font information if at least one page has been defined. */
        if ($this->_page > 0) {
            $this->_out(sprintf('BT /F%d %.2' . FILE_PDF_FLOAT . ' Tf ET', $this->_current_font['i'], $this->_font_size_pt));
        }
    }

    /**
     * Defines the size of the current font.
     *
     * @param float $size  The size (in points).
     *
     * @see setFont()
     */
    function setFontSize($size)
    {
        /* If the font size is already the current font size, just return. */
        if ($this->_font_size_pt == $size) {
            return;
        }
        /* Set the current font size, both in points and scaled to user
         * units. */
        $this->_font_size_pt = $size;
        $this->_font_size = $size / $this->_scale;

        /* Output font information if at least one page has been defined. */
        if ($this->_page > 0) {
            $this->_out(sprintf('BT /F%d %.2' . FILE_PDF_FLOAT . ' Tf ET', $this->_current_font['i'], $this->_font_size_pt));
        }
    }

    /**
     * Defines the style of the current font.
     *
     * @param string $style  The font style.
     *
     * @since File_PDF 0.2.0
     * @since Horde 3.2
     * @see setFont()
     */
    function setFontStyle($style)
    {
        return $this->setFont($this->_font_family, $style);
    }

    /**
     * Creates a new internal link and returns its identifier.
     *
     * An internal link is a clickable area which directs to another place
     * within the document.
     *
     * The identifier can then be passed to {@link cell()}, {@link()} write,
     * {@link image()} or {@link link()}. The destination is defined with
     * {@link setLink()}.
     *
     * @see cell()
     * @see write()
     * @see image()
     * @see link()
     * @see setLink()
     */
    function addLink()
    {
        $n = count($this->_links) + 1;
        $this->_links[$n] = array(0, 0);
        return $n;
    }

    /**
     * Defines the page and position a link points to.
     *
     * @param integer $link  The link identifier returned by {@link addLink()}.
     * @param float $y       Ordinate of target position; -1 indicates the
     *                       current position. The default value is 0 (top of
     *                       page).
     * @param integer $page  Number of target page; -1 indicates the current
     *                       page.
     *
     * @see addLink()
     */
    function setLink($link, $y = 0, $page = -1)
    {
        if ($y == -1) {
            $y = $this->y;
        }
        if ($page == -1) {
            $page = $this->_page;
        }
        $this->_links[$link] = array($page, $y);
    }

    /**
     * Puts a link on a rectangular area of the page.
     *
     * Text or image links are generally put via {@link cell()}, {@link
     * write()} or {@link image()}, but this method can be useful for instance
     * to define a clickable area inside an image.
     *
     * All coordinates can be negative to provide values from the right or
     * bottom edge of the page (since File_PDF 0.2.0, Horde 3.2).
     *
     * @param float $x       Abscissa of the upper-left corner of the
     *                       rectangle.
     * @param float $y       Ordinate of the upper-left corner of the
     *                       rectangle.
     * @param float $width   Width of the rectangle.
     * @param float $height  Height of the rectangle.
     * @param mixed $link    URL or identifier returned by {@link addLink()}.
     *
     * @see addLink()
     * @see cell()
     * @see write()
     * @see image()
     */
    function link($x, $y, $width, $height, $link)
    {
        if ($x < 0) {
            $x += $this->w;
        }
        if ($y < 0) {
            $y += $this->h;
        }

        /* Set up the coordinates with correct scaling in pt. */
        $x      = $this->_toPt($x);
        $y      = $this->hPt - $this->_toPt($y);
        $width  = $this->_toPt($width);
        $height = $this->_toPt($height);

        /* Save link to page links array. */
        $this->_link($x, $y, $width, $height, $link);
    }

    /**
     * Prints a character string.
     *
     * The origin is on the left of the first character, on the baseline. This
     * method allows to place a string precisely on the page, but it is
     * usually easier to use {@link cell()}, {@link multiCell()} or {@link
     * write()} which are the standard methods to print text.
     *
     * All coordinates can be negative to provide values from the right or
     * bottom edge of the page (since File_PDF 0.2.0, Horde 3.2).
     *
     * @param float $x      Abscissa of the origin.
     * @param float $y      Ordinate of the origin.
     * @param string $text  String to print.
     *
     * @see setFont()
     * @see cell()
     * @see multiCell()
     * @see write()
     */
    function text($x, $y, $text)
    {
        if ($x < 0) {
            $x += $this->w;
        }
        if ($y < 0) {
            $y += $this->h;
        }

        /* Scale coordinates into points and set correct Y position. */
        $x = $this->_toPt($x);
        $y = $this->hPt - $this->_toPt($y);

        /* Escape any potentially harmful characters. */
        $text = $this->_escape($text);

        $out = sprintf('BT %.2' . FILE_PDF_FLOAT . ' %.2' . FILE_PDF_FLOAT . ' Td (%s) Tj ET', $x, $y, $text);
        if ($this->_underline && $text != '') {
            $out .= ' ' . $this->_doUnderline($x, $y, $text);
        }
        if ($this->_color_flag) {
            $out = sprintf('q %s %s Q', $this->_text_color, $out);
        }
        $this->_out($out);
    }

    /**
     * Whenever a page break condition is met, the method is called, and the
     * break is issued or not depending on the returned value. The default
     * implementation returns a value according to the mode selected by
     * {@link setAutoPageBreak()}.
     * This method is called automatically and should not be called directly
     * by the application.
     *
     * @return boolean
     *
     * @see setAutoPageBreak()
     */
    function acceptPageBreak()
    {
        return $this->_auto_page_break;
    }

    /**
     * Prints a cell (rectangular area) with optional borders, background
     * color and character string.
     *
     * The upper-left corner of the cell corresponds to the current
     * position. The text can be aligned or centered. After the call, the
     * current position moves to the right or to the next line. It is possible
     * to put a link on the text.  If automatic page breaking is enabled and
     * the cell goes beyond the limit, a page break is done before outputting.
     *
     * @param float $width   Cell width. If 0, the cell extends up to the right
     *                       margin.
     * @param float $height  Cell height.
     * @param string $text   String to print.
     * @param mixed $border  Indicates if borders must be drawn around the
     *                       cell. The value can be either a number:
     *                         - 0: no border (default)
     *                         - 1: frame
     *                       or a string containing some or all of the
     *                       following characters (in any order):
     *                         - L: left
     *                         - T: top
     *                         - R: right
     *                         - B: bottom
     * @param integer $ln    Indicates where the current position should go
     *                       after the call. Possible values are:
     *                         - 0: to the right (default)
     *                         - 1: to the beginning of the next line
     *                         - 2: below
     *                       Putting 1 is equivalent to putting 0 and calling
     *                       {@link newLine()} just after.
     * @param string $align  Allows to center or align the text. Possible
     *                       values are:
     *                         - L or empty string: left (default)
     *                         - C: center
     *                         - R: right
     * @param integer $fill  Indicates if the cell fill type. Possible values
     *                       are:
     *                         - 0: transparent (default)
     *                         - 1: painted
     * @param string $link   URL or identifier returned by {@link addLink()}.
     *
     * @see setFont()
     * @see setDrawColor()
     * @see setFillColor()
     * @see setLineWidth()
     * @see addLink()
     * @see newLine()
     * @see multiCell()
     * @see write()
     * @see setAutoPageBreak()
     */
    function cell($width, $height = 0, $text = '', $border = 0, $ln = 0,
                  $align = '', $fill = 0, $link = '')
    {
        $k = $this->_scale;
        if ($this->y + $height > $this->_page_break_trigger &&
            !$this->_in_footer && $this->acceptPageBreak()) {
            $x = $this->x;
            $ws = $this->_word_spacing;
            if ($ws > 0) {
                $this->_word_spacing = 0;
                $this->_out('0 Tw');
            }
            $result = $this->addPage($this->_current_orientation);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
            $this->x = $x;
            if ($ws > 0) {
                $this->_word_spacing = $ws;
                $this->_out(sprintf('%.3' . FILE_PDF_FLOAT . ' Tw', $ws * $k));
            }
        }
        if ($width == 0) {
            $width = $this->w - $this->_right_margin - $this->x;
        }
        $s = '';
        if ($fill == 1 || $border == 1) {
            if ($fill == 1) {
                $op = ($border == 1) ? 'B' : 'f';
            } else {
                $op = 'S';
            }
            $s = sprintf('%.2' . FILE_PDF_FLOAT . ' %.2' . FILE_PDF_FLOAT . ' %.2' . FILE_PDF_FLOAT . ' %.2' . FILE_PDF_FLOAT . ' re %s ', $this->x * $k, ($this->h - $this->y) * $k, $width * $k, -$height * $k, $op);
        }
        if (is_string($border)) {
            if (strpos($border, 'L') !== false) {
                $s .= sprintf('%.2' . FILE_PDF_FLOAT . ' %.2' . FILE_PDF_FLOAT . ' m %.2' . FILE_PDF_FLOAT . ' %.2' . FILE_PDF_FLOAT . ' l S ', $this->x * $k, ($this->h - $this->y) * $k, $this->x * $k, ($this->h - ($this->y + $height)) * $k);
            }
            if (strpos($border, 'T') !== false) {
                $s .= sprintf('%.2' . FILE_PDF_FLOAT . ' %.2' . FILE_PDF_FLOAT . ' m %.2' . FILE_PDF_FLOAT . ' %.2' . FILE_PDF_FLOAT . ' l S ', $this->x * $k, ($this->h - $this->y) * $k, ($this->x + $width) * $k, ($this->h - $this->y) * $k);
            }
            if (strpos($border, 'R') !== false) {
                $s .= sprintf('%.2' . FILE_PDF_FLOAT . ' %.2' . FILE_PDF_FLOAT . ' m %.2' . FILE_PDF_FLOAT . ' %.2' . FILE_PDF_FLOAT . ' l S ', ($this->x + $width) * $k, ($this->h - $this->y) * $k, ($this->x + $width) * $k, ($this->h - ($this->y + $height)) * $k);
            }
            if (strpos($border, 'B') !== false) {
                $s .= sprintf('%.2' . FILE_PDF_FLOAT . ' %.2' . FILE_PDF_FLOAT . ' m %.2' . FILE_PDF_FLOAT . ' %.2' . FILE_PDF_FLOAT . ' l S ', $this->x * $k, ($this->h - ($this->y + $height)) * $k, ($this->x + $width) * $k, ($this->h - ($this->y + $height)) * $k);
            }
        }
        if ($text != '') {
            if ($align == 'R') {
                $dx = $width - $this->_cell_margin - $this->getStringWidth($text);
            } elseif ($align == 'C') {
                $dx = ($width - $this->getStringWidth($text)) / 2;
            } else {
                $dx = $this->_cell_margin;
            }
            if ($this->_color_flag) {
                $s .= 'q ' . $this->_text_color . ' ';
            }
            $text = str_replace(')', '\\)', str_replace('(', '\\(', str_replace('\\', '\\\\', $text)));
            $test2 = ((.5 * $height) + (.3 * $this->_font_size));
            $test1 = $this->fhPt - (($this->y + $test2) * $k);
            $x = ($this->x + $dx) * $k;
            $y = ($this->h - ($this->y + .5 * $height + .3 * $this->_font_size)) * $k;
            $s .= sprintf('BT %.2' . FILE_PDF_FLOAT . ' %.2' . FILE_PDF_FLOAT . ' Td (%s) Tj ET', $x, $y, $text);
            if ($this->_underline) {
                $s .= ' ' . $this->_doUnderline($x, $y, $text);
            }
            if ($this->_color_flag) {
                $s .= ' Q';
            }
            if ($link) {
                $this->link($this->x + $dx, $this->y + .5 * $height- .5 * $this->_font_size, $this->getStringWidth($text), $this->_font_size, $link);
            }
        }
        if ($s) {
            $this->_out($s);
        }
        $this->_last_height = $height;
        if ($ln > 0) {
            /* Go to next line. */
            $this->y += $height;
            if ($ln == 1) {
                $this->x = $this->_left_margin;
            }
        } else {
            $this->x += $width;
        }
    }

    /**
     * This method allows printing text with line breaks.
     *
     * They can be automatic (as soon as the text reaches the right border of
     * the cell) or explicit (via the \n character). As many cells as
     * necessary are output, one below the other. Text can be aligned,
     * centered or justified. The cell block can be framed and the background
     * painted.
     *
     * @param float $width   Width of cells. If 0, they extend up to the right
     *                       margin of the page.
     * @param float $height  Height of cells.
     * @param string $text   String to print.
     * @param mixed $border  Indicates if borders must be drawn around the cell
     *                       block. The value can be either a number:
     *                         - 0: no border (default)
     *                         - 1: frame
     *                       or a string containing some or all of the
     *                       following characters (in any order):
     *                         - L: left
     *                         - T: top
     *                         - R: right
     *                         - B: bottom
     * @param string $align  Sets the text alignment. Possible values are:
     *                         - L: left alignment
     *                         - C: center
     *                         - R: right alignment
     *                         - J: justification (default value)
     * @param integer $fill  Indicates if the cell background must:
     *                         - 0: transparent (default)
     *                         - 1: painted
     *
     * @see setFont()
     * @see setDrawColor()
     * @see setFillColor()
     * @see setLineWidth()
     * @see cell()
     * @see write()
     * @see setAutoPageBreak()
     */
    function multiCell($width, $height, $text, $border = 0, $align = 'J',
                       $fill = 0)
    {
        $cw = &$this->_current_font['cw'];
        if ($width == 0) {
            $width = $this->w - $this->_right_margin - $this->x;
        }
        $wmax = ($width-2 * $this->_cell_margin) * 1000 / $this->_font_size;
        $s = str_replace("\r", '', $text);
        $nb = strlen($s);
        if ($nb > 0 && $s[$nb-1] == "\n") {
            $nb--;
        }
        $b = 0;
        if ($border) {
            if ($border == 1) {
                $border = 'LTRB';
                $b = 'LRT';
                $b2 = 'LR';
            } else {
                $b2 = '';
                if (strpos($border, 'L') !== false) {
                    $b2 .= 'L';
                }
                if (strpos($border, 'R') !== false) {
                    $b2 .= 'R';
                }
                $b = (strpos($border, 'T') !== false) ? $b2 . 'T' : $b2;
            }
        }
        $sep = -1;
        $i   = 0;
        $j   = 0;
        $l   = 0;
        $ns  = 0;
        $nl  = 1;
        while ($i < $nb) {
            /* Get next character. */
            $c = $s[$i];
            if ($c == "\n") {
                /* Explicit line break. */
                if ($this->_word_spacing > 0) {
                    $this->_word_spacing = 0;
                    $this->_out('0 Tw');
                }
                $result = $this->cell($width, $height, substr($s, $j, $i-$j),
                                      $b, 2, $align, $fill);
                if (is_a($result, 'PEAR_Error')) {
                    return $result;
                }
                $i++;
                $sep = -1;
                $j = $i;
                $l = 0;
                $ns = 0;
                $nl++;
                if ($border && $nl == 2) {
                    $b = $b2;
                }
                continue;
            }
            if ($c == ' ') {
                $sep = $i;
                $ls = $l;
                $ns++;
            }
            $l += $cw[$c];
            if ($l > $wmax) {
                /* Automatic line break. */
                if ($sep == -1) {
                    if ($i == $j) {
                        $i++;
                    }
                    if ($this->_word_spacing > 0) {
                        $this->_word_spacing = 0;
                        $this->_out('0 Tw');
                    }
                    $result = $this->cell($width, $height,
                                          substr($s, $j, $i - $j), $b, 2,
                                          $align, $fill);
                    if (is_a($result, 'PEAR_Error')) {
                        return $result;
                    }
                } else {
                    if ($align == 'J') {
                        $this->_word_spacing = ($ns>1)
                            ? ($wmax - $ls) / 1000 * $this->_font_size / ($ns - 1)
                            : 0;
                        $this->_out(sprintf('%.3' . FILE_PDF_FLOAT . ' Tw',
                                            $this->_word_spacing * $this->_scale));
                    }
                    $result = $this->cell($width, $height,
                                          substr($s, $j, $sep - $j),
                                          $b, 2, $align, $fill);
                    if (is_a($result, 'PEAR_Error')) {
                        return $result;
                    }
                    $i = $sep + 1;
                }
                $sep = -1;
                $j = $i;
                $l = 0;
                $ns = 0;
                $nl++;
                if ($border && $nl == 2) {
                    $b = $b2;
                }
            } else {
                $i++;
            }
        }
        /* Last chunk. */
        if ($this->_word_spacing > 0) {
            $this->_word_spacing = 0;
            $this->_out('0 Tw');
        }
        if ($border && strpos($border, 'B') !== false) {
            $b .= 'B';
        }
        $result = $this->cell($width, $height, substr($s, $j, $i), $b, 2,
                              $align, $fill);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }
        $this->x = $this->_left_margin;
    }

    /**
     * This method prints text from the current position.
     *
     * When the right margin is reached (or the \n character is met) a line
     * break occurs and text continues from the left margin. Upon method exit,
     * the current position is left just at the end of the text.
     *
     * It is possible to put a link on the text.
     *
     * Example:
     * <code>
     * // Begin with regular font
     * $pdf->setFont('Arial', '', 14);
     * $pdf->write(5, 'Visit ');
     * // Then put a blue underlined link
     * $pdf->setTextColor(0, 0, 255);
     * $pdf->setFont('', 'U');
     * $pdf->write(5, 'www.fpdf.org', 'http://www.fpdf.org');
     * </code>
     *
     * @param float $height  Line height.
     * @param string $text   String to print.
     * @param mixed $link    URL or identifier returned by {@link addLink()}.
     *
     * @see setFont()
     * @see addLink()
     * @see multiCell()
     * @see setAutoPageBreak()
     */
    function write($height, $text, $link = '')
    {
        $cw = &$this->_current_font['cw'];
        $width = $this->w - $this->_right_margin - $this->x;
        $wmax = ($width - 2 * $this->_cell_margin) * 1000 / $this->_font_size;
        $s = str_replace("\r", '', $text);
        $nb = strlen($s);
        $sep = -1;
        $i = 0;
        $j = 0;
        $l = 0;
        $nl = 1;
        while ($i < $nb) {
            /* Get next character. */
            $c = $s{$i};
            if ($c == "\n") {
                /* Explicit line break. */
                $result = $this->cell($width, $height, substr($s, $j, $i - $j),
                                      0, 2, '', 0, $link);
                if (is_a($result, 'PEAR_Error')) {
                    return $result;
                }
                $i++;
                $sep = -1;
                $j = $i;
                $l = 0;
                if ($nl == 1) {
                    $this->x = $this->_left_margin;
                    $width = $this->w - $this->_right_margin - $this->x;
                    $wmax = ($width - 2 * $this->_cell_margin) * 1000 / $this->_font_size;
                }
                $nl++;
                continue;
            }
            if ($c == ' ') {
                $sep = $i;
                $ls = $l;
            }
            $l += (isset($cw[$c]) ? $cw[$c] : 0);
            if ($l > $wmax) {
                /* Automatic line break. */
                if ($sep == -1) {
                    if ($this->x > $this->_left_margin) {
                        /* Move to next line. */
                        $this->x = $this->_left_margin;
                        $this->y += $height;
                        $width = $this->w - $this->_right_margin - $this->x;
                        $wmax = ($width - 2 * $this->_cell_margin) * 1000 / $this->_font_size;
                        $i++;
                        $nl++;
                        continue;
                    }
                    if ($i == $j) {
                        $i++;
                    }
                    $result = $this->cell($width, $height,
                                          substr($s, $j, $i - $j),
                                          0, 2, '', 0, $link);
                    if (is_a($result, 'PEAR_Error')) {
                        return $result;
                    }
                } else {
                    $result = $this->cell($width, $height,
                                          substr($s, $j, $sep - $j),
                                          0, 2, '', 0, $link);
                    if (is_a($result, 'PEAR_Error')) {
                        return $result;
                    }
                    $i = $sep + 1;
                }
                $sep = -1;
                $j = $i;
                $l = 0;
                if ($nl == 1) {
                    $this->x = $this->_left_margin;
                    $width = $this->w - $this->_right_margin - $this->x;
                    $wmax = ($width - 2 * $this->_cell_margin) * 1000 / $this->_font_size;
                }
                $nl++;
            } else {
                $i++;
            }
        }
        /* Last chunk. */
        if ($i != $j) {
            $result = $this->cell($l / 1000 * $this->_font_size, $height,
                                  substr($s, $j, $i), 0, 0, '', 0, $link);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }
    }

    /**
     * Writes text at an angle.
     *
     * All coordinates can be negative to provide values from the right or
     * bottom edge of the page (since File_PDF 0.2.0, Horde 3.2).
     *
     * @param integer $x         X coordinate.
     * @param integer $y         Y coordinate.
     * @param string $text       Text to write.
     * @param float $text_angle  Angle to rotate (Eg. 90 = bottom to top).
     * @param float $font_angle  Rotate characters as well as text.
     *
     * @see setFont()
     */
    function writeRotated($x, $y, $text, $text_angle, $font_angle = 0)
    {
        if ($x < 0) {
            $x += $this->w;
        }
        if ($y < 0) {
            $y += $this->h;
        }

        /* Escape text. */
        $text = $this->_escape($text);

        $font_angle += 90 + $text_angle;
        $text_angle *= M_PI / 180;
        $font_angle *= M_PI / 180;

        $text_dx = cos($text_angle);
        $text_dy = sin($text_angle);
        $font_dx = cos($font_angle);
        $font_dy = sin($font_angle);

        $s= sprintf('BT %.2' . FILE_PDF_FLOAT . ' %.2' . FILE_PDF_FLOAT . ' %.2' . FILE_PDF_FLOAT . ' %.2' . FILE_PDF_FLOAT . ' %.2' . FILE_PDF_FLOAT . ' %.2' . FILE_PDF_FLOAT . ' Tm (%s) Tj ET',
                    $text_dx, $text_dy, $font_dx, $font_dy,
                    $x * $this->_scale, ($this->h-$y) * $this->_scale, $text);

        if ($this->_draw_color) {
            $s = 'q ' . $this->_draw_color . ' ' . $s . ' Q';
        }
        $this->_out($s);
    }

    /**
     * Prints an image in the page.
     *
     * The upper-left corner and at least one of the dimensions must be
     * specified; the height or the width can be calculated automatically in
     * order to keep the image proportions. Supported formats are JPEG and
     * PNG.
     *
     * All coordinates can be negative to provide values from the right or
     * bottom edge of the page (since File_PDF 0.2.0, Horde 3.2).
     *
     * For JPEG, all flavors are allowed:
     *   - gray scales
     *   - true colors (24 bits)
     *   - CMYK (32 bits)
     *
     * For PNG, are allowed:
     *   - gray scales on at most 8 bits (256 levels)
     *   - indexed colors
     *   - true colors (24 bits)
     * but are not supported:
     *   - Interlacing
     *   - Alpha channel
     *
     * If a transparent color is defined, it will be taken into account (but
     * will be only interpreted by Acrobat 4 and above).
     * The format can be specified explicitly or inferred from the file
     * extension.
     * It is possible to put a link on the image.
     *
     * Remark: if an image is used several times, only one copy will be
     * embedded in the file.
     *
     * @param string $file   Name of the file containing the image.
     * @param float $x       Abscissa of the upper-left corner.
     * @param float $y       Ordinate of the upper-left corner.
     * @param float $width   Width of the image in the page. If equal to zero,
     *                       it is automatically calculated to keep the
     *                       original proportions.
     * @param float $height  Height of the image in the page. If not specified
     *                       or equal to zero, it is automatically calculated
     *                       to keep the original proportions.
     * @param string $type   Image format. Possible values are (case
     *                       insensitive): JPG, JPEG, PNG. If not specified,
     *                       the type is inferred from the file extension.
     * @param mixed $link    URL or identifier returned by {@link addLink()}.
     *
     * @see addLink()
     */
    function image($file, $x, $y, $width = 0, $height = 0, $type = '',
                   $link = '')
    {
        if ($x < 0) {
            $x += $this->w;
        }
        if ($y < 0) {
            $y += $this->h;
        }

        if (!isset($this->_images[$file])) {
            /* First use of image, get some file info. */
            if ($type == '') {
                $pos = strrpos($file, '.');
                if ($pos === false) {
                    return $this->raiseError(sprintf('Image file has no extension and no type was specified: %s', $file));
                }
                $type = substr($file, $pos + 1);
            }
            $type = strtolower($type);
            $mqr = get_magic_quotes_runtime();
            set_magic_quotes_runtime(0);
            if ($type == 'jpg' || $type == 'jpeg') {
                $info = $this->_parseJPG($file);
            } elseif ($type == 'png') {
                $info = $this->_parsePNG($file);
            } else {
                return $this->raiseError(sprintf('Unsupported image file type: %s', $type));
            }
            if (is_a($info, 'PEAR_Error')) {
                return $info;
            }
            set_magic_quotes_runtime($mqr);
            $info['i'] = count($this->_images) + 1;
            $this->_images[$file] = $info;
        } else {
            $info = $this->_images[$file];
        }

        /* Make sure all vars are converted to pt scale. */
        $x      = $this->_toPt($x);
        $y      = $this->hPt - $this->_toPt($y);
        $width  = $this->_toPt($width);
        $height = $this->_toPt($height);

        /* If not specified do automatic width and height calculations. */
        if (empty($width) && empty($height)) {
            $width = $info['w'];
            $height = $info['h'];
        } elseif (empty($width)) {
            $width = $height * $info['w'] / $info['h'];
        } elseif (empty($height)) {
            $height = $width * $info['h'] / $info['w'];
        }

        $this->_out(sprintf('q %.2' . FILE_PDF_FLOAT . ' 0 0 %.2' . FILE_PDF_FLOAT . ' %.2' . FILE_PDF_FLOAT . ' %.2' . FILE_PDF_FLOAT . ' cm /I%d Do Q', $width, $height, $x, $y - $height, $info['i']));

        /* Set any link if requested. */
        if ($link) {
            $this->_link($x, $y, $width, $height, $link);
        }
    }

    /**
     * Performs a line break.
     *
     * The current abscissa goes back to the left margin and the ordinate
     * increases by the amount passed in parameter.
     *
     * @param float $height  The height of the break. By default, the value
     *                       equals the height of the last printed cell.
     *
     * @see cell()
     */
    function newLine($height = '')
    {
        $this->x = $this->_left_margin;
        if (is_string($height)) {
            $this->y += $this->_last_height;
        } else {
            $this->y += $height;
        }
    }

    /**
     * Returns the abscissa of the current position in user units.
     *
     * @return float
     *
     * @see setX()
     * @see getY()
     * @see setY()
     */
    function getX()
    {
        return $this->x;
    }

    /**
     * Defines the abscissa of the current position.
     *
     * If the passed value is negative, it is relative to the right of the
     * page.
     *
     * @param float $x  The value of the abscissa.
     *
     * @see getX()
     * @see getY()
     * @see setY()
     * @see setXY()
     */
    function setX($x)
    {
        if ($x >= 0) {
            /* Absolute value. */
            $this->x = $x;
        } else {
            /* Negative, so relative to right edge of the page. */
            $this->x = $this->w + $x;
        }
    }

    /**
     * Returns the ordinate of the current position in user units.
     *
     * @return float
     *
     * @see setY()
     * @see getX()
     * @see setX()
     */
    function getY()
    {
        return $this->y;
    }

    /**
     * Defines the ordinate of the current position.
     *
     * If the passed value is negative, it is relative to the bottom of the
     * page.
     *
     * @param float $y  The value of the ordinate.
     *
     * @see getX()
     * @see getY()
     * @see setY()
     * @see setXY()
     */
    function setY($y)
    {
        if ($y >= 0) {
            /* Absolute value. */
            $this->y = $y;
        } else {
            /* Negative, so relative to bottom edge of the page. */
            $this->y = $this->h + $y;
        }
    }

    /**
     * Defines the abscissa and ordinate of the current position.
     *
     * If the passed values are negative, they are relative respectively to
     * the right and bottom of the page.
     *
     * @param float $x  The value of the abscissa.
     * @param float $y  The value of the ordinate.
     *
     * @see setX()
     * @see setY()
     */
    function setXY($x, $y)
    {
        $this->setY($y);
        $this->setX($x);
    }

    /**
     * Returns the current buffer content and resets the buffer.
     *
     * Use this method when creating large files to avoid memory problems.
     * This method doesn't work in combination with the output() or save()
     * methods, use getOutput() at the end. Calling this method doubles the
     * memory usage during the call.
     *
     * @since File_PDF 0.2.0
     * @since Horde 3.2
     * @see getOutput()
     */
    function flush()
    {
        // Make sure we have the file header.
        $this->_beginDoc();

        $buffer = $this->_buffer;
        $this->_buffer = '';
        $this->_flushed = true;
        $this->_buflen += strlen($buffer);

        return $buffer;
    }

    /**
     * Returns the raw PDF file.
     *
     * @see output()
     * @see flush()
     */
    function getOutput()
    {
        /* Check whether file has been closed. */
        if ($this->_state < 3) {
            $result = $this->close();
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }

        return $this->_buffer;
    }

    /**
     * Sends the buffered data to the browser.
     *
     * @param string $filename  The filename for the output file.
     * @param boolean $inline   True if inline, false if attachment.
     */
    function output($filename = 'unknown.pdf', $inline = false)
    {
        /* Check whether the buffer has been flushed already. */
        if ($this->_flushed) {
            return $this->raiseError('The buffer has been flushed already, don\'t use output() in combination with flush().');
        }

        /* Check whether file has been closed. */
        if ($this->_state < 3) {
            $result = $this->close();
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }

        /* Check if headers have been sent. */
        if (headers_sent()) {
            return $this->raiseError('Unable to send PDF file, some data has already been output to browser');
        }

        /* If HTTP_Download is not available return a PEAR_Error. */
        if (!include_once 'HTTP/Download.php') {
            return $this->raiseError('Missing PEAR package HTTP_Download');
        }

        /* Params for the output. */
        $disposition = $inline ? HTTP_DOWNLOAD_INLINE : HTTP_DOWNLOAD_ATTACHMENT;
        $params = array('data'               => $this->_buffer,
                        'contenttype'        => 'application/pdf',
                        'contentdisposition' => array($disposition, $filename));
        /* Output the file. */
        return HTTP_Download::staticSend($params);
    }

    /**
     * Saves the PDF file on the filesystem.
     *
     * @param string $filename  The filename for the output file.
     */
    function save($filename = 'unknown.pdf')
    {
        /* Check whether the buffer has been flushed already. */
        if ($this->_flushed) {
            return $this->raiseError('The buffer has been flushed already, don\'t use save() in combination with flush().');
        }

        /* Check whether file has been closed. */
        if ($this->_state < 3) {
            $result = $this->close();
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }

        $f = fopen($filename, 'wb');
        if (!$f) {
            return $this->raiseError(sprintf('Unable to save PDF file: %s', $filename));
        }
        fwrite($f, $this->_buffer, strlen($this->_buffer));
        fclose($f);
    }

    function _toPt($val)
    {
        return $val * $this->_scale;
    }

    function _getFontFile($fontkey, $path = '')
    {
        static $font_widths = array();

        if (!isset($font_widths[$fontkey])) {
            if (!empty($path)) {
                $file = $path . strtolower($fontkey) . '.php';
            } else {
                $file = 'File/PDF/fonts/' . strtolower($fontkey) . '.php';
            }
            include $file;
            if (!isset($font_widths[$fontkey])) {
                return $this->raiseError(sprintf('Could not include font metric file: %s', $file));
            }
        }

        return $font_widths;
    }

    function _link($x, $y, $width, $height, $link)
    {
        /* Save link to page links array. */
        $this->_page_links[$this->_page][] = array($x, $y, $width, $height, $link);
    }

    function _beginDoc()
    {
        /* Start document, but only if not yet started. */
        if ($this->_state < 1) {
            $this->_state = 1;
            $this->_out('%PDF-1.3');
        }
    }

    function _putPages()
    {
        $nb = $this->_page;
        if (!empty($this->_alias_nb_pages)) {
            /* Replace number of pages. */
            for ($n = 1; $n <= $nb; $n++) {
                $this->_pages[$n] = str_replace($this->_alias_nb_pages, $nb, $this->_pages[$n]);
            }
        }
        if ($this->_default_orientation == 'P') {
            $wPt = $this->fwPt;
            $hPt = $this->fhPt;
        } else {
            $wPt = $this->fhPt;
            $hPt = $this->fwPt;
        }
        $filter = ($this->_compress) ? '/Filter /FlateDecode ' : '';
        for ($n = 1; $n <= $nb; $n++) {
            /* Page */
            $this->_newobj();
            $this->_out('<</Type /Page');
            $this->_out('/Parent 1 0 R');
            if (isset($this->_orientation_changes[$n])) {
                $this->_out(sprintf('/MediaBox [0 0 %.2' . FILE_PDF_FLOAT . ' %.2' . FILE_PDF_FLOAT . ']', $hPt, $wPt));
            }
            $this->_out('/Resources 2 0 R');
            if (isset($this->_page_links[$n])) {
                /* Links */
                $annots = '/Annots [';
                foreach ($this->_page_links[$n] as $pl) {
                    $rect = sprintf('%.2' . FILE_PDF_FLOAT . ' %.2' . FILE_PDF_FLOAT . ' %.2' . FILE_PDF_FLOAT . ' %.2' . FILE_PDF_FLOAT . '', $pl[0], $pl[1], $pl[0] + $pl[2], $pl[1] - $pl[3]);
                    $annots .= '<</Type /Annot /Subtype /Link /Rect [' . $rect . '] /Border [0 0 0] ';
                    if (is_string($pl[4])) {
                        $annots .= '/A <</S /URI /URI ' . $this->_textString($pl[4]) . '>>>>';
                    } else {
                        $l = $this->_links[$pl[4]];
                        $height = isset($this->_orientation_changes[$l[0]]) ? $wPt : $hPt;
                        $annots .= sprintf('/Dest [%d 0 R /XYZ 0 %.2' . FILE_PDF_FLOAT . ' null]>>', 1 + 2 * $l[0], $height - $l[1] * $this->_scale);
                    }
                }
                $this->_out($annots . ']');
            }
            $this->_out('/Contents ' . ($this->_n + 1) . ' 0 R>>');
            $this->_out('endobj');
            /* Page content */
            $p = ($this->_compress) ? gzcompress($this->_pages[$n]) : $this->_pages[$n];
            $this->_newobj();
            $this->_out('<<' . $filter . '/Length ' . strlen($p) . '>>');
            $this->_putStream($p);
            $this->_out('endobj');
        }
        /* Pages root */
        $this->_offsets[1] = $this->_buflen + strlen($this->_buffer);
        $this->_out('1 0 obj');
        $this->_out('<</Type /Pages');
        $kids = '/Kids [';
        for ($i = 0; $i < $nb; $i++) {
            $kids .= (3 + 2 * $i) . ' 0 R ';
        }
        $this->_out($kids . ']');
        $this->_out('/Count ' . $nb);
        $this->_out(sprintf('/MediaBox [0 0 %.2' . FILE_PDF_FLOAT . ' %.2' . FILE_PDF_FLOAT . ']', $wPt, $hPt));
        $this->_out('>>');
        $this->_out('endobj');
    }

    function _putFonts()
    {
        $nf = $this->_n;
        foreach ($this->_diffs as $diff) {
            /* Encodings */
            $this->_newobj();
            $this->_out('<</Type /Encoding /BaseEncoding /WinAnsiEncoding /Differences [' . $diff . ']>>');
            $this->_out('endobj');
        }
        $mqr = get_magic_quotes_runtime();
        set_magic_quotes_runtime(0);
        foreach ($this->_font_files as $file => $info) {
            /* Font file embedding. */
            $this->_newobj();
            $this->_font_files[$file]['n'] = $this->_n;
            $size = filesize($file);
            if (!$size) {
                return $this->raiseError('Font file not found');
            }
            $this->_out('<</Length ' . $size);
            if (substr($file, -2) == '.z') {
                $this->_out('/Filter /FlateDecode');
            }
            $this->_out('/Length1 ' . $info['length1']);
            if (isset($info['length2'])) {
                $this->_out('/Length2 ' . $info['length2'] . ' /Length3 0');
            }
            $this->_out('>>');
            $f = fopen($file, 'rb');
            $this->_putStream(fread($f, $size));
            fclose($f);
            $this->_out('endobj');
        }
        set_magic_quotes_runtime($mqr);
        foreach ($this->_fonts as $k => $font) {
            /* Font objects */
            $this->_newobj();
            $this->_fonts[$k]['n'] = $this->_n;
            $name = $font['name'];
            $this->_out('<</Type /Font');
            $this->_out('/BaseFont /' . $name);
            if ($font['type'] == 'core') {
                /* Standard font. */
                $this->_out('/Subtype /Type1');
                if ($name != 'Symbol' && $name != 'ZapfDingbats') {
                    $this->_out('/Encoding /WinAnsiEncoding');
                }
            } else {
                /* Additional font. */
                $this->_out('/Subtype /' . $font['type']);
                $this->_out('/FirstChar 32');
                $this->_out('/LastChar 255');
                $this->_out('/Widths ' . ($this->_n + 1) . ' 0 R');
                $this->_out('/FontDescriptor ' . ($this->_n + 2) . ' 0 R');
                if ($font['enc']) {
                    if (isset($font['diff'])) {
                        $this->_out('/Encoding ' . ($nf + $font['diff']) . ' 0 R');
                    } else {
                        $this->_out('/Encoding /WinAnsiEncoding');
                    }
                }
            }
            $this->_out('>>');
            $this->_out('endobj');
            if ($font['type'] != 'core') {
                /* Widths. */
                $this->_newobj();
                $cw = &$font['cw'];
                $s = '[';
                for ($i = 32; $i <= 255; $i++) {
                    $s .= $cw[chr($i)] . ' ';
                }
                $this->_out($s . ']');
                $this->_out('endobj');
                /* Descriptor. */
                $this->_newobj();
                $s = '<</Type /FontDescriptor /FontName /' . $name;
                foreach ($font['desc'] as $k => $v) {
                    $s .= ' /' . $k . ' ' . $v;
                }
                $file = $font['file'];
                if ($file) {
                    $s .= ' /FontFile' . ($font['type'] == 'Type1' ? '' : '2') . ' ' . $this->_font_files[$file]['n'] . ' 0 R';
                }
                $this->_out($s . '>>');
                $this->_out('endobj');
            }
        }
    }

    function _putImages()
    {
        $filter = ($this->_compress) ? '/Filter /FlateDecode ' : '';
        foreach ($this->_images as $file => $info) {
            $this->_newobj();
            $this->_images[$file]['n'] = $this->_n;
            $this->_out('<</Type /XObject');
            $this->_out('/Subtype /Image');
            $this->_out('/Width ' . $info['w']);
            $this->_out('/Height ' . $info['h']);
            if ($info['cs'] == 'Indexed') {
                $this->_out('/ColorSpace [/Indexed /DeviceRGB ' . (strlen($info['pal'])/3 - 1) . ' ' . ($this->_n + 1) . ' 0 R]');
            } else {
                $this->_out('/ColorSpace /' . $info['cs']);
                if ($info['cs'] == 'DeviceCMYK') {
                    $this->_out('/Decode [1 0 1 0 1 0 1 0]');
                }
            }
            $this->_out('/BitsPerComponent ' . $info['bpc']);
            $this->_out('/Filter /' . $info['f']);
            if (isset($info['parms'])) {
                $this->_out($info['parms']);
            }
            if (isset($info['trns']) && is_array($info['trns'])) {
                $trns = '';
                $i_max = count($info['trns']);
                for ($i = 0; $i < $i_max; $i++) {
                    $trns .= $info['trns'][$i] . ' ' . $info['trns'][$i] . ' ';
                }
                $this->_out('/Mask [' . $trns . ']');
            }
            $this->_out('/Length ' . strlen($info['data']) . '>>');
            $this->_putStream($info['data']);
            $this->_out('endobj');

            /* Palette. */
            if ($info['cs'] == 'Indexed') {
                $this->_newobj();
                $pal = ($this->_compress) ? gzcompress($info['pal']) : $info['pal'];
                $this->_out('<<' . $filter . '/Length ' . strlen($pal) . '>>');
                $this->_putStream($pal);
                $this->_out('endobj');
            }
        }
    }

    function _putResources()
    {
        $this->_putFonts();
        $this->_putImages();
        /* Resource dictionary */
        $this->_offsets[2] = $this->_buflen + strlen($this->_buffer);
        $this->_out('2 0 obj');
        $this->_out('<</ProcSet [/PDF /Text /ImageB /ImageC /ImageI]');
        $this->_out('/Font <<');
        foreach ($this->_fonts as $font) {
            $this->_out('/F' . $font['i'] . ' ' . $font['n'] . ' 0 R');
        }
        $this->_out('>>');
        if (count($this->_images)) {
            $this->_out('/XObject <<');
            foreach ($this->_images as $image) {
                $this->_out('/I' . $image['i'] . ' ' . $image['n'] . ' 0 R');
            }
            $this->_out('>>');
        }
        $this->_out('>>');
        $this->_out('endobj');
    }

    function _putInfo()
    {
        $this->_out('/Producer ' . $this->_textString('Horde PDF'));
        if (!empty($this->_info['title'])) {
            $this->_out('/Title ' . $this->_textString($this->_info['title']));
        }
        if (!empty($this->_info['subject'])) {
            $this->_out('/Subject ' . $this->_textString($this->_info['subject']));
        }
        if (!empty($this->_info['author'])) {
            $this->_out('/Author ' . $this->_textString($this->_info['author']));
        }
        if (!empty($this->keywords)) {
            $this->_out('/Keywords ' . $this->_textString($this->keywords));
        }
        if (!empty($this->creator)) {
            $this->_out('/Creator ' . $this->_textString($this->creator));
        }
        $this->_out('/CreationDate ' . $this->_textString('D:' . date('YmdHis')));
    }

    function _putCatalog()
    {
        $this->_out('/Type /Catalog');
        $this->_out('/Pages 1 0 R');
        if ($this->_zoom_mode == 'fullpage') {
            $this->_out('/OpenAction [3 0 R /Fit]');
        } elseif ($this->_zoom_mode == 'fullwidth') {
            $this->_out('/OpenAction [3 0 R /FitH null]');
        } elseif ($this->_zoom_mode == 'real') {
            $this->_out('/OpenAction [3 0 R /XYZ null null 1]');
        } elseif (!is_string($this->_zoom_mode)) {
            $this->_out('/OpenAction [3 0 R /XYZ null null ' . ($this->_zoom_mode / 100) . ']');
        }
        if ($this->_layout_mode == 'single') {
            $this->_out('/PageLayout /SinglePage');
        } elseif ($this->_layout_mode == 'continuous') {
            $this->_out('/PageLayout /OneColumn');
        } elseif ($this->_layout_mode == 'two') {
            $this->_out('/PageLayout /TwoColumnLeft');
        }
    }

    function _putTrailer()
    {
        $this->_out('/Size ' . ($this->_n + 1));
        $this->_out('/Root ' . $this->_n . ' 0 R');
        $this->_out('/Info ' . ($this->_n - 1) . ' 0 R');
    }

    function _endDoc()
    {
        $this->_putPages();
        $this->_putResources();
        /* Info */
        $this->_newobj();
        $this->_out('<<');
        $this->_putInfo();
        $this->_out('>>');
        $this->_out('endobj');
        /* Catalog */
        $this->_newobj();
        $this->_out('<<');
        $this->_putCatalog();
        $this->_out('>>');
        $this->_out('endobj');
        /* Cross-ref */
        $o = $this->_buflen + strlen($this->_buffer);
        $this->_out('xref');
        $this->_out('0 ' . ($this->_n + 1));
        $this->_out('0000000000 65535 f ');
        for ($i = 1; $i <= $this->_n; $i++) {
            $this->_out(sprintf('%010d 00000 n ', $this->_offsets[$i]));
        }
        /* Trailer */
        $this->_out('trailer');
        $this->_out('<<');
        $this->_putTrailer();
        $this->_out('>>');
        $this->_out('startxref');
        $this->_out($o);
        $this->_out('%%EOF');
        $this->_state = 3;
    }

    function _beginPage($orientation)
    {
        $this->_page++;
        $this->_pages[$this->_page] = '';
        $this->_state = 2;
        $this->x = $this->_left_margin;
        $this->y = $this->_top_margin;
        $this->_last_height = 0;
        /* Page orientation */
        if (!$orientation) {
            $orientation = $this->_default_orientation;
        } else {
            $orientation = strtoupper($orientation[0]);
            if ($orientation != $this->_default_orientation) {
                $this->_orientation_changes[$this->_page] = true;
            }
        }
        if ($orientation != $this->_current_orientation) {
            /* Change orientation */
            if ($orientation == 'P') {
                $this->wPt = $this->fwPt;
                $this->hPt = $this->fhPt;
                $this->w   = $this->fw;
                $this->h   = $this->fh;
            } else {
                $this->wPt = $this->fhPt;
                $this->hPt = $this->fwPt;
                $this->w   = $this->fh;
                $this->h   = $this->fw;
            }
            $this->_page_break_trigger = $this->h - $this->_break_margin;
            $this->_current_orientation = $orientation;
        }
    }

    function _endPage()
    {
        /* End of page contents */
        $this->_state = 1;
    }

    function _newobj()
    {
        /* Begin a new object */
        $this->_n++;
        $this->_offsets[$this->_n] = $this->_buflen + strlen($this->_buffer);
        $this->_out($this->_n . ' 0 obj');
    }

    function _doUnderline($x, $y, $text)
    {
        /* Set the rectangle width according to text width. */
        $width  = $this->getStringWidth($text, true);

        /* Set rectangle position and height, using underline position and
         * thickness settings scaled by the font size. */
        $y = $y + ($this->_current_font['up'] * $this->_font_size_pt / 1000);
        $height = -$this->_current_font['ut'] * $this->_font_size_pt / 1000;

        return sprintf('%.2' . FILE_PDF_FLOAT . ' %.2' . FILE_PDF_FLOAT . ' %.2' . FILE_PDF_FLOAT . ' %.2' . FILE_PDF_FLOAT . ' re f', $x, $y, $width, $height);
    }

    function _parseJPG($file)
    {
        /* Extract info from a JPEG file. */
        $img = @getimagesize($file);
        if (!$img) {
            return $this->raiseError(sprintf('Missing or incorrect image file: %s', $file));
        }
        if ($img[2] != 2) {
            return $this->raiseError(sprintf('Not a JPEG file: %s', $file));
        }
        if (!isset($img['channels']) || $img['channels'] == 3) {
            $colspace = 'DeviceRGB';
        } elseif ($img['channels'] == 4) {
            $colspace = 'DeviceCMYK';
        } else {
            $colspace = 'DeviceGray';
        }
        $bpc = isset($img['bits']) ? $img['bits'] : 8;

        /* Read whole file. */
        $f = fopen($file, 'rb');
        $data = fread($f, filesize($file));
        fclose($f);

        return array('w' => $img[0], 'h' => $img[1], 'cs' => $colspace, 'bpc' => $bpc, 'f' => 'DCTDecode', 'data' => $data);
    }

    function _parsePNG($file)
    {
        /* Extract info from a PNG file. */
        $f = fopen($file, 'rb');
        if (!$f) {
            return $this->raiseError(sprintf('Unable to open image file: %s', $file));
        }

        /* Check signature. */
        if (fread($f, 8) != chr(137) . 'PNG' . chr(13) . chr(10) . chr(26) . chr(10)) {
            return $this->raiseError(sprintf('Not a PNG file: %s', $file));
        }

        /* Read header chunk. */
        fread($f, 4);
        if (fread($f, 4) != 'IHDR') {
            return $this->raiseError(sprintf('Incorrect PNG file: %s', $file));
        }
        $width = $this->_freadInt($f);
        $height = $this->_freadInt($f);
        $bpc = ord(fread($f, 1));
        if ($bpc > 8) {
            return $this->raiseError(sprintf('16-bit depth not supported: %s', $file));
        }
        $ct = ord(fread($f, 1));
        if ($ct == 0) {
            $colspace = 'DeviceGray';
        } elseif ($ct == 2) {
            $colspace = 'DeviceRGB';
        } elseif ($ct == 3) {
            $colspace = 'Indexed';
        } else {
            return $this->raiseError(sprintf('Alpha channel not supported: %s', $file));
        }
        if (ord(fread($f, 1)) != 0) {
            return $this->raiseError(sprintf('Unknown compression method: %s', $file));
        }
        if (ord(fread($f, 1)) != 0) {
            return $this->raiseError(sprintf('Unknown filter method: %s', $file));
        }
        if (ord(fread($f, 1)) != 0) {
            return $this->raiseError(sprintf('Interlacing not supported: %s', $file));
        }
        fread($f, 4);
        $parms = '/DecodeParms <</Predictor 15 /Colors ' . ($ct == 2 ? 3 : 1) . ' /BitsPerComponent ' . $bpc . ' /Columns ' . $width . '>>';
        /* Scan chunks looking for palette, transparency and image data. */
        $pal = '';
        $trns = '';
        $data = '';
        do {
            $n = $this->_freadInt($f);
            $type = fread($f, 4);
            if ($type == 'PLTE') {
                /* Read palette */
                $pal = fread($f, $n);
                fread($f, 4);
            } elseif ($type == 'tRNS') {
                /* Read transparency info */
                $t = fread($f, $n);
                if ($ct == 0) {
                    $trns = array(ord(substr($t, 1, 1)));
                } elseif ($ct == 2) {
                    $trns = array(ord(substr($t, 1, 1)), ord(substr($t, 3, 1)), ord(substr($t, 5, 1)));
                } else {
                    $pos = strpos($t, chr(0));
                    if (is_int($pos)) {
                        $trns = array($pos);
                    }
                }
                fread($f, 4);
            } elseif ($type == 'IDAT') {
                /* Read image data block */
                $data .= fread($f, $n);
                fread($f, 4);
            } elseif ($type == 'IEND') {
                break;
            } else {
                fread($f, $n + 4);
            }
        } while ($n);

        if ($colspace == 'Indexed' && empty($pal)) {
            return $this->raiseError(sprintf('Missing palette in: %s', $file));
        }
        fclose($f);

        return array('w' => $width, 'h' => $height, 'cs' => $colspace, 'bpc' => $bpc, 'f' => 'FlateDecode', 'parms' => $parms, 'pal' => $pal, 'trns' => $trns, 'data' => $data);
    }

    function _freadInt($f)
    {
        /* Read a 4-byte integer from file. */
        $i  = ord(fread($f, 1)) << 24;
        $i += ord(fread($f, 1)) << 16;
        $i += ord(fread($f, 1)) << 8;
        $i += ord(fread($f, 1));
        return $i;
    }

    function _textString($s)
    {
        /* Format a text string */
        return '(' . $this->_escape($s) . ')';
    }

    function _escape($s)
    {
        /* Add \ before \, ( and ) */
        return str_replace(array('\\', ')', '('),
                           array('\\\\', '\\)', '\\('),
                           $s);
    }

    function _putStream($s)
    {
        $this->_out('stream');
        $this->_out($s);
        $this->_out('endstream');
    }

    function _out($s)
    {
        /* Add a line to the document. */
        if ($this->_state == 2) {
            $this->_pages[$this->_page] .= $s . "\n";
        } else {
            $this->_buffer .= $s . "\n";
        }
    }

}
