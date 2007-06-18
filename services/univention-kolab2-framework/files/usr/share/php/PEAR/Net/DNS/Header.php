<?php
/*
 *  License Information:
 *
 *    Net_DNS:  A resolver library for PHP
 *    Copyright (c) 2002-2003 Eric Kilfoil eric@ypass.net
 *
 *    This library is free software; you can redistribute it and/or
 *    modify it under the terms of the GNU Lesser General Public
 *    License as published by the Free Software Foundation; either
 *    version 2.1 of the License, or (at your option) any later version.
 *
 *    This library is distributed in the hope that it will be useful,
 *    but WITHOUT ANY WARRANTY; without even the implied warranty of
 *    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 *    Lesser General Public License for more details.
 *
 *    You should have received a copy of the GNU Lesser General Public
 *    License along with this library; if not, write to the Free Software
 *    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 */

/*  Net_DNS_Header object definition {{{ */
/**
 * Object representation of the HEADER section of a DNS packet
 *
 * The Net_DNS::Header class contains the values of a DNS  packet.  It parses
 * the header of a DNS packet or can  generate the binary data
 * representation of the packet.  The format of the header is described in
 * RFC1035.
 *
 * @package Net_DNS
 */
class Net_DNS_Header
{
    /* class variable definitions {{{ */
    /**
     * The packet's request id
     *
     * The request id of the packet represented as  a 16 bit integer.
     */
    var $id;
    /**
     * The QR bit in a DNS packet header
     *
     * The QR bit as described in RFC1035.  QR is set to 0 for queries, and
     * 1 for repsones.
     */
    var $qr;
    /**
     * The OPCODE name of this packet.
     *
     * The string value (name) of the opcode for the DNS packet.
     */
    var $opcode;
    /**
     * The AA (authoritative answer) bit in a DNS packet header
     *
     * The AA bit as described in RFC1035.  AA is set to  1 if the answer
     * is authoritative.  It has no meaning if QR is set to 0.
     */
    var $aa;
    /**
     * The TC (truncated) bit in a DNS packet header
     *
     * This flag is set to 1 if the response was truncated.  This flag has
     * no meaning in a query packet.
     */
    var $tc;
    /**
     * The RD (recursion desired) bit in a DNS packet header
     *
     * This bit should be set to 1 in a query if recursion  is desired by
     * the DNS server.
     */
    var $rd;
    /**
     * The RA (recursion available) bit in a DNS packet header
     *
     * This bit is set to 1 by the DNS server if the server is willing to
     * perform recursion.
     */
    var $ra;
    /**
     * The RCODE name for this packet.
     *
     * The string value (name) of the rcode for the DNS packet.
     */
    var $rcode;
    /**
     * Number of questions contained within the packet
     *
     * 16bit integer representing the number of questions in the question
     * section of the DNS packet.
     *
     * @var integer $qdcount
     * @see     Net_DNS_Question class
     */
    var $qdcount;
    /**
     * Number of answer RRs contained within the packet
     *
     * 16bit integer representing the number of answer resource records
     * contained in the answer section of the DNS packet.
     *
     * @var integer $ancount
     * @see     Net_DNS_RR class
     */
    var $ancount;
    /**
     * Number of authority RRs within the packet
     *
     * 16bit integer representing the number of authority (NS) resource
     * records  contained in the authority section of the DNS packet.
     *
     * @var integer $nscount
     * @see     Net_DNS_RR class
     */
    var $nscount;
    /**
     * Number of additional RRs within the packet
     *
     * 16bit integer representing the number of additional resource records
     * contained in the additional section of the DNS packet.
     *
     * @var integer $arcount
     * @see     Net_DNS_RR class
     */
    var $arcount;

    /* }}} */
    /* class constructor - Net_DNS_Header($data = "") {{{ */
    /**
     * Initializes the default values for the Header object.
     * 
     * Builds a header object from either default values, or from a DNS
     * packet passed into the constructor as $data
     *
     * @param string $data  A DNS packet of which the header will be parsed.
     * @return  object  Net_DNS_Header
     * @access public
     */
    function Net_DNS_Header($data = '')
    {
        if ($data != '') {
            /*
             * The header MUST be at least 12 bytes.
             * Passing the full datagram to this constructor
             * will examine only the header section of the DNS packet
             */
            if (strlen($data) < 12)
                return(0);

            $a = unpack('nid/C2flags/n4counts', $data);
            $this->id      = $a['id'];
            $this->qr      = ($a['flags1'] >> 7) & 0x1;
            $this->opcode  = ($a['flags1'] >> 3) & 0xf;
            $this->aa      = ($a['flags1'] >> 2) & 0x1;
            $this->tc      = ($a['flags1'] >> 1) & 0x1;
            $this->rd      = $a['flags1'] & 0x1;
            $this->ra      = ($a['flags2'] >> 7) & 0x1;
            $this->rcode   = $a['flags2'] & 0xf;
            $this->qdcount = $a['counts1'];
            $this->ancount = $a['counts2'];
            $this->nscount = $a['counts3'];
            $this->arcount = $a['counts4'];
        }
        else {
            $this->id      = Net_DNS_Resolver::nextid();
            $this->qr      = 0;
            $this->opcode  = 0;
            $this->aa      = 0;
            $this->tc      = 0;
            $this->rd      = 1;
            $this->ra      = 0;
            $this->rcode   = 0;
            $this->qdcount = 1;
            $this->ancount = 0;
            $this->nscount = 0;
            $this->arcount = 0;
        }

        if (Net_DNS::opcodesbyval($this->opcode)) {
            $this->opcode = Net_DNS::opcodesbyval($this->opcode);
        }
        if (Net_DNS::rcodesbyval($this->rcode)) {
            $this->rcode = Net_DNS::rcodesbyval($this->rcode);
        }
    }

    /* }}} */
    /* Net_DNS_Header::display() {{{ */
    /**
     * Displays the properties of the header.
     *
     * Displays the properties of the header.
     *
     * @access public
     */
    function display()
    {
        echo $this->string();
    }

    /* }}} */
    /* Net_DNS_Header::string() {{{ */
    /**
     * Returns a formatted string containing the properties of the header.
     *
     * @return string   a formatted string containing the properties of the header.
     * @access public
     */
    function string()
    {
        $retval = ';; id = ' . $this->id . "\n";
        if ($this->opcode == 'UPDATE') {
            $retval .= ';; qr = ' . $this->qr . '    ' .
                'opcode = ' . $this->opcode . '    '   .
                'rcode = ' . $this->rcode . "\n";
            $retval .= ';; zocount = ' . $this->qdcount . '  ' .  
                'prcount = ' . $this->ancount . '  '           .
                'upcount = ' . $this->nscount . '  '           .
                'adcount = ' . $this->arcount . "\n";
        } else {
            $retval .= ';; qr = ' . $this->qr . '    ' .
                'opcode = ' . $this->opcode . '    '   .
                'aa = ' . $this->aa . '    '           .
                'tc = ' . $this->tc . '    '           .
                'rd = ' . $this->rd . "\n";

            $retval .= ';; ra = ' . $this->ra . '    ' .
                'rcode  = ' . $this->rcode . "\n";

            $retval .= ';; qdcount = ' . $this->qdcount . '  ' .
                'ancount = ' . $this->ancount . '  '    .
                'nscount = ' . $this->nscount . '  '    .
                'arcount = ' . $this->arcount . "\n";
        }
        return($retval);
    }

    /* }}} */
    /* Net_DNS_Header::data() {{{ */
    /**
     * Returns the binary data containing the properties of the header
     *
     * Packs the properties of the Header object into a binary string
     * suitable for using as the Header section of a DNS packet.
     *
     * @return string   binary representation of the header object
     * @access public
     */
    function data()
    {
        $opcode = Net_DNS::opcodesbyname($this->opcode);
        $rcode  = Net_DNS::rcodesbyname($this->rcode);

        $byte2 = ($this->qr << 7)
            | ($opcode << 3)
            | ($this->aa << 2)
            | ($this->tc << 1)
            | ($this->rd);

        $byte3 = ($this->ra << 7) | $rcode;

        return pack('nC2n4', $this->id,
                $byte2,
                $byte3,
                $this->qdcount,
                $this->ancount,
                $this->nscount,
                $this->arcount);
    }

    /* }}} */
}
/* }}} */
/* VIM settings {{{
 * Local variables:
 * tab-width: 4
 * c-basic-offset: 4
 * soft-stop-width: 4
 * c indent on
 * expandtab on
 * End:
 * vim600: sw=4 ts=4 sts=4 cindent fdm=marker et
 * vim<600: sw=4 ts=4
 * }}} */
?>
