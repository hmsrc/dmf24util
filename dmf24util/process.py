"""

 This is a library for miscellanous scripting support functions

"""
import sys, os
import subprocess
import shlex
from tempfile import SpooledTemporaryFile
import time

__all__=['validate_sudo', 'dangerous_process', 'pipestring_process', 'poll_processes', 'process', 'process_results', 'process_run', 'processes', 'run_processes', 'subprocess', 'typical_process']

# misc

def validate_sudo():
    subprocess.call(['sudo', '-v'])

# Subprocess wrappers

#
# Some simple wrappers for subprocess for common use cases.
#


def process_run(cmd_string, stdin=None):
    """Given a string representing a single command, open a process, and return
    the Popen process object.
    http://docs.python.org/2/library/subprocess.html#popen-objects

    >>> process_object = process_run('echo test')
    >>> isinstance(process_object, subprocess.Popen)
    True
    """
    return subprocess.Popen(shlex.split(cmd_string),
                                    stdin=stdin,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)


def process_results(process_object):
    """Given a process object, wait for it to complete then return a tuple:
    
    >>> (returncode, stdout, stderr) = process_results(process_run('echo my process'))
    >>> returncode
    0
    >>> stdout
    'my process\\n'
    >>> stderr
    ''
    """
    (stdout, stderr)=process_object.communicate()
    return (process_object.returncode, stdout, stderr)

def run_processes(cmdlist):
    """ Run a list of processes and return the list of objects without
    waiting for results
    
    >>> process_objects=run_processes(['echo one', 'echo two'])
    >>> [isinstance(obj, subprocess.Popen) for obj in process_objects]
    [True, True]
    """
    return [process_run(cmd) for cmd in cmdlist]

def processes(cmdlist):
    """Spawns a list of processes in rapid succession, then waits for all of them
    to exit.  Returns a list of result tuples [(exitcode, stdin, stderr), ...]

    >>> processes(['echo process 1', 'echo process 2'])
    [(0, 'process 1\\n', ''), (0, 'process 2\\n', '')]
    """
    return [process_results(proc) for proc in run_processes(cmdlist)]

def poll_processes(proclist, wait=3, tries=3, debug=None):
    """Given a list of process objects, poll each process in the list
    and update return codes.  Pull the list 'tries' times and wait 'wait'
    seconds between tries

    >>> process_objects=poll_processes(run_processes(['echo one', 'echo two']))    
    >>> [isinstance(obj.returncode, int) for obj in process_objects]
    [True, True]
    """
    if debug:
        sys.stderr.write("polling...\n")
    for proc in proclist:
        proc.poll()
    if tries!=0 and None in [proc.returncode for proc in proclist]:
        if debug:
            sys.stderr.write("Some processes not finished, sleeping %s seconds...\n" % wait)
        time.sleep(wait)
        poll_processes(proclist, wait=wait, tries=tries-1)
    return proclist

def process(cmd_string, stdin=None):
    """Given a string representing a single command, open a process, wait for it to terminate and then
    return standard out and standard in as a tuple
    
    >>> process("echo 1 2")
    (0, '1 2\\n', '')
    """
    return process_results(process_run(cmd_string, stdin=stdin))

def pipestring_process(cmd_string, stdin_string=''):
    """Pipe a python string to standard input for cmd_string

    >>> pipestring_process('grep 2', '1\\n2\\n3\\n')
    (0, '2\\n', '')
    """
    f=SpooledTemporaryFile()
    f.write(stdin_string)
    f.seek(0)
    results=process(cmd_string, stdin=f)
    f.close()
    return results

def typical_process(cmd_string, error_message='', stdin=None, stdout=None, stderr=None):
    """Call a process, write the results to stdout and stderr, and for nonzero
    return codes, print a custom error message before calling sys.exit.

    To write to files other than standard out and standard error, set
    the stdout and stderr parameters to file objects.

    Return (exitcode, stdout, stderr) for zero return codes."""

    if stdout is None:
        stdout=sys.stdout
    if stderr is None:
        stderr=sys.stderr

    results = process(cmd_string, stdin=stdin)
    stderr.write(results[2])
    stdout.write(results[1])
    if results[0] != 0:
        stderr.write(error_message)
        sys.exit(results[0])
    return results

def dangerous_process(cmd_string, error_message='', stdin=None, stdout=None,
                      stderr=None, sudo=False):
    """For processes that should be interactively verified before running.
    If the command uses 'sudo' to elevate privileges, set sudo to true and
    'sudo -v' will be called before executing the process."""
    sys.stdout.write("Running: %s\n" % cmd_string)
    checkval = raw_input("Confirm [y/N]:")
    if checkval.capitalize() == 'Y':
        if sudo:
            validate_sudo()
        typical_process(cmd_string,
                        error_message=error_message,
                        stdin=stdin,
                        stdout=stdout,
                        stderr=stderr)

if __name__=='__main__':
    import doctest
    doctest.testmod()
