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

/* Net_DNS_Question object definition {{{ */
/**
 * Builds or parses the QUESTION section of a DNS packet
 *
 * Builds or parses the QUESTION section of a DNS packet
 *
 * @package Net_DNS
 */
class Net_DNS_Question
{
    /* class variable definitions {{{ */
    var $qname = NULL;
    var $qtype = NULL;
    var $qclass = NULL;

    /* }}} */
    /* class constructor Net_DNS_Question($qname, $qtype, $qclass) {{{ */
    function Net_DNS_Question($qname, $qtype, $qclass)
    {
        if (   is_null(Net_DNS::typesbyname($qtype))
                &&  !is_null(Net_DNS::classesbyname($qtype))
                && is_null(Net_DNS::classesbyname($qclass))
                &&  !is_null(Net_DNS::typesbyname($qclass))) {

            $t = $qtype;
            $qtype = $qclass;
            $qclass = $t;
        }

        $this->qname = $qname;
        $this->qtype = $qtype;
        $this->qclass = $qclass;
    }

    /* }}} */
    /* Net_DNS_Question::display() {{{*/
    function display()
    {
        echo $this->string() . "\n";
    }

    /*}}}*/
    /* Net_DNS_Question::string() {{{*/
    function string()
    {
        return($this->qname . ".\t" . $this->qclass . "\t" . $this->qtype);
    }

    /*}}}*/
    /* Net_DNS_Question::data(&$packet, $offset) {{{*/
    function data($packet, $offset)
    {
        $data = $packet->dn_comp($this->qname, $offset);
        $data .= pack('n', Net_DNS::typesbyname(strtoupper($this->qtype)));
        $data .= pack('n', Net_DNS::classesbyname(strtoupper($this->qclass)));
        return($data);
    }

    /*}}}*/
}
/* }}} */
/* VIM settings{{{
 * Local variables:
 * tab-width: 4
 * c-basic-offset: 4
 * soft-stop-width: 4
 * c indent on
 * End:
 * vim600: sw=4 ts=4 sts=4 cindent fdm=marker et
 * vim<600: sw=4 ts=4
 * }}} */
?>
