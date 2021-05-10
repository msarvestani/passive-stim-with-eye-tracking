# Template for a triggering class. 
# A triggering class must contain each of these functions.
#They can be empty / do nothing, but they must all be defined.
#Have a look at the noTrigger class for an example of a minimal implementation.

class trigger:
    def __init__(self, args):
        print "Template trigger code initializing"
        raise NotImplementedError

    def preStim(self, args):
        print "This code runs before each stim is displayed"
        raise NotImplementedError

    def postStim(self, args):
        print "This code runs after each stim is displayed"
        raise NotImplementedError

    def preFlip(self, args):
        print "This code runs before each stimulus frame is displayed"
        raise NotImplementedError

    def postFlip(self, args):
        print "This code runs after each stimulus frame is displayed"
        raise NotImplementedError

    def wrapUp(self, args):
        print "This code is run after all stimuli have run."
        raise NotImplementedError 