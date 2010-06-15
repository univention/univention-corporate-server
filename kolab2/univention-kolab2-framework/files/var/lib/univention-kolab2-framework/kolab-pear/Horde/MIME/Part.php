<?php

require_once 'Horde/String.php';
require_once dirname(__FILE__) . '/../MIME.php';

/** @constant MIME_PART_EOL The character(s) used internally for EOLs. */
define('MIME_PART_EOL', "\n");

/** @constant MIME_PART_RFC_EOL The character string designated by RFCs 822/2045 to designate EOLs in MIME messages. */
define('MIME_PART_RFC_EOL', "\r\n");

/* Default MIME parameters. */
/** @constant MIME_DEFAULT_CHARSET The default MIME character set. */
define('MIME_DEFAULT_CHARSET', 'us-ascii');

/** @constant MIME_DEFAULT_DESCRIPTION The default MIME description. */
define('MIME_DEFAULT_DESCRIPTION', _("unnamed"));

/** @constant MIME_DEFAULT_DISPOSITION The default MIME disposition. */
define('MIME_DEFAULT_DISPOSITION', 'inline');

/** @constant MIME_DEFAULT_ENCODING The default MIME encoding. */
define('MIME_DEFAULT_ENCODING', '7bit');

/**
 * The MIME_Part:: class provides a wrapper around MIME parts and methods
 * for dealing with them.
 *
 * $Horde: framework/MIME/MIME/Part.php,v 1.173 2004/05/04 15:07:14 chuck Exp $
 *
 * Copyright 1999-2004 Chuck Hagenbuch <chuck@horde.org>
 * Copyright 2002-2004 Michael Slusarz <slusarz@bigworm.colorado.edu>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @author  Michael Slusarz <slusarz@bigworm.colorado.edu>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 1.3
 * @package Horde_MIME
 */
class MIME_Part {

    /**
     * The type (ex.: text) of this part.
     * Per RFC 2045, the default is 'application'.
     *
     * @var string $_type
     */
    var $_type = 'application';

    /**
     * The subtype (ex.: plain) of this part.
     * Per RFC 2045, the default is 'octet-stream'.
     *
     * @var string $_subtype
     */
    var $_subtype = 'octet-stream';

    /**
     * The body of the part.
     *
     * @var string $_contents
     */
    var $_contents = '';

    /**
     * The desired transfer encoding of this part.
     *
     * @var string $_transferEncoding
     */
    var $_transferEncoding = MIME_DEFAULT_ENCODING;

    /**
     * The current transfer encoding of the contents of this part.
     *
     * @var string $_currentEncoding
     */
    var $_currentEncoding = null;

    /**
     * Should the message be encoded via 7-bit?
     *
     * @var boolean $_encode7bit
     */
    var $_encode7bit = true;

    /**
     * The description of this part.
     *
     * @var string $_description
     */
    var $_description = '';

    /**
     * The disposition of this part (inline or attachment).
     *
     * @var string $_disposition
     */
    var $_disposition = MIME_DEFAULT_DISPOSITION;

    /**
     * The disposition parameters of this part.
     *
     * @var array $_dispositionParameters
     */
    var $_dispositionParameters = array();

    /**
     * The content type parameters of this part.
     *
     * @var array $_contentTypeParameters
     */
    var $_contentTypeParameters = array();

    /**
     * The subparts of this part.
     *
     * @var array $_parts
     */
    var $_parts = array();

    /**
     * Information/Statistics on the subpart.
     *
     * @var array $_information
     */
    var $_information = array();

    /**
     * The list of CIDs for this part.
     *
     * @var array $_cids
     */
    var $_cids = array();

    /**
     * The MIME ID of this part.
     *
     * @var string $_mimeid
     */
    var $_mimeid = null;

    /**
     * The sequence to use as EOL for this part.
     * The default is currently to output the EOL sequence internally as
     * just "\n" instead of the canonical "\r\n" required in RFC 822 & 2045.
     * To be RFC complaint, the full <CR><LF> EOL combination should be used
     * when sending a message.
     * It is not crucial here since the PHP/PEAR mailing functions will handle
     * the EOL details.
     *
     * @var string $_eol
     */
    var $_eol = MIME_PART_EOL;

    /**
     * Internal class flags.
     *
     * @var array $_flags
     */
    var $_flags = array();

    /**
     * Part -> ID mapping cache.
     *
     * @var array $_idmap
     */
    var $_idmap = array();

    /**
     * Unique MIME_Part boundary string.
     *
     * @var string $_boundary
     */
    var $_boundary = null;

    /**
     * Default value for this Part's size.
     *
     * @var integer $_bytes
     */
    var $_bytes = 0;

    /**
     * The content-ID for this part.
     *
     * @var string $_contentid
     */
    var $_contentid = null;

    /**
     * MIME_Part constructor.
     *
     * @access public
     *
     * @param optional string $mimetype     The content type of the part.
     * @param optional string $contents     The body of the part.
     * @param optional string $charset      The character set of the part.
     * @param optional string $disposition  The content disposition of the
     *                                      part.
     * @param optional string $encoding     The content encoding of the
     *                                      contents.
     */
    function MIME_Part($mimetype = null, $contents = null,
                       $charset = MIME_DEFAULT_CHARSET, $disposition = null,
                       $encoding = null)
    {
        /* Create the unique MIME_Part boundary string. */
        $this->_generateBoundary();

        /* The character set should always be set, even if we are dealing
         * with Content-Types other than text/*. */
        $this->setCharset($charset);

        if (!is_null($mimetype)) {
            $this->setType($mimetype);
        }
        if (!is_null($contents)) {
            $this->setContents($contents, $encoding);
        }
        if (!is_null($disposition)) {
            $this->setDisposition($disposition);
        }
    }

    /**
     * Set the content-disposition of this part.
     *
     * @access public
     *
     * @param string $disposition  The content-disposition to set (inline or
     *                             attachment).
     */
    function setDisposition($disposition)
    {
        $disposition = String::lower($disposition);

        if (($disposition == 'inline') || ($disposition == 'attachment')) {
            $this->_disposition = $disposition;
        }
    }

    /**
     * Get the content-disposition of this part.
     *
     * @access public
     *
     * @return string  The part's content-disposition.
     */
    function getDisposition()
    {
        return $this->_disposition;
    }

    /**
     * Set the name of this part.
     *
     * @access public
     *
     * @param string $name The name to set.
     */
    function setName($name)
    {
        $this->setContentTypeParameter('name', $name);
    }

    /**
     * Get the name of this part.
     *
     * @access public
     *
     * @param optional boolean $decode   MIME decode description?
     * @param optional boolean $default  If the name parameter doesn't exist,
     *                                   should we use the default name from
     *                                   the description parameter?
     *
     * @return string  The name of the part.
     */
    function getName($decode = false, $default = false)
    {
        $name = $this->getContentTypeParameter('name');

        if ($default && empty($name)) {
            $name = preg_replace('|\W|', '_', $this->getDescription(false, true));
        }

        if ($decode) {
            return trim(MIME::decode($name));
        } else {
            return $name;
        }
    }

    /**
     * Set the body contents of this part.
     *
     * @access public
     *
     * @param string $contents           The part body.
     * @param optional string $encoding  The current encoding of the contents.
     */
    function setContents($contents, $encoding = null)
    {
        $this->_contents = $contents;
        $this->_flags['contentsSet'] = true;
        $this->_currentEncoding = (is_null($encoding)) ? $this->getCurrentEncoding() : MIME::encoding($encoding, MIME_STRING);
    }

    /**
     * Add to the body contents of this part.
     *
     * @access public
     *
     * @param string $contents           The contents to append to the current
     *                                   part body.
     * @param optional string $encoding  The current encoding of the contents.
     *                                   If not specified, will try to auto
     *                                   determine the encoding.
     */
    function appendContents($contents, $encoding = null)
    {
        $this->setContents($this->_contents . $contents, $encoding);
    }

    /**
     * Clears the body contents of this part.
     *
     * @access public
     */
    function clearContents()
    {
        $this->_contents = '';
        $this->_flags['contentsSet'] = false;
        $this->_currentEncoding = null;
    }

    /**
     * Return the body of the part.
     *
     * @access public
     *
     * @return string  The raw body of the part.
     */
    function getContents()
    {
        return $this->_contents;
    }

    /**
     * Returns the contents in strict RFC 822 & 2045 output - namely, all
     * newlines end with the canonical <CR><LF> sequence.
     *
     * @access public
     *
     * @return string  The entire MIME part.
     */
    function getCanonicalContents()
    {
        return $this->replaceEOL($this->getContents(), MIME_PART_RFC_EOL);
    }

    /**
     * Transfer encode the contents (to the transfer encoding identified via
     * getTransferEncoding()) and set as the part's new contents.
     *
     * @access public
     */
    function transferEncodeContents()
    {
        $contents = $this->transferEncode();
        $this->_currentEncoding = $this->_flags['lastTransferEncode'];
        $this->setContents($contents, $this->_currentEncoding);
        $this->setTransferEncoding($this->_currentEncoding);
    }

    /**
     * Transfer decode the contents and set them as the new contents.
     *
     * @access public
     */
    function transferDecodeContents()
    {
        $contents = $this->transferDecode();
        $this->_currentEncoding = $this->_flags['lastTransferDecode'];
        $this->setTransferEncoding($this->_currentEncoding);

        /* Don't set contents if they are empty, because this will do stuff
           like reset the internal bytes field, even though we shouldn't do
           that (the user has their reasons to set the bytes field to a
           non-zero value without putting the contents into this part. */
        if (!empty($contents)) {
            $this->setContents($contents, $this->_currentEncoding);
        }
    }

    /**
     * Set the mimetype of this part.
     *
     * @access public
     *
     * @param string $mimetype  The mimetype to set (ex.: text/plain).
     */
    function setType($mimetype)
    {
        /* RFC 2045: Any entity with unrecognized encoding must be treated
           as if it has a Content-Type of "application/octet-stream"
           regardless of what the Content-Type field actually says. */
        if ($this->_transferEncoding == 'x-unknown') {
            return;
        }

        /* Set the 'setType' flag. */
        $this->_flags['setType'] = true;

        list($this->_type, $this->_subtype) = explode('/', String::lower($mimetype));
        if (($type = MIME::type($this->_type, MIME_STRING))) {
            $this->_type = $type;

            /* Set the boundary string for 'multipart/*' parts. */
            if ($type == 'multipart') {
                if (!$this->getContentTypeParameter('boundary')) {
                    $this->setContentTypeParameter('boundary', $this->_generateBoundary());
                }
            } else {
                $this->clearContentTypeParameter('boundary');
            }
        } else {
            $this->_type = 'x-unknown';
            $this->clearContentTypeParameter('boundary');
        }
    }

     /**
      * Get the full MIME Content-Type of this part.
      *
      * @access public
      *
      * @param optional boolean $charset  Append character set information to
      *                                   the end of the content type if this
      *                                   is a text/* part.
      *
      * @return string  The mimetype of this part
      *                 (ex.: text/plain; charset=us-ascii).
      */
     function getType($charset = false)
     {
         if (!isset($this->_type) || !isset($this->_subtype)) {
             return false;
         }
         $ptype = $this->getPrimaryType();
         $type = $ptype . '/' . $this->getSubType();
         if ($charset && ($ptype == 'text')) {
             $type .= '; ' . 'charset="' . $this->getCharset() . '"';
         }
         return $type;
     }

    /**
     * If the subtype of a MIME part is unrecognized by an application, the
     * default type should be used instead (See RFC 2046).  This method
     * returns the default subtype for a particular primary MIME Type.
     *
     * @access public
     *
     * @return string  The default mimetype of this part (ex.: text/plain).
     */
    function getDefaultType()
    {
        switch ($this->getPrimaryType()) {
        case 'text':
            /* RFC 2046 (4.1.4): text parts default to text/plain. */
            return 'text/plain';

        case 'multipart':
            /* RFC 2046 (5.1.3): multipart parts default to multipart/mixed. */
            return 'multipart/mixed';

        default:
            /* RFC 2046 (4.2, 4.3, 4.4, 4.5.3, 5.2.4): all others default to
               application/octet-stream. */
            return 'application/octet-stream';
        }
    }

    /**
     * Get the primary type of this part.
     *
     * @access public
     *
     * @return string  The primary MIME type of this part.
     */
    function getPrimaryType()
    {
        return $this->_type;
    }

    /**
     * Get the subtype of this part.
     *
     * @access public
     *
     * @return string  The MIME subtype of this part.
     */
    function getSubType()
    {
        return $this->_subtype;
    }

    /**
     * Set the character set of this part.
     *
     * @access public
     *
     * @param optional string $charset  The character set of this part.
     */
    function setCharset($charset)
    {
        $this->setContentTypeParameter('charset', $charset);
    }

    /**
     * Get the character set of this part. This function only will return
     * data if this is a text/* part.
     *
     * @access public
     *
     * @return string  The character set of this part.  Returns null if there
     *                 is no character set.
     */
    function getCharset()
    {
        /* If this is not a text/* part, character set isn't pertinent. */
        if ($this->getPrimaryType() != 'text') {
            return null;
        }

        $charset = $this->getContentTypeParameter('charset');

        return (empty($charset)) ? null : $charset;
    }

    /**
     * Set the description of this part.
     *
     * @access public
     *
     * @param string $description  The description of this part.
     */
    function setDescription($description)
    {
        $this->_description = MIME::encode($description, $this->getCharset());
    }

    /**
     * Get the description of this part.
     *
     * @access public
     *
     * @param optional boolean $decode   MIME decode description?
     * @param optional boolean $default  If the name parameter doesn't exist,
     *                                   should we use the default name from
     *                                   the description parameter?
     *
     * @return string  The description of this part.
     */
    function getDescription($decode = false, $default = false)
    {
        $desc = $this->_description;

        if ($default && empty($desc)) {
            $desc = $this->getName();
            if (empty($desc)) {
                $desc = MIME_DEFAULT_DESCRIPTION;
            }
        }

        if ($decode) {
            return MIME::decode($desc);
        } else {
            return $desc;
        }
    }

    /**
     * Set the transfer encoding to use for this part.
     *
     * @access public
     *
     * @param string $encoding  The transfer encoding to use.
     */
    function setTransferEncoding($encoding)
    {
        if (($mime_encoding = MIME::encoding($encoding, MIME_STRING))) {
            $this->_transferEncoding = $mime_encoding;
        } else {
            /* RFC 2045: Any entity with unrecognized encoding must be treated
               as if it has a Content-Type of "application/octet-stream"
               regardless of what the Content-Type field actually says. */
            $this->setType('application/octet-stream');
            $this->_transferEncoding = 'x-unknown';
        }
    }

    /**
     * Add a MIME subpart.
     *
     * @access public
     *
     * @param object MIME_Part $mime_part  Add a MIME_Part subpart to the
     *                                     current MIME_Part.
     * @param optional string $index       The index of the added MIME_Part.
     */
    function addPart($mime_part, $index = null)
    {
        /* Add the part to the parts list. */
        if (is_null($index)) {
            end($this->_parts);
            $id = key($this->_parts) + 1;
            $ptr = &$this->_parts;
        } else {
            $ptr = &$this->_partFind($index, $this->_parts, true);
            if (($pos = strrpos($index, '.'))) {
                $id = substr($index, $pos + 1);
            } else {
                $id = $index;
            }
        }

        /* Set the MIME ID if it has not already been set. */
        if ($mime_part->getMIMEId() === null) {
            $mime_part->setMIMEId($id);
        }

        /* Store the part now. */
        $ptr[$id] = $mime_part;

        /* Clear the ID -> Part mapping cache. */
        $this->_idmap = array();
    }

    /**
     * Get a list of all MIME subparts.
     *
     * @access public
     *
     * @return array  An array of the MIME_Part subparts.
     */
    function getParts()
    {
        return $this->_parts;
    }

    /**
     * Retrieve a specific MIME part.
     *
     * @access public
     *
     * @param string $id  The MIME_Part ID string.
     *
     * @return object MIME_Part  The MIME_Part requested.  Returns false if
     *                           the part doesn't exist.
     */
    function getPart($id)
    {
        $orig = null;
        $mimeid = $this->getMIMEId();

        /* Return this part if:
           1) There is only one part (e.g. the MIME ID is 0, or the
              MIME ID is 1 and there are no subparts.
           2) $id matches this parts MIME ID. */
        if (($id == 0) ||
            (($id == 1) && !count($this->_parts)) ||
            (!empty($mimeid) && ($id == $mimeid))) {
            return $this;
        }

        return $this->_partFind($id, $this->_parts);
    }

    /**
     * Remove a MIME_Part subpart.
     *
     * @access public
     *
     * @param string $id  The MIME Part to delete.
     */
    function removePart($id)
    {
        if (($ptr = &$this->_partFind($id, $this->_parts))) {
            unset($ptr);
            $this->_idmap = array();
        }
    }

    /**
     * Alter a current MIME subpart.
     *
     * @access public
     *
     * @param string $id                   The MIME Part ID to alter.
     * @param object MIME_Part $mime_part  The MIME Part to store.
     */
    function alterPart($id, $mime_part)
    {
        if (($ptr = &$this->_partFind($id, $this->_parts))) {
            $ptr = $mime_part;
            $this->_idmap = array();
        }
    }

    /**
     * Function used to find a specific MIME Part by ID.
     *
     * @access private
     *
     * @param string $id                  The MIME_Part ID string.
     * @param array &$parts               A list of MIME_Part objects.
     * @param optional boolean $retarray  Return a pointer to the array that
     *                                    stores (would store) the part
     *                                    rather than the part itself?
     */
    function &_partFind($id, &$parts, $retarray = false)
    {
        if (empty($this->_idmap)) {
            $this->_generateIdMap($this->_parts);
        }

        if ($retarray) {
            if ($pos = strrpos($id, '.')) {
                $id = substr($id, 0, $pos);
            } else {
                return $parts;
            }
        }

        if (isset($this->_idmap[$id])) {
            return $this->_idmap[$id];
        } else {
            return false;
        }
    }

    /**
     * Generates a mapping of MIME_Parts with their MIME IDs.
     *
     * @access private
     *
     * @param array &$parts  An array of MIME_Parts to map.
     */
    function _generateIdMap(&$parts)
    {
        if (!empty($parts)) {
            foreach (array_keys($parts) as $key) {
                $ptr = &$parts[$key];
                $this->_idmap[$ptr->getMIMEId()] = &$ptr;
                $this->_generateIdMap($ptr->_parts);
            }
        }
    }

    /**
     * Add information about the MIME_Part.
     *
     * @access public
     *
     * @param string $label  The information label.
     * @param mixed $data    The information to store.
     */
    function setInformation($label, $data)
    {
        $this->_information[$label] = $data;
    }

    /**
     * Retrieve information about the MIME_Part.
     *
     * @access public
     *
     * @param string $label  The information label.
     *
     * @return mixed  The information requested.
     *                Returns false if $label is not set.
     */
    function getInformation($label)
    {
        return (isset($this->_information[$label])) ? $this->_information[$label] : false;
    }

    /**
     * Add a disposition parameter to this part.
     *
     * @access public
     *
     * @param string $label  The disposition parameter label.
     * @param string $data   The disposition parameter data.
     */
    function setDispositionParameter($label, $data)
    {
        $this->_dispositionParameters[$label] = $data;
    }

    /**
     * Get a disposition parameter from this part.
     *
     * @access public
     *
     * @param string $label  The disposition parameter label.
     *
     * @return string  The data requested.
     *                 Returns false if $label is not set.
     */
    function getDispositionParameter($label)
    {
        return (isset($this->_dispositionParameters[$label])) ? $this->_dispositionParameters[$label] : false;
    }

    /**
     * Get all parameters from the Content-Disposition header.
     *
     * @access public
     *
     * @return array  An array of all the parameters
     *                Returns the empty array if no parameters set.
     */
    function getAllDispositionParameters()
    {
        return $this->_dispositionParameters;
    }

    /**
     * Add a content type parameter to this part.
     *
     * @access public
     *
     * @param string $label  The disposition parameter label.
     * @param string $data   The disposition parameter data.
     */
    function setContentTypeParameter($label, $data)
    {
        $this->_contentTypeParameters[$label] = $data;
    }

    /**
     * Clears a content type parameter from this part.
     *
     * @access public
     *
     * @param string $label  The disposition parameter label.
     * @param string $data   The disposition parameter data.
     */
    function clearContentTypeParameter($label)
    {
        unset($this->_contentTypeParameters[$label]);
    }

    /**
     * Get a content type parameter from this part.
     *
     * @access public
     *
     * @param string $label  The content type parameter label.
     *
     * @return string  The data requested.
     *                 Returns false if $label is not set.
     */
    function getContentTypeParameter($label)
    {
        return (isset($this->_contentTypeParameters[$label])) ? $this->_contentTypeParameters[$label] : false;
    }

    /**
     * Get all parameters from the Content-Type header.
     *
     * @access public
     *
     * @return array  An array of all the parameters
     *                Returns the empty array if no parameters set.
     */
    function getAllContentTypeParameters()
    {
        return $this->_contentTypeParameters;
    }

    /**
     * Sets a new string to use for EOLs.
     *
     * @access public
     *
     * @param string $eol  The string to use for EOLs.
     */
    function setEOL($eol)
    {
        $this->_eol = $eol;
    }

    /**
     * Get the string to use for EOLs.
     *
     * @access public
     *
     * @return string  The string to use for EOLs.
     */
    function getEOL()
    {
        return $this->_eol;
    }

    /**
     * Add the appropriate MIME headers for this part to an existing array.
     *
     * @access public
     *
     * @param optional array $headers  An array of any other headers for the
     *                                 part.
     *
     * @return array  The headers, with the MIME headers added.
     */
    function header($headers = array())
    {
        $eol = $this->getEOL();
        $ptype = $this->getPrimaryType();
        $stype = $this->getSubType();

        /* Get the character set for this part. */
        $charset = $this->getCharset();

        /* Get the Content-Type - this is ALWAYS required. */
        $ctype = $this->getType(true);
        foreach ($this->getAllContentTypeParameters() as $key => $value) {
            /* Skip the charset key since that would have already been
             * added to $ctype by getType(). */
            if ($key == 'charset') {
                continue;
            }
            $ctype .= '; ' . $key . '="' . MIME::encode($value, $charset) . '"';
        }
        $headers['Content-Type'] = MIME::wrapHeaders('Content-Type', $ctype, $eol);

        /* Get the description, if any. */
        if (($descrip = $this->getDescription())) {
            $headers['Content-Description'] = MIME::wrapHeaders('Content-Description', MIME::encode($descrip, $charset), $eol);
        }

        /* RFC 2045 [4] - message/rfc822 and message/partial require the
           MIME-Version header only if they themselves claim to be MIME
           compliant. */
        if (($ptype == 'message') &&
            (($stype == 'rfc822') || ($stype == 'partial')) &&
            (strstr($this->getContents(), 'MIME-Version: 1.0'))) {
            $headers['MIME-Version'] = '1.0';
        }

        /* message/* parts require no additional header information. */
        if ($ptype == 'message') {
            return $headers;
        }

        /* Don't show Content-Disposition for multipart messages unless
           there is a name parameter. */
        $name = $this->getName();
        if (($ptype != 'multipart') || !empty($name)) {
            $disp = $this->getDisposition();

            /* Add any disposition parameter information, if available. */
            if (!empty($name)) {
                $disp .= '; ' . 'filename="' . MIME::encode($name, $charset) . '"';
            }

            $headers['Content-Disposition'] = MIME::wrapHeaders('Content-Disposition', $disp, $eol);
        }

        /* Add transfer encoding information. */
        $headers['Content-Transfer-Encoding'] = $this->getTransferEncoding();

        /* Add content ID information. */
        if (!is_null($this->_contentid)) {
            $headers['Content-ID'] = $this->_contentid;
        }

        return $headers;
    }

    /**
     * Return the entire part in MIME format. Includes headers on request.
     *
     * @access public
     *
     * @param optional boolean $headers  Include the MIME headers?
     *
     * @return string  The MIME string.
     */
    function toString($headers = true)
    {
        $eol = $this->getEOL();
        $ptype = $this->getPrimaryType();
        $text = '';

        if ($headers) {
            foreach ($this->header() as $key => $val) {
                $text .= $key . ': ' . $val . $eol;
            }
            $text .= $eol;
        }

        /* Any information about a message/* is embedded in the message
           contents themself. Simply output the contents of the part
           directly and return. */
        if ($ptype == 'message') {
            return $text . $this->getContents();
        }

        $text .= $this->transferEncode();

        /* Deal with multipart messages. */
        if ($ptype == 'multipart') {
            $boundary = trim($this->getContentTypeParameter('boundary'), '"');
            if (!($this->getContents())) {
                $text .= 'This message is in MIME format.' . $eol;
            }
            foreach ($this->getParts() as $part) {
                $text .= $eol . '--' . $boundary . $eol;
                $oldEOL = $part->getEOL();
                $part->setEOL($eol);
                $text .= $part->toString(true);
                $part->setEOL($oldEOL);
            }
            $text .= $eol . '--' . $boundary . '--' . $eol;
        }

        return $text;
    }

    /**
     * Returns the encoded part in strict RFC 822 & 2045 output - namely, all
     * newlines end with the canonical <CR><LF> sequence.
     *
     * @access public
     *
     * @param optional boolean $headers  Include the MIME headers?
     *
     * @return string  The entire MIME part.
     */
    function toCanonicalString($headers = true)
    {
        $string = $this->toString($headers);
        return $this->replaceEOL($string, MIME_PART_RFC_EOL);
    }

    /**
     * Should we make sure the message is encoded via 7-bit (e.g. to adhere
     * to mail delivery standards such as RFC 2821)?
     *
     * @access public
     *
     * @param boolean $use7bit  Use 7-bit encoding?
     */
    function strict7bit($use7bit)
    {
        $this->_encode7bit = $use7bit;
    }

    /**
     * Get the transfer encoding for the part based on the user requested
     * transfer encoding and the current contents of the part.
     *
     * @access public
     *
     * @return string  The transfer-encoding of this part.
     */
    function getTransferEncoding()
    {
        $encoding = $this->_transferEncoding;
        $ptype = $this->getPrimaryType();
        $text = str_replace($this->getEOL(), ' ', $this->getContents());

        /* If there are no contents, return whatever the current value of
           $_transferEncoding is. */
        if (empty($text)) {
            return $encoding;
        }

        switch ($ptype) {
        case 'message':
            /* RFC 2046 [5.2.1] - message/rfc822 messages only allow 7bit,
               8bit, and binary encodings. If the current encoding is either
               base64 or q-p, switch it to 8bit instead.
               RFC 2046 [5.2.2, 5.2.3, 5.2.4] - All other message/* messages
               only allow 7bit encodings. */
            if ($this->getSubType() == 'rfc822') {
                $encoding = '8bit';
            } else {
                $encoding = '7bit';
            }
            break;

        case 'text':
            if (MIME::is8bit($text)) {
                if ($this->_encode7bit) {
                    $encoding = 'quoted-printable';
                } else {
                    $encoding = '8bit';
                }
            }
            break;

        default:
            /* By default, if there is 8bit data, we MUST either 8bit or
               base64 encode contents. */
            if (MIME::is8bit($text)) {
                if ($this->_encode7bit) {
                    $encoding = 'base64';
                } else {
                    $encoding = '8bit';
                }
            }
            break;
        }

        return $encoding;
    }

    /**
     * Retrieves the current encoding of the contents in the object.
     *
     * @access public
     *
     * @return string  The current encoding.
     */
    function getCurrentEncoding()
    {
        return (is_null($this->_currentEncoding)) ? $this->_transferEncoding : $this->_currentEncoding;
    }

    /**
     * Encodes the contents with the part's transfer encoding.
     *
     * @access public
     *
     * @return string  The encoded text.
     */
    function transferEncode()
    {
        $contents = $this->getContents();
        $encoding = $this->getTransferEncoding();
        $eol = $this->getEOL();

        /* Set the 'lastTransferEncode' flag so that transferEncodeContents()
           can save a call to getTransferEncoding(). */
        $this->_flags['lastTransferEncode'] = $encoding;

        /* If contents are empty, or contents are already encoded to the
           correct encoding, return now. */
        if (empty($contents) ||
            ($encoding == $this->_currentEncoding)) {
            return $contents;
        }

        switch ($encoding) {
        /* Base64 Encoding: See RFC 2045, section 6.8 */
        case 'base64':
            /* Keeping these two lines separate seems to use much less
               memory than combining them (as of PHP 4.3). */
            $encoded_contents = base64_encode($contents);
            return chunk_split($encoded_contents, 76, $eol);

        /* Quoted-Printable Encoding: See RFC 2045, section 6.7 */
        case 'quoted-printable':
            $output = MIME::quotedPrintableEncode($contents, $eol);
            if (($eollength = String::length($eol))) {
                return substr($output, 0, $eollength * -1);
            } else {
                return $output;
            }

        default:
            return $this->replaceEOL($contents);
        }
    }

    /**
     * Decodes the contents of the part to either a 7bit or 8bit encoding.
     *
     * @access public
     *
     * @return string  The decoded text.
     *                 Returns the empty string if there is no text to decode.
     */
    function transferDecode()
    {
        $contents = $this->getContents();
        $encoding = $this->getCurrentEncoding();

        /* If the contents are empty, return now. */
        if (empty($contents)) {
            $this->_flags['lastTransferDecode'] = $encoding;
            return $contents;
        }

        switch ($encoding) {
        case 'base64':
            $message = base64_decode($contents);
            $this->_flags['lastTransferDecode'] = '8bit';
            break;

        case 'quoted-printable':
            $message = preg_replace("/=\r?\n/", '', $contents);
            $message = $this->replaceEOL($message);
            $message = quoted_printable_decode($message);
            $this->_flags['lastTransferDecode'] = (MIME::is8bit($message)) ? '8bit' : '7bit';
            break;

        /* Support for uuencoded encoding - although not required by RFCs,
           some mailers may still encode this way. */
        case 'uuencode':
        case 'x-uuencode':
        case 'x-uue':
            require_once 'Mail/mimeDecode.php';
            $files = &Mail_mimeDecode::uudecode($contents);
            $message = $files[0]['filedata'];
            $this->_flags['lastTransferDecode'] = '8bit';
            break;

        default:
            if (isset($this->_flags['lastTransferDecode']) &&
                ($this->_flags['lastTransferDecode'] != $encoding)) {
                $message = $this->replaceEOL($contents);
            } else {
                $message = $contents;
            }
            $this->_flags['lastTransferDecode'] = $encoding;
            break;
        }

        return $message;
    }

    /**
     * Split the contents of the current Part into its respective subparts,
     * if it is multipart MIME encoding. Unlike the imap_*() functions, this
     * will preserve all MIME header information.
     *
     * The boundary content-type parameter must be set for this function to
     * work correctly.
     *
     * @access public
     *
     * @return boolean  True if the contents were successfully split.
     *                  False if any error occurred.
     */
    function splitContents()
    {
        if (!($boundary = $this->getContentTypeParameter('boundary'))) {
            return false;
        }

        if (!($contents = $this->getContents())) {
            return false;
        }

        $eol = $this->getEOL();

        foreach (explode($eol, $contents) as $line) {
            $pos = strpos($line, '--' . $boundary);
            if ($pos === false && isset($part_ptr)) {
                $data[] = $line;
            } elseif ($pos === 0) {
                if (isset($part_ptr)) {
                    $this->_parts[$part_ptr]->setContents(implode($eol, $data));
                    $this->_parts[$part_ptr]->splitContents();
                    next($this->_parts);
                } else {
                    reset($this->_parts);
                }
                if (isset($data)) {
                    unset($data);
                }
                $data = array();
                $part_ptr = key($this->_parts);
            }
        }

        return true;
    }

    /**
     * Replace newlines in this part's contents with those specified by either
     * the given newline sequence or the part's current EOL setting.
     *
     * @access public
     *
     * @param string $text          The text to replace.
     * @param optional string $eol  The EOL sequence to use. If not present,
     *                              uses the part's current EOL setting.
     *
     * @return string  The text with the newlines replaced by the desired
     *                 newline sequence.
     */
    function replaceEOL($text, $eol = null)
    {
        if (is_null($eol)) {
            $eol = $this->getEOL();
        }
        return preg_replace("/\r?\n/", $eol, $text);
    }

    /**
     * Return the unique MIME_Part boundary string generated for this object.
     * This may not be the boundary string used when building the message
     * since a user defined 'boundary' Content-Type parameter will override
     * this value.
     *
     * @access public
     *
     * @return string  The unique boundary string.
     */
    function getUniqueID()
    {
        return $this->_boundary;
    }

    /**
     * Determine the size of a MIME_Part and its child members.
     *
     * @access public
     *
     * @return integer  Size of the MIME_Part, in bytes.
     */
    function getBytes()
    {
        $bytes = 0;

        if (empty($this->_flags['contentsSet']) && $this->_bytes) {
            $bytes = $this->_bytes;
        } elseif ($this->getPrimaryType() == 'multipart') {
            foreach ($this->getParts() as $part) {
                /* Skip multipart entries (since this may result in double
                   counting). */
                if ($part->getPrimaryType() != 'multipart') {
                    $bytes += $part->getBytes();
                }
            }
        } else {
            if ($this->getPrimaryType() == 'text') {
                $bytes = String::length($this->getContents(), $this->getCharset());
            } else {
                $bytes = strlen($this->getContents());
            }
        }

        return $bytes;
    }

    /**
     * Explicitly set the size (in bytes) of this part. This value will only
     * be returned (via getBytes()) if there are no contents currently set.
     * This function is useful for setting the size of the part when the
     * contents of the part are not fully loaded (i.e. creating a MIME_Part
     * object from IMAP header information without loading the data of the
     * part).
     *
     * @access public
     *
     * @param integer $bytes  The size of this part in bytes.
     */
    function setBytes($bytes)
    {
        $this->_bytes = $bytes;
    }

    /**
     * Output the size of this MIME_Part in KB.
     *
     * @access public
     *
     * @return string  Size of the MIME_Part, in string format.
     */
    function getSize()
    {
        $bytes = $this->getBytes();
        if (empty($bytes)) {
            return $bytes;
        }

        $localeinfo = NLS::getLocaleInfo();
        return number_format($bytes / 1024, 2, $localeinfo['decimal_point'], '');
     }

    /**
     * Add to the list of CIDs for this part.
     *
     * @access public
     *
     * @param array $cids  A list of MIME IDs of the part.
     *                     Key - MIME ID
     *                     Value - CID for the part
     */
    function addCID($cids = array())
    {
        $this->_cids += $cids;
    }

    /**
     * Returns the list of CIDs for this part.
     *
     * @access public
     *
     * @return array  The list of CIDs for this part.
     */
    function getCIDList()
    {
        asort($this->_cids, SORT_STRING);
        return $this->_cids;
    }

    /**
     * Sets the Content-ID header for this part.
     *
     * @access public
     *
     * @param optional string $cid  Use this CID (if not already set).  Else,
     *                              generate a random CID.
     */
    function setContentID($cid = null)
    {
        if (is_null($this->_contentid)) {
            $this->_contentid = (is_null($cid)) ? (base_convert(microtime(), 10, 36) . '@' . $_SERVER['SERVER_NAME']) : $cid;
        }
        return $this->_contentid;
    }

    /**
     * Alter the MIME ID of this part.
     *
     * @access public
     *
     * @param string $mimeid  The MIME ID.
     */
    function setMIMEId($mimeid)
    {
        $this->_mimeid = $mimeid;
    }

    /**
     * Returns the MIME ID of this part.
     *
     * @access public
     *
     * @return string  The MIME ID.
     */
    function getMIMEId()
    {
        return $this->_mimeid;
    }

    /**
     * Returns the relative MIME ID of this part.
     * e.g., if the base part has MIME ID of 2, and you want the first
     * subpart of the base part, the relative MIME ID is 2.1.
     *
     * @access public
     *
     * @param string $id  The relative part ID.
     *
     * @return string  The relative MIME ID.
     */
    function getRelativeMIMEId($id)
    {
        $rel = $this->getMIMEId();
        return (empty($rel)) ? $id : $rel . '.' . $id;
    }

    /**
     * Returns a mapping of all MIME IDs to their content-types.
     *
     * @access public
     *
     * @return array  KEY: MIME ID, VALUE: Content type
     */
    function contentTypeMap()
    {
        $map = array($this->getMIMEId() => $this->getType());
        foreach ($this->_parts as $val) {
            $map += $val->contentTypeMap();
        }
        return $map;
    }

    /**
     * Generate the unique boundary string (if not already done).
     *
     * @access private
     *
     * @return string  The boundary string.
     */
    function _generateBoundary()
    {
        if (is_null($this->_boundary)) {
            $this->_boundary = '=_' . base_convert(microtime(), 10, 36);
        }
        return $this->_boundary;
    }

}
