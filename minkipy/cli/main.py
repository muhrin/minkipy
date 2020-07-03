import pprint

import click

import minkipy

pretty = pprint.PrettyPrinter(depth=4)  # pylint: disable=invalid-name


@click.group()
def minki():
    pass


@minki.command()
@click.option('--project', '-p', default=None, help='The project to use')
@click.option('--folder',
              '-f',
              default='',
              help="The folder to run the task in. "
              "Defaults to the id of the task as the folder name")
@click.option('--queue', '-q', default=None, help='The queue to send the task to')
@click.argument('cmd', type=str)
@click.argument('args', type=str, nargs=-1)
def submit(project, folder, queue, cmd, args):
    """Submit a task to a queue.  Will use the project default queue if not supplied."""
    proj = minkipy.workon(project)
    if queue is None:
        queue = proj.default_queue

    task = minkipy.task(cmd, args, folder)
    minkipy.queue(queue).submit(task)


@minki.command()
@click.option('--project', '-p', default=None, help='The project to use')
@click.option('--max-tasks', '-n', default=1, help='Number of tasks to process')
@click.option('--timeout',
              '-t',
              default=10.,
              help='The maximum time (in seconds) to wait for a new task')
@click.argument('queue', type=str, default=None, required=False)
def run(project, max_tasks, timeout, queue):
    """Process a number of tasks.  Will use the project default queue if not supplied."""
    proj = minkipy.workon(project)
    if queue is None:
        queue = proj.default_queue

    task_queue = minkipy.queue(queue)
    num_ran = minkipy.workers.run(task_queue, max_tasks, timeout)
    click.echo("Ran {} tasks".format(num_ran))


@minki.command()
@click.option('--project', '-p', default=None, help='The project to use, defaults to active')
@click.option('--count', '-c', is_flag=True, help='Only show the number of tasks in each queue')
@click.argument('queues', type=str, nargs=-1)
def list(project, count: bool, queues):  # pylint: disable=redefined-builtin
    """List queued tasks.  Will use the project default queue if not supplied."""
    proj = minkipy.workon(project)
    if not queues:
        queues = (proj.default_queue,)

    for queue in queues:
        minki_queue = minkipy.queue(queue)
        click.echo("{}:".format(queue))
        verbosity = 2 if not count else 0
        minki_queue.list(verbosity=verbosity)


@minki.command()
@click.option('--project', '-p', default=None, help='The project to use, defaults to active')
@click.argument('queue', type=str, default=None, required=False)
def purge(project, queue):
    """Remove all the tasks in a queue.  Will use the project default queue if not supplied."""
    proj = minkipy.workon(project)
    if queue is None:
        queue = proj.default_queue

    minki_queue = minkipy.queue(queue)
    num_purged = minki_queue.purge()
    click.echo("Cancelled {} tasks".format(num_purged))


@minki.command()
@click.argument('project', type=str)
def workon(project):
    """Set the active project"""
    try:
        minkipy.set_active_project(project)
    except ValueError as exc:
        click.echo(exc)
        return 1

    click.echo("Done")
    return 0
