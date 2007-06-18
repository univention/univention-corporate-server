<?php
//
// +----------------------------------------------------------------------+
// | PHP Version 4                                                        |
// +----------------------------------------------------------------------+
// | Copyright (c) 1997-2002 The PHP Group                                |
// +----------------------------------------------------------------------+
// | This source file is subject to version 2.02 of the PHP license,      |
// | that is bundled with this package in the file LICENSE, and is        |
// | available at through the world-wide-web at                           |
// | http://www.php.net/license/2_02.txt.                                 |
// | If you did not receive a copy of the PHP license and are unable to   |
// | obtain it through the world-wide-web, please send a note to          |
// | license@php.net so we can mail you a copy immediately.               |
// +----------------------------------------------------------------------+
// | Authors: Shane Caraveo <shane@caraveo.com>                           |
// | 		  Ralf Hofmann <ralf.hofmann@verdisoft.com>					  |
// +----------------------------------------------------------------------+
//
// $Id: DIME.php,v 1.1.2.1 2005/10/05 14:39:47 steuwer Exp $
//

require_once 'PEAR.php';
/**
 *
 *  DIME Encoding/Decoding
 *
 * What is it?
 *   This class enables you to manipulate and build
 *   a DIME encapsulated message.
 *
 * http://www.ietf.org/internet-drafts/draft-nielsen-dime-02.txt
 *
 * 09/18/02 Ralf -  A huge number of changes to be compliant 
 * 					with the DIME Specification Release 17 June 2002
 * 
 * TODO: lots of stuff needs to be tested.
 *           Definitily have to go through DIME spec and
 *           make things work right, most importantly, sec 3.3
 *           make examples, document
 *
 * see test/dime_mesage_test.php for example of usage
 * 
 * @author  Shane Caraveo <shane@caraveo.com>, 
 *          Ralf Hofmann <ralf.hofmann@verdisoft.com>	 
 * @version $Revision: 1.1.2.1 $
 * @package Net_DIME
 */
define('NET_DIME_TYPE_UNCHANGED',0x00);
define('NET_DIME_TYPE_MEDIA',0x01);
define('NET_DIME_TYPE_URI',0x02);
define('NET_DIME_TYPE_UNKNOWN',0x03);
define('NET_DIME_TYPE_NONE',0x04);

define('NET_DIME_VERSION',0x0001);

define('NET_DIME_RECORD_HEADER',12);

define('NET_DIME_FLAGS', 0);
define('NET_DIME_OPTS_LEN', 1);
define('NET_DIME_ID_LEN', 2);
define('NET_DIME_TYPE_LEN', 3);
define('NET_DIME_DATA_LEN', 4);
define('NET_DIME_OPTS', 5);
define('NET_DIME_ID', 6);
define('NET_DIME_TYPE', 7);
define('NET_DIME_DATA', 8);

class Net_DIME_Record extends PEAR
{
    // these are used to hold the padded length
    var $OPTS_LENGTH = 0;
    var $ID_LENGTH = 0;
    var $TYPE_LENGTH = 0; 
    var $DATA_LENGTH = 0;
    var $_haveOpts = FALSE;
    var $_haveID = FALSE;
    var $_haveType = FALSE;
    var $_haveData = FALSE;
    var $debug = FALSE;
    var $padstr = "\0";
    /**
     * Elements
     * [NET_DIME_FLAGS],    16 bits: VERSION:MB:ME:CF:TYPE_T
     * [NET_DIME_OPTS_LEN], 16 bits: OPTIONS_LENGTH
     * [NET_DIME_ID_LEN],   16 bits: ID_LENGTH
     * [NET_DIME_TYPE_LEN], 16 bits: TYPE_LENGTH
     * [NET_DIME_DATA_LEN], 32 bits: DATA_LENGTH
	 * [NET_DIME_OPTS]             : OPTIONS
	 * [NET_DIME_ID]     		   : ID
	 * [NET_DIME_TYPE]             : TYPE
	 * [NET_DIME_DATA]             : DATA
     */
    var $Elements = array(NET_DIME_FLAGS => 0,  NET_DIME_OPTS_LEN => 0, 
	                      NET_DIME_ID_LEN => 0, NET_DIME_TYPE_LEN => 0, 
     					  NET_DIME_DATA_LEN => 0,
	 					  NET_DIME_OPTS => '',
						  NET_DIME_ID => '',
						  NET_DIME_TYPE => '',
						  NET_DIME_DATA => '');
    
    function Net_DIME_Record($debug = FALSE)
    {
        $this->debug = $debug;
        if ($debug) $this->padstr = '*';
    }

    function setMB()
    {
        $this->Elements[NET_DIME_FLAGS] |= 0x0400;
    }

    function setME()
    {
        $this->Elements[NET_DIME_FLAGS] |= 0x0200;
    }

    function setCF()
    {
        $this->Elements[NET_DIME_FLAGS] |= 0x0100;
    }

    function isChunk()
    {
        return $this->Elements[NET_DIME_FLAGS] & 0x0100;
    }

    function isEnd()
    {
        return $this->Elements[NET_DIME_FLAGS] & 0x0200;
    }
    
    function isStart()
    {
        return $this->Elements[NET_DIME_FLAGS] & 0x0400;
    }
    
    function getID()
    {
        return $this->Elements[NET_DIME_ID];
    }

    function getType()
    {
        return $this->Elements[NET_DIME_TYPE];
    }

    function getData()
    {
        return $this->Elements[NET_DIME_DATA];
    }
    
    function getDataLength()
    {
        return $this->Elements[NET_DIME_DATA_LEN];
    }
    
    function setType($typestring, $type=NET_DIME_TYPE_UNKNOWN)
    {
        $typelen = strlen($typestring) & 0xFFFF;
        $type = $type << 4;
        $this->Elements[NET_DIME_FLAGS] = ($this->Elements[NET_DIME_FLAGS] & 0xFF0F) | $type;
        $this->Elements[NET_DIME_TYPE_LEN] = $typelen;
        $this->TYPE_LENGTH = $this->_getPadLength($typelen);
        $this->Elements[NET_DIME_TYPE] = $typestring;
    }
    
    function generateID()
    {
        $id = md5(time());
        $this->setID($id);
        return $id;
    }
    
    function setID($id)
    {
        $idlen = strlen($id) & 0xFFFF;
        $this->Elements[NET_DIME_ID_LEN] = $idlen;
        $this->ID_LENGTH = $this->_getPadLength($idlen);
        $this->Elements[NET_DIME_ID] = $id;
    }
    
    function setData($data, $size=0)
    {
        $datalen = $size?$size:strlen($data);
        $this->Elements[NET_DIME_DATA_LEN] = $datalen;
        $this->DATA_LENGTH = $this->_getPadLength($datalen);
        $this->Elements[NET_DIME_DATA] = $data;
    }
    
    function encode()
    {
		// insert version 
	    $this->Elements[NET_DIME_FLAGS] = ($this->Elements[NET_DIME_FLAGS] & 0x07FF) | (NET_DIME_VERSION << 11);

        // the real dime encoding
        $format =   '%c%c%c%c%c%c%c%c%c%c%c%c'.
                    '%'.$this->OPTS_LENGTH.'s'.
                    '%'.$this->ID_LENGTH.'s'.
                    '%'.$this->TYPE_LENGTH.'s'.
                    '%'.$this->DATA_LENGTH.'s';
        return sprintf($format,
	                   ($this->Elements[NET_DIME_FLAGS]&0x0000FF00)>>8,
    	               ($this->Elements[NET_DIME_FLAGS]&0x000000FF),
        	           ($this->Elements[NET_DIME_OPTS_LEN]&0x0000FF00)>>8,
            	       ($this->Elements[NET_DIME_OPTS_LEN]&0x000000FF),
        	           ($this->Elements[NET_DIME_ID_LEN]&0x0000FF00)>>8,
            	       ($this->Elements[NET_DIME_ID_LEN]&0x000000FF),
        	           ($this->Elements[NET_DIME_TYPE_LEN]&0x0000FF00)>>8,
            	       ($this->Elements[NET_DIME_TYPE_LEN]&0x000000FF),
                	   ($this->Elements[NET_DIME_DATA_LEN]&0xFF000000)>>24,
	                   ($this->Elements[NET_DIME_DATA_LEN]&0x00FF0000)>>16,
    	               ($this->Elements[NET_DIME_DATA_LEN]&0x0000FF00)>>8,
        	           ($this->Elements[NET_DIME_DATA_LEN]&0x000000FF),
            	       str_pad($this->Elements[NET_DIME_OPTS], $this->OPTS_LENGTH, $this->padstr),
            	       str_pad($this->Elements[NET_DIME_ID], $this->ID_LENGTH, $this->padstr),
                	   str_pad($this->Elements[NET_DIME_TYPE], $this->TYPE_LENGTH, $this->padstr),
	                   str_pad($this->Elements[NET_DIME_DATA], $this->DATA_LENGTH, $this->padstr));
    }
    
    function _getPadLength($len)
    {
        $pad = 0;
        if ($len) {
            $pad = $len % 4;
            if ($pad) $pad = 4 - $pad;
        }
        return $len + $pad;
    }
    
    function decode(&$data)
    {
        // REAL DIME decoding
        $this->Elements[NET_DIME_FLAGS]    = (hexdec(bin2hex($data[0]))<<8) + hexdec(bin2hex($data[1]));
        $this->Elements[NET_DIME_OPTS_LEN] = (hexdec(bin2hex($data[2]))<<8) + hexdec(bin2hex($data[3]));
        $this->Elements[NET_DIME_ID_LEN]   = (hexdec(bin2hex($data[4]))<<8) + hexdec(bin2hex($data[5]));
        $this->Elements[NET_DIME_TYPE_LEN] = (hexdec(bin2hex($data[6]))<<8) + hexdec(bin2hex($data[7]));
        $this->Elements[NET_DIME_DATA_LEN] = (hexdec(bin2hex($data[8]))<<24) +
		                             (hexdec(bin2hex($data[9]))<<16) +
                                     (hexdec(bin2hex($data[10]))<<8) +
                                      hexdec(bin2hex($data[11]));
        $p = 12;
		
		$version = (($this->Elements[NET_DIME_FLAGS]>>11) & 0x001F);
		
		if ($version == NET_DIME_VERSION) 
		{
	        $this->OPTS_LENGTH = $this->_getPadLength($this->Elements[NET_DIME_OPTS_LEN]);        
	        $this->ID_LENGTH = $this->_getPadLength($this->Elements[NET_DIME_ID_LEN]);
	        $this->TYPE_LENGTH = $this->_getPadLength($this->Elements[NET_DIME_TYPE_LEN]);
	        $this->DATA_LENGTH = $this->_getPadLength($this->Elements[NET_DIME_DATA_LEN]);
	                
	        $datalen = strlen($data);
	        $this->Elements[NET_DIME_OPTS] = substr($data,$p,$this->Elements[NET_DIME_OPTS_LEN]);
	        $this->_haveOpts = (strlen($this->Elements[NET_DIME_OPTS]) == $this->Elements[NET_DIME_OPTS_LEN]);
	        if ($this->_haveOpts) {
	            $p += $this->OPTS_LENGTH;		
		        $this->Elements[NET_DIME_ID] = substr($data,$p,$this->Elements[NET_DIME_ID_LEN]);
		        $this->_haveID = (strlen($this->Elements[NET_DIME_ID]) == $this->Elements[NET_DIME_ID_LEN]);
		        if ($this->_haveID) {
		            $p += $this->ID_LENGTH;
		            $this->Elements[NET_DIME_TYPE] = substr($data,$p,$this->Elements[NET_DIME_TYPE_LEN]);
		            $this->_haveType = (strlen($this->Elements[NET_DIME_TYPE]) == $this->Elements[NET_DIME_TYPE_LEN]);
		            if ($this->_haveType) {
		                $p += $this->TYPE_LENGTH;
		                $this->Elements[NET_DIME_DATA] = substr($data,$p,$this->Elements[NET_DIME_DATA_LEN]);
		                $this->_haveData = (strlen($this->Elements[NET_DIME_DATA]) == $this->Elements[NET_DIME_DATA_LEN]);
		                if ($this->_haveData) {
		                    $p += $this->DATA_LENGTH;
		                } else {
		                    $p += strlen($this->Elements[NET_DIME_DATA]);
		                }
		            } else {
		                $p += strlen($this->Elements[NET_DIME_TYPE]);
					}
		        } else {
		            $p += strlen($this->Elements[NET_DIME_ID]);
				}
		    } else {
		    	$p += strlen($this->Elements[NET_DIME_OPTS]);					
	        }
		}
        return substr($data, $p);
    }
    
    function addData(&$data)
    {
        $datalen = strlen($data);
        $p = 0;
        if (!$this->_haveOpts) {
            $have = strlen($this->Elements[NET_DIME_OPTS]);
            $this->Elements[NET_DIME_OPTS] .= substr($data,$p,$this->Elements[NET_DIME_OPTS_LEN]-$have);
            $this->_haveOpts = (strlen($this->Elements[NET_DIME_OPTS]) == $this->Elements[DIME_OTPS_LEN]);
            if (!$this->_haveOpts) return NULL;
            $p += $this->OPTS_LENGTH-$have;
        }
        if (!$this->_haveID) {
            $have = strlen($this->Elements[NET_DIME_ID]);
            $this->Elements[NET_DIME_ID] .= substr($data,$p,$this->Elements[NET_DIME_ID_LEN]-$have);
            $this->_haveID = (strlen($this->Elements[NET_DIME_ID]) == $this->Elements[NET_DIME_ID_LEN]);
            if (!$this->_haveID) return NULL;
            $p += $this->ID_LENGTH-$have;
        }
        if (!$this->_haveType && $p < $datalen) {
            $have = strlen($this->Elements[NET_DIME_TYPE]);
            $this->Elements[NET_DIME_TYPE] .= substr($data,$p,$this->Elements[NET_DIME_TYPE_LEN]-$have);
            $this->_haveType = (strlen($this->Elements[NET_DIME_TYPE]) == $this->Elements[NET_DIME_TYPE_LEN]);
            if (!$this->_haveType) return NULL;
            $p += $this->TYPE_LENGTH-$have;
        }
        if (!$this->_haveData && $p < $datalen) {
            $have = strlen($this->Elements[NET_DIME_DATA]);
            $this->Elements[NET_DIME_DATA] .= substr($data,$p,$this->Elements[NET_DIME_DATA_LEN]-$have);
            $this->_haveData = (strlen($this->Elements[NET_DIME_DATA]) == $this->Elements[NET_DIME_DATA_LEN]);
            if (!$this->_haveData) return NULL;
            $p += $this->DATA_LENGTH-$have;
        }
        return substr($data,$p);
    }   
}


class Net_DIME_Message extends PEAR
{

    var $record_size = 4096;
    #var $records =array();
    var $parts = array();
    var $currentPart = -1;
    var $stream = NULL;
    var $_currentRecord;
    var $_proc = array();
    var $type;
    var $typestr;
    var $mb = 1;
    var $me = 0;
    var $cf = 0;
    var $id = NULL;
    var $debug = FALSE;
    /**
     * constructor
     *
     * this currently takes a file pointer as provided
     * by fopen
     *
     * TODO: integrate with the php streams stuff
     */
    function Net_DIME_Message($stream=NULL, $record_size = 4096, $debug = FALSE)
    {
        $this->stream = $stream;
        $this->record_size = $record_size;
        $this->debug = $debug;
    }
    
    function _makeRecord(&$data, $typestr='', $id=NULL, $type=NET_DIME_TYPE_UNKNOWN)
    {
        $record = new Net_DIME_Record($this->debug);
        if ($this->mb) {
            $record->setMB();
            // all subsequent records are not message begin!
            $this->mb = 0; 
        }
        if ($this->me) $record->setME();
        if ($this->cf) $record->setCF();
        $record->setData($data);
        $record->setType($typestr,$type);
        if ($id) $record->setID($id);
        #if ($this->debug) {
        #    print str_replace('\0','*',$record->encode());
        #}
        return $record->encode();
    }
    
    function startChunk(&$data, $typestr='', $id=NULL, $type=NET_DIME_TYPE_UNKNOWN)
    {
        $this->me = 0;
        $this->cf = 1;
        $this->type = $type;
        $this->typestr = $typestr;
        if ($id) {
            $this->id = $id;
        } else {
            $this->id = md5(time());
        }
        return $this->_makeRecord($data, $this->typestr, $this->id, $this->type);
    }

    function doChunk(&$data)
    {
        $this->me = 0;
        $this->cf = 1;
        return $this->_makeRecord($data, NULL, NULL, NET_DIME_TYPE_UNCHANGED);
    }

    function endChunk()
    {
        $this->cf = 0;
        $data = NULL;
        $rec = $this->_makeRecord($data, NULL, NULL, NET_DIME_TYPE_UNCHANGED);
        $this->id = 0;
        $this->cf = 0;
        $this->id = 0;
        $this->type = NET_DIME_TYPE_UNKNOWN;
        $this->typestr = NULL;
        return $rec;
    }
    
    function endMessage()
    {
        $this->me = 1;
        $data = NULL;
        $rec = $this->_makeRecord($data, NULL, NULL, NET_DIME_TYPE_NONE);
        $this->me = 0;
        $this->mb = 1;
        $this->id = 0;
        return $rec;
    }
    
    /**
     * sendRecord
     *
     * given a chunk of data, it creates DIME records
     * and writes them to the stream
     *
     */
    function sendData(&$data, $typestr='', $id=NULL, $type=NET_DIME_TYPE_UNKNOWN)
    {
        $len = strlen($data);
        if ($len > $this->record_size) {
            $chunk = substr($data, 0, $this->record_size);
            $p = $this->record_size;
            $rec = $this->startChunk($chunk,$typestr,$id,$type);
            fwrite($this->stream, $rec);
            while ($p < $len) {
                $chunk = substr($data, $p, $this->record_size);
                $p += $this->record_size;
                $rec = $this->doChunk($chunk);
                fwrite($this->stream, $rec);
            }
            $rec = $this->endChunk();
            fwrite($this->stream, $rec);
            return;
        }
        $rec = $this->_makeRecord($data, $typestr,$id,$type);
        fwrite($this->stream, $rec);
    }
    
    function sendEndMessage()
    {
        $rec = $this->endMessage();
        fwrite($this->stream, $rec);
    }
    
    /**
     * sendFile
     *
     * given a filename, it reads the file,
     * creates records and writes them to the stream
     *
     */
    function sendFile($filename, $typestr='', $id=NULL, $type=NET_DIME_TYPE_UNKNOWN)
    {
        $f = fopen($filename, "rb");
        if ($f) {
            if ($data = fread($f, $this->record_size)) {
                $this->startChunk($data,$typestr,$id,$type);
            }
            while ($data = fread($f, $this->record_size)) {
                $this->doChunk($data,$typestr,$id,$type);
            }
            $this->endChunk();
            fclose($f);
        }
    }

    /**
     * encodeData
     *
     * given data, encode it in DIME
     *
     */
    function encodeData($data, $typestr='', $id=NULL, $type=NET_DIME_TYPE_UNKNOWN)
    {
        $len = strlen($data);
        $resp = '';
        if ($len > $this->record_size) {
            $chunk = substr($data, 0, $this->record_size);
            $p = $this->record_size;
            $resp .= $this->startChunk($chunk,$typestr,$id,$type);
            while ($p < $len) {
                $chunk = substr($data, $p, $this->record_size);
                $p += $this->record_size;
                $resp .= $this->doChunk($chunk);
            }
            $resp .= $this->endChunk();
        } else {
            $resp .= $this->_makeRecord($data, $typestr,$id,$type);
        }
        return $resp;
    }

    /**
     * sendFile
     *
     * given a filename, it reads the file,
     * creates records and writes them to the stream
     *
     */
    function encodeFile($filename, $typestr='', $id=NULL, $type=NET_DIME_TYPE_UNKNOWN)
    {
        $f = fopen($filename, "rb");
        if ($f) {
            if ($data = fread($f, $this->record_size)) {
                $resp = $this->startChunk($data,$typestr,$id,$type);
            }
            while ($data = fread($f, $this->record_size)) {
                $resp = $this->doChunk($data,$typestr,$id,$type);
            }
            $resp = $this->endChunk();
            fclose($f);
        }
        return $resp;
    }
    
    /**
     * _processData
     *
     * creates Net_DIME_Records from provided data
     *
     */
    function _processData(&$data)
    {
        $leftover = NULL;
        if (!$this->_currentRecord) {
            $this->_currentRecord = new Net_DIME_Record($this->debug);
            $data = $this->_currentRecord->decode($data);
        } else {
            $data = $this->_currentRecord->addData($data);
        }
				
        if ($this->_currentRecord->_haveData) {
            if (count($this->parts)==0 && !$this->_currentRecord->isStart()) {
                // raise an error!
                return PEAR::raiseError('First Message is not a DIME begin record!');
            }

            if ($this->_currentRecord->isEnd() && $this->_currentRecord->getDataLength()==0) {
                return NULL;
            }
            
            if ($this->currentPart < 0 && !$this->_currentRecord->isChunk()) {
                $this->parts[] = array();
                $this->currentPart = count($this->parts)-1;
                $this->parts[$this->currentPart]['id']   = $this->_currentRecord->getID();
                $this->parts[$this->currentPart]['type'] = $this->_currentRecord->getType();
                $this->parts[$this->currentPart]['data'] = $this->_currentRecord->getData();
                $this->currentPart = -1;
            } else {
                if ($this->currentPart < 0) {
                    $this->parts[] = array();
                    $this->currentPart = count($this->parts)-1;
                    $this->parts[$this->currentPart]['id']   = $this->_currentRecord->getID();
                    $this->parts[$this->currentPart]['type'] = $this->_currentRecord->getType();
                    $this->parts[$this->currentPart]['data'] = $this->_currentRecord->getData();
                } else {
                    $this->parts[$this->currentPart]['data'] .= $this->_currentRecord->getData();
                    if (!$this->_currentRecord->isChunk()) {
                        // we reached the end of the chunk
                        $this->currentPart = -1;
                    }
                }
            }
            #$this->records[] = $this->_currentRecord;
            if (!$this->_currentRecord->isEnd()) $this->_currentRecord = NULL;
        }
        return NULL;
    }
    
    /**
     * decodeData
     *
     * decodes a DIME encrypted string of data
     *
     */
    function decodeData(&$data) {
        while (strlen($data) >= NET_DIME_RECORD_HEADER) {
            $err = $this->_processData($data);
            if (PEAR::isError($err)) {
                return $err;
            }
        }
    }
    
    /**
     * read
     *
     * reads the stream and creates
     * an array of records
     *
     * it can accept the start of a previously read buffer
     * this is usefull in situations where you need to read
     * headers before discovering that the data is DIME encoded
     * such as in the case of reading an HTTP response.
     */
    function read($buf=NULL)
    {
        while ($data = fread($this->stream, 8192)) {
            if ($buf) {
                $data = $buf.$data;
                $buf = NULL;
            }
            if ($this->debug)
                echo "read: ".strlen($data)." bytes\n";
            $err = $this->decodeData($data);
            if (PEAR::isError($err)) {
                return $err;
            }
            
            // store any leftover data to be used again
            // should be < NET_DIME_RECORD_HEADER bytes
            $buf = $data;
        }
        if (!$this->_currentRecord || !$this->_currentRecord->isEnd()) {
            return PEAR::raiseError('reached stream end without end record');
        }
        return NULL;
    }
}
?>