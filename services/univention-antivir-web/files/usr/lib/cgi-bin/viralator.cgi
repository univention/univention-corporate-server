#!/usr/bin/perl -T

# Viralator
# Author Info:    viralator@loddington.com Copyright 2001 Duncan Hall
# changes from 0.8->0.9 Open IT S.r.l. (http://www.openit.it):
#  - Diaolin (diaolin@diaolin.com)
#  - Marco Ciampa (ciampix@libero.it)
# Changes from 0.9pre2.1:
#  - Alceu Rodrigues de Freitas Junior (glasswalk3r@yahoo.com.br)
#
# This script is licenced under the GPL. But if you feel the need to
# contribute please send RAM from one of your co-workers machines!
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#
# There you go you have been warned. Dont hold me responsible for anything
# that goes wrong with this script or any damage or security
# breach that is caused by this script. I dont know your system and it is
# up to you to make sure it is secure and stable. Just dont hold
# me responsible for anything.
#

# Todo:
# remove duplicated code by creating new functions

###############################################################################
####                                                                       ####
#### You should not need to change anything from here on in, but if you do ####
#### I have added more comments than you can poke a stick at               ####
####                                                                       ####
###############################################################################


##########################
# INITIALIZING MODULES
##########################

use CGI;
use warnings;
use strict;
use CGI::Carp;
use LWP 5.66;
use URI::Split qw (uri_split);
use sigtrap 'handler' => \&terminated, 'normal-signals';
use Digest::MD5 qw(md5_base64);
use IPC::Open3;

# generate just one header per document
{
    no warnings;
    $CGI::HEADER_ONCE = 1;
# security settings (upload is disable!)
    $CGI::POST_MAX = 1024 * 100;
    $CGI::DISABLE_UPLOADS = 1;

}
#+++#
#+++#


##################
# CONFIGURATION
##################

open(CONFIG,"</etc/viralator/viralator.conf")
    || die('Error opening the config file','Cannot open /etc/viralator/viralator.conf');

my @config;

while (<CONFIG>) {
#jumping no interesting lines
    next if $_ =~ /#/;
    chomp;
    next unless ($_ =~ /\-\>/);
    my @temp = split(/\-\>/,$_);

#removes spaces at the begging and at the end of each string
    foreach(@temp) {

        s/^\s+//;
        s/\s+$//;

    }

    $temp[1] = 'X' unless (defined($temp[1]));
    push (@config,@temp);
}

close(CONFIG);

my %config = @config;
undef(@config);

# checking the values

my @test = qw(default_language
              antivirus
              scannerpath
              virusscanner
              viruscmd
              alert
	      secret
              downloads
              downloadsdir);

foreach (@test) {
    die("No directive $_ declared in /etc/viralator/viralator.conf") unless (exists $config{$_});
}

foreach (@test) {
    die("No value on $_ in /etc/viralator/viralator.conf") if ($config{$_} eq 'X');
}

undef (@test);

#reading language file

open(LANG,"</etc/viralator/languages/$config{default_language}")
  || die "Cannot read the default language file $config{default_language} at /etc/viralator/language\n";

my @lang;

while (<LANG>) {
#jumping no interesting lines
    next if $_ =~ /#/;
    chomp;
    next unless ($_ =~ /=/);
# cleaning up values
    $_ =~ s/\s+=\s+/=/;
    my @temp = split(/=/,$_);
    $temp[1] = 'X' unless (defined($temp[1]));
    push (@lang,@temp);
}

my %lang = @lang;
undef(@lang);

#######################
# START OF THE PROGRAM
#######################


# VERSION
my $version = 'Viralator 0.9.2.6';

my $viralator = new CGI;

#testing the download repository
test_repository("$config{downloads}");

#the name of this script plus path
my $scriptname = $viralator->script_name();

#The address of the server this script lives on
my $servername = $viralator->server_name();

#The user IP address connected to the proxy
my $client = $viralator->remote_addr();

# date and ugly date functions rewritten to fix some tainting problems
my $date = scalar localtime;

#a really big number for our popup!
my $uglydate = time;

# the sum of data length read by LWP file fetcher
my $datasum = 0;

# how much data a "bar" represents
use constant BAR => '<td bgcolor="#FF3333" width=7>&nbsp;</td>';
my $bar_value = 0;
my $count_bar = 0;

my $site = 'http://viralator.sourceforge.net';
my $requestpage = $viralator->referer;

# Step 1 Pick up the URL of the file from Apache ENV and the page it came from

#if we do not go any param, this means problems! Probaly
# the redirector program is not configurated correctly:
# Viralator should receive at least the "url" parameter

unless ( $viralator->param() ) {

    error('error',"$lang{noparam}",'No paramaters received. Please check your redirection program.');

# at least one, we're fine
} else {

# very first call, from the redirector
    unless ($viralator->param('action')) {

        my $url = $viralator->param('url');
        test_param('url',"$url");

        print $viralator->header(-expires => 'now');
        print $viralator->start_html(-title   =>"$version",
                                     -site    =>"$site",
                                     -BGCOLOR =>'#FFFFFF'
                                    );
        load_css();

        print $viralator->h3($lang{presentation});
        print "<P>$lang{startclick} ";
        print $viralator->submit(-value   => "$lang{start}",
                                 -onClick => 'WinOpen()');
	print '</P>';

        unless ( defined($requestpage) and ($requestpage ne '') ) {

            print $viralator->p("$lang{requestpage}
                               <INPUT TYPE=\"button\" VALUE=\"$lang{here}\" onClick=\"history.go(-1);\">");
        } else {

# extracting only the main url from referer information
	    my @main_page = uri_split($requestpage);
            print $viralator->p($lang{meanwhile});

print <<BLOCK;
<ul>
<li>$lang{requestpage} <a href="$requestpage">$lang{here}</a>.</li>
<li>$lang{mainpage} <a href="$main_page[0]://$main_page[1]">$lang{here}</a>.</li>
</ul>
BLOCK
        }

#################################
# Fake sites
#
# on many sites it can be found an ugly problem due to the fake URL passed
# from remote sites, the result is a strange \ .............
# If you know anything about this sites and you want to permit your users
# downloading anyway, you can put a abortregexi into squirm.patterns like this
# this example is a site that has convinced us to write this workaround
# www.powerarchiver.com
#
# abortregexi (^http://www\.powerachiver\.com/.*)
#
# in this case all your users can download from powerarchiver without virus
# scanning :-(
##################################

        if ($url=~/\s*\?\s*/ | $url=~/\s*\\\s*/) {

print <<BLOCK;
<SCRIPT LANGUAGE="JAVASCRIPT">
<!--
function WinOpen() {
open("http://$servername$scriptname?action=errpop","$uglydate","width=600,height=200,scrollbars=1,resize=no");
}
//-->
</SCRIPT>
BLOCK

        } else {

# Lets start by returning the user to the page they found the file on and
# launching a pop up window
# The pop up windows should have some useful info in it about whats going on.


print <<BLOCK;
<SCRIPT LANGUAGE="JAVASCRIPT">
<!--
function WinOpen() {
open("http://$servername$scriptname?action=popup&fileurl=$url","$uglydate","width=600,height=400,scrollbars=1,resize=no");
}
//-->
</SCRIPT>
BLOCK
        }

        print $viralator->end_html;

# ACTION !
# ok, we got action call and maybe more parameters

    } else {

        my $action  = $viralator->param('action');
        test_param('action',"$action");

# error in the file request
        if ($action eq 'errpop') {

            print $viralator->header(-expires => 'now');
            print $viralator->start_html(-title=>"$version",
                                         -site=>"$site",
                                         -BGCOLOR=>'#FFFFFF'
                                        );
            load_css();
            print $viralator->start_center;
            print $viralator->h1($lang{dinerr});
	    print $viralator->p($lang{urlerr});
	    print $viralator->p($lang{admincall});
            print $viralator->start_form;

            print $viralator->submit(-value   => "$lang{wclosew}",
                                     -onClick => 'window.close()');

            print $viralator->endform;
            print $viralator->end_center;
            print $viralator->end_html;

# Step 2
# downloading the file
        } elsif ($action eq 'popup') {

            my $fileurl = $viralator->param('fileurl');
	    my $result;
	    my $username;
	    my $password;

# fileurl should be tested as well against taint values

	    #+++#
            if ($fileurl =~ /(^[\w\.\-\_\?\~\+\:\/\s]+$)/) {
                $fileurl = $1;

            } else {

                error ("$lang{invalid_char} $fileurl","$lang{invalid_char} $fileurl");

	    }

            my $filename = parse_fileurl($fileurl);

#we use these later if a password is needed
            $username = $viralator->param('username') if ($viralator->param('username'));
            $password = $viralator->param('password') if ($viralator->param('password'));

            $| = 1;

            print $viralator->header(-expires => 'now');
            print $viralator->start_html(-title   =>"$version",
                                         -site    =>"$site",
                                         -BGCOLOR =>'#FFFFFF',
                                         -onload  =>'clearInterval(intervalID1);');
            load_css();

print <<BLOCK;
<SCRIPT LANGUAGE="JavaScript">
<!--
function checkPageBase() {
    window.scrollBy(0,1000);
}
var intervalID1 = setInterval("checkPageBase()",10);
//-->
</script>
BLOCK

            $result = get_file($username,$password,$fileurl,$filename);

	    CHECKIT: {

	        if ($result == 0) {

                    print $viralator->p("$lang{download_error}");
                    print '<center>';
                    print $viralator->submit(-value   => "$lang{wclosew}",
                                             -onClick => 'window.close()');
                    print '</center>';
                    print $viralator->end_html;
                    last CHECKIT;

		}


		if ($result == 2) {

                    print $viralator->end_html;
                    last CHECKIT;

		}

		if ($result == 1) {

# calling the antivirus program
                    cleanit($fileurl,$filename);

#If $filename exists in the download dir then it is clean or has been
#cleaned (depending on your scanner options),if not then the virus scanner
#has renamed or deleted the file (depending on your scanner options) and
#it is infected

# We check to see if the filename is greater than 1 character long

                    my $filenamesize = length($filename);

                    if ( (-e "$config{downloads}/$filename") && ($filenamesize > 1) )  {

# Check $filename for spaces or odd charaxters
                        my $original_filename = $filename;

# This rewebifies the file name
                        $filename =~ s/([^a-zA-Z0-9_\+\.\-])/"%".unpack("H*",$1)/ge;
                        print $viralator->p("$lang{oktodown}");

print <<BLOCK;
<META HTTP-EQUIV="Refresh" CONTENT="1; URL=$config{downloadsdir}/$filename">
<strong>$lang{oncedown}</strong>
BLOCK

# Form to close download window
                        print $viralator->start_form(-method=>'post',
                                                     -action=>"http://$servername/$scriptname");

#changing the value of the parameter 'action'
                        $viralator->param(-name=>'action',-value=>'delete');

                        print $viralator->hidden(-name    => 'action',
                                                 -default => 'delete');

                        print $viralator->hidden(-name    => 'filename',
                                                 -default => "$original_filename");

      	                my $delete_digest = md5_base64($filename,$config{secret});

	                print $viralator->hidden(-name => 'digest',
	                                         -default => "$delete_digest");

                        print '<p align="center">';
                        print $viralator->submit(-name => "$lang{wclosew}");
                        print '</p>';

                        print $viralator->end_form;

#added a Javascript function to make the button being visible without using the lift bar
# thanks to Guillaume Girard (cyberoux@wanadoo.fr) for the tip
                        print '<SCRIPT LANGUAGE="JavaScript">window.scrollBy(0,1000);</script>';


                    } else {

                        print $viralator->h2("$lang{vfounddl}");
                        error('warning',"$lang{fileremoved}",
		              "Problem with request made by $client: file does not exists or is too short.",
		              'noheader');

                    }

                    print $viralator->end_html;
		    last CHECKIT;

# end of $result = 1
                }

# end of CHECKIT block
            }


# Kill process downloading file, delete file and close window

        } elsif ( $action eq 'delete') {

            print $viralator->header(-expires => 'now');

            my $filename = $viralator->param('filename');
	    my $received_digest = $viralator->param('digest');

# let's check out if the digest is corrected
	    my $digest = md5_base64($filename,$config{secret});

   	    error ('warning',$lang{md5_error}.$lang{admincall},
	        'Received corrupted data when trying to stop a download','noheader')
	        unless ( $received_digest eq $digest );


	    $filename = clean_taint($filename,'\w\.\-\_');
	    $config{downloads} = clean_taint($config{downloads},'\w\.\/\-\_');


            print $viralator->start_html(-title=>"$version",
                                         -site=>"$site",
                                         -BGCOLOR=>'#FFFFFF',
                                         -onload=>'setTimeout(window.close,2000);');

            load_css();

            print "<br>$lang{wremoving} $filename $lang{wfromsrv}... ";

            unlink "$config{downloads}/$filename" ||
                error('error',"$lang{rm_error}","$lang{rm_error}: $!");

            print 'OK';

            print $viralator->end_html;


# this function will cancel a download request
# it will kill the process running the download, erase the downloaded file
# and close the user window

        } elsif ($action eq 'StopMe') {

            my $filename = $viralator->param('filename');
	    my $processid = $viralator->param('processid');
	    my $received_digest = $viralator->param('digest');

# let's check out if the digest is corrected
	    my $digest = md5_base64($filename,$processid,$config{secret});

            print $viralator->header(-expires => 'now');

   	    error ('warning',$lang{md5_error},
	        'Received corrupted data when trying to stop a download','noheader')
	        unless ( $received_digest eq $digest );


            print $viralator->start_html(-title=>"$version",
                                         -site=>"$site",
                                         -BGCOLOR=>'#FFFFFF',
                                         -onload=>'setTimeout(window.close,2000);');

	    load_css();

            print $viralator->p("$lang{downabort}");

            print $viralator->p($lang{kill});
	    $processid = clean_taint($processid,'\d+');
	    kill 'TERM',$processid;

            print $viralator->p("$lang{wremoving} $filename $lang{wfromsrv}");

            $config{downloads} = clean_taint($config{downloads},'\w\.\/\-\_');
            $filename = clean_taint($filename,'\w\.\-\_');

            unlink "$config{downloads}/$filename" ||
                error('error',"$lang{rm_error}","$lang{rm_error}: $!");

            print $viralator->end_html;


# not defined value for action, shows error
# this message must be translated and put in a language file

        } else {


            error('error',$lang{no_resource},
	        'Invalid value for action parameter');

        }

    }

}



############################
##### FUNCTION AREA ########
############################


# Hands errors gracefully

sub error {

    open(ERRDBG,">/tmp/errdbg");
# message type: warning or error
    my $type = shift;

# title of the page
    my $title;

    if ($type eq 'warning') {

        $title = $lang{warning};

    } else {

        $title = $lang{error};

    }


# this one goes to the browser
    my $message = shift;
# this one goes to the log file
    my $die = shift;
# checks if the header is necessary
    my $header = shift;
    print ERRDBG "Dies ist der Header: --".$header."--\n";

    unless (defined($header) and $header !~ /noheader/) {

        print $viralator->header(-expires=> 'now');
        print ERRDBG $viralator->header(-expires=> 'now');

        print $viralator->start_html(-title=>"$version: $title",
                                     -site=>"$site",
                                     -BGCOLOR=>'#FFFFFF');
        print ERRDBG $viralator->start_html(-title=>"$version: $title",
                                     -site=>"$site",
                                     -BGCOLOR=>'#FFFFFF');

    }

    print $viralator->h1($title);
    print $viralator->p($message);
    print $viralator->p($lang{admincall});

    print ERRDBG $viralator->h1($title);
    print ERRDBG $viralator->p($message);
    print ERRDBG $viralator->p($lang{admincall});

    print '<center>';
    print $viralator->submit(-value   => "$lang{wclosew}",
                             -onClick => 'window.close()');
    print '</center>';
    print $viralator->end_html;

    print ERRDBG '<center>';
    print ERRDBG $viralator->submit(-value   => "$lang{wclosew}",
                             -onClick => 'window.close()');
    print ERRDBG '</center>';
    print ERRDBG $viralator->end_html;
    close ERRDBG;

    die "$type: $die";

}

# download the file
# A good part of this function code was gently given by Oleg Y. Ivanov <g16@mail.ru>

sub get_file {

    my $username = shift;
    my $password = shift;
    my $fileurl  = shift;
    my $filename = shift;

    delete @ENV{qw(IFS CDPATH ENV BASH_ENV)};
    $ENV{PATH} = "/usr/bin";
    #+++#
    $ENV{FTP_PASSIVE} = 1;
    #+++#

    $config{downloads} = clean_taint($config{downloads},'\w\.\/\-\_');

    $fileurl  = clean_taint($fileurl,'\s\+\~\w\/\:\_\-\.\?');
    $filename = clean_taint($filename,'\w\-\_\.');

    my $fetcher = LWP::UserAgent->new(timeout => 300);

	if ( not $config{proxyhost} eq '' ) {
		#$proxyhost = $config{proxyhost};
		#$proxyport = $config{proxyport};
		$fetcher->proxy('http', "http://$config{proxyhost}:$config{proxyport}/");
	}

# defining a cool name for the "browser"
    $fetcher->agent($version);
    $fetcher->protocols_allowed([qw(http https ftp)]);

#first, checking if the filename exists on the server and getting more information about it
    my $response = $fetcher->head($fileurl);

    if ( $response->header('WWW-Authenticate') ) {

        unless ( defined($username) ) {

            my $realm_name = $response->header('WWW-Authenticate');
            my $pos = index($realm_name,'"');
            $realm_name = substr($realm_name,$pos+1,index($realm_name,'"',$pos+1));
            $realm_name =~ s/^\"//;
	    $realm_name =~ s/\"$//;


	    print $viralator->h3("$lang{authrequired} \"$realm_name\"");
            print $viralator->p("$lang{pleaseuserpass} $fileurl");

            print $viralator->start_form(-method=>'post',
                                         -action=>"http://$servername/$scriptname");

            print $viralator->hidden(-name    => 'action',
                                     -default => 'popup');

            print $viralator->hidden(-name    => 'filename',
                                     -default => "$filename");

	    print $viralator->hidden(-name    => 'fileurl',
                                     -default => "$fileurl");

	    print "<P>$lang{wusername}: ";
            print $viralator->textfield(-name => 'username');
	    print '<BR>';

	    print "$lang{wpassword}: ";
            print $viralator->password_field(-name => 'password');
	    print '</P>';

            print '<p align="center">';
            print $viralator->submit(-name => "$lang{tryagain}");
            print '</p>';

            print $viralator->end_form;

# exiting
	    return(2);


        } else {

            $username = clean_taint($username,'\w\-\_');
            $password = clean_taint($password,'\w\-\_\.\?\!\@\#\$\%\&');

# constructing 'netloc'
            my $pos = index($fileurl,'//')+2;
            my $lk  = substr($fileurl,$pos,index($fileurl,'/',$pos)-$pos);
            my $lk1 = $response->header('Client-Peer');
            $pos    = index($lk1,':');
            $lk1    = substr($lk1,$pos+1);
            $lk    .= ":$lk1";

# extracting realm name
            $lk1 = $response->header('WWW-Authenticate');
            $pos = index($lk1,'"');
            $lk1 = substr($lk1,$pos+1,index($lk1,'"',$pos+1));
            $lk1 =~ s/^\"//;
	    $lk1 =~ s/\"$//;

            $fetcher->credentials($lk,$lk1,$username,$password);

# trying again
            $response = $fetcher->head($fileurl);


        }

    }


# change the if code to an "case" structure

    if ($response->is_success) {

        my $filetype = $response->content_type;
	my $filesize = $response->content_length;
	$bar_value = $filesize/50;
	$filesize = fbytes($filesize);

#changing value of the parameter 'action'
#the value 'popup' sticks on it

        $viralator->param(-name=>'action',-value=>'StopMe');


# form
        print $viralator->h3($lang{downloading});

        print $viralator->start_form(-method=>'post',
                                         -action=>"$scriptname");

        print $viralator->hidden(-name    => 'action',
                                 -default => 'StopMe');

        print $viralator->hidden(-name    => 'filename',
                                 -default => "$filename");

# this parameter will be necessary so Viralator download can be canceled
        print $viralator->hidden(-name    => 'processid',
	                         -default => "$$");

	my $stop_digest = md5_base64($filename,$$,$config{secret});

	print $viralator->hidden(-name => 'digest',
	                         -default => "$stop_digest");

        print $viralator->submit(-name => "$lang{stop}");
        print $viralator->endform;

	print $viralator->table( { -border => 1},
	      		         $viralator->Tr( [
				                 $viralator->td( ["Requested file type",$filetype] ),
				                 $viralator->td( ["Request file size",$filesize] )
				                 ])
			       );


# getting the file
# this prints the start of the progress bar
#Each bar represents $bar_value bytes
print <<BLOCK;
<br>
<table border=0 width="350" cellpadding=0 cellspacing=2>
<tr>
<td>Download progress bar:</td>
</tr>
<tr bgcolor="#CCCCCC" valign="middle">
<td>
<table border=1 width="350">
<tr><td>
<table border=0 cellpadding=0 cellspacing=0><tr>
BLOCK

# file concurrency hack
# should use sysopen function to avoid race conditions

        open(FILE,">$config{downloads}/$filename") || error("Cannot created $filename: $!",
                                                           "Cannot created $filename: $!");

        $response = $fetcher->get($fileurl,':content_cb' => \&callback);
        my $result = ($response->is_success) ? 1 : 0;
        close(FILE);

        while ( $count_bar < 50 ) {

            print BAR;
	    $count_bar++;

        }


# this prints the end of progress bar
        print '</tr></table></td></tr></table></td></tr></table>';
        print $viralator->p($lang{finished});
        print $viralator->hr;

	return($result);


    } elsif ($response->status_line =~ /404 Not Found/) {

        print $viralator->p("404 $lang{filenotfound}");
        return 0;

    } elsif ($response->status_line =~ /Host not found/) {

        print $viralator->p($lang{hostnotfound});
        return 0;

    } elsif ($response->status_line =~ /401 Authorization Required/) {

        print $viralator->h3($lang{error});
        print $viralator->p($lang{autherr});
	print $viralator->p("$lang{totry} <a href=\"http://$servername$scriptname?action=popup&fileurl=$fileurl\">$lang{here}</a>");
	return 0;

    } else {

        my $undeferror = $response->status_line;
	warn "undefined error $undeferror";
	print $viralator->p("An undefined error ocorred: $undeferror");
	print $viralator->p($lang{admincall});
	return 0;

    }


}

#antivirus calling to clean downloaded file

sub cleanit {

    my $fileurl  = shift;
    my $filename = shift;


# untaint data
    $config{scannerpath}  = clean_taint($config{scannerpath},'\w\.\/\-\_');
    $config{virusscanner} = clean_taint($config{virusscanner},'\w');
    $config{viruscmd}     = clean_taint($config{viruscmd},'\w\.\_\-\s');
    $config{downloads}    = clean_taint($config{downloads},'\w\.\/\-\_');

    delete @ENV{qw(IFS CDPATH ENV BASH_ENV)};
    $ENV{PATH} = "$config{scannerpath}";

    print $viralator->p("$lang{wviruscan} $filename $lang{takeawhile}");

    if (-e "$config{downloads}/$filename") {

#        open(VIRUS,"$config{virusscanner} $config{viruscmd} $config{downloads}/$filename 2>&1|") ||
#             error('error',"$lang{antivirus_error}$lang{admincall}","Error when running the antivirus program: $!",'noheader');

        my $pid = open3(\*TOCHILD,\*FROMCHILD,\*FROMCHILD,$config{virusscanner},
	    $config{viruscmd},"$config{downloads}/$filename");


#         while(<VIRUS>) {
        while(<FROMCHILD>) {

            if ($_ =~ /$config{alert}/) {

                unlink "$config{downloads}/$filename" ||
                    error('error',"$lang{rm_error}","$lang{rm_error}: $!");

                error('warning',"$lang{vfounddl}: $lang{fileremoved}.",
		    "Virus found in file requested by $client",'noheader');

            } else {
#                print $viralator->comment("...\n");
# should define a variable at viralator.conf to show or not the virus scanner info

                print $viralator->p("$_");

            }

	}

#    close(VIRUS);
        close(TOCHILD);
        close(FROMCHILD);

        waitpid $pid, 0;

    } else {

        error('warning',$lang{no_resource},'No file','noheader');

    }


    print $viralator->hr;

}


# tests the download repository

sub test_repository {

    my $dir = shift;
    opendir(DIR,"$config{downloads}") ||
        error('error',"$lang{repository}","Cannot open $config{downloads}: $!");

    close(DIR);
}


# parses the filename from the url

sub parse_fileurl {

    my $fileurl = shift;
    my $position;
    my @temp;

# cuts http:// ahd similar stuff, if it's there
#    $fileurl =~ s/^http\:\/\///;
#    $fileurl =~ s/^https\:\/\///;
#    $fileurl =~ s/^ftp\:\/\///;

    $fileurl =~ s/^[hf]t+ps?\:\/\///;

    error('warning',$lang{urlerr},$lang{urlerr}) if ($fileurl eq '');

#this puts the fileurl into an array

    @temp = split (/\//,$fileurl);
    $position = @temp - 1;

    my $filename = splice(@temp, $position);

    $filename = clean_taint($filename,'\w\-\_\.');

    return $filename;

}


# test if the parameter has a value
# $object is the object being treated, the variable name without "$"
# $param is the variable itself, with it's value
sub test_param {

    my $object = shift;
    my $param  = shift;

    error('error',"$object: $lang{missing_parameter}","$object: $lang{missing_parameter}")
        if ( $param eq '' or ( !defined($param) )  );

}

sub clean_taint {

    my $word = shift;
    my $pattern = shift;

    if ($word =~ /(^[$pattern]+$)/) {

        return($1);

    } else {

        error ('warning',"$lang{invalid_char} $word","$lang{invalid_char} $word - $client",'noheader');
    }


}


sub callback {

   my ($data, $response, $protocol) = @_;

   $datasum += length($data);

   my $total_printed = $bar_value * $count_bar;

   if ( ($datasum >= $total_printed) and ($count_bar < 50) ) {

       print BAR;
       $count_bar++;

   }

   print FILE "$data";

}


#function borrowed from lwp-download,v 2.1 2002/01/03 02:09:24 gisl

sub fbytes {
    my $n = int(shift);
    if ($n >= 1024 * 1024) {
        return sprintf "%.3g MB", $n / (1024.0 * 1024);
    } elsif ($n >= 1024) {
        return sprintf "%.3g KB", $n / 1024.0;
    } else {
        return "$n bytes";
    }
}

sub load_css {

print <<BLOCK;
<STYLE>
A:link { color: #0000FF; text-decoration: none; }
A:visited { color: #6600FF; text-decoration: none; }
A:active { color: #DC143C; }
A:hover {  text-decoration: underline; }
body { SCROLLBAR-FACE-COLOR: #006699;
       SCROLLBAR-HIGHLIGHT-COLOR: #0099FF;
       SCROLLBAR-SHADOW-COLOR: #0099FF;
       SCROLLBAR-3DLIGHT-COLOR: #336666;
       SCROLLBAR-ARROW-COLOR: #0099FF;
       SCROLLBAR-TRACK-COLOR: #333366;
       SCROLLBAR-DARKSHADOW-COLOR: #333366;
       rgb: }
h3 { font-family: Verdana,Arial,Helvetica; }
td { font-family: Verdana,Arial,Helvetica; }
p { font-family: Verdana,Arial,Helvetica; }
b { font-family: Verdana,Arial,Helvetica; }
li { font-family: Verdana,Arial,Helvetica; }
</STYLE>
BLOCK

}


# to be called when the script receives a kill sign
sub terminated {

    my $date = localtime(time);
    die "[$date] viralator.cgi:warning: request process killed by $client\n";

}
