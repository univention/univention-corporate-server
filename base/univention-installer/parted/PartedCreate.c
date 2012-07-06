/*
 * Univention Installer
 *  C source code for the parted wrapper
 *
 * Copyright 2004-2012 Univention GmbH
 *
 * http://www.univention.de/
 *
 * All rights reserved.
 *
 * The source code of this program is made available
 * under the terms of the GNU Affero General Public License version 3
 * (GNU AGPL V3) as published by the Free Software Foundation.
 *
 * Binary versions of this program provided by Univention to you as
 * well as other copyrighted, protected or trademarked materials like
 * Logos, graphics, fonts, specific documentations and configurations,
 * cryptographic keys etc. are subject to a license agreement between
 * you and Univention and not subject to the GNU AGPL V3.
 *
 * In the case you use this program under the terms of the GNU AGPL V3,
 * the program is provided in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public
 * License with the Debian GNU/Linux or Univention distribution in file
 * /usr/share/common-licenses/AGPL-3; if not, see
 * <http://www.gnu.org/licenses/>.
 */
#include <parted/parted.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <dlfcn.h>
#include <getopt.h>


#define CIL2SEC(DEV,A) ( (A-1)*DEV->hw_geom.heads*DEV->hw_geom.sectors)

#define PART_TYP_PRIMARY		0
#define PART_TYP_LOGICAL		1
#define PART_TYP_EXTENDED		2
#define PART_TYP_FREE_PRIMARY		10
#define PART_TYP_FREE_LOGICAL		11
#define PART_TYP_FREE_EXTENDED		12
#define PART_TYP_UNUSED 		99


void PartIOInit()
{
	ped_device_probe_all();
}

void PartIOFree()
{
	return;
}

void part_search_device( char *device_name    ,
                         int  partition_type  ,
			 char *filesystem_name,
			 int  start_value     ,
			 int  start_unit      ,
			 int  end_value       ,
			 int  end_unit        ,
			 int  end_relative     )
{
	PedFileSystemType	*fs_type;
	PedDevice		*dev = NULL;
	PedDisk			*disk;
	PedPartition		*new_part;
	PedConstraint		*constraint;
	PedSector		sect_start = 0;
	PedSector		sect_end   = 0;

	fs_type = ped_file_system_type_get( filesystem_name );
	if( fs_type==NULL )
	{
		fprintf( stderr, "Error: No file_system_type for \"%s\".\n", filesystem_name );
		return;
	}

	dev  = ped_device_get( device_name );
	if( dev==NULL )
	{
		fprintf( stderr, "Error: No device for \"%s\".\n", device_name );
		return;
	}

	disk = ped_disk_new( dev );
	if( disk==NULL )
	{
		fprintf( stderr, "Error: Can't create new disk.\n" );
		return;
	}

	ped_disk_print(disk);

	constraint = ped_constraint_any(dev);
	if( constraint==NULL )
	{
		fprintf( stderr, "Error: Can't get constraint for \"%s\".\n", device_name );
		return;
	}

	if( end_value == 0 )
	{
		end_value = dev->hw_geom.cylinders;
		end_unit  = 'c';
	}

	switch( start_unit )
	{
		case 'c' :
			sect_start = CIL2SEC(dev,start_value);
			break;

		case 'k' :
			sect_start = start_value * (1024 / dev->sector_size);
			break;

		case 'm' :
			sect_start = start_value * (1024 * 1024 / dev->sector_size);
			break;

		case 'g' :
			sect_start = start_value * (1024 * 1024 * 1024 / dev->sector_size);
			break;

		default:
			fprintf( stderr, "Error: Unknown unit \"%c\" for start-value.\n", start_unit );
			return;
	}

	switch( end_unit )
	{
		case 'c' :
			sect_end   = CIL2SEC(dev,end_value);
			break;

		case 'k' :
			sect_end = end_value * (1024 / dev->sector_size);
			break;

		case 'm' :
			sect_end = end_value * (1024 * 1024 / dev->sector_size);
			break;

		case 'g' :
			sect_end = end_value * (1024 * 1024 * 1024 / dev->sector_size);
			break;

		default:
			fprintf( stderr, "Error: Unknown unit \"%c\" for end-value.\n", end_unit );
			return;
	}

	if( end_relative == 1 )
	{
		sect_end += sect_start;
	}

	new_part = ped_partition_new( disk          ,
	                              partition_type,
				      fs_type       ,
				      sect_start    ,
				      sect_end       );
	if( !new_part )
	{
		fprintf( stderr                                                                                  ,
		         "Error: Can't create new partition type=%d from %d (Sector %llu) to %d (Sector %llu).\n",
			 partition_type                                                                          ,
			 start_value                                                                             ,
			 sect_start                                                                              ,
			 end_value                                                                               ,
			 sect_end                                                                                 );
		return;
	}

	if( !ped_disk_add_partition( disk      ,
	                             new_part  ,
				     constraint ) )
	{
		fprintf( stderr                                                                                  ,
		         "Error: Can't create add partition type=%d from %d (Sector %llu) to %d (Sector %llu).\n",
			 partition_type                                                                          ,
			 start_value                                                                             ,
			 sect_start                                                                              ,
			 end_value                                                                               ,
			 sect_end                                                                                 );
		return;
	}

	ped_disk_commit( disk );
	printf( "number=%d\n", new_part->num );
	ped_constraint_destroy( constraint );

	return;
}

void print_usage()
{
	printf( "Use PartedCreate:\n" );
	printf( "PartedCreate -d|--device Device-Name\n" );
	printf( "  [-t|--type       Partitiontype-Number]\n" );
	printf( "  [-f|--filesystem Filesystem-Name]\n" );
	printf( "  [-s|--start      Partition-Start (Cylinder-Number)]\n" );
	printf( "  [-e|--end        Partition-End (Cylinder-Number)]\n" );
	printf( "or:\n" );
	printf( "PartedCreate -h|--help\n\n" );
	printf( "Defaults are\n" );
	printf( "  Partitiontype-Number = 0\n" );
	printf( "  Filesystem-Name = ext2\n" );
	printf( "  Partition-Start = 0\n" );
	printf( "  Partition-End = 0. This 0 mean the last of cylinders.\n\n" );
	printf( "Partition-Start and Partition-End have the unit c for cylinder.\n" );
	printf( "  Another valid units are k or K for kilo, m or M for Mega and g or G for Giga.\n\n" );
	printf( "The Partition-End can have a '+' sign for a relative value (eg +128M).\n" );
}

int main( int argc, char *argv[] )
{
        char		*short_options = "d:s:e:t:f:hv";
	struct option	long_options[] =
	{
		{ "device",     required_argument, 0, 'd' },
		{ "type",	required_argument, 0, 't' },
		{ "filesystem",	required_argument, 0, 'f' },
		{ "start",	required_argument, 0, 's' },
		{ "end",	required_argument, 0, 'e' },
		{ "help",	no_argument,       0, 'h' },
		{ "verbose",	no_argument,       0, 'v' },
		{ 0, 0, 0, 0 }
	};
	int	c;
	int	option_index		= 0;
	int     optarg_len;
	char    unit;
	char    sign;

	char	*device_name		= NULL;
	int	partition_type		= -1;
	char	*filesystem_name	= NULL;
	int	start_value		= -1;
	char	start_unit		= 'c';
	int	end_value		= -1;
	char	end_unit		= 'c';
	int	end_relative		= 0;

	int	verbose			= 0;

	while( (c=getopt_long( argc         ,
	                       argv         ,
			       short_options,
			       long_options ,
			       &option_index ) ) != -1 )
	{
		switch( c )
		{
			case 'd':
				device_name = optarg;
				break;

			case 't':
				partition_type = atoi(optarg);
				break;

			case 'f':
				filesystem_name = optarg;
				break;

			case 's':
				start_value = atoi(optarg);
				optarg_len = strlen(optarg);
				if( optarg_len > 0 )
				{
					unit = optarg[optarg_len-1];
					switch( unit )
					{
						case 'k' :
						case 'K' :
							start_unit = 'k';
							break;

						case 'm' :
						case 'M' :
							start_unit = 'm';
							break;

						case 'g' :
						case 'G' :
							start_unit = 'g';
							break;

						case 'c' :
						case 'C' :
						default:
							start_unit = 'c';
					}
				}
				break;

			case 'e':
				end_value = atoi(optarg);
				optarg_len = strlen(optarg);
				if( optarg_len > 0 )
				{
					sign = optarg[0];
					if( sign == '+' )
					{
						end_relative = 1;
					}

					unit = optarg[optarg_len-1];
					switch( unit )
					{
						case 'k' :
						case 'K' :
							end_unit = 'k';
							break;

						case 'm' :
						case 'M' :
							end_unit = 'm';
							break;

						case 'g' :
						case 'G' :
							end_unit = 'g';
							break;

						case 'c' :
						case 'C' :
						default:
							end_unit = 'c';
					}
				}
				break;

			case 'v':
				verbose = 1;
				break;

			case 'h':
			default:
				print_usage();
				exit(1);
		}
	}

	if( verbose )
	{
		printf( "Start with PartedCreate.\n" );
	}

	if( !device_name )
	{
		printf( "Error: Device not set. Try -d Device-Name\n" );
		print_usage();
		exit(1);
	}

	if( partition_type < 0 )
	{
		partition_type = 0;
		if( verbose )
		{
			printf( "Set Partitiontype-Number to %d\n", partition_type );
		}
	}
	else
	{
		if( verbose )
		{
			printf( "Partitiontype-Number is %d\n", partition_type );
		}
	}

	if( !filesystem_name )
	{
		filesystem_name = "ext2";
		if( verbose )
		{
			printf( "Set Filesystem-Name to %s\n", filesystem_name );
		}
	}
	else
	{
		if( verbose )
		{
			printf( "Filesystem-Name is %s\n", filesystem_name );
		}
	}


	if( start_value < 1 )
	{
		start_value = 1;
		start_unit  = 'c';
		if( verbose )
		{
			printf( "Set Partition-Start to %d %c\n", start_value, start_unit );
		}
	}
	else
	{
		if( verbose )
		{
			printf( "Partition-Start is %d %c\n", start_value, start_unit );
		}
	}

	if( end_value < 0 )
	{
		end_value = 0;
		end_unit  = 'c';
		if( verbose )
		{
			printf( "Set Partition-End to %d %c\n", end_value, end_unit );
		}
	}
	else
	{
		if( verbose )
		{
			printf( "Partition-End is %d %c\n", end_value, end_unit );
		}
	}

	PartIOInit();
	part_search_device( device_name    ,
	                    partition_type ,
			    filesystem_name,
			    start_value    ,
			    start_unit     ,
			    end_value      ,
			    end_unit       ,
			    end_relative    );

	return 0;
}
