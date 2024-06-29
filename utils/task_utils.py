import logging
from functools import wraps
from datetime import datetime, timedelta
import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor

# Import the custom logging utilities
from .logging_helper import get_logger, log_exception, timed_function, sanitize_log_data

# Initialize logger
logger = get_logger(__name__)

# Initialize the scheduler
jobstores = {
    'default': SQLAlchemyJobStore(url='sqlite:///jobs.sqlite')
}
executors = {
    'default': ThreadPoolExecutor(20),
    'processpool': ProcessPoolExecutor(5)
}
job_defaults = {
    'coalesce': False,
    'max_instances': 3
}
scheduler = BackgroundScheduler(jobstores=jobstores, executors=executors, job_defaults=job_defaults, timezone=pytz.UTC)


@log_exception(logger)
@timed_function(logger)
def initialize_scheduler():
    """
    Initialize and start the background scheduler.

    This function sets up the APScheduler with predefined jobstores, executors, and job defaults.
    It should be called once when the application starts.

    Raises:
        Exception: If there's an error starting the scheduler.

    Example:
        initialize_scheduler()
    """
    try:
        scheduler.start()
        logger.info("Scheduler initialized and started successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize scheduler: {str(e)}")
        raise


@log_exception(logger)
@timed_function(logger)
def schedule_task(func, trigger, **trigger_args):
    """
    Schedule a task to be executed according to the specified trigger.

    Args:
        func (callable): The function to be executed.
        trigger (str): The type of trigger ('date', 'interval', or 'cron').
        **trigger_args: Arguments specific to the trigger type.

    Returns:
        str: The ID of the scheduled job.

    Raises:
        ValueError: If an invalid trigger type is provided.

    Example:
        def my_task():
            print("Executing my task")

        # Schedule task to run every day at 2:30 PM
        job_id = schedule_task(my_task, 'cron', hour=14, minute=30)
    """
    job = None
    try:
        if trigger == 'date':
            job = scheduler.add_job(func, 'date', **trigger_args)
        elif trigger == 'interval':
            job = scheduler.add_job(func, 'interval', **trigger_args)
        elif trigger == 'cron':
            job = scheduler.add_job(func, 'cron', **trigger_args)
        else:
            raise ValueError(f"Invalid trigger type: {trigger}")

        logger.info(f"Task {func.__name__} scheduled with job ID: {job.id}")
        return job.id
    except Exception as e:
        logger.error(f"Failed to schedule task {func.__name__}: {str(e)}")
        raise


@log_exception(logger)
def cancel_task(job_id):
    """
    Cancel a scheduled task.

    Args:
        job_id (str): The ID of the job to be cancelled.

    Raises:
        Exception: If there's an error cancelling the task.

    Example:
        cancel_task('my_job_id')
    """
    try:
        scheduler.remove_job(job_id)
        logger.info(f"Task with job ID {job_id} cancelled successfully.")
    except Exception as e:
        logger.error(f"Failed to cancel task with job ID {job_id}: {str(e)}")
        raise


@log_exception(logger)
def list_scheduled_tasks():
    """
    List all currently scheduled tasks.

    Returns:
        list: A list of dictionaries containing information about each scheduled job.

    Example:
        tasks = list_scheduled_tasks()
        for task in tasks:
            print(f"Job ID: {task['id']}, Next run time: {task['next_run_time']}")
    """
    try:
        jobs = scheduler.get_jobs()
        tasks = []
        for job in jobs:
            task_info = {
                'id': job.id,
                'func': job.func.__name__,
                'trigger': str(job.trigger),
                'next_run_time': job.next_run_time
            }
            tasks.append(task_info)
        logger.info(f"Retrieved {len(tasks)} scheduled tasks.")
        return tasks
    except Exception as e:
        logger.error(f"Failed to list scheduled tasks: {str(e)}")
        raise


@log_exception(logger)
@timed_function(logger)
def execute_task(func, *args, **kwargs):
    """
    Execute a task immediately and log its execution.

    This function is useful for running tasks on-demand or for testing scheduled tasks.

    Args:
        func (callable): The function to be executed.
        *args: Positional arguments to pass to the function.
        **kwargs: Keyword arguments to pass to the function.

    Returns:
        The return value of the executed function.

    Example:
        def my_task(x, y):
            return x + y

        result = execute_task(my_task, 3, 4)
        print(result)  # Output: 7
    """
    try:
        logger.info(f"Executing task: {func.__name__}")
        result = func(*args, **kwargs)
        logger.info(f"Task {func.__name__} executed successfully.")
        return result
    except Exception as e:
        logger.error(f"Failed to execute task {func.__name__}: {str(e)}")
        raise


def task_wrapper(func):
    """
    A decorator to wrap tasks with logging and error handling.

    This decorator should be used on functions that are scheduled as tasks.
    It ensures proper logging of task execution and handles any exceptions.

    Args:
        func (callable): The function to be wrapped.

    Returns:
        callable: The wrapped function.

    Example:
        @task_wrapper
        def my_scheduled_task():
            # Task logic here
            pass

        schedule_task(my_scheduled_task, 'interval', hours=1)
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            logger.info(f"Starting execution of task: {func.__name__}")
            result = func(*args, **kwargs)
            logger.info(f"Task {func.__name__} completed successfully.")
            return result
        except Exception as e:
            logger.exception(f"Error in task {func.__name__}: {str(e)}")
            raise

    return wrapper


# Initialize the scheduler when this module is imported
initialize_scheduler()
