#include "internal.h"





/****************************************************************************/
#if (defined _WIN32 && defined _MSC_VER && !defined WIN_KERNEL_BUILD)

  /* TRD : any Windows (user-mode) on any CPU with the Microsoft C compiler

           _WIN32             indicates 64-bit or 32-bit Windows
           _MSC_VER           indicates Microsoft C compiler
           !WIN_KERNEL_BUILD  indicates Windows user-mode
  */

  unsigned int abstraction_cpu_count()
  {
    SYSTEM_INFO
      si;

    GetNativeSystemInfo( &si );

    return( (unsigned int) si.dwNumberOfProcessors );
  }

#endif





/****************************************************************************/
#if (defined _WIN32 && defined _MSC_VER && defined WIN_KERNEL_BUILD)

  /* TRD : any Windows on any CPU with the Microsoft C compiler

           _WIN32            indicates 64-bit or 32-bit Windows
           _MSC_VER          indicates Microsoft C compiler
           WIN_KERNEL_BUILD  indicates Windows kernel
  */

  unsigned int abstraction_cpu_count()
  {
    unsigned int
      active_processor_count;

    active_processor_count = KeQueryActiveProcessorCount( NULL );

    return( active_processor_count );
  }

#endif





/****************************************************************************/
#if (defined __linux__ && __GNUC__)

  /* TRD : Linux on any CPU with GCC

           this function I believe is Linux specific and varies by UNIX flavour

           __linux__  indicates Linux
           __GNUC__   indicates GCC
  */

  unsigned int abstraction_cpu_count()
  {
    long int
      cpu_count;

    cpu_count = sysconf( _SC_NPROCESSORS_ONLN );

    return( (unsigned int) cpu_count );
  }

#endif

