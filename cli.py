#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import absolute_import
import logging
import os
import sys
import subprocess
import textwrap
import psutil
import argparse
import daemon
import time
import signal
from collections import namedtuple

GUNICORN_WORKER_READY_PREFIX = "[ready] "
WORKER_REFRESH_BATCH_SIZE = 1
WORKER_REFRESH_INTERVAL = 30


def restart_workers(gunicorn_master_proc, num_workers_expected):
    """
    Runs forever, monitoring the child processes of @gunicorn_master_proc and
    restarting workers occasionally.

    Each iteration of the loop traverses one edge of this state transition
    diagram, where each state (node) represents
    [ num_ready_workers_running / num_workers_running ]. We expect most time to
    be spent in [n/n]. `bs` is the setting webserver.worker_refresh_batch_size.

    The horizontal transition at ? happens after the new worker parses all the
    dags (so it could take a while!)

       V ─────────────────────────────────────────────────────────────────────┐
    [n / n] ──TTIN──> [ [n, n+bs) / n + bs ] ────?───> [n + bs/n + bs] ──TTOU─┘
       ^                          ^───────────────┘
       │
       │      ┌────────────────v
       └──────┴────── [ [0, n) / n ] <─── start

    We change the number of workers by sending TTIN and TTOU to the gunicorn
    master process, which increases and decreases the number of child workers
    respectively. Gunicorn guarantees that on TTOU workers are terminated
    gracefully and that the oldest worker is terminated.
    """

    def wait_until_true(fn):
        """
        Sleeps until fn is true
        """
        while not fn():
            time.sleep(0.1)

    def get_num_workers_running(gunicorn_master_proc):
        workers = psutil.Process(gunicorn_master_proc.pid).children()
        return len(workers)

    def get_num_ready_workers_running(gunicorn_master_proc):
        workers = psutil.Process(gunicorn_master_proc.pid).children()
        ready_workers = [
            proc for proc in workers
            if GUNICORN_WORKER_READY_PREFIX in proc.cmdline()[0]
        ]
        return len(ready_workers)

    def start_refresh(gunicorn_master_proc):
        batch_size = WORKER_REFRESH_BATCH_SIZE
        logging.debug('%s doing a refresh of %s workers',
                      state, batch_size)
        sys.stdout.flush()
        sys.stderr.flush()

        excess = 0
        for _ in range(batch_size):
            gunicorn_master_proc.send_signal(signal.SIGTTIN)
            excess += 1
            wait_until_true(lambda: num_workers_expected + excess ==
                            get_num_workers_running(gunicorn_master_proc))

    wait_until_true(lambda: num_workers_expected ==
                    get_num_workers_running(gunicorn_master_proc))

    while True:
        num_workers_running = get_num_workers_running(gunicorn_master_proc)
        num_ready_workers_running = get_num_ready_workers_running(gunicorn_master_proc)

        state = '[{0} / {1}]'.format(num_ready_workers_running, num_workers_running)

        # Whenever some workers are not ready, wait until all workers are ready
        if num_ready_workers_running < num_workers_running:
            logging.debug('%s some workers are starting up, waiting...', state)
            sys.stdout.flush()
            time.sleep(1)

        # Kill a worker gracefully by asking gunicorn to reduce number of workers
        elif num_workers_running > num_workers_expected:
            excess = num_workers_running - num_workers_expected
            logging.debug('%s killing %s workers', state, excess)

            for _ in range(excess):
                gunicorn_master_proc.send_signal(signal.SIGTTOU)
                excess -= 1
                wait_until_true(lambda: num_workers_expected + excess ==
                                get_num_workers_running(gunicorn_master_proc))

        # Start a new worker by asking gunicorn to increase number of workers
        elif num_workers_running == num_workers_expected:
            refresh_interval = WORKER_REFRESH_INTERVAL
            logging.debug(
                '%s sleeping for %ss starting doing a refresh...',
                state, refresh_interval
            )
            time.sleep(refresh_interval)
            start_refresh(gunicorn_master_proc)

        else:
            # num_ready_workers_running == num_workers_running < num_workers_expected
            logging.error((
                "%s some workers seem to have died and gunicorn"
                "did not restart them as expected"
            ), state)
            time.sleep(10)
            if len(
                psutil.Process(gunicorn_master_proc.pid).children()
            ) < num_workers_expected:
                start_refresh(gunicorn_master_proc)


def stop(args, **kwargs):
    path = os.path.expanduser("~/data_mgt")
    if not os.path.exists(path):
        os.makedirs(path)

    default_pidfile = os.path.join(path, 'data_mgt.pid')
    pidfile = args.pid or default_pidfile
    if os.path.isfile(pidfile):
        with open(pidfile, 'r') as f:
            for pid in f.readlines():
                print('Kill Frogdoctor Process: %s' % pid)
                p = psutil.Process(int(pid))
                p.terminate()
    else:
        print('No such processes')


def restart(args, **kwargs):
    stop(args, **kwargs)
    webserver(args, **kwargs)


def webserver(args, **kwargs):
    access_logfile = args.access_logfile or \
        settings.get('webserver', 'access_logfile')
    error_logfile = args.error_logfile or \
        settings.get('webserver', 'error_logfile')
    num_workers = args.workers or settings.get('webserver', 'workers')
    worker_timeout = (args.worker_timeout or
                      settings.get('webserver', 'webserver_worker_timeout'))
    ssl_cert = args.ssl_cert or conf.get('webserver', 'web_server_ssl_cert')
    ssl_key = args.ssl_key or conf.get('webserver', 'web_server_ssl_key')
    if not ssl_cert and ssl_key:
        raise FrogdoctorException(
            'An SSL certificate must also be provided for use with ' + ssl_key)
    if ssl_cert and not ssl_key:
        raise FrogdoctorException(
            'An SSL key must also be provided for use with ' + ssl_cert)

    RUNMODE = settings.get('core', 'run_mode').strip("'\"")
    if args.debug:
        cmd = sys.argv[0]
        subcommand = 'runserver'
        args = [cmd, subcommand, '%s:%s' % (args.hostname, args.port)]
        django_cmd(args)
    else:
        pid, stdout, stderr, log_file = setup_locations("webserver",
                                                        pid=args.pid)
        print(
            textwrap.dedent('''\
                Running the Gunicorn Server with:
                Workers: {num_workers} {args.workerclass}
                Host: {args.hostname}:{args.port}
                Timeout: {worker_timeout}
                Logfiles: {access_logfile} {error_logfile}
                PID: {pid}
                =================================================================\
            '''.format(**locals())))

        GUNICORN_CONFIG = os.path.join(BASE_DIR, 'bin',
                                       'gunicorn_config.py')
        run_args = [
            'gunicorn',
            '-w', str(num_workers),
            '-k', str(args.workerclass),
            '-t', str(worker_timeout),
            '-b', args.hostname + ':' + str(args.port),
            '-n', 'frogdoctor-webserver',
            '-p', str(pid),
            '-c', GUNICORN_CONFIG
        ]

        if args.access_logfile:
            run_args += ['--access-logfile', str(args.access_logfile)]

        if args.error_logfile:
            run_args += ['--error-logfile', str(args.error_logfile)]

        if args.daemon:
            run_args += ["-D"]
        if ssl_cert:
            run_args += ['--certfile', ssl_cert, '--keyfile', ssl_key]

        run_args += ["wsgi:application"]

        gunicorn_master_proc = subprocess.Popen(run_args)

        def kill_proc(dummy_signum, dummy_frame):
            gunicorn_master_proc.terminate()
            gunicorn_master_proc.wait()
            sys.exit(0)

        signal.signal(signal.SIGINT, kill_proc)
        signal.signal(signal.SIGTERM, kill_proc)

        # These run forever until SIG{INT, TERM, KILL, ...} signal is sent
        if settings.getint('webserver', 'worker_refresh_interval') > 0:
            restart_workers(gunicorn_master_proc, num_workers)
        else:
            while True:
                time.sleep(1)


def django_cmd(args):
    manage.run(args=args)


def version(args, **kwargs):
    print(conf.HEADER.format(version=get_version(),
                             company_name=get_company_name()))

Arg = namedtuple(
    'Arg', ['flags', 'help', 'action', 'default', 'nargs', 'type', 'choices',
            'metavar', 'required'])
Arg.__new__.__defaults__ = (None, None, None, None, None, None, None, None)


class CLIFactory(object):
    args = {
        'pid': Arg(
            ("--pid", ), "PID file location",
            nargs='?'),
        'daemon': Arg(
            ("-D", "--daemon"), "Daemonize instead of running"
                                "in the foreground",
            "store_true"),
        'stderr': Arg(
            ("--stderr", ), "Redirect stderr to this file"),
        'stdout': Arg(
            ("--stdout", ), "Redirect stdout to this file"),
        'log_file': Arg(
            ("-l", "--log-file"), "Location of the log file"),
        # webserver
        'port': Arg(
            ("-p", "--port"),
            type=int,
            help="The port on which to run the server"),
        'workers': Arg(
            ("-w", "--workers"),
            type=int,
            help="Number of workers to run the webserver on"),
        'workerclass': Arg(
            ("-k", "--workerclass"),
            choices=['sync', 'eventlet', 'gevent', 'tornado'],
            help="The worker class to use for Gunicorn"),
        'worker_timeout': Arg(
            ("-t", "--worker_timeout"),
            default=20,
            type=int,
            help="The timeout for waiting on webserver workers"),
        'hostname': Arg(
            ("-hn", "--hostname"),
            default='0.0.0.0',
            help="Set the hostname on which to run the web server"),
        'debug': Arg(
            ("-d", "--debug"),
            "Use the server that ships with Flask in debug mode",
            "store_true"),
        'access_logfile': Arg(
            ("-A", "--access_logfile"),
            default='-',
            help="The logfile to store the webserver access log."
                 "Use '-' to print to stderr."),
        'error_logfile': Arg(
            ("-E", "--error_logfile"),
            default='-',
            help="The logfile to store the webserver error log."
                 "Use '-' to print to stderr."),
    }
    subparsers = (
        {
            'func': webserver,
            'help': "Start a frogdoctor webserver instance",
            'args': ('port', 'workers', 'workerclass', 'worker_timeout',
                     'pid', 'daemon', 'stdout', 'stderr', 'access_logfile',
                     'error_logfile', 'log_file', 'ssl_cert', 'ssl_key',
                     'hostname', 'debug'),
        }, {
            'func': stop,
            'help': 'Stop a frogdoctor webserver instance',
            'args': ('pid', )
        }, {
            'func': restart,
            'help': 'Restart a frogdoctor webserver instance',
            'args': ('port', 'workers', 'workerclass', 'worker_timeout',
                     'pid', 'daemon', 'stdout', 'stderr', 'access_logfile',
                     'error_logfile', 'log_file', 'ssl_cert', 'ssl_key',
                     'hostname', 'debug')
        }, {
            'func': version,
            'help': "Show the version",
            'args': tuple(),
        }
    )
    subparsers_dict = {sp['func'].__name__: sp for sp in subparsers}

    @classmethod
    def get_parser(cls):
        parser = argparse.ArgumentParser(description='Frogdoctor Platform.')
        subparsers = parser.add_subparsers(
            help='sub-command help', dest='subcommand')
        subparsers.required = True

        subparser_list = cls.subparsers_dict.keys()
        for sub in subparser_list:
            sub = cls.subparsers_dict[sub]
            sp = subparsers.add_parser(sub['func'].__name__, help=sub['help'])
            sp.set_defaults(func=sub['func'])
            if sub.get('external_args'):
                get_argument_parser(parser=sp)
                for arg in sub['extra_args']:
                    arg = cls.args[arg]
                    kwargs = {
                        f: getattr(arg, f)
                        for f in arg._fields if f != 'flags' and getattr(arg, f)}
                    sp.add_argument(*arg.flags, **kwargs)
            else:
                for arg in sub['args']:
                    arg = cls.args[arg]
                    kwargs = {
                        f: getattr(arg, f)
                        for f in arg._fields if f != 'flags' and getattr(arg, f)}
                    sp.add_argument(*arg.flags, **kwargs)
        return parser


def get_parser():
    return CLIFactory.get_parser()
