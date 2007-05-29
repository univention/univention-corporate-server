use ExtUtils::MakeMaker;
#use ExtUtils::MM_Unix;
#use Data::Dumper;
# See lib/ExtUtils/MakeMaker.pm for details of how to influence
# the contents of the Makefile that is written.
# 	$Id: Makefile.PL,v 1.2 2003/09/08 07:14:36 thorsten Exp $
#$makefile = MM->new	
WriteMakefile
  ('NAME'		=> 'Unidump',
   'VERSION'	        => '0.5',
   'PREREQ_PM'		=> {
     'AppConfig' => 1.50,
     'Class::Accessor' => 0,
     'Data::ShowTable' => 0,
     'File::Remove' => 0,
     'Date::Parse' => 2.0,
     'Unix::Syslog' => 0.9,
     'Date::Parse'  => 0
     },
   'MAN3PODS' => {
     'Unidump.pm' => '$(INST_MAN3DIR)/Unidump.$(MAN3EXT)',
     'Unidump/Logger.pm' => '$(INST_MAN3DIR)/Unidump::Logger.$(MAN3EXT)',
     'Unidump/History.pm' => '$(INST_MAN3DIR)/Unidump::History.$(MAN3EXT)',
     'Unidump/Units.pm' => '$(INST_MAN3DIR)/Unidump::Units.$(MAN3EXT)',
     'Unidump/Strategy.pm' => '$(INST_MAN3DIR)/Unidump::Strategy.$(MAN3EXT)',
     'Unidump/Config.pm' => '$(INST_MAN3DIR)/Unidump::Config.$(MAN3EXT)'
     },  
   'EXE_FILES' => [qw(scripts/unidump 
		      scripts/unilabel    scripts/unirest    
		        scripts/unilib   
		      scripts/uniresume  scripts/unitoc
		      scripts/uniflush   scripts/unilist
		      scripts/unisched  scripts/unihist 
		      scripts/uniproper   scripts/unistat
		      scripts/unihrest)],
   'PMLIBDIRS' => [qw(lib Unidump)],
   'AUTHOR' => 'Joerg Ungethuem <joerg.ungethuem@enersim.de>',
   'ABSTRACT' => 
   'Unidump - Perl extension for scheduled backup',
   );

#$makefile->flush;
#print Dumper $makefile;
