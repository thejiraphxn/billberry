from snowflake_id import Generator

def is_pretty(numstr):
    if numstr.startswith('0'):
        return False
    for i in range(len(numstr) - 2):
        if numstr[i] == numstr[i+1] == numstr[i+2]:
            return False
        
    for i in range(len(numstr) - 3):
        s = numstr[i:i+4]
        if s in '0123456789' or s in '9876543210':
            return False
        try:
            nums = [int(c) for c in s]
            if nums == list(range(nums[0], nums[0]+4)):
                return False
            if nums == list(range(nums[0], nums[0]-4, -1)):
                return False
        except:
            continue
    return True

def generate_pretty_id():
    gen = Generator(datacenter_id=1, worker_id=1)
    while True:
        id_int = gen.generate()
        numstr = str(id_int)[-10:]
        if is_pretty(numstr):
            return numstr
        