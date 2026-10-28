"""Pure selected-source integer model. No memory access or target operation."""
def uint(value,bits):
    if type(value)is not int or not 0<=value<1<<bits:
        raise ValueError('unsigned integer domain')
    return value

def band(mean,factor):
    mean=uint(mean,32);factor=uint(factor,16)
    delta=((mean*factor)&0xffffffff)>>8
    return ((mean-delta)&0xffff,(mean+delta)&0xffff)

def observe(mean,factor,threshold,value,counter,flag,aggregate):
    """One lane in c058/c314; no in-band reset, all stores have target width."""
    lower,upper=band(mean,factor)
    for v in (threshold,value,counter,aggregate):uint(v,16)
    uint(flag,8)
    outside=value>upper or value<lower
    if outside:
        counter=(counter+1)&0xffff
        if counter>threshold:
            if flag==0:aggregate=(aggregate+1)&0xffff
            flag=1
    return dict(lower=lower,upper=upper,outside=outside,counter=counter,
                flag=flag,aggregate=aggregate)

def publish(counter,flag):
    return (2*uint(counter,16)+uint(flag,8))&0xffff

def local_admission(primary,secondary,aa,ac,override):
    uint(primary,16);uint(secondary,8);uint(aa,16);uint(ac,16);uint(override,8)
    sb=(aa==1 or ac==1)and override!=0
    return (primary&1)==0 and (secondary==0 or sb)
