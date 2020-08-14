try:
    import cmd2

except ImportError:

    def get_commands():
        return []
else:
    import argparse
    import sys

    from . import projects

    class MinkiCommands(cmd2.CommandSet):
        workon_parser = argparse.ArgumentParser()
        workon_parser.add_argument('project', type=str)

        @cmd2.with_argparser(workon_parser)
        def do_workon(self, args):  # pylint: disable=no-self-use
            try:
                project = projects.workon(args.project)
            except ValueError as exc:
                print(exc, file=sys.stderr)
                return 1
            else:
                print("Switched to '{}'".format(project))

            return 0

    def get_commands():
        """Get all the pyos shell commands served by minkipy"""
        return [MinkiCommands()]
