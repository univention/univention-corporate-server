#include "internal.h"





/****************************************************************************/
#if (defined _WIN32 && defined _MSC_VER && !defined WIN_KERNEL_BUILD)

  /* TRD : any Windows (user-mode) on any CPU with the Microsoft C compiler

           _WIN32             indicates 64-bit or 32-bit Windows
           _MSC_VER           indicates Microsoft C compiler
           !WIN_KERNEL_BUILD  indicates Windows user-mode
  */

  void abstraction_thread_wait( thread_state_t thread_state )
  {
    WaitForSingleObject( thread_state, INFINITE );

    return;
  }

#endif





/****************************************************************************/
#if (defined _WIN32 && defined _MSC_VER && defined WIN_KERNEL_BUILD)

  /* TRD : any Windows on any CPU with the Microsoft C compiler

           _WIN32            indicates 64-bit or 32-bit Windows
           _MSC_VER          indicates Microsoft C compiler
           WIN_KERNEL_BUILD  indicates Windows kernel
  */

  void abstraction_thread_wait( thread_state_t thread_state )
  {
    KeWaitForSingleObject( thread_state, Executive, KernelMode, FALSE, NULL );

    return;
  }

#endif





/****************************************************************************/
#if (defined __unix__)

  /* TRD : any UNIX on any CPU with any compiler

           I assumed pthreads is available on any UNIX.

           __unix__   indicates Solaris, Linux, HPUX, etc
  */

  void abstraction_thread_wait( thread_state_t thread_state )
  {
    pthread_join( thread_state,  NULL );

    return;
  }

#endif

