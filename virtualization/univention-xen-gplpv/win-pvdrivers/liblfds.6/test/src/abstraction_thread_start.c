#include "internal.h"





/****************************************************************************/
#if (defined _WIN32 && defined _MSC_VER && !defined WIN_KERNEL_BUILD)

  /* TRD : any Windows (user-mode) on any CPU with the Microsoft C compiler

           _WIN32             indicates 64-bit or 32-bit Windows
           _MSC_VER           indicates Microsoft C compiler
           !WIN_KERNEL_BUILD  indicates Windows user-mode
  */

  int abstraction_thread_start( thread_state_t *thread_state, unsigned int cpu, thread_function_t thread_function, void *thread_user_state )
  {
    int
      rv = 0;

    DWORD
      thread_id;

    DWORD_PTR
      affinity_mask,
      result;

    assert( thread_state != NULL );
    // TRD : cpu can be any value in its range
    assert( thread_function != NULL );
    // TRD : thread_user_state can be NULL

    affinity_mask = (DWORD_PTR) (1 << cpu);

    *thread_state = CreateThread( NULL, 0, thread_function, thread_user_state, NO_FLAGS, &thread_id );

    result = SetThreadAffinityMask( *thread_state, affinity_mask );

    if( *thread_state != NULL and result != 0 )
      rv = 1;

    return( rv );
  }

#endif





/****************************************************************************/
#if (defined _WIN32 && defined _MSC_VER && defined WIN_KERNEL_BUILD)

  /* TRD : any Windows on any CPU with the Microsoft C compiler

           _WIN32            indicates 64-bit or 32-bit Windows
           _MSC_VER          indicates Microsoft C compiler
           WIN_KERNEL_BUILD  indicates Windows kernel
  */

  int abstraction_thread_start( thread_state_t *thread_state, unsigned int cpu, thread_function_t thread_function, void *thread_user_state )
  {
    int
      rv = 0;

    KAFFINITY
      affinity_mask

    NTSTATUS
      nts_create,
      nts_affinity;

    assert( thread_state != NULL );
    // TRD : cpu can be any value in its range
    assert( thread_function != NULL );
    // TRD : thread_user_state can be NULL

    affinity_mask = 1 << cpu;

    nts_create = PsCreateSystemThread( thread_state, THREAD_ALL_ACCESS, NULL, NULL, NULL, thread_function, thread_user_state );

    nts_affinity = ZwSetInformationThread( thread_state, ThreadAffinityMask, &affinity_mask, sizeof(KAFFINITY) );

    if( nts_create == STATUS_SUCCESS and nts_affinity == STATUS_SUCCESS )
      rv = 1;

    return( rv );
  }

#endif





/****************************************************************************/
#if (defined __unix__)

  /* TRD : any UNIX on any CPU with any compiler

           I assumed pthreads is available on any UNIX.

           __unix__   indicates Solaris, Linux, HPUX, etc
  */

  int abstraction_thread_start( thread_state_t *thread_state, unsigned int cpu, thread_function_t thread_function, void *thread_user_state )
  {
    int
      rv = 0,
      rv_create;

    assert( thread_state != NULL );
    // TRD : cpu can be any value in its range
    assert( thread_function != NULL );
    // TRD : thread_user_state can be NULL

    rv_create = pthread_create( thread_state, NULL, thread_function, thread_user_state );

    if( rv_create == 0 )
      rv = 1;

    return( rv );
  }

#endif

