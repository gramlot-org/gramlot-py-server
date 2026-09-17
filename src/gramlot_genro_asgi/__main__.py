"""Run a local experimental Genro ASGI host."""
import argparse
from pathlib import Path
from genro_asgi import BaseServer
from .application import GramlotApplication


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--instance', help='Legacy GnrApp instance name or directory')
    parser.add_argument('--port', type=int, default=8065)
    args = parser.parse_args()
    if args.instance:
        from gnr.app.gnrapp import GnrApp
        from .genropy import GenropyApplication
        legacy = GnrApp(args.instance)
        legacy.db.closeConnection()
        legacy.db.clearCurrentEnv()
        application = GenropyApplication(args.directory, genropy_application=legacy)
    else:
        application = GramlotApplication(args.directory)
    BaseServer(applications=[application]).serve(host='127.0.0.1', port=args.port)


if __name__ == '__main__':
    main()
