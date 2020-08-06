try:
    import cmd2

except ImportError:

    def get_commands():
        return []
else:
    import argparse

    from . import projects

    class MinkiCommands(cmd2.CommandSet):
        workon_parser = argparse.ArgumentParser()
        workon_parser.add_argument('project', type=str)

        @cmd2.with_argparser(workon_parser)
        def do_workon(self, app: cmd2.Cmd, args):  # pylint: disable=no-self-use
            try:
                project = projects.workon(args.project)
            except ValueError as exc:
                app.perror(exc)
            else:
                app.poutput("Switched to '{}'".format(project))

    def get_commands():
        """Get all the pyos shell commands served by minkipy"""
        return [MinkiCommands()]
