#!/usr/bin/env python3
"""Execute actual released smoothing opcodes in a bounded C55 model.
Not cycle-accurate; does not emulate peripherals, interrupts or all status effects.
"""
from pathlib import Path
import argparse,json,random
from patch_firmware import parse,file_offset,sha
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('firmware',type=Path)
args=p.parse_args()
b=args.firmware.read_bytes()
patch=json.loads((ROOT/'patches/1.9C.json').read_text())
if sha(b) not in {x['sha256'] for x in patch['targets'].values()}:
 p.error('Expected a reconstructed release image')
ss,end=parse(b)
labels=json.loads((ROOT/'patches/clock-labels.json').read_text())
def read(a,n):o=file_offset(ss,a);return b[o:o+n]
def signed(v,bits):v&=(1<<bits)-1;return v-(1<<bits) if v>>(bits-1) else v
class CPU:
 def __init__(self,m,status=0x100):
  self.m=dict(m);self.ac=[0]*4;self.r={i:0 for i in range(4,16)}
  self.sp=0x1ff00;self.initial_sp=self.sp;self.st1=status;self.tc=False
  self.skip=False;self.writes=[];self.loads=[];self.steps=0;self.depth=0;self.minsp=self.sp;self.system_stack=[]
 def get(self,i):return self.ac[i] if i<4 else signed(self.r[i],16)
 def set(self,i,v):
  if i<4:self.ac[i]=signed(v,40)
  else:self.r[i]=v&65535
 def put(self,a,v):self.m[a]=v&65535;self.writes.append(a)
 def push(self,v):self.sp-=1;self.put(self.sp,v);self.minsp=min(self.sp,self.minsp)
 def pop(self):v=self.m[self.sp];self.sp+=1;return v
 def dbl(self,a):
  assert a%2==0,hex(a)
  self.loads.append(a)
  v=self.m[a]<<16|self.m[a+1]
  return signed(v,32) if self.st1&0x100 else v
 def putdbl(self,a,v):assert a%2==0;self.put(a,v>>16);self.put(a+1,v)
 def condition(self,c):
  if c in (0x64,0x74):return self.tc if c==0x64 else not self.tc
  v=self.get(c&15)
  return [v==0,v!=0,v<0,v<=0,v>0,v>=0][c>>4]
 def run(self,pc):
  for _ in range(30000):
   self.steps+=1;p=pc;d=read(pc,8);n=None
   if d[0]==0x6a:pc=int.from_bytes(d[1:4],'big');continue
   if d[0]==0x6c:
    self.system_stack.append((pc+4)>>16);self.push(pc+4);self.depth+=1;pc=int.from_bytes(d[1:4],'big');continue
   if d[:2]==bytes.fromhex('4804'):
    if self.depth==0:return
    lo=self.pop();hi=self.system_stack.pop();pc=hi<<16|lo;self.depth-=1;continue
   if d[0]==0x6d:
    pc+=4+(int.from_bytes(d[2:4],'big',signed=True) if self.condition(d[1]) else 0);continue
   if d[0]==0x96:
    self.skip=not self.condition(0x64 if d[1]==0xe4 else d[1]);pc+=2;continue
   if d[:2] in (bytes.fromhex('b506'),bytes.fromhex('bb06')):
    assert d[2]==0x98
    if d[0]==0xb5:self.push(self.st1)
    else:self.st1=self.pop()
    n=3
   elif d[:2]==bytes.fromhex('4683'):self.st1|=0x100;n=2
   elif d[:2]==bytes.fromhex('5007'):
    assert self.sp%2==0,('double push alignment',hex(p),hex(self.sp))
    self.push(self.ac[0]);self.push(self.ac[0]>>16);n=2
   elif d[:2]==bytes.fromhex('5003'):
    hi=self.pop();lo=self.pop();self.ac[0]=signed(hi<<16|lo,32);n=2
   elif d[0]==0x50 and d[1] in (0x46,0x66):self.push(self.get(d[1]>>4));n=2
   elif d[0]==0x50 and d[1] in (0x42,0x62):self.set(d[1]>>4,self.pop());n=2
   elif d[0]==0x4e:self.sp+=signed(d[1],8);n=2
   elif d[0] in (0xa0,0xa1) and d[1]==0x31:
    val=self.m[int.from_bytes(d[2:5],'big')]
    self.ac[d[0]&1]=signed(val,16) if self.st1&0x100 else val;n=5
   elif d[0]==0x76:self.set(d[3]>>4,signed(int.from_bytes(d[1:3],'big'),16));n=4
   elif d[0]==0x3c:
    if not self.skip:self.set(d[1]&15,d[1]>>4)
    self.skip=False;n=2
   elif d[0]==0x22:self.set(d[1]&15,self.get(d[1]>>4));n=2
   elif d[0]==0x90:
    self.r[(d[1]&15)]=self.ac[d[1]>>4]&0x7fffff;n=2
   elif d[0]==0x24:
    if not self.skip:self.set(d[1]&15,self.get(d[1]&15)+self.get(d[1]>>4))
    self.skip=False;n=2
   elif d[0]==0x26:self.set(d[1]&15,self.get(d[1]&15)-self.get(d[1]>>4));n=2
   elif d[0] in (0x40,0x42):
    k=d[1]>>4;reg=d[1]&15;self.set(reg,self.get(reg)+(k if d[0]==0x40 else -k));n=2
   elif d[:2]==bytes.fromhex('444a'):self.set(10,self.get(10)>>1);n=2
   elif d[:3]==bytes.fromhex('18018a'):self.set(8,self.get(10)&1);n=3
   elif d[0]==0x10:
    dst=(d[1]>>6)&3;src=(d[1]>>4)&3;shift=signed(d[2],6)
    v=self.ac[src]
    if d[1]&15==5:
     if not self.st1&(1<<10):v=signed(v,32) if self.st1&0x100 else v&0xffffffff
     v=v<<shift if shift>=0 else v>>-shift
     assert -(1<<31)<=v<(1<<31),('arithmetic range',hex(p),v)
    else:
     assert d[1]&15==7 and shift==8
     v<<=shift
    self.ac[dst]=signed(v,40);n=3
   elif d[0]==0xed:
    if d[1]==0x31:addr=int.from_bytes(d[3:6],'big');n=6
    elif d[1] in (0x61,0x63,0x6d):
     addr=self.r[11]+(int.from_bytes(d[3:5],'big',signed=True) if d[1]==0x6d else 0)
     n=5 if d[1]==0x6d else 3
     if d[1]==0x63:self.r[11]+=2
    else:raise AssertionError(d.hex())
    self.ac[d[2]>>4]=self.dbl(addr)
   elif d[0]==0xeb:
    assert d[1] in (0x21,0x23)
    self.putdbl(self.r[9],self.ac[d[2]>>4]);self.r[9]+=2 if d[1]==0x23 else 0;n=3
   elif d[:3] in (bytes.fromhex('120810'),bytes.fromhex('124450')):
    self.tc=self.ac[0]>=self.ac[1] if d[1]==8 else self.get(4)<self.get(5);n=3
   elif d[:2]==bytes.fromhex('c031'):self.put(int.from_bytes(d[2:5],'big'),self.ac[0]);n=5
   elif d[:3]==bytes.fromhex('e63100'):self.put(int.from_bytes(d[3:6],'big'),0);n=6
   elif d[0]==0x20:raise AssertionError(('unreachable padding executed',hex(p)))
   else:raise AssertionError(('unknown',hex(p),d.hex()))
   pc+=n
  raise AssertionError('execution limit')

def fixture(samples,flag,start=0):
 m={0x7bcc:1,0x7bcd:start,0x7bce:3000,0x7bd8:flag&65535,0x7bd0:2,0x7bd1:0,0x7bd2:3,0x7bd3:0}
 for k,frame in enumerate(samples):
  for ch,v in enumerate(frame):
   a=0x6300+(ch//2)*256+k*4+(ch%2)*2;m[a]=(v>>16)&65535;m[a+1]=v&65535
 return m

def reference(samples,flag):
 v=[row[:] for row in samples]
 if flag:
  for k in (range(32) if flag>0 else range(31,-1,-1)):
   weight=31-k if flag>0 else k;target=k if flag>0 else k+1
   for ch in range(4):
    a=signed(samples[k][ch],32)>>8;b=signed(samples[k+1][ch],32)>>8
    v[target][ch]=((a*32+(b-a)*weight)//32<<8)&0xffffffff
 return ([samples[0]]+v if flag>0 else v[1:] if flag<0 else v),v

rng=random.Random(92027)
suites=[[[0]*4 for _ in range(64)],[[0x7fffffff,0x80000000,0xffffffff,0x00000100] for _ in range(64)],[[((0x7fffff if k%2 else -0x800000)<<8)&0xffffffff]*4 for k in range(64)]]
suites += [[[rng.getrandbits(32) for _ in range(4)] for _ in range(64)] for _ in range(40)]
# Distinct lane ramps and isolated impulses catch stride, channel and source overwrite errors.
suites.append([[(10000*k+c*13)<<8 for c in range(4)] for k in range(64)])
for ch in range(4):
 v=[[0]*4 for _ in range(64)];v[15][ch]=0x7fffff00;suites.append(v)
count=0;maxsteps={};maxstack=0
for samples in suites:
 for flag in (-1,0,1):
  for start in (0,2,2996,2998):
   m=fixture(samples,flag,start);cpu=CPU(m);cpu.sp-=1;initial=cpu.sp;cpu.r[6]=0x4567
   cpu.run(0x3d96d)
   expected,staged=reference(samples,flag)
   assert cpu.sp==initial and cpu.r[6]==0x4567 and cpu.st1==0x100
   assert cpu.m[0x7bcd]==(start+2*len(expected))%3000 and cpu.m[0x7bd8]==0
   for k,frame in enumerate(expected):
    for ch,val in enumerate(frame):
     a=(0x20000 if ch<2 else 0x30000)+((start+2*k)%3000)*2+(ch%2)*2
     actual=cpu.m[a]<<16|cpu.m[a+1];assert actual==val,('sample',flag,start,k,ch,hex(actual),hex(val))
   for k,frame in enumerate(staged):
    for ch,val in enumerate(frame):
     a=0x6300+(ch//2)*256+k*4+(ch%2)*2
     assert cpu.m[a]<<16|cpu.m[a+1]==val
   allowedwrites={0x7bcd,0x7bd8}|set(range(cpu.minsp,0x1ff00))|set(range(0x20000,0x20000+6000))|set(range(0x30000,0x30000+6000))
   if flag:allowedwrites|=set(range(0x6300,0x6500))
   assert set(cpu.writes)<=allowedwrites
   assert all(a in (0x7bd0,0x7bd2) or 0x6300<=a<0x6500 for a in cpu.loads)
   maxsteps[flag]=max(maxsteps.get(flag,0),cpu.steps);maxstack=max(maxstack,0x1ff00-cpu.minsp);count+=1
# Disabled producer is inert, including pending correction and input buffers.
cpu=CPU(fixture(suites[2],-1));cpu.m[0x7bcc]=0;before=dict(cpu.m);cpu.run(0x3d96d);assert cpu.m==before
# Direct worker: restores caller registers and complete status word, across
# incoming SXMD/M40/SATD settings. This does not emulate saturation hardware;
# the checked arithmetic stays strictly within signed32 at every shift.
statuscases=0
for flag in (-1,1):
 for status in range(0,0x800,0x100):
  cpu=CPU(fixture(suites[2],flag),status);cpu.sp-=1;cpu.initial_sp=cpu.sp;cpu.ac[0]=2998;cpu.r[4]=17;cpu.r[6]=42
  cpu.run(labels['worker'])
  assert cpu.ac[0]==2998 and cpu.r[4]==17 and cpu.r[6]==42 and cpu.st1==status and cpu.sp==cpu.initial_sp
  _,staged=reference(suites[2],flag)
  for k,frame in enumerate(staged):
   for ch,val in enumerate(frame):
    a=0x6300+ch//2*256+k*4+ch%2*2;assert cpu.m[a]<<16|cpu.m[a+1]==val
  statuscases+=1
report=dict(status='PASS — bounded emitted-opcode checks',producer_cases=count,worker_status_cases=statuscases,max_instructions=maxsteps,max_stack_words=maxstack,normal_blocks='exact raw32 samples',corrected_blocks='65/63 frames; shared dyadic phase for four channels; floor quantization <1 significant24-bit LSB',limitations=['Not cycle-accurate or peripheral emulation','Linear interpolation attenuates high frequencies during correction','Does not assess audible quality or long-term reliability'])
print(json.dumps(report,indent=2))
