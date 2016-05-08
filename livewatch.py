import os
import signal
import sys
from subprocess import Popen
from time import time, sleep

def log( message ):
    print 'LiveWatch: ' + message

class LiveWatch:
    def __init__(self,
                 cmd,
                 maximum_number_of_restarts=10,
                 probe = None,
                 probe_frequency=10,
                 status_file=None ):
        self._cmd = cmd
        self._maximumNumberOfRestarts = maximum_number_of_restarts
        self._probeFrequency = probe_frequency
        self._restartCount = 0
        self._probe = probe
        self._lastProbeTime = time()
        self._process = start_process(self._cmd)

    def run(self):
        terminated = False
        while not terminated:
            result = self.__tick();
            sleep(0.3);
            if result == 'stop':
                exit(1)

    def __tick(self):
        rc = self._process.poll()
        if ( rc is not None ):
            return self.restart()
        elif ( time() - self._lastProbeTime ) > 10:
            self._lastProbeTime = time()
            probe_result = self.probe()
            if not probe_result:
                self.restart()
        else:
            return 'continue'

    def restart(self):
        if ( self._process.returncode is None ):
            kill_process(self._process)

        self._restartCount += 1
        if self._restartCount > 10:
            return 'stop'

        self._process = start_process(self._cmd)
        return 'continue'


    def process_terminated(self):
        if self._restartCount + 1:
            return None

    def probe(self):
        if (self._probe is not None):
            log( 'probing...' )


            if not self._probe():
                log( 'probe failed' )
                return False
            else:
                log('probe OK')
                return True
        return True

    def probe_failed(self):
        if self._restartCount + 1:
            return None
        else:
            kill_process( self._process )
            self._process = start_process(self.cmd)
            return

def start_process( cmd ):
    log("starting process \"{0}\"".format(cmd) )
    p  = Popen( cmd, shell=True, cwd='.')
    log("    process started, pid: {0}".format(p.pid))
    return p

def kill_process( process ):
    log( "killing process \"{0}\"".format(process.pid) )
    os.kill( process.pid, signal.SIGTERM)


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Executes program, watches for it and restarts it if necessary')
    parser.add_argument( 'cmd', type=str, help='program to execute and watch' )
    parser.add_argument( 'args',nargs=argparse.REMAINDER, help='program args' )
    parser.add_argument( '-p', '--probe', type=str, action='store' );
    parser.add_argument( '-s', '--status-file', type=str, action='store' );
    parser.add_argument( '-e', '--probe-frequency', type=int, default=10, action='store' );
    parser.add_argument( '-m', '--maximum-restarts', type=int, default=3, action='store' );


    args = parser.parse_args( sys.argv[1:] );

    probe = None
    if args.probe is not None:
        def script_probe():
            log('running probe {0}'.format(args.probe))
            p = Popen(args.probe, shell=True, cwd='.')
            rc = p.wait()
            log( ' exit code: {0}'.format(rc))
            return rc == 0

        probe = script_probe


    live_watch = LiveWatch([args.cmd] + args.args,
                           maximum_number_of_restarts=args.maximum_restarts,
                           probe_frequency=args.probe_frequency,
                           probe = probe,
                           status_file = args.status_file)
    live_watch.run();


if __name__ == '__main__':
    main()