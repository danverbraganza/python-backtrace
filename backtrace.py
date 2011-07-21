'''
Backtrace.py
------------

This module provides the backtrace function decorator.

This module maintains the stacktrace for every function that has been decorated,
and has not yet returned.
In addition, the arguments and return values of the last LOG_SIZE functions to
have returned is also saved.
'''

__author__ = "Danver Braganza"
__date__   = "2011-07-21"

import sys

LOG_SIZE = 5

# Naughty use of globals because I was getting late
_curr_stack = None
_returned_buffer = [0, [None] * LOG_SIZE]
# Cheap ringbuffer implementation

_last_val = None
_error_printed = False

def backtrace(fn):
    '''
    Function decorator, returns a function which saves its stack information.
    ''' 
    def backtraced_fn(*fn_args, **fn_kwargs):
        global _last_val
        with StackManager(fn, fn_args, fn_kwargs):
            _last_val = fn(*fn_args, **fn_kwargs)
            return _last_val
    backtraced_fn.func_name = fn.func_name
    return backtraced_fn

class StackFrame(object):
    '''
    This object stores the function name, the arguments, and, if present, the return value, of a
    particular function invocation.
    '''
    
    def __init__(self, parent, fn, args, kwargs):
        self.parent = parent
        self.fn = fn.func_name
        self.args = ",".join(map(str, args) +
                             ["{}={}".format(key,value) for key, value
                              in kwargs.items()])
        self.retval = None

    def level_rep(self, level, show_return=True):
        '''
        Return a string representation of this function invocation out, along with all its parents recursively.
        
        ''' 
        entab = '    ' * level
        rep = '{function}({args})'.format(
            function=self.fn, args=self.args)
        if show_return and self.retval is not None:
            rep += '\n\t{entab}Returned {ret}'.format(entab=entab,ret=repr(self.retval))
        if self.parent is not None:
            rep += '\n\t{entab}Parent was: {parent}'.format(entab=entab,parent=self.parent.level_rep(level + 1, show_return=False))
        else:
            rep += '\n\t{entab}Parent was ROOT'.format(entab=entab)
        return rep     

    def __repr__(self):
        return self.level_rep(0)
      
                             
class StackManager(object):
    def __init__(self, *args):
        self.args = args
        
    def __enter__(self):
        global _curr_stack
        _curr_stack = StackFrame(_curr_stack, *self.args)

    def __exit__(self, tipe, value, tb):
        global _curr_stack, _returned_buffer, _last_val
        if tb is None:  #Nothing went obviously wrong
            #Move current frame off the stack
            old_frame = _curr_stack
            _curr_stack = _curr_stack.parent
            old_frame.retval = _last_val
            #Put it in the circular buffer storing the last returned stack frames
            _returned_buffer[1][_returned_buffer[0]] = old_frame
            _returned_buffer[0] = (_returned_buffer[0] + 1) % LOG_SIZE
        else:
            global _error_printed
            if not _error_printed: #Only print out the error once
                print >>sys.stderr, "Error detected.  Printing backtrace"
                self.print_log()
                _error_printed = True 
            return False #Signal to Python that the error was not handled

    def print_log(self):
        for i in range(1, LOG_SIZE + 1):
            frame = _returned_buffer[1][(_returned_buffer[0] - i) % LOG_SIZE]
            if frame is not None:
                print >>sys.stderr, "Previous returned call: " + repr(frame)
        print >>sys.stderr, _curr_stack

if __name__ == "__main__":
    @backtrace
    def fib(n):
        if n <= 0:
            return 1
        b = fib(n - 2)
        a = fib(n - 1)
        if a - b < 3: return "Whoops"
        #Simulating a mistake which will not cause an exception until used.
        return a + b

    print "Return is " + str(fib(9)) #Never prints out

    

            
            
    


            
        


