#include "internal.h"





/****************************************************************************/
void test_abstraction( void )
{
  printf( "\n"
          "Abstraction Tests\n"
          "=================\n" );

  abstraction_test_increment();
  abstraction_test_dcas();

  return;
}





/****************************************************************************/
void abstraction_test_increment( void )
{
  unsigned int
    loop,
    cpu_count;

  thread_state_t
    *thread_handles;

  atom_t
    shared_counter = 0,
    atomic_shared_counter = 0;

  /* TRD : here we test abstraction_increment

           first, we run one thread per CPU where each thread increments
           a shared counter 10,000,000 times - however, this first test
           does NOT use atomic increment; it uses "++"

           second, we repeat the exercise, but this time using
           abstraction_increment()

           if the final value in the first test is less than (10,000,000*cpu_count)
           then the system is sensitive to non-atomic increments; this means if
           our atomic version of the test passes, we can have some degree of confidence
           that it works

           if the final value in the first test is in fact correct, then we can't know
           that our atomic version has changed anything

           and of course if the final value in the atomic test is wrong, we know things
           are broken
  */

  internal_display_test_name( "Atomic increment" );

  cpu_count = abstraction_cpu_count();

  thread_handles = malloc( sizeof(thread_state_t) * cpu_count );

  // TRD : non-atomic
  for( loop = 0 ; loop < cpu_count ; loop++ )
    abstraction_thread_start( &thread_handles[loop], loop, abstraction_test_internal_thread_increment, &shared_counter );

  for( loop = 0 ; loop < cpu_count ; loop++ )
    abstraction_thread_wait( thread_handles[loop] );

  // TRD : atomic
  for( loop = 0 ; loop < cpu_count ; loop++ )
    abstraction_thread_start( &thread_handles[loop], loop, abstraction_test_internal_thread_atomic_increment, &atomic_shared_counter );

  for( loop = 0 ; loop < cpu_count ; loop++ )
    abstraction_thread_wait( thread_handles[loop] );

  free( thread_handles );

  // TRD : results
  if( shared_counter < (10000000 * cpu_count) and atomic_shared_counter == (10000000 * cpu_count) )
    puts( "passed" );

  if( shared_counter == (10000000 * cpu_count) and atomic_shared_counter == (10000000 * cpu_count) )
    puts( "indeterminate" );

  if( atomic_shared_counter < (10000000 * cpu_count) )
    puts( "failed" );

  return;
}





/****************************************************************************/
thread_return_t CALLING_CONVENTION abstraction_test_internal_thread_increment( void *shared_counter )
{
  volatile atom_t
    count = 0;

  /* TRD : atom_t must be volatile or the compiler
           optimizes it away into a single store
  */

  assert( shared_counter != NULL );

  while( count++ < 10000000 )
    (*(atom_t *) shared_counter)++;

  return( (thread_return_t) EXIT_SUCCESS );
}





/****************************************************************************/
thread_return_t CALLING_CONVENTION abstraction_test_internal_thread_atomic_increment( void *shared_counter )
{
  atom_t
    count = 0;

  assert( shared_counter != NULL );

  while( count++ < 10000000 )
    abstraction_increment( shared_counter );

  return( (thread_return_t) EXIT_SUCCESS );
}





/****************************************************************************/
void abstraction_test_dcas( void )
{
  unsigned int
    loop,
    cpu_count;

  thread_state_t
    *thread_handles;

  struct abstraction_test_dcas_state
    *atds;

  ALIGN(ALIGN_DOUBLE_POINTER) volatile atom_t
    shared_counter[2] = { 0, 0 };

  atom_t
    local_total = 0;

  /* TRD : here we test abstraction_dcas

           we run one thread per CPU
           we use abstraction_dcas() to increment a shared counter
           every time a thread successfully increments the counter,
           it increments a thread local counter
           the threads run for ten seconds
           after the threads finish, we total the local counters
           they should equal the shared counter
  */

  internal_display_test_name( "Atomic DCAS" );

  cpu_count = abstraction_cpu_count();

  atds = malloc( sizeof(struct abstraction_test_dcas_state) * cpu_count );

  for( loop = 0 ; loop < cpu_count ; loop++ )
  {
    (atds+loop)->shared_counter = shared_counter;
    (atds+loop)->local_counter = 0;
  }

  thread_handles = malloc( sizeof(thread_state_t) * cpu_count );

  for( loop = 0 ; loop < cpu_count ; loop++ )
    abstraction_thread_start( &thread_handles[loop], loop, abstraction_test_internal_thread_dcas, atds+loop );

  for( loop = 0 ; loop < cpu_count ; loop++ )
    abstraction_thread_wait( thread_handles[loop] );

  free( thread_handles );

  // TRD : results
  for( loop = 0 ; loop < cpu_count ; loop++ )
    local_total += (atds+loop)->local_counter;

  if( local_total == shared_counter[0] )
    puts( "passed" );

  if( local_total != shared_counter[0] )
    puts( "failed" );

  // TRD : cleanup
  free( atds );

  return;
}





/****************************************************************************/
thread_return_t CALLING_CONVENTION abstraction_test_internal_thread_dcas( void *abstraction_test_dcas_state )
{
  struct abstraction_test_dcas_state
    *atds;

  time_t
    start_time;

  ALIGN(ALIGN_DOUBLE_POINTER) atom_t
    exchange[2],
    compare[2];

  assert( abstraction_test_dcas_state != NULL );

  atds = (struct abstraction_test_dcas_state *) abstraction_test_dcas_state;

  time( &start_time );

  while( time(NULL) < start_time + 10 )
  {
    compare[0] = *atds->shared_counter;
    compare[1] = *(atds->shared_counter+1);

    do
    {
      exchange[0] = compare[0] + 1;
      exchange[1] = compare[1];
    }
    while( 0 == abstraction_dcas(atds->shared_counter, exchange, compare) );

    atds->local_counter++;
  }

  return( (thread_return_t) EXIT_SUCCESS );
}

