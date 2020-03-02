import pprint

import click

import minkipy

from . import default
from . import tasks
from . import workers
from . import queues

pretty = pprint.PrettyPrinter(depth=4)


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
@click.option('--queue', '-q', default=default.QUEUE, help='The queue to send the task to')
@click.argument('cmd', type=str)
@click.argument('args', type=str, nargs=-1)
def submit(project, folder, queue, cmd, args):
    """Submit a task to a queue"""
    minkipy.workon(project)
    task = minkipy.task(cmd, args, folder)
    minkipy.queue(queue).submit(task)


@minki.command()
@click.option('--project', '-p', default=None, help='The project to use')
@click.option('--max-tasks', '-n', default=1, help='Number of tasks to process')
@click.option('--timeout',
              '-t',
              default=10.,
              help='The maximum time (in seconds) to wait for a new task')
@click.argument('queue', type=str, default=default.QUEUE)
def run(project, max_tasks, timeout, queue):
    """Process a number of tasks"""
    minkipy.workon(project)
    task_queue = minkipy.queue(queue)
    workers.run(task_queue, max_tasks, timeout)


@minki.command()
@click.option('--project', '-p', default=None, help='The project to use, defaults to active')
@click.argument('queue', type=str, default=default.QUEUE)
def list(project, queue):
    """List queued tasks"""
    minkipy.workon(project)

    ls_queue = queues.queue(queue)
    for task in ls_queue:
        print("{} {}".format(task.obj_id, task.cmd))


@minki.group()
def project():
    pass


@project.command()
@click.argument('name', type=str)
def create(name):
    project = minkipy.project(name)
    click.echo("Created project '{}'".format(name))
    click.echo(pretty.pformat(project.to_dict()))


@project.command()
def list():
    active = minkipy.get_active_project()
    for project in minkipy.get_projects().values():
        line = [project.name]
        if project.uuid == active.uuid:
            line.append('[active]')

        click.echo(" ".join(line))


@project.command()
@click.argument('project', type=str)
def show(project):
    """Show the project settings"""
    projects = minkipy.get_projects()
    if project not in projects:
        click.echo("Project not found")
        return 1

    click.echo(pretty.pformat(projects[project].to_dict()))


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
