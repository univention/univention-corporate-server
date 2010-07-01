<?php

require_once dirname(__FILE__) . '/../Image.php';

/**
 * This class implements the Horde_Image:: API for PNG images. It
 * mainly provides some utility functions, such as the ability to make
 * pixels or solid images for now.
 *
 * $Horde: framework/Image/Image/png.php,v 1.19.10.12 2009-01-06 15:23:12 jan Exp $
 *
 * Copyright 2003-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Mike Cochrane <mike@graftonhall.co.nz>
 * @since   Horde 3.0
 * @package Horde_Image
 */
class Horde_Image_png extends Horde_Image {

    /**
     * The array of pixel data.
     *
     * @var array
     */
    var $_img = array();

    /**
     * Color depth (only 8 and 16 implemented).
     *
     * @var integer
     */
    var $_colorDepth = 8;

    /**
     * Color type (only 2 (true color) implemented).
     *
     * @var integer
     */
    var $_colorType = 2;

    /**
     * Compression method (0 is the only current valid value).
     *
     * @var integer
     */
    var $_compressionMethod = 0;

    /**
     * Filter method (0 is the only current valid value).
     *
     * @var integer
     */
    var $_filterMethod = 0;

    /**
     * Interlace method (only 0 (no interlace) implemented).
     *
     * @var integer
     */
    var $_interlaceMethod = 0;

    /**
     * PNG image constructor.
     */
    function Horde_Image_png($params)
    {
        parent::Horde_Image($params);

        if (!empty($params['width'])) {
            $this->rectangle(0, 0, $params['width'], $params['height'], $this->_background, $this->_background);
        }
    }

    function getContentType()
    {
        return 'image/png';
    }

    /**
     * Return the raw data for this image.
     *
     * @return string  The raw image data.
     */
    function raw()
    {
        return
            $this->_header() .
            $this->_IHDR() .

            /* Say what created the image file. */
            $this->_tEXt('Software', 'Horde Framework Image_png Class') .

            /* Set the last modified date/time. */
            $this->_tIME() .

            $this->_IDAT() .
            $this->_IEND();
    }

    /**
     * Reset the image data.
     */
    function reset()
    {
        parent::reset();
        $this->_img = array();
    }

    /**
     * Draw a rectangle.
     *
     * @param integer $x       The left x-coordinate of the rectangle.
     * @param integer $y       The top y-coordinate of the rectangle.
     * @param integer $width   The width of the rectangle.
     * @param integer $height  The height of the rectangle.
     * @param string $color    The line color of the rectangle.
     * @param string $fill     The color to fill the rectangle with.
     */
    function rectangle($x, $y, $width, $height, $color = 'black', $fill = 'none')
    {
        list($r, $g, $b) = $this->getRGB($color);
        if ($fill != 'none') {
            list($fR, $fG, $fB) = $this->getRGB($fill);
        }

        $x2 = $x + $width;
        $y2 = $y + $height;

        for ($h = $y; $h <= $y2; $h++) {
            for ($w = $x; $w <= $x2; $w++) {
                // See if we're on an edge.
                if ($w == $x || $h == $y || $w == $x2 || $h == $y2) {
                    $this->_img[$h][$w] = array('r' => $r, 'g' => $g, 'b' => $b);
                } elseif ($fill != 'none') {
                    $this->_img[$h][$w] = array('r' => $fR, 'g' => $fG, 'b' => $fB);
                }
            }
        }
    }

    /**
     * Create the PNG file header.
     */
    function _header()
    {
        return pack('CCCCCCCC', 137, 80, 78, 71, 13, 10, 26, 10);
    }

    /**
     * Create Image Header block.
     */
    function _IHDR()
    {
        $data = pack('a4NNCCCCC', 'IHDR', $this->_width, $this->_height, $this->_colorDepth, $this->_colorType, $this->_compressionMethod, $this->_filterMethod, $this->_interlaceMethod);
        return pack('Na' . strlen($data) . 'N', strlen($data) - 4, $data, crc32($data));
    }

    /**
     * Create IEND block.
     */
    function _IEND()
    {
        $data = 'IEND';
        return pack('Na' . strlen($data) . 'N', strlen($data) - 4, $data, crc32($data));
    }

    /**
     * Create Image Data block.
     */
    function _IDAT()
    {
        $data = '';
        $prevscanline = null;
        $filter = 0;
        for ($i = 0; $i < $this->_height; $i++) {
            $scanline = array();
            $data .= chr($filter);
            for ($j = 0; $j < $this->_width; $j++) {
                if ($this->_colorDepth == 8) {
                    $scanline[$j] = pack('CCC', $this->_img[$i][$j]['r'], $this->_img[$i][$j]['g'], $this->_img[$i][$j]['b']);
                } elseif ($this->_colorDepth == 16) {
                    $scanline[$j] = pack('nnn', $this->_img[$i][$j]['r'] << 8, $this->_img[$i][$j]['g'] << 8, $this->_img[$i][$j]['b'] << 8);
                }

                if ($filter == 0) {
                    /* No Filter. */
                    $data .= $scanline[$j];
                } elseif ($filter == 2) {
                    /* Up Filter. */
                    $pixel = $scanline[$j] - $prevscanline[$j];
                    if ($this->_colorDepth == 8) {
                        $data .= pack('CCC', $pixel >> 16, ($pixel >> 8) & 0xFF, $pixel & 0xFF);
                    } elseif ($this->_colorDepth == 16) {
                        $data .= pack('nnn', ($pixel >> 32), ($pixel >> 16) & 0xFFFF, $pixel & 0xFFFF);
                    }
                }
            }
            $prevscanline = $scanline;
        }
        $compressed = gzdeflate($data, 9);

        $data = 'IDAT' . pack('CCa' . strlen($compressed) . 'a4', 0x78, 0x01, $compressed, $this->_Adler32($data));
        return pack('Na' . strlen($data) . 'N', strlen($data) - 4, $data, crc32($data));
    }

    /**
     * Create tEXt block.
     */
    function _tEXt($keyword, $text)
    {
        $data = 'tEXt' . $keyword . "\0" . $text;
        return pack('Na' . strlen($data) . 'N', strlen($data) - 4, $data, crc32($data));
    }

    /**
     * Create last modified time block.
     */
    function _tIME($date = null)
    {
        if (is_null($date)) {
            $date = time();
        }

        $data = 'tIME' . pack('nCCCCC', intval(date('Y', $date)), intval(date('m', $date)), intval(date('j', $date)), intval(date('G', $date)), intval(date('i', $date)), intval(date('s', $date)));
        return pack('Na' . strlen($data) . 'N', strlen($data) - 4, $data, crc32($data));
    }

    /**
     * Calculate an Adler32 checksum for a string.
     */
    function _Adler32($input)
    {
        $s1 = 1;
        $s2 = 0;
        $iMax = strlen($input);
        for ($i = 0; $i < $iMax; $i++) {
            $s1 = ($s1 + ord($input[$i])) % 0xFFF1;
            $s2 = ($s2 + $s1) % 0xFFF1;
        }
        return pack('N', (($s2 << 16) | $s1));
    }

}
