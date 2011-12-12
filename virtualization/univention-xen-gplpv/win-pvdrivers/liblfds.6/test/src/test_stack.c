#include "internal.h"





/****************************************************************************/
void test_stack( void )
{
  unsigned int
    loop,
    cpu_count;

  struct stack_state
    *ss;

  thread_state_t
    *thread_handles;

  /* TRD : there are 5 tests

           1. single reader thread per CPU
              - stack always empty
           2. single writer thread per CPU
              - stack always full
           3. one reader and one writer thread per CPU
              - stack balanced
           4. one reader and two writer threads per CPU
              - stack grows
           5. two reader and one writer thread per CPU
              - stack tends to empty
  */

  cpu_count = abstraction_cpu_count();

  printf( "\n"
          "Stack Test\n"
          "==========\n" );

  // TRD : 1. single reader thread per CPU

  printf( "\n"
          "1. single reader thread per CPU\n"
          "===============================\n" );

  stack_new( &ss, 10000 );

  thread_handles = (thread_state_t *) malloc( sizeof(thread_state_t) * cpu_count * 1 );

  for( loop = 0 ; loop < cpu_count ; loop++ )
    abstraction_thread_start( &thread_handles[loop], loop, stack_internal_thread_reader, ss );

  for( loop = 0 ; loop < cpu_count ; loop++ )
    abstraction_thread_wait( thread_handles[loop] );

  stack_delete( ss, NULL, NULL );

  free( thread_handles );

  // TRD : 2. single writer thread per CPU

  printf( "\n"
          "2. single writer thread per CPU\n"
          "===============================\n" );

  stack_new( &ss, 10000 );

  thread_handles = (thread_state_t *) malloc( sizeof(thread_state_t) * cpu_count * 1 );

  for( loop = 0 ; loop < cpu_count ; loop++ )
    abstraction_thread_start( &thread_handles[loop], loop, stack_internal_thread_writer, ss );

  for( loop = 0 ; loop < cpu_count ; loop++ )
    abstraction_thread_wait( thread_handles[loop] );

  stack_delete( ss, NULL, NULL );

  free( thread_handles );

  // TRD : 3. one reader and one writer thread per CPU

  printf( "\n"
          "3. one reader and one writer thread per CPU\n"
          "===========================================\n" );

  stack_new( &ss, 10000 );

  thread_handles = (thread_state_t *) malloc( sizeof(thread_state_t) * cpu_count * 2 );

  for( loop = 0 ; loop < cpu_count ; loop++ )
  {
    abstraction_thread_start( &thread_handles[loop], loop, stack_internal_thread_reader, ss );
    abstraction_thread_start( &thread_handles[loop+cpu_count], loop, stack_internal_thread_writer, ss );
  }

  for( loop = 0 ; loop < cpu_count * 2 ; loop++ )
    abstraction_thread_wait( thread_handles[loop] );

  stack_delete( ss, NULL, NULL );

  free( thread_handles );

  // TRD : 4. one reader and two writer threads per CPU

  printf( "\n"
          "4. one reader and two writer threads per CPU\n"
          "============================================\n" );

  stack_new( &ss, 10000 );

  thread_handles = (thread_state_t *) malloc( sizeof(thread_state_t) * cpu_count * 3 );

  for( loop = 0 ; loop < cpu_count ; loop++ )
  {
    abstraction_thread_start( &thread_handles[loop], loop, stack_internal_thread_reader, ss );
    abstraction_thread_start( &thread_handles[loop+cpu_count], loop, stack_internal_thread_writer, ss );
    abstraction_thread_start( &thread_handles[loop+cpu_count*2], loop, stack_internal_thread_writer, ss );
  }

  for( loop = 0 ; loop < cpu_count * 3 ; loop++ )
    abstraction_thread_wait( thread_handles[loop] );

  stack_delete( ss, NULL, NULL );

  free( thread_handles );

  // TRD : 5. two reader and one writer thread per CPU

  printf( "\n"
          "5. two reader and one writer thread per CPU\n"
          "===========================================\n" );

  stack_new( &ss, 10000 );

  thread_handles = (thread_state_t *) malloc( sizeof(thread_state_t) * cpu_count * 3 );

  for( loop = 0 ; loop < cpu_count ; loop++ )
  {
    abstraction_thread_start( &thread_handles[loop], loop, stack_internal_thread_reader, ss );
    abstraction_thread_start( &thread_handles[loop+cpu_count], loop, stack_internal_thread_reader, ss );
    abstraction_thread_start( &thread_handles[loop+cpu_count*2], loop, stack_internal_thread_writer, ss );
  }

  for( loop = 0 ; loop < cpu_count * 3 ; loop++ )
    abstraction_thread_wait( thread_handles[loop] );

  stack_delete( ss, NULL, NULL );

  free( thread_handles );

  return;
}





/****************************************************************************/
thread_return_t CALLING_CONVENTION stack_internal_thread_reader( void *stack_state )
{
  struct stack_state
    *ss;

  void
    *user_data;

  time_t
    start_time;

  unsigned long long int
    count = 0;

  assert( stack_state != NULL );

  ss = (struct stack_state *) stack_state;

  time( &start_time );

  while( time(NULL) < start_time + 10 )
  {
    if( stack_pop(ss, &user_data) )
      count++;
  }

  printf( "read count = %llu\n", count );

  return( (thread_return_t) EXIT_SUCCESS );
}





/****************************************************************************/
thread_return_t CALLING_CONVENTION stack_internal_thread_writer( void *stack_state )
{
  struct stack_state
    *ss;

  time_t
    start_time;

  unsigned long long int
    count = 0;

  assert( stack_state != NULL );

  ss = (struct stack_state *) stack_state;

  time( &start_time );

  while( time(NULL) < start_time + 10 )
  {
    // TRD : we don't store any user data
    if( stack_push(ss, NULL) )
      count++;
  }

  printf( "write count = %llu\n", count );

  return( (thread_return_t) EXIT_SUCCESS );
}

