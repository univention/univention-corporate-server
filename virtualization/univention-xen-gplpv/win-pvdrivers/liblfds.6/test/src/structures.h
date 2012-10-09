/***** structs *****/
#pragma pack( push, ALIGN_DOUBLE_POINTER )

/***** abstraction tests *****/
struct abstraction_test_dcas_state
{
  volatile atom_t
    *shared_counter;

  atom_t
    local_counter;
};

/***** freelist tests *****/
struct freelist_test_popping_state
{
  struct freelist_state
    *fs,
    *fs_thread_local;
};

struct freelist_test_pushing_state
{
  atom_t
    thread_number;

  struct freelist_state
    *source_fs,
    *fs;
};

struct freelist_test_popping_and_pushing_state
{
  struct freelist_state
    *local_fs,
    *fs;
};

struct freelist_test_counter_and_thread_number
{
  atom_t
    thread_number;

  unsigned long long int
    counter;
};

/***** queue tests *****/
struct queue_test_enqueuing_state
{
  struct queue_state
    *qs;

  atom_t
    counter;
};

struct queue_test_dequeuing_state
{
  struct queue_state
    *qs;

  int
    error_flag;
};

struct queue_test_enqueuing_and_dequeuing_state
{
  struct queue_state
    *qs;

  atom_t
    counter,
    thread_number,
    *per_thread_counters;

  unsigned int
    cpu_count;

  int
    error_flag;
};

struct queue_test_rapid_enqueuing_and_dequeuing_state
{
  struct queue_state
    *qs;

  atom_t
    counter;
};

/***** ringbuffer tests *****/
struct ringbuffer_test_reading_state
{
  struct ringbuffer_state
    *rs;

  int
    error_flag;

  atom_t
    read_count;
};

struct ringbuffer_test_writing_state
{
  struct ringbuffer_state
    *rs;

  atom_t
    write_count;
};

struct ringbuffer_test_reading_and_writing_state
{
  struct ringbuffer_state
    *rs;

  atom_t
    counter,
    *per_thread_counters;

  unsigned int
    cpu_count;

  int
    error_flag;
};

/***** slist tests *****/
struct slist_thread_start_state
{
  struct slist_state
    *ss;

  struct slist_element
    *se;

  time_t
    duration;

  unsigned long int
    iteration_modulo;
};

/***** stack tests *****/

/***** freelist benchmarks *****/
struct freelist_benchmark
{
  struct freelist_state
    *fs;

  atom_t
    operation_count;
};

/***** queue benchmarks *****/
struct queue_benchmark
{
  struct queue_state
    *qs;

  atom_t
    operation_count;
};

/***** ringbuffer benchmarks *****/
struct ringbuffer_benchmark
{
  struct ringbuffer_state
    *rs;

  atom_t
    operation_count;
};

/***** stack benchmarks *****/
struct stack_benchmark
{
  struct stack_state
    *ss;

  atom_t
    operation_count;
};

#pragma pack( pop )

