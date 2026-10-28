"""Pure narrow stock-control effects. Call admission and asynchronous writes external."""
def u16(value):
 if type(value)is not int or not 0<=value<=65535:raise ValueError('u16')
 return value

def arm(trainer,latch,root2468):
 u16(trainer);u16(latch);u16(root2468)
 if latch==0 and root2468==1 and trainer==0:trainer=1
 if trainer==3:trainer=1
 return trainer

def pause(trainer,first_argument):
 u16(trainer)
 return 3 if first_argument==0 and trainer==1 else trainer

def finish(trainer,publish_control):
 u16(trainer);u16(publish_control)
 return (2,publish_control==1)if trainer==1 else(trainer,False)

def gate_on(gate):
 u16(gate)
 return 1 if gate==0 else gate

def gate_off(gate):
 u16(gate)
 return 0 if gate==1 else gate

def dispatch_gate(mode,gate):
 u16(mode)
 return gate_on(gate)if mode in(8,10)else gate_off(gate)
