<?php
/*
 *  Module written/ported by Eric Kilfoil <eric@ypass.net>
 * 
 *  This is the copyright notice from the PERL Net::DNS module:
 *
 *  Copyright (c) 1997-2000 Michael Fuhr.  All rights reserved.  This
 *  program is free software; you can redistribute it and/or modify it
 *  under the same terms as Perl itself.
 *
 *  The majority of this is _NOT_ my code.  I simply ported it from the
 *  PERL Net::DNS module.  
 *
 *  The author of the Net::DNS module is Michael Fuhr <mike@fuhr.org>
 *  http://www.fuhr.org/~mfuhr/perldns/
 *
 *  I _DO_ maintain this code, and Miachael Fuhr has nothing to with the
 *  porting of this code to PHP.  Any questions directly related to this
 *  class library should be directed to me.
 *
 *  I'll be setting up a CVS repository for this class soon.  The more
 *  emails i get concerning this, the more apt i am to do it.
 *
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

/* Include information {{{ */

    $phpdns_basedir = 'Net';
    require_once("$phpdns_basedir/DNS/Header.php");
    require_once("$phpdns_basedir/DNS/Question.php");
    require_once("$phpdns_basedir/DNS/Packet.php");
    require_once("$phpdns_basedir/DNS/Resolver.php");
    require_once("$phpdns_basedir/DNS/RR.php");

/* }}} */
/* GLOBAL VARIABLE definitions {{{ */

// Used by the Net_DNS_Resolver object to generate an ID
mt_srand((double) microtime() * 10000);
$_Net_DNS_packet_id = (int)mt_rand(0, 65535);

/* }}} */
/* Net_DNS object definition (incomplete) {{{ */
/**
 * Initializes a resolver object
 *
 * Net_DNS allows you to query a nameserver for DNS  lookups.  It bypasses the
 * system resolver library  entirely, which allows you to query any nameserver,
 * set your own values for retries, timeouts, recursion,  etc.
 *
 * @author Eric Kilfoil <eric@ypass.net>
 * @package Net_DNS
 * @version 0.01alpha
 */
class Net_DNS
{
    /* class variable definitions {{{ */
    /**
     * A default resolver object created on instantiation
     *
     * @var object Net_DNS_Resolver
     */
    var $resolver;
    var $VERSION = '1.00b2'; // This should probably be a define :(
    var $PACKETSZ = 512;
    var $HFIXEDSZ = 12;
    var $QFIXEDSZ = 4;
    var $RRFIXEDSZ = 10;
    var $INT32SZ = 4;
    var $INT16SZ = 2;
    /* }}} */
    /* class constructor - Net_DNS() {{{ */
    /**
     * Initializes a resolver object
     *
     * @see Net_DNS_Resolver
     */
    function Net_DNS()
    {
        $this->resolver = new Net_DNS_Resolver();
    }
    /* }}} */
    /* Net_DNS::opcodesbyname() {{{ */
    /**
     * Translates opcode names to integers
     *
     * Translates the name of a DNS OPCODE into it's assigned  number
     * listed in RFC1035, RFC1996, or RFC2136. Valid  OPCODES are:
     * <ul>
     *   <li>QUERY   
     *   <li>IQUERY   
     *   <li>STATUS   
     *   <li>NS_NOTIFY_OP   
     *   <li>UPDATE
     * <ul>
     * 
     * @param   string  $opcode A DNS Packet OPCODE name
     * @return  integer The integer value of an OPCODE
     * @see     Net_DNS::opcodesbyval()
     */
    function opcodesbyname($opcode)
    {
        $op = array(
                'QUERY'        => 0,   // RFC 1035
                'IQUERY'       => 1,   // RFC 1035
                'STATUS'       => 2,   // RFC 1035
                'NS_NOTIFY_OP' => 4,   // RFC 1996
                'UPDATE'       => 5,   // RFC 2136
                );
        if (! strlen($op[$opcode])) {
            $op[$opcode] = NULL;
        }
        return($op[$opcode]);
    }

    /* }}} */
    /* Net_DNS::opcodesbyval() {{{*/
    /**
     * Translates opcode integers into names
     *
     * Translates the integer value of an opcode into it's name
     * 
     * @param   integer $opcodeval  A DNS packet opcode integer
     * @return  string  The name of the OPCODE
     * @see     Net_DNS::opcodesbyname()
     */
    function opcodesbyval($opcodeval)
    {
        $opval = array(
                0 => 'QUERY',
                1 => 'IQUERY',
                2 => 'STATUS',
                4 => 'NS_NOTIFY_OP',
                5 => 'UPDATE',
                );
        if (! strlen($opval[$opcodeval])) {
            $opval[$opcodeval] = NULL;
        }
        return($opval[$opcodeval]);
    }

    /*}}}*/
    /* Net_DNS::rcodesbyname() {{{*/
    /**
     * Translates rcode names to integers
     *
     * Translates the name of a DNS RCODE (result code) into it's assigned number.
     * <ul>
     *   <li>NOERROR   
     *   <li>FORMERR   
     *   <li>SERVFAIL   
     *   <li>NXDOMAIN   
     *   <li>NOTIMP   
     *   <li>REFUSED   
     *   <li>YXDOMAIN   
     *   <li>YXRRSET   
     *   <li>NXRRSET   
     *   <li>NOTAUTH   
     *   <li>NOTZONE
     * <ul>
     * 
     * @param   string  $rcode  A DNS Packet RCODE name
     * @return  integer The integer value of an RCODE
     * @see     Net_DNS::rcodesbyval()
     */
    function rcodesbyname($rcode)
    {
        $rc = array(
                'NOERROR'   => 0,   // RFC 1035
                'FORMERR'   => 1,   // RFC 1035
                'SERVFAIL'  => 2,   // RFC 1035
                'NXDOMAIN'  => 3,   // RFC 1035
                'NOTIMP'    => 4,   // RFC 1035
                'REFUSED'   => 5,   // RFC 1035
                'YXDOMAIN'  => 6,   // RFC 2136
                'YXRRSET'   => 7,   // RFC 2136
                'NXRRSET'   => 8,   // RFC 2136
                'NOTAUTH'   => 9,   // RFC 2136
                'NOTZONE'   => 10,    // RFC 2136
                );
        if (! strlen($rc[$rcode])) {
            $rc[$rcode] = NULL;
        }
        return($rc[$rcode]);
    }

    /*}}}*/
    /* Net_DNS::rcodesbyval() {{{*/
    /**
     * Translates rcode integers into names
     *
     * Translates the integer value of an rcode into it's name
     * 
     * @param   integer $rcodeval   A DNS packet rcode integer
     * @return  string  The name of the RCODE
     * @see     Net_DNS::rcodesbyname()
     */
    function rcodesbyval($rcodeval)
    {
        $rc = array(
                0 => 'NOERROR',
                1 => 'FORMERR',
                2 => 'SERVFAIL',
                3 => 'NXDOMAIN',
                4 => 'NOTIMP',
                5 => 'REFUSED',
                6 => 'YXDOMAIN',
                7 => 'YXRRSET',
                8 => 'NXRRSET',
                9 => 'NOTAUTH',
                10 => 'NOTZONE',
                );
        if (! strlen($rc[$rcodeval])) {
            $rc[$rcodeval] = NULL;
        }
        return($rc[$rcodeval]);
    }

    /*}}}*/
    /* Net_DNS::typesbyname() {{{*/
    /**
     * Translates RR type names into integers
     *
     * Translates a Resource Record from it's name to it's  integer value.
     * Valid resource record types are:
     *
     * <ul>
     *   <li>A   
     *   <li>NS   
     *   <li>MD   
     *   <li>MF   
     *   <li>CNAME   
     *   <li>SOA   
     *   <li>MB   
     *   <li>MG   
     *   <li>MR   
     *   <li>NULL   
     *   <li>WKS   
     *   <li>PTR   
     *   <li>HINFO   
     *   <li>MINFO   
     *   <li>MX   
     *   <li>TXT   
     *   <li>RP   
     *   <li>AFSDB   
     *   <li>X25   
     *   <li>ISDN   
     *   <li>RT   
     *   <li>NSAP   
     *   <li>NSAP_PTR   
     *   <li>SIG   
     *   <li>KEY   
     *   <li>PX   
     *   <li>GPOS   
     *   <li>AAAA   
     *   <li>LOC   
     *   <li>NXT   
     *   <li>EID   
     *   <li>NIMLOC   
     *   <li>SRV   
     *   <li>ATMA   
     *   <li>NAPTR   
     *   <li>TSIG   
     *   <li>UINFO   
     *   <li>UID   
     *   <li>GID   
     *   <li>UNSPEC   
     *   <li>IXFR   
     *   <li>AXFR   
     *   <li>MAILB   
     *   <li>MAILA   
     *   <li>ANY
     * <ul>
     * 
     * @param   string  $rrtype A DNS packet RR type name   
     * @return  integer The integer value of an RR type
     * @see     Net_DNS::typesbyval()
     */
    function typesbyname($rrtype)
    {
        $rc = array(
                'A'             => 1,
                'NS'            => 2,
                'MD'            => 3,
                'MF'            => 4,
                'CNAME'         => 5,
                'SOA'           => 6,
                'MB'            => 7,
                'MG'            => 8,
                'MR'            => 9,
                'NULL'          => 10,
                'WKS'           => 11,
                'PTR'           => 12,
                'HINFO'         => 13,
                'MINFO'         => 14,
                'MX'            => 15,
                'TXT'           => 16,
                'RP'            => 17,
                'AFSDB'         => 18,
                'X25'           => 19,
                'ISDN'          => 20,
                'RT'            => 21,
                'NSAP'          => 22,
                'NSAP_PTR'      => 23,
                'SIG'           => 24,
                'KEY'           => 25,
                'PX'            => 26,
                'GPOS'          => 27,
                'AAAA'          => 28,
                'LOC'           => 29,
                'NXT'           => 30,
                'EID'           => 31,
                'NIMLOC'        => 32,
                'SRV'           => 33,
                'ATMA'          => 34,
                'NAPTR'         => 35,
                'UINFO'         => 100,
                'UID'           => 101,
                'GID'           => 102,
                'UNSPEC'        => 103,
                'TSIG'          => 250,
                'IXFR'          => 251,
                'AXFR'          => 252,
                'MAILB'         => 253,
                'MAILA'         => 254,
                'ANY'           => 255,
                );
                if (! strlen($rc[$rrtype])) {
                    $rc[$rrtype] = NULL;
                }
                return($rc[$rrtype]);
    }

    /*}}}*/
    /* Net_DNS::typesbyval() {{{*/
    /**
     * Translates RR type integers into names
     *
     * Translates the integer value of an RR type into it's name
     * 
     * @param   integer $rrtypeval  A DNS packet RR type integer
     * @return  string  The name of the RR type
     * @see     Net_DNS::typesbyname()
     */
    function typesbyval($rrtypeval)
    {
        $rc = array(
                1 => 'A',
                2 => 'NS',
                3 => 'MD',
                4 => 'MF',
                5 => 'CNAME',
                6 => 'SOA',
                7 => 'MB',
                8 => 'MG',
                9 => 'MR',
                10 => 'NULL',
                11 => 'WKS',
                12 => 'PTR',
                13 => 'HINFO',
                14 => 'MINFO',
                15 => 'MX',
                16 => 'TXT',
                17 => 'RP',
                18 => 'AFSDB',
                19 => 'X25',
                20 => 'ISDN',
                21 => 'RT',
                22 => 'NSAP',
                23 => 'NSAP_PTR',
                24 => 'SIG',
                25 => 'KEY',
                26 => 'PX',
                27 => 'GPOS',
                28 => 'AAAA',
                29 => 'LOC',
                30 => 'NXT',
                31 => 'EID',
                32 => 'NIMLOC',
                33 => 'SRV',
                34 => 'ATMA',
                35 => 'NAPTR',
                100 => 'UINFO',
                101 => 'UID',
                102 => 'GID',
                103 => 'UNSPEC',
                250 => 'TSIG',
                251 => 'IXFR',
                252 => 'AXFR',
                253 => 'MAILB',
                254 => 'MAILA',
                255 => 'ANY',
                );
                if (! strlen($rc[$rrtypeval])) {
                    $rc[$rrtypeval] = NULL;
                }
                return($rc[$rrtypeval]);
    }

    /*}}}*/
    /* Net_DNS::classesbyname() {{{*/
    /**
     * translates a DNS class from it's name to it's  integer value. Valid
     * class names are:
     * <ul>
     *   <li>IN   
     *   <li>CH   
     *   <li>HS   
     *   <li>NONE   
     *   <li>ANY
     * </ul>
     * 
     * @param   string  $class  A DNS packet class type
     * @return  integer The integer value of an class type
     * @see     Net_DNS::classesbyval()
     */
    function classesbyname($class)
    {
        $rc = array(
                'IN'            => 1,
                'CH'            => 3,
                'HS'            => 4,
                'NONE'          => 254,
                'ANY'           => 255
                );
        if (! isset($rc[$class])) {
            $rc[$class] = NULL;
        }
        return($rc[$class]);
    }

    /*}}}*/
    /* Net_DNS::classesbyval() {{{*/
    /**
     * Translates RR class integers into names
     *
     * Translates the integer value of an RR class into it's name
     * 
     * @param   integer $classval   A DNS packet RR class integer
     * @return  string  The name of the RR class
     * @see     Net_DNS::classesbyname()
     */
    function classesbyval($classval)
    {
        $rc = array(
                1 => 'IN',
                3 => 'CH',
                4 => 'HS',
                254 => 'NONE',
                255 => 'ANY'
                );
        if (! strlen($rc[$classval])) {
            $rc[$classval] = NULL;
        }
        return($rc[$classval]);
    }

    /*}}}*/
    /* not completed - Net_DNS::mx() {{{*/
    /*}}}*/
    /* not completed - Net_DNS::yxrrset() {{{*/
    /*}}}*/
    /* not completed - Net_DNS::nxrrset() {{{*/
    /*}}}*/
    /* not completed - Net_DNS::yxdomain() {{{*/
    /*}}}*/
    /* not completed - Net_DNS::nxdomain() {{{*/
    /*}}}*/
    /* not completed - Net_DNS::rr_add() {{{*/
    /*}}}*/
    /* not completed - Net_DNS::rr_del() {{{*/
    /*}}}*/
}
/* }}} */
/* VIM Settings {{{
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
