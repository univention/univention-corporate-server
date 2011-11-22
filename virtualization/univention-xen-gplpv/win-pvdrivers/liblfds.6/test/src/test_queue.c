#include "internal.h"





/****************************************************************************/
void test_queue( void )
{
  printf( "\n"
          "Queue Tests\n"
          "===========\n" );

  queue_test_enqueuing();
  queue_test_dequeuing();
  queue_test_enqueuing_and_dequeuing();
  queue_test_rapid_enqueuing_and_dequeuing();

  return;
}





/****************************************************************************/
void queue_test_enqueuing( void )
{
  unsigned int
    loop,
    cpu_count;

  thread_state_t
    *thread_handles;

  struct queue_state
    *qs;

  struct queue_test_enqueuing_state
    *qtes;

  atom_t
    user_data,
    thread,
    count,
    *per_thread_counters;

  struct validation_info
    vi = { 1000000, 1000000 };

  enum data_structure_validity
    dvs[2];

  /* TRD : create an empty queue with 1,000,000 elements in its freelist
           then run one thread per CPU
           where each thread busy-works, enqueuing elements (until there are no more elements)
           each element's void pointer of user data is (thread number | element number)
           where element_number is a thread-local counter starting at 0
           where the thread_number occupies the top byte

           when we're done, we check that all the elements are present
           and increment on a per-thread basis
  */

  internal_display_test_name( "Enqueuing" );

  cpu_count = abstraction_cpu_count();

  queue_new( &qs, 1000000 );

  qtes = malloc( sizeof(struct queue_test_enqueuing_state) * cpu_count );

  for( loop = 0 ; loop < cpu_count ; loop++ )
  {
    (qtes+loop)->qs = qs;
    (qtes+loop)->counter = (atom_t) loop << (sizeof(atom_t)*8-8);
  }

  thread_handles = malloc( sizeof(thread_state_t) * cpu_count );

  for( loop = 0 ; loop < cpu_count ; loop++ )
    abstraction_thread_start( &thread_handles[loop], loop, queue_test_internal_thread_simple_enqueuer, qtes+loop );

  for( loop = 0 ; loop < cpu_count ; loop++ )
    abstraction_thread_wait( thread_handles[loop] );

  free( thread_handles );

  free( qtes );

  /* TRD : first, validate the queue

           then dequeue
           we expect to find element numbers increment on a per thread basis
  */

  queue_query( qs, QUEUE_QUERY_VALIDATE, &vi, dvs );

  per_thread_counters = malloc( sizeof(atom_t) * cpu_count );

  for( loop = 0 ; loop < cpu_count ; loop++ )
    *(per_thread_counters+loop) = 0;

  while( dvs[0] == VALIDITY_VALID and dvs[1] == VALIDITY_VALID and queue_dequeue(qs, (void *) &user_data) )
  {
    thread = user_data >> (sizeof(atom_t)*8-8);
    count = (user_data << 8) >> 8;

    if( thread >= cpu_count )
    {
      dvs[0] = VALIDITY_INVALID_TEST_DATA;
      break;
    }

    if( count < per_thread_counters[thread] )
      dvs[0] = VALIDITY_INVALID_ADDITIONAL_ELEMENTS;

    if( count > per_thread_counters[thread] )
      dvs[0] = VALIDITY_INVALID_MISSING_ELEMENTS;

    if( count == per_thread_counters[thread] )
      per_thread_counters[thread]++;
  }

  free( per_thread_counters );

  queue_delete( qs, NULL, NULL );

  internal_display_test_result( 2, "queue", dvs[0], "queue freelist", dvs[1] );

  return;
}





/****************************************************************************/
thread_return_t CALLING_CONVENTION queue_test_internal_thread_simple_enqueuer( void *queue_test_enqueuing_state )
{
  struct queue_test_enqueuing_state
    *qtes;

  assert( queue_test_enqueuing_state != NULL );

  qtes = (struct queue_test_enqueuing_state *) queue_test_enqueuing_state;

  // TRD : top byte of counter is already our thread number
  while( queue_enqueue(qtes->qs, (void *) qtes->counter++) );

  return( (thread_return_t) EXIT_SUCCESS );
}





/****************************************************************************/
void queue_test_dequeuing( void )
{
  unsigned int
    loop,
    cpu_count;

  thread_state_t
    *thread_handles;

  struct queue_state
    *qs;

  struct queue_test_dequeuing_state
    *qtds;

  struct validation_info
    vi = { 0, 0 };

  enum data_structure_validity
    dvs[2];

  /* TRD : create a queue with 1,000,000 elements

           use a single thread to enqueue every element
           each elements user data is an incrementing counter

           then run one thread per CPU
           where each busy-works dequeuing

           when an element is dequeued, we check (on a per-thread basis) the
           value deqeued is greater than the element previously dequeued
  */

  internal_display_test_name( "Dequeuing" );

  cpu_count = abstraction_cpu_count();

  queue_new( &qs, 1000000 );

  for( loop = 0 ; loop < 1000000 ; loop++ )
    queue_enqueue( qs, (void *) (atom_t) loop );

  qtds = malloc( sizeof(struct queue_test_dequeuing_state) * cpu_count );

  for( loop = 0 ; loop < cpu_count ; loop++ )
  {
    (qtds+loop)->qs = qs;
    (qtds+loop)->error_flag = LOWERED;
  }

  thread_handles = malloc( sizeof(thread_state_t) * cpu_count );

  for( loop = 0 ; loop < cpu_count ; loop++ )
    abstraction_thread_start( &thread_handles[loop], loop, queue_test_internal_thread_simple_dequeuer, qtds+loop );

  for( loop = 0 ; loop < cpu_count ; loop++ )
    abstraction_thread_wait( thread_handles[loop] );

  free( thread_handles );

  // TRD : check queue is empty
  queue_query( qs, QUEUE_QUERY_VALIDATE, (void *) &vi, (void *) dvs );

  // TRD : check for raised error flags
  for( loop = 0 ; loop < cpu_count ; loop++ )
    if( (qtds+loop)->error_flag == RAISED )
      dvs[0] = VALIDITY_INVALID_TEST_DATA;

  free( qtds );

  queue_delete( qs, NULL, NULL );

  internal_display_test_result( 2, "queue", dvs[0], "queue freelist", dvs[1] );

  return;
}





/****************************************************************************/
thread_return_t CALLING_CONVENTION queue_test_internal_thread_simple_dequeuer( void *queue_test_dequeuing_state )
{
  struct queue_test_dequeuing_state
    *qtds;

  atom_t
    *prev_user_data,
    *user_data;

  assert( queue_test_dequeuing_state != NULL );

  qtds = (struct queue_test_dequeuing_state *) queue_test_dequeuing_state;

  queue_dequeue( qtds->qs, (void *) &prev_user_data );

  while( queue_dequeue(qtds->qs, (void *) &user_data) )
  {
    if( user_data <= prev_user_data )
      qtds->error_flag = RAISED;

    prev_user_data = user_data;
  }

  return( (thread_return_t) EXIT_SUCCESS );
}





/****************************************************************************/
void queue_test_enqueuing_and_dequeuing( void )
{
  unsigned int
    loop,
    subloop,
    cpu_count;

  thread_state_t
    *thread_handles;

  struct queue_state
    *qs;

  struct queue_test_enqueuing_and_dequeuing_state
    *qteds;

  struct validation_info
    vi = { 0, 0 };

  enum data_structure_validity
    dvs[2];

  internal_display_test_name( "Enqueuing and dequeuing (10 seconds)" );

  cpu_count = abstraction_cpu_count();

  queue_new( &qs, cpu_count );

  qteds = malloc( sizeof(struct queue_test_enqueuing_and_dequeuing_state) * cpu_count );

  for( loop = 0 ; loop < cpu_count ; loop++ )
  {
    (qteds+loop)->qs = qs;
    (qteds+loop)->thread_number = loop;
    (qteds+loop)->counter = (atom_t) loop << (sizeof(atom_t)*8-8);
    (qteds+loop)->cpu_count = cpu_count;
    (qteds+loop)->error_flag = LOWERED;
    (qteds+loop)->per_thread_counters = malloc( sizeof(atom_t) * cpu_count );

    for( subloop = 0 ; subloop < cpu_count ; subloop++ )
      *((qteds+loop)->per_thread_counters+subloop) = 0;
  }

  thread_handles = malloc( sizeof(thread_state_t) * cpu_count );

  for( loop = 0 ; loop < cpu_count ; loop++ )
    abstraction_thread_start( &thread_handles[loop], loop, queue_test_internal_thread_enqueuer_and_dequeuer, qteds+loop );

  for( loop = 0 ; loop < cpu_count ; loop++ )
    abstraction_thread_wait( thread_handles[loop] );

  free( thread_handles );

  queue_query( qs, QUEUE_QUERY_VALIDATE, (void *) &vi, (void *) dvs );

  for( loop = 0 ; loop < cpu_count ; loop++ )
    if( (qteds+loop)->error_flag == RAISED )
      dvs[0] = VALIDITY_INVALID_TEST_DATA;

  for( loop = 0 ; loop < cpu_count ; loop++ )
    free( (qteds+loop)->per_thread_counters );

  free( qteds );

  queue_delete( qs, NULL, NULL );

  internal_display_test_result( 2, "queue", dvs[0], "queue freelist", dvs[1] );

  return;
}





/****************************************************************************/
thread_return_t CALLING_CONVENTION queue_test_internal_thread_enqueuer_and_dequeuer( void *queue_test_enqueuing_and_dequeuing_state )
{
  struct queue_test_enqueuing_and_dequeuing_state
    *qteds;

  time_t
    start_time;

  atom_t
    thread,
    count,
    user_data;

  assert( queue_test_enqueuing_and_dequeuing_state != NULL );

  qteds = (struct queue_test_enqueuing_and_dequeuing_state *) queue_test_enqueuing_and_dequeuing_state;

  time( &start_time );

  while( time(NULL) < start_time + 10 )
  {
    queue_enqueue( qteds->qs, (void *) (qteds->counter++) );
    queue_dequeue( qteds->qs, (void *) &user_data );

    thread = user_data >> (sizeof(atom_t)*8-8);
    count = (user_data << 8) >> 8;

    if( thread >= qteds->cpu_count )
      qteds->error_flag = RAISED;
    else
    {
      if( count < qteds->per_thread_counters[thread] )
        qteds->error_flag = RAISED;

      if( count >= qteds->per_thread_counters[thread] )
        qteds->per_thread_counters[thread] = count+1;
    }
  }

  return( (thread_return_t) EXIT_SUCCESS );
}





/****************************************************************************/
void queue_test_rapid_enqueuing_and_dequeuing( void )
{
  unsigned int
    loop,
    cpu_count;

  thread_state_t
    *thread_handles;

  struct queue_state
    *qs;

  struct queue_test_rapid_enqueuing_and_dequeuing_state
    *qtreds;

  struct validation_info
    vi = { 50000, 50000 };

  atom_t
    user_data,
    thread,
    count,
    *per_thread_counters;

  enum data_structure_validity
    dvs[2];

  internal_display_test_name( "Rapid enqueuing and dequeuing (10 seconds)" );

  cpu_count = abstraction_cpu_count();

  queue_new( &qs, 100000 );

  for( loop = 0 ; loop < 50000 ; loop++ )
    queue_enqueue( qs, NULL );

  qtreds = malloc( sizeof(struct queue_test_rapid_enqueuing_and_dequeuing_state) * cpu_count );

  for( loop = 0 ; loop < cpu_count ; loop++ )
  {
    (qtreds+loop)->qs = qs;
    (qtreds+loop)->counter = (atom_t) loop << (sizeof(atom_t)*8-8);
  }

  thread_handles = malloc( sizeof(thread_state_t) * cpu_count );

  for( loop = 0 ; loop < cpu_count ; loop++ )
    abstraction_thread_start( &thread_handles[loop], loop, queue_test_internal_thread_rapid_enqueuer_and_dequeuer, qtreds+loop );

  for( loop = 0 ; loop < cpu_count ; loop++ )
    abstraction_thread_wait( thread_handles[loop] );

  free( thread_handles );

  queue_query( qs, QUEUE_QUERY_VALIDATE, (void *) &vi, (void *) dvs );

  // TRD : now check results
  per_thread_counters = malloc( sizeof(atom_t) * cpu_count );

  for( loop = 0 ; loop < cpu_count ; loop++ )
    *(per_thread_counters+loop) = 0;

  while( dvs[0] == VALIDITY_VALID and dvs[1] == VALIDITY_VALID and queue_dequeue(qs, (void *) &user_data) )
  {
    thread = user_data >> (sizeof(atom_t)*8-8);
    count = (user_data << 8) >> 8;

    if( thread >= cpu_count )
    {
      dvs[0] = VALIDITY_INVALID_TEST_DATA;
      break;
    }

    if( per_thread_counters[thread] == 0 )
      per_thread_counters[thread] = count;

    if( count < per_thread_counters[thread] )
      dvs[0] = VALIDITY_INVALID_ADDITIONAL_ELEMENTS;

    if( count >= per_thread_counters[thread] )
      per_thread_counters[thread] = count+1;
  }

  free( per_thread_counters );

  free( qtreds );

  queue_delete( qs, NULL, NULL );

  internal_display_test_result( 2, "queue", dvs[0], "queue freelist", dvs[1] );

  return;
}





/****************************************************************************/
thread_return_t CALLING_CONVENTION queue_test_internal_thread_rapid_enqueuer_and_dequeuer( void *queue_test_rapid_enqueuing_and_dequeuing_state )
{
  struct queue_test_rapid_enqueuing_and_dequeuing_state
    *qtreds;

  time_t
    start_time;

  atom_t
    user_data;

  assert( queue_test_rapid_enqueuing_and_dequeuing_state != NULL );

  qtreds = (struct queue_test_rapid_enqueuing_and_dequeuing_state *) queue_test_rapid_enqueuing_and_dequeuing_state;

  time( &start_time );

  while( time(NULL) < start_time + 10 )
  {
    queue_enqueue( qtreds->qs, (void *) (qtreds->counter++) );
    queue_dequeue( qtreds->qs, (void *) &user_data );
  }

  return( (thread_return_t) EXIT_SUCCESS );
}

