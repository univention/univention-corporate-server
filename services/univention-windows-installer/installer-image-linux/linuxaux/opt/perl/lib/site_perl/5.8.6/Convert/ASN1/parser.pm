# 1 "y.tab.pl"
#$yysccsid = "@(#)yaccpar 1.8 (Berkeley) 01/20/91 (Perl 2.0 12/31/92)";

# 22 "parser.y"

;# Copyright (c) 2000-2002 Graham Barr <gbarr@pobox.com>. All rights reserved.
;# This program is free software; you can redistribute it and/or
;# modify it under the same terms as Perl itself.

package Convert::ASN1::parser;

;# $Id: parser.pm,v 1.1.2.1 2007/03/08 09:08:01 jmm Exp $

use strict;
use Convert::ASN1 qw(:all);
use vars qw(
  $asn $yychar $yyerrflag $yynerrs $yyn @yyss
  $yyssp $yystate @yyvs $yyvsp $yylval $yys $yym $yyval
);

BEGIN { Convert::ASN1->_internal_syms }

my $yydebug=0;
my %yystate;

my %base_type = (
  BOOLEAN	    => [ asn_encode_tag(ASN_BOOLEAN),		opBOOLEAN ],
  INTEGER	    => [ asn_encode_tag(ASN_INTEGER),		opINTEGER ],
  BIT_STRING	    => [ asn_encode_tag(ASN_BIT_STR),		opBITSTR  ],
  OCTET_STRING	    => [ asn_encode_tag(ASN_OCTET_STR),		opSTRING  ],
  STRING	    => [ asn_encode_tag(ASN_OCTET_STR),		opSTRING  ],
  NULL 		    => [ asn_encode_tag(ASN_NULL),		opNULL    ],
  OBJECT_IDENTIFIER => [ asn_encode_tag(ASN_OBJECT_ID),		opOBJID   ],
  REAL		    => [ asn_encode_tag(ASN_REAL),		opREAL    ],
  ENUMERATED	    => [ asn_encode_tag(ASN_ENUMERATED),	opINTEGER ],
  ENUM		    => [ asn_encode_tag(ASN_ENUMERATED),	opINTEGER ],
  'RELATIVE-OID'    => [ asn_encode_tag(ASN_RELATIVE_OID),	opROID	  ],

  SEQUENCE	    => [ asn_encode_tag(ASN_SEQUENCE | ASN_CONSTRUCTOR), opSEQUENCE ],
  SET               => [ asn_encode_tag(ASN_SET      | ASN_CONSTRUCTOR), opSET ],

  ObjectDescriptor  => [ asn_encode_tag(ASN_UNIVERSAL |  7), opSTRING ],
  UTF8String        => [ asn_encode_tag(ASN_UNIVERSAL | 12), opUTF8 ],
  NumericString     => [ asn_encode_tag(ASN_UNIVERSAL | 18), opSTRING ],
  PrintableString   => [ asn_encode_tag(ASN_UNIVERSAL | 19), opSTRING ],
  TeletexString     => [ asn_encode_tag(ASN_UNIVERSAL | 20), opSTRING ],
  T61String         => [ asn_encode_tag(ASN_UNIVERSAL | 20), opSTRING ],
  VideotexString    => [ asn_encode_tag(ASN_UNIVERSAL | 21), opSTRING ],
  IA5String         => [ asn_encode_tag(ASN_UNIVERSAL | 22), opSTRING ],
  UTCTime           => [ asn_encode_tag(ASN_UNIVERSAL | 23), opUTIME ],
  GeneralizedTime   => [ asn_encode_tag(ASN_UNIVERSAL | 24), opGTIME ],
  GraphicString     => [ asn_encode_tag(ASN_UNIVERSAL | 25), opSTRING ],
  VisibleString     => [ asn_encode_tag(ASN_UNIVERSAL | 26), opSTRING ],
  ISO646String      => [ asn_encode_tag(ASN_UNIVERSAL | 26), opSTRING ],
  GeneralString     => [ asn_encode_tag(ASN_UNIVERSAL | 27), opSTRING ],
  CharacterString   => [ asn_encode_tag(ASN_UNIVERSAL | 28), opSTRING ],
  UniversalString   => [ asn_encode_tag(ASN_UNIVERSAL | 28), opSTRING ],
  BMPString         => [ asn_encode_tag(ASN_UNIVERSAL | 30), opSTRING ],

  CHOICE => [ '', opCHOICE ],
  ANY    => [ '', opANY ],
);

;# Given an OP, wrap it in a SEQUENCE

sub explicit {
  my $op = shift;
  my @seq = @$op;

  @seq[cTYPE,cCHILD,cVAR,cLOOP] = ('SEQUENCE',[$op],undef,undef);
  @{$op}[cTAG,cOPT] = ();

  \@seq;
}

# 74 "y.tab.pl"

sub constWORD () { 1 }
sub constCLASS () { 2 }
sub constSEQUENCE () { 3 }
sub constSET () { 4 }
sub constCHOICE () { 5 }
sub constOF () { 6 }
sub constIMPLICIT () { 7 }
sub constEXPLICIT () { 8 }
sub constOPTIONAL () { 9 }
sub constLBRACE () { 10 }
sub constRBRACE () { 11 }
sub constCOMMA () { 12 }
sub constANY () { 13 }
sub constASSIGN () { 14 }
sub constNUMBER () { 15 }
sub constENUM () { 16 }
sub constCOMPONENTS () { 17 }
sub constPOSTRBRACE () { 18 }
sub constDEFINED () { 19 }
sub constBY () { 20 }
sub constYYERRCODE () { 256 }
my @yylhs = (                                               -1,
    0,    0,    2,    2,    3,    3,    6,    6,    6,    6,
    8,   13,   13,   12,   14,   14,   14,    9,    9,    9,
   10,   18,   18,   18,   18,   18,   19,   19,   11,   16,
   16,   20,   20,   20,   21,    1,    1,   22,   22,   22,
   24,   24,   24,   24,   23,   23,   23,   15,   15,    4,
    4,    5,    5,    5,   17,   17,   25,    7,    7,
);
my @yylen = (                                                2,
    1,    1,    3,    4,    4,    1,    1,    1,    1,    1,
    3,    1,    1,    6,    1,    1,    1,    4,    4,    4,
    4,    1,    1,    1,    2,    1,    0,    3,    1,    1,
    2,    1,    3,    3,    4,    1,    2,    1,    3,    3,
    2,    1,    1,    1,    4,    1,    3,    0,    1,    0,
    1,    0,    1,    1,    1,    3,    2,    0,    1,
);
my @yydefred = (                                             0,
    0,   51,    0,    0,    1,    0,    0,   46,    0,   38,
    0,    0,    0,    0,   54,   53,    0,    0,    0,    3,
    0,    6,    0,   11,    0,    0,    0,    0,   47,    0,
   39,   40,    0,   22,    0,    0,    0,    0,   44,   42,
    0,   43,    0,   29,   45,    4,    0,    0,    0,    0,
    7,    8,    9,   10,    0,   25,    0,   49,   41,    0,
    0,    0,    0,    0,    0,   32,   59,    5,    0,    0,
    0,   55,    0,   18,   19,    0,   20,    0,    0,   28,
   57,   21,    0,    0,    0,   34,   33,   56,    0,    0,
   17,   15,   16,    0,   35,   14,
);
my @yydgoto = (                                              4,
    5,    6,   20,    7,   17,   50,   68,    8,   51,   52,
   53,   54,   43,   94,   59,   64,   71,   44,   56,   65,
   66,    9,   10,   45,   72,
);
my @yysindex = (                                             7,
    9,    0,   12,    0,    0,   19,   51,    0,   34,    0,
   75,   51,   31,   -1,    0,    0,   90,   55,   55,    0,
   51,    0,  114,    0,   75,   26,   53,   61,    0,   77,
    0,    0,  114,    0,   26,   53,   64,   76,    0,    0,
   89,    0,   96,    0,    0,    0,   55,   55,  111,  103,
    0,    0,    0,    0,   94,    0,  130,    0,    0,   77,
  122,  128,   77,  139,   78,    0,    0,    0,  154,  143,
   33,    0,   51,    0,    0,   51,    0,  111,  111,    0,
    0,    0,  130,  119,  114,    0,    0,    0,   26,   53,
    0,    0,    0,   89,    0,    0,
);
my @yyrindex = (                                           149,
  100,    0,    0,    0,    0,  159,  106,    0,   39,    0,
  100,  133,    0,    0,    0,    0,    0,  149,  140,    0,
  133,    0,    0,    0,  100,    0,    0,    0,    0,  100,
    0,    0,    0,    0,   16,   29,   42,   69,    0,    0,
   37,    0,    0,    0,    0,    0,  149,  149,    0,  125,
    0,    0,    0,    0,    0,    0,    0,    0,    0,  100,
    0,    0,  100,    0,  150,    0,    0,    0,    0,    0,
    0,    0,  133,    0,    0,  133,    0,    0,  151,    0,
    0,    0,    0,    0,    0,    0,    0,    0,   73,   88,
    0,    0,    0,    3,    0,    0,
);
my @yygindex = (                                             0,
   28,    0,  135,    1,  -11,   79,    0,    8,  -17,  -18,
  -16,  142,    0,    0,   72,    0,    0,    0,    0,    0,
   50,    0,  123,    0,   80,
);
sub constYYTABLESIZE () { 166 }
my @yytable = (                                             29,
   23,   12,   48,   48,   40,   39,   41,    1,    2,   33,
    2,   21,   25,   48,   48,   23,   23,   13,   22,   14,
   48,   12,   11,    3,   23,   21,   23,   23,   24,   24,
   12,   24,   22,   23,   13,   47,   48,   24,   36,   24,
   24,   27,   27,   82,   83,   18,   24,   48,   48,   36,
   27,   19,   27,   27,   48,   30,    2,   15,   16,   27,
   73,   84,   48,   76,   85,   92,   91,   93,   26,   26,
   49,    3,   23,   23,   61,   62,    2,   26,    2,   26,
   26,   23,   55,   23,   23,   57,   26,   24,   24,   78,
   23,    3,   26,   27,   28,   79,   24,   58,   24,   24,
   50,   60,   50,   50,   50,   24,   50,   50,   52,   52,
   52,   63,   50,   69,   34,   50,   35,   36,   28,   34,
   67,   89,   90,   28,   58,   58,   37,   86,   87,   38,
   70,   37,   74,   52,   38,   52,   52,   52,   75,   37,
   31,   32,   50,   50,   50,   52,   50,   50,   52,   77,
   37,   50,   50,   50,   80,   50,   50,   81,    2,   46,
   30,   31,   88,   95,   42,   96,
);
my @yycheck = (                                             17,
   12,    1,    0,    1,   23,   23,   23,    1,    2,   21,
    2,   11,   14,   11,   12,    0,    1,    6,   11,    1,
   18,    6,   14,   17,    9,   25,   11,   12,    0,    1,
   30,    1,   25,   18,    6,   10,    0,    9,    0,   11,
   12,    0,    1,   11,   12,   12,   18,   11,   12,   11,
    9,   18,   11,   12,   18,    1,    2,    7,    8,   18,
   60,   73,   10,   63,   76,   84,   84,   84,    0,    1,
   10,   17,    0,    1,   47,   48,    2,    9,    2,   11,
   12,    9,   19,   11,   12,   10,   18,    0,    1,   12,
   18,   17,    3,    4,    5,   18,    9,    9,   11,   12,
    1,    6,    3,    4,    5,   18,    7,    8,    3,    4,
    5,    1,   13,   20,    1,   16,    3,    4,    5,    1,
   18,    3,    4,    5,    0,    1,   13,   78,   79,   16,
    1,   13,   11,    1,   16,    3,    4,    5,   11,    0,
   18,   19,    3,    4,    5,   13,    7,    8,   16,   11,
   11,    3,    4,    5,    1,    7,    8,   15,    0,   25,
   11,   11,   83,   85,   23,   94,
);
sub constYYFINAL () { 4 }



sub constYYMAXTOKEN () { 20 }
# 270 "y.tab.pl"

sub yyclearin { $yychar = -1; }
sub yyerrok { $yyerrflag = 0; }
sub YYERROR { ++$yynerrs; &yy_err_recover; }
sub yy_err_recover
{
  if ($yyerrflag < 3)
  {
    $yyerrflag = 3;
    while (1)
    {
      if (($yyn = $yysindex[$yyss[$yyssp]]) && 
          ($yyn += constYYERRCODE()) >= 0 && 
          $yyn <= $#yycheck && $yycheck[$yyn] == constYYERRCODE())
      {




        $yyss[++$yyssp] = $yystate = $yytable[$yyn];
        $yyvs[++$yyvsp] = $yylval;
        next yyloop;
      }
      else
      {




        return(1) if $yyssp <= 0;
        --$yyssp;
        --$yyvsp;
      }
    }
  }
  else
  {
    return (1) if $yychar == 0;
# 321 "y.tab.pl"

    $yychar = -1;
    next yyloop;
  }
0;
} # yy_err_recover

sub yyparse
{

  if ($yys = $ENV{'YYDEBUG'})
  {
    $yydebug = int($1) if $yys =~ /^(\d)/;
  }


  $yynerrs = 0;
  $yyerrflag = 0;
  $yychar = (-1);

  $yyssp = 0;
  $yyvsp = 0;
  $yyss[$yyssp] = $yystate = 0;

yyloop: while(1)
  {
    yyreduce: {
      last yyreduce if ($yyn = $yydefred[$yystate]);
      if ($yychar < 0)
      {
        if (($yychar = &yylex) < 0) { $yychar = 0; }
# 360 "y.tab.pl"

      }
      if (($yyn = $yysindex[$yystate]) && ($yyn += $yychar) >= 0 &&
              $yyn <= $#yycheck && $yycheck[$yyn] == $yychar)
      {




        $yyss[++$yyssp] = $yystate = $yytable[$yyn];
        $yyvs[++$yyvsp] = $yylval;
        $yychar = (-1);
        --$yyerrflag if $yyerrflag > 0;
        next yyloop;
      }
      if (($yyn = $yyrindex[$yystate]) && ($yyn += $yychar) >= 0 &&
            $yyn <= $#yycheck && $yycheck[$yyn] == $yychar)
      {
        $yyn = $yytable[$yyn];
        last yyreduce;
      }
      if (! $yyerrflag) {
        &yyerror('syntax error');
        ++$yynerrs;
      }
      return undef if &yy_err_recover;
    } # yyreduce




    $yym = $yylen[$yyn];
    $yyval = $yyvs[$yyvsp+1-$yym];
    switch:
    {
my $label = "State$yyn";
goto $label if exists $yystate{$label};
last switch;
State1: {
# 96 "parser.y"

{ $yyval = { '' => $yyvs[$yyvsp-0] }; 
last switch;
} }
State3: {
# 101 "parser.y"

{
		  $yyval = { $yyvs[$yyvsp-2], [$yyvs[$yyvsp-0]] };
		
last switch;
} }
State4: {
# 105 "parser.y"

{
		  $yyval=$yyvs[$yyvsp-3];
		  $yyval->{$yyvs[$yyvsp-2]} = [$yyvs[$yyvsp-0]];
		
last switch;
} }
State5: {
# 112 "parser.y"

{
		  $yyvs[$yyvsp-1]->[cTAG] = $yyvs[$yyvsp-3];
		  $yyval = $yyvs[$yyvsp-2] ? explicit($yyvs[$yyvsp-1]) : $yyvs[$yyvsp-1];
		
last switch;
} }
State11: {
# 126 "parser.y"

{
		  @{$yyval = []}[cTYPE,cCHILD] = ('COMPONENTS', $yyvs[$yyvsp-0]);
		
last switch;
} }
State14: {
# 136 "parser.y"

{
		  $yyvs[$yyvsp-1]->[cTAG] = $yyvs[$yyvsp-3];
		  @{$yyval = []}[cTYPE,cCHILD,cLOOP,cOPT] = ($yyvs[$yyvsp-5], [$yyvs[$yyvsp-1]], 1, $yyvs[$yyvsp-0]);
		  $yyval = explicit($yyval) if $yyvs[$yyvsp-2];
		
last switch;
} }
State18: {
# 149 "parser.y"

{
		  @{$yyval = []}[cTYPE,cCHILD] = ('SEQUENCE', $yyvs[$yyvsp-1]);
		
last switch;
} }
State19: {
# 153 "parser.y"

{
		  @{$yyval = []}[cTYPE,cCHILD] = ('SET', $yyvs[$yyvsp-1]);
		
last switch;
} }
State20: {
# 157 "parser.y"

{
		  @{$yyval = []}[cTYPE,cCHILD] = ('CHOICE', $yyvs[$yyvsp-1]);
		
last switch;
} }
State21: {
# 163 "parser.y"

{
		  @{$yyval = []}[cTYPE] = ('ENUM');
		
last switch;
} }
State22: {
# 168 "parser.y"

{ @{$yyval = []}[cTYPE] = $yyvs[$yyvsp-0]; 
last switch;
} }
State23: {
# 169 "parser.y"

{ @{$yyval = []}[cTYPE] = $yyvs[$yyvsp-0]; 
last switch;
} }
State24: {
# 170 "parser.y"

{ @{$yyval = []}[cTYPE] = $yyvs[$yyvsp-0]; 
last switch;
} }
State25: {
# 172 "parser.y"

{
		  @{$yyval = []}[cTYPE,cCHILD,cDEFINE] = ('ANY',undef,$yyvs[$yyvsp-0]);
		
last switch;
} }
State26: {
# 175 "parser.y"

{ @{$yyval = []}[cTYPE] = $yyvs[$yyvsp-0]; 
last switch;
} }
State27: {
# 178 "parser.y"

{ $yyval=undef; 
last switch;
} }
State28: {
# 179 "parser.y"

{ $yyval=$yyvs[$yyvsp-0]; 
last switch;
} }
State30: {
# 185 "parser.y"

{ $yyval = $yyvs[$yyvsp-0]; 
last switch;
} }
State31: {
# 186 "parser.y"

{ $yyval = $yyvs[$yyvsp-1]; 
last switch;
} }
State32: {
# 190 "parser.y"

{
		  $yyval = [ $yyvs[$yyvsp-0] ];
		
last switch;
} }
State33: {
# 194 "parser.y"

{
		  push @{$yyval=$yyvs[$yyvsp-2]}, $yyvs[$yyvsp-0];
		
last switch;
} }
State34: {
# 198 "parser.y"

{
		  push @{$yyval=$yyvs[$yyvsp-2]}, $yyvs[$yyvsp-0];
		
last switch;
} }
State35: {
# 204 "parser.y"

{
		  @{$yyval=$yyvs[$yyvsp-0]}[cVAR,cTAG] = ($yyvs[$yyvsp-3],$yyvs[$yyvsp-2]);
		  $yyval = explicit($yyval) if $yyvs[$yyvsp-1];
		
last switch;
} }
State36: {
# 211 "parser.y"

{ $yyval = $yyvs[$yyvsp-0]; 
last switch;
} }
State37: {
# 212 "parser.y"

{ $yyval = $yyvs[$yyvsp-1]; 
last switch;
} }
State38: {
# 216 "parser.y"

{
		  $yyval = [ $yyvs[$yyvsp-0] ];
		
last switch;
} }
State39: {
# 220 "parser.y"

{
		  push @{$yyval=$yyvs[$yyvsp-2]}, $yyvs[$yyvsp-0];
		
last switch;
} }
State40: {
# 224 "parser.y"

{
		  push @{$yyval=$yyvs[$yyvsp-2]}, $yyvs[$yyvsp-0];
		
last switch;
} }
State41: {
# 230 "parser.y"

{
		  @{$yyval=$yyvs[$yyvsp-1]}[cOPT] = ($yyvs[$yyvsp-0]);
		
last switch;
} }
State45: {
# 239 "parser.y"

{
		  @{$yyval=$yyvs[$yyvsp-0]}[cVAR,cTAG] = ($yyvs[$yyvsp-3],$yyvs[$yyvsp-2]);
		  $yyval->[cOPT] = $yyvs[$yyvsp-3] if $yyval->[cOPT];
		  $yyval = explicit($yyval) if $yyvs[$yyvsp-1];
		
last switch;
} }
State47: {
# 246 "parser.y"

{
		  @{$yyval=$yyvs[$yyvsp-0]}[cTAG] = ($yyvs[$yyvsp-2]);
		  $yyval = explicit($yyval) if $yyvs[$yyvsp-1];
		
last switch;
} }
State48: {
# 252 "parser.y"

{ $yyval = undef; 
last switch;
} }
State49: {
# 253 "parser.y"

{ $yyval = 1;     
last switch;
} }
State50: {
# 257 "parser.y"

{ $yyval = undef; 
last switch;
} }
State52: {
# 261 "parser.y"

{ $yyval = undef; 
last switch;
} }
State53: {
# 262 "parser.y"

{ $yyval = 1;     
last switch;
} }
State54: {
# 263 "parser.y"

{ $yyval = 0;     
last switch;
} }
State55: {
# 266 "parser.y"

{
last switch;
} }
State56: {
# 267 "parser.y"

{
last switch;
} }
State57: {
# 270 "parser.y"

{
last switch;
} }
State58: {
# 273 "parser.y"

{
last switch;
} }
State59: {
# 274 "parser.y"

{
last switch;
} }
# 653 "y.tab.pl"

    } # switch
    $yyssp -= $yym;
    $yystate = $yyss[$yyssp];
    $yyvsp -= $yym;
    $yym = $yylhs[$yyn];
    if ($yystate == 0 && $yym == 0)
    {




      $yystate = constYYFINAL();
      $yyss[++$yyssp] = constYYFINAL();
      $yyvs[++$yyvsp] = $yyval;
      if ($yychar < 0)
      {
        if (($yychar = &yylex) < 0) { $yychar = 0; }
# 679 "y.tab.pl"

      }
      return $yyvs[$yyvsp] if $yychar == 0;
      next yyloop;
    }
    if (($yyn = $yygindex[$yym]) && ($yyn += $yystate) >= 0 &&
        $yyn <= $#yycheck && $yycheck[$yyn] == $yystate)
    {
        $yystate = $yytable[$yyn];
    } else {
        $yystate = $yydgoto[$yym];
    }




    $yyss[++$yyssp] = $yystate;
    $yyvs[++$yyvsp] = $yyval;
  } # yyloop
} # yyparse
# 278 "parser.y"


my %reserved = (
  'OPTIONAL' 	=> constOPTIONAL(),
  'CHOICE' 	=> constCHOICE(),
  'OF' 		=> constOF(),
  'IMPLICIT' 	=> constIMPLICIT(),
  'EXPLICIT' 	=> constEXPLICIT(),
  'SEQUENCE'    => constSEQUENCE(),
  'SET'         => constSET(),
  'ANY'         => constANY(),
  'ENUM'        => constENUM(),
  'ENUMERATED'  => constENUM(),
  'COMPONENTS'  => constCOMPONENTS(),
  '{'		=> constLBRACE(),
  '}'		=> constRBRACE(),
  ','		=> constCOMMA(),
  '::='         => constASSIGN(),
  'DEFINED'     => constDEFINED(),
  'BY'		=> constBY()
);

my $reserved = join("|", reverse sort grep { /\w/ } keys %reserved);

my %tag_class = (
  APPLICATION => ASN_APPLICATION,
  UNIVERSAL   => ASN_UNIVERSAL,
  PRIVATE     => ASN_PRIVATE,
  CONTEXT     => ASN_CONTEXT,
  ''	      => ASN_CONTEXT # if not specified, its CONTEXT
);

;##
;## This is NOT thread safe !!!!!!
;##

my $pos;
my $last_pos;
my @stacked;

sub parse {
  local(*asn) = \($_[0]);
  ($pos,$last_pos,@stacked) = ();

  eval {
    local $SIG{__DIE__};
    compile(verify(yyparse()));
  }
}

sub compile_one {
  my $tree = shift;
  my $ops = shift;
  my $name = shift;
  foreach my $op (@$ops) {
    next unless ref($op) eq 'ARRAY';
    bless $op;
    my $type = $op->[cTYPE];
    if (exists $base_type{$type}) {
      $op->[cTYPE] = $base_type{$type}->[1];
      $op->[cTAG] = defined($op->[cTAG]) ? asn_encode_tag($op->[cTAG]): $base_type{$type}->[0];
    }
    else {
      die "Unknown type '$type'\n" unless exists $tree->{$type};
      my $ref = compile_one(
		  $tree,
		  $tree->{$type},
		  defined($op->[cVAR]) ? $name . "." . $op->[cVAR] : $name
		);
      if (defined($op->[cTAG]) && $ref->[0][cTYPE] == opCHOICE) {
        @{$op}[cTYPE,cCHILD] = (opSEQUENCE,$ref);
      }
      else {
        @{$op}[cTYPE,cCHILD,cLOOP] = @{$ref->[0]}[cTYPE,cCHILD,cLOOP];
      }
      $op->[cTAG] = defined($op->[cTAG]) ? asn_encode_tag($op->[cTAG]): $ref->[0][cTAG];
    }
    $op->[cTAG] |= chr(ASN_CONSTRUCTOR)
      if length $op->[cTAG] && ($op->[cTYPE] == opSET || $op->[cTYPE] == opSEQUENCE);

    if ($op->[cCHILD]) {
      ;# If we have children we are one of
      ;#  opSET opSEQUENCE opCHOICE

      compile_one($tree, $op->[cCHILD], defined($op->[cVAR]) ? $name . "." . $op->[cVAR] : $name);

      ;# If a CHOICE is given a tag, then it must be EXPLICIT
      if ($op->[cTYPE] == opCHOICE && defined($op->[cTAG]) && length($op->[cTAG])) {
	$op = bless explicit($op);
	$op->[cTYPE] = opSEQUENCE;
      }

      if ( @{$op->[cCHILD]} > 1) {
        ;#if ($op->[cTYPE] != opSEQUENCE) {
        ;# Here we need to flatten CHOICEs and check that SET and CHOICE
        ;# do not contain duplicate tags
        ;#}
	if ($op->[cTYPE] == opSET) {
	  ;# In case we do CER encoding we order the SET elements by thier tags
	  my @tags = map { 
	    length($_->[cTAG])
		? $_->[cTAG]
		: $_->[cTYPE] == opCHOICE
			? (sort map { $_->[cTAG] } $_->[cCHILD])[0]
			: ''
	  } @{$op->[cCHILD]};
	  @{$op->[cCHILD]} = @{$op->[cCHILD]}[sort { $tags[$a] cmp $tags[$b] } 0..$#tags];
	}
      }
      else {
	;# A SET of one element can be treated the same as a SEQUENCE
	$op->[cTYPE] = opSEQUENCE if $op->[cTYPE] == opSET;
      }
    }
  }
  $ops;
}

sub compile {
  my $tree = shift;

  ;# The tree should be valid enough to be able to
  ;#  - resolve references
  ;#  - encode tags
  ;#  - verify CHOICEs do not contain duplicate tags

  ;# once references have been resolved, and also due to
  ;# flattening of COMPONENTS, it is possible for an op
  ;# to appear in multiple places. So once an op is
  ;# compiled we bless it. This ensure we dont try to
  ;# compile it again.

  while(my($k,$v) = each %$tree) {
    compile_one($tree,$v,$k);
  }

  $tree;
}

sub verify {
  my $tree = shift or return;
  my $err = "";

  ;# Well it parsed correctly, now we
  ;#  - check references exist
  ;#  - flatten COMPONENTS OF (checking for loops)
  ;#  - check for duplicate var names

  while(my($name,$ops) = each %$tree) {
    my $stash = {};
    my @scope = ();
    my $path = "";
    my $idx = 0;

    while($ops) {
      if ($idx < @$ops) {
	my $op = $ops->[$idx++];
	my $var;
	if (defined ($var = $op->[cVAR])) {
	  
	  $err .= "$name: $path.$var used multiple times\n"
	    if $stash->{$var}++;

	}
	if (defined $op->[cCHILD]) {
	  if (ref $op->[cCHILD]) {
	    push @scope, [$stash, $path, $ops, $idx];
	    if (defined $var) {
	      $stash = {};
	      $path .= "." . $var;
	    }
	    $idx = 0;
	    $ops = $op->[cCHILD];
	  }
	  elsif ($op->[cTYPE] eq 'COMPONENTS') {
	    splice(@$ops,--$idx,1,expand_ops($tree, $op->[cCHILD]));
	  }
          else {
	    die "Internal error\n";
          }
	}
      }
      else {
	my $s = pop @scope
	  or last;
	($stash,$path,$ops,$idx) = @$s;
      }
    }
  }
  die $err if length $err;
  $tree;
}

sub expand_ops {
  my $tree = shift;
  my $want = shift;
  my $seen = shift || { };
  
  die "COMPONENTS OF loop $want\n" if $seen->{$want}++;
  die "Undefined macro $want\n" unless exists $tree->{$want};
  my $ops = $tree->{$want};
  die "Bad macro for COMPUNENTS OF '$want'\n"
    unless @$ops == 1
        && ($ops->[0][cTYPE] eq 'SEQUENCE' || $ops->[0][cTYPE] eq 'SET')
        && ref $ops->[0][cCHILD];
  $ops = $ops->[0][cCHILD];
  for(my $idx = 0 ; $idx < @$ops ; ) {
    my $op = $ops->[$idx++];
    if ($op->[cTYPE] eq 'COMPONENTS') {
      splice(@$ops,--$idx,1,expand_ops($tree, $op->[cCHILD], $seen));
    }
  }

  @$ops;
}

sub _yylex {
  my $ret = &_yylex;
  warn $ret;
  $ret;
}

sub yylex {
  return shift @stacked if @stacked;

  while ($asn =~ /\G(?:
	  (\s+|--[^\n]*)
	|
	  ([,{}]|::=)
	|
	  ($reserved)\b
	|
	  (
	    (?:OCTET|BIT)\s+STRING
	   |
	    OBJECT\s+IDENTIFIER
	   |
	    RELATIVE-OID
	  )\b
	|
	  (\w+(?:-\w+)*)
	|
	    \[\s*
	  (
	   (?:(?:APPLICATION|PRIVATE|UNIVERSAL|CONTEXT)\s+)?
	   \d+
          )
	    \s*\]
	|
	  \((\d+)\)
	)/sxgo
  ) {

    ($last_pos,$pos) = ($pos,pos($asn));

    next if defined $1; # comment or whitespace

    if (defined $2 or defined $3) {
      #A comma is not required after a '}' so to aid the
      #parser we insert a fake token after any '}'
      push @stacked, constPOSTRBRACE() if defined $2 and $+ eq '}';

      return $reserved{$yylval = $+};
    }

    if (defined $4) {
      ($yylval = $+) =~ s/\s+/_/g;
      return constWORD();
    }

    if (defined $5) {
      $yylval = $+;
      return constWORD();
    }

    if (defined $6) {
      my($class,$num) = ($+ =~ /^([A-Z]*)\s*(\d+)$/);
      $yylval = asn_tag($tag_class{$class}, $num); 
      return constCLASS();
    }

    if (defined $7) {
      $yylval = $+;
      return constNUMBER();
    }

    die "Internal error\n";

  }

  die "Parse error before ",substr($asn,$pos,40),"\n"
    unless $pos == length($asn);

  0
}

sub yyerror {
  die @_," ",substr($asn,$last_pos,40),"\n";
}

1;

# 1001 "y.tab.pl"

%yystate = ('State11','','State30','','State31','','State50','','State32',
'','State14','','State33','','State52','','State34','','State53','',
'State35','','State54','','State36','','State18','','State55','','State37',
'','State19','','State56','','State38','','State57','','State39','',
'State58','','State59','','State1','','State3','','State4','','State5','',
'State20','','State21','','State22','','State40','','State23','','State41',
'','State24','','State25','','State26','','State27','','State45','',
'State28','','State47','','State48','','State49','');

1;
