<?php
/**
 * The Browser_imode:: class extends the Browser API by providing
 * specific information about Imode handsets.
 *
 * $Horde: framework/Browser/Browser/imode.php,v 1.7.12.9 2009-01-06 15:22:55 jan Exp $
 *
 * Copyright 2000-2007 Mika Tuupola
 * Copyright 2002-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @since   Horde 3.0
 * @package Horde_Browser
 */
class Browser_imode {

    /**
     * Device data. From http://www.nttdocomo.co.jp/i/tag/s5.html#5_1
     *
     * @var array
     */
    var $_data = array(
        'D209i' => array(
            'imagewidth' => 96, 'imageheight' => 90,
            'textwidth' => 8, 'textheight' => 7,
            'color' => 256,
            'imageformats' => array('gif')
        ),
        'F209i' => array(
            'imagewidth' => 96, 'imageheight' => 91,
            'textwidth' => 8, 'textheight' => 7,
            'color' => 256,
            'imageformats' => array('gif')
        ),
        'N209i' => array(
            'imagewidth' => 108, 'imageheight' => 82,
            'textwidth' => 9, 'textheight' => 6,
            'color' => 'grey',
            'imageformats' => array('gif')
        ),
        'P209i' => array(
            'imagewidth' => 96, 'imageheight' => 87,
            'textwidth' => 8, 'textheight' => 6,
            'color' => 'grey',
            'imageformats' => array('gif')
        ),
        'P209is' => array(
            'imagewidth' => 96, 'imageheight' => 87,
            'textwidth' => 8, 'textheight' => 6,
            'color' => 256,
            'imageformats' => array('gif')
        ),
        'R209i' => array(
            'imagewidth' => 96, 'imageheight' => 72,
            'textwidth' => 8, 'textheight' => 6,
            'color' => 'grey',
            'imageformats' => array('gif')
        ),
        'ER209i' => array(
            'imagewidth' => 120, 'imageheight' => 72,
            'textwidth' => 10, 'textheight' => 6,
            'color' => 'grey',
            'imageformats' => array('gif')
        ),
        'KO209i' => array(
            'imagewidth' => 96, 'imageheight' => 96,
            'textwidth' => 8, 'textheight' => 8,
            'color' => 256,
            'imageformats' => array('gif')
        ),
        'D210i' => array(
            'imagewidth' => 96, 'imageheight' => 91,
            'textwidth' => 8, 'textheight' => 7,
            'color' => 256,
            'imageformats' => array('gif')
        ),
        'F210i' => array(
            'imagewidth' => 96, 'imageheight' => 113,
            'textwidth' => 8, 'textheight' => 8,
            'color' => 256,
            'imageformats' => array('gif')
        ),
        'N210i' => array(
            'imagewidth' => 118, 'imageheight' => 113,
            'textwidth' => 10, 'textheight' => 8,
            'color' => 256,
            'imageformats' => array('gif')
        ),
        'P210i' => array(
            'imagewidth' => 96, 'imageheight' => 91,
            'textwidth' => 8, 'textheight' => 6,
            'color' => 256,
            'imageformats' => array('gif')
        ),
        'KO210i' => array(
            'imagewidth' => 96, 'imageheight' => 96,
            'textwidth' => 8, 'textheight' => 8,
            'color' => 256,
            'imageformats' => array('gif')
        ),
        'SO210i' => array(
            'imagewidth' => 120, 'imageheight' => 113,
            'textwidth' => 8, 'textheight' => 7,
            'color' => 256,
            'imageformats' => array('gif')
        ),
        'D501i' => array(
            'imagewidth' => 96, 'imageheight' => 72,
            'textwidth' => 8, 'textheight' => 6,
            'color' => 'black',
            'imageformats' => array('gif')
        ),
        'F501i' => array(
            'imagewidth' => 112, 'imageheight' => 84,
            'textwidth' => 8, 'textheight' => 6,
            'color' => 'black',
            'imageformats' => array('gif')
        ),
        'N501i' => array(
            'imagewidth' => 118, 'imageheight' => 128,
            'textwidth' => 10, 'textheight' =>10,
            'color' => 'black',
            'imageformats' => array('gif')
        ),
        'P501i' => array(
            'imagewidth' => 96, 'imageheight' => 120,
            'textwidth' => 8, 'textheight' => 8,
            'color' => 'black',
            'imageformats' => array('gif')
        ),
        'D502i' => array(
            'imagewidth' => 96, 'imageheight' => 90,
            'textwidth' => 8, 'textheight' => 7,
            'color' => 256,
            'imageformats' => array('gif')
        ),
        'F502i' => array(
            'imagewidth' => 96, 'imageheight' => 91,
            'textwidth' => 8, 'textheight' => 7,
            'color' => 256,
            'imageformats' => array('gif')
        ),
        'F502it' => array(
            'imagewidth' => 96, 'imageheight' => 91,
            'textwidth' => 8, 'textheight' => 7,
            'color' => 256,
            'imageformats' => array('gif')
        ),
        'N502i' => array(
            'imagewidth' => 118, 'imageheight' => 128,
            'textwidth' => 10, 'textheight' => 10,
            'color' => 'grey',
            'imageformats' => array('gif')
        ),
        'N502it' => array(
            'imagewidth' => 118, 'imageheight' => 128,
            'textwidth' => 10, 'textheight' => 10,
            'color' => 256,
            'imageformats' => array('gif')
        ),
        'P502i' => array(
            'imagewidth' => 96, 'imageheighth' => 117,
            'textwidth' => 8, 'textheight' => 8,
            'color' => 'grey',
            'imageformats' => array('gif')
        ),
        'NM502i' => array(
            'imagewidth' => 111, 'imageheight' => 77,
            'textwidth' => 8, 'textheight' => 6,
            'color' => 'black',
            'imageformats' => array('gif')
        ),
        'SO502i' => array(
            'imagewidth' => 120, 'imageheight' => 120,
            'textwidth' => 8, 'textheight' => 8,
            'color' => 'grey',
            'imageformats' => array('gif')
        ),
        'SO502iwm' => array(
            'imagewidth' => 120, 'imageheight' => 113,
            'textwidth' => 8, 'textheight' => 7,
            'color' => 256,
            'imageformats' => array('gif')
        ),
        'F503i' => array(
            'imagewidth' => 120, 'imageheight' => 130,
            'textwidth' => 10, 'textheight' => 10,
            'color' => 256,
            'imageformats' => array('gif')
        ),
        'F503iS' => array(
            'imagewidth' => 120, 'imageheight' => 130,
            'textwidth' => 12, 'textheight' => 12,
            'color' => 4096,
            'imageformats' => array('gif')
        ),
        'P503i' => array(
            'imagewidth' => 120, 'imageheight' => 130,
            'textwidth' => 12, 'textheight' => 10,
            'color' => 256,
            'imageformats' => array('gif')
        ),
        'P503iS' => array(
            'imagewidth' => 120, 'imageheight' => 130,
            'textwidth' => 12, 'textheight' => 10,
            'color' => 256,
            'imageformats' => array('gif')
        ),
        'SO503i' => array(
            'imagewidth' => 120, 'imageheight' => 113,
            'textwidth' => 8.5, 'textheight' => 7,
            'color' => 65536,
            'imageformats' => array('gif')
        ),
        'D503i' => array(
            'imagewidth' => 132, 'imageheight' => 126,
            'textwidth' => 8, 'textheight' => 7,
            'color' => 4096,
            'imageformats' => array('gif')
        ),
        'N503i' => array(
            'imagewidth' => 118, 'imageheight' => 128,
            'textwidth' => 10, 'textheight' => 10,
            'color' => 4096,
            'imageformats' => array('gif', 'jpg')
        ),
        'N503iS' => array(
            'imagewidth' => 118, 'imageheight' => 128,
            'textwidth' => 10, 'textheight' => 10,
            'color' => 4096,
            'imageformats' => array('gif', 'jpg')
        ),
        'N691i' => array(
            'imagewidth' => 96, 'imageheight' => 72,
            'textwidth' => 8, 'textheight' => 6,
            'color' => 'grey',
            'imageformats' => array('gif')
        ),
        'SH821i' => array(
            'imagewidth' => 96, 'imageheight' => 78,
            'textwidth' => 8, 'textheight' => 6,
            'color' => 256,
            'imageformats' => array('gif')
        ),
        'N821i' => array(
            'imagewidth' => 118, 'imageheight' => 128,
            'textwidth' => 10, 'textheight' => 10,
            'color' => 'grey',
            'imageformats' => array('gif')
        ),
        'P821i' => array(
            'imagewidth' => 118, 'imageheight' => 128,
            'textwidth' => 10, 'textheight' => 10,
            'color' => 'grey',
            'imageformats' => array('gif')
        ),
        'safe' => array(
            'imagewidth' => 94, 'imageheight' => 72,
            'textwidth' => 8, 'textheight' => 6,
            'color' => 'black',
            'imageformats' => array('gif')
        )
    );

    var $_manufacturerlist = array(
        'D' => 'Mitsubishi',
        'P' => 'Panasonic (Matsushita)',
        'NM' => 'Nokia',
        'SO' => 'Sony',
        'F' => 'Fujitsu',
        'N' => 'Nec',
        'SH' => 'Sharp',
        'ER' => 'Ericsson',
        'R' => 'Japan Radio',
        'KO' => 'Kokusai (Hitachi)'
    );

    var $_extra = array(
        't' => 'Transport layer',
        'e' => 'English language',
        's' => 'Second version'
    );

    var $_user_agent;
    var $_model;
    var $_manufacturer;
    var $_httpversion;
    var $_cache = 5;

    /**
     * Does not handle bogus user_agents or most of the other error
     * situation properly yet.
     *
     * Example usage:
     *   $ua = &new Browser_imode($_SERVEr['HTTP_USER_AGENT']);
     *
     * @param string $input  The user agent to match.
     */
    function Browser_imode($input)
    {
        $_error = 0;
        $temp = explode('/', $input);

        $this->_user_agent = $input;
        $this->_httpversion = $temp[1];
        $this->_model = $temp[2];
        if ($temp[3]) {
            $this->_cache = substr($temp[3], 1);
        }

        preg_match('/(^[a-zA-Z]+)([0-9]+i)(.*)\/?(.*)/', $this->_model, $matches);

        // @TODO: Fix situation of unknown manufacturer. Implement
        // extrainfo properly.
        $this->_manufacturer = $this->_manufacturerlist[$matches[1]];
        $this->_extra = $matches[3];

        if (!($this->_data[$this->_model])) {
            $_error = PEAR::raiseError('Unknown User Agent');
        }
    }

    /**
     * Example usage:
     *  $imagedim    = $ua->getImageDimensions();
     *  $imagewidth  = $imagedim[0];
     *  $imageheight = $imagedim[1];
     *
     * @return array  The maximum imagewidth and imageheight that
     *                fit on the handset screen without scrolling.
     */
    function getImageDimensions()
    {
        $data = $this->_data[$this->_model];
        return array($data['imagewidth'], $data['imageheight']);
    }

    /**
     * Example usage:
     *  $textdim    = $ua->getTextDimensions();
     *  $textwidth  = $textdim[0];
     *  $textheight = $textdim[1];
     *
     * @return array  The Maximum textwidth and textheight that
     *                fit on the handset screen without scrolling.
     */
    function getTextDimensions()
    {
        return array($this->_data[$this->_model]['textwidth'],
                     $this->_data[$this->_model]['textheight']);
    }

    /**
     * @return integer  The amount of handset cache in kilobytes.
     */
    function getCache()
    {
        return (int)$this->_cache;
    }

    function getManufacturer()
    {
        return $this->_manufacturer;
    }

    function getExtra()
    {
        return $this->_extra;
    }

    function getImageFormats()
    {
        return $this->_data[$this->_model]['imageformats'];
    }

    /**
     * @return integer  Which color model the handset supports.
     *   Values have the following meaning:
     *     0 -> black and white
     *     1 -> 4 tone greyscale
     *     2 -> 256 color
     */
    function getColor()
    {
        return $this->_data[$this->_model]['color'];
    }

    function getHTTPVersion()
    {
        return $this->_httpversion;
    }

    function isColor()
    {
        return $this->_data[$this->_model]['color'] == 256;
    }

    function isGreyScale()
    {
        return $this->_data[$this->_model]['color'] == 'grey';
    }

    function isBlackAndWhite()
    {
        return $this->_data[$this->_model]['color'] == 'black';
    }

}
