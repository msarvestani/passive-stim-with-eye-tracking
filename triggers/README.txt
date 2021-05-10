Triggering code
===============

Triggering code is separate from the stimulus display code. Each of the files in this directory is for a specific type of triggering.

To get a sense of how the triggering code works, take a look at "abstractTrigger.py" and "noTrigger.py". 

**abstractTrigger.py** is the abstract class: it lays down some rules about how every trigger class will operate. It says that, to be a triggering class, you are required to have certain functions like preStim and postStim in there.

**noTrigger.py** is the smallest possible concrete class that implements abstractTrigger. All its methods just pass, they do nothing. This is what you want when a stimulus does not need any triggering.

All of the required functions take an argument called "args". This is your spot to pass in any data that the function will need. For example, on preStim, you might want to send out a stim number via a DAQ. The stimulus display code can pass the stim number to its triggering class through the args parameter. If you need multiple arguments, just pass a Python list.



