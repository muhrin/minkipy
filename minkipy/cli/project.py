import pprint

import click

import minkipy
from . import main

pretty = pprint.PrettyPrinter(depth=4)  # pylint: disable=invalid-name


@main.minki.group('project')
def project_():
    pass


@project_.command()
@click.argument('name', type=str)
def create(name):
    project = minkipy.project(name)
    click.echo("Created project '{}'".format(name))
    click.echo(pretty.pformat(project.to_dict()))


@project_.command()
def list():  # pylint: disable=redefined-builtin
    active = minkipy.get_active_project()
    for project in minkipy.get_projects().values():
        line = [project.name]
        if project.uuid == active.uuid:
            line.append('[active]')

        click.echo(" ".join(line))


@project_.command()
@click.argument('project', type=str, default=None, required=False)
def show(project):
    """Show the project settings"""
    if project is None:
        proj = minkipy.get_active_project()
    else:
        proj = minkipy.get_projects().get(project, None)

    click.echo("{}:".format(proj.name))

    if proj is None:
        click.echo("Project not found")
        return 1

    click.echo(pretty.pformat(proj.to_dict()))
    return 0
