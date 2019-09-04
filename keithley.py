import serial
import time
import datetime
import yagmail
import time
import numpy as np

class channel:
    '''
    Parameters
    ------------
    Here are some params
    '''
    def __init__(self, UpLim, LowLim, chanNums = [], initCmds = [], name = "default", \
                 convData = lambda x: x, \
                 logD = "C:/Users/E5/Desktop/Allan LABVIEW/E5 Logger/LoggerData", \
                 logDBackup = "C:/Users/E5/Desktop/Allan LABVIEW/E5 Logger/KeithleyLoggerBackup", \
                 errD = "C:/Users/E5/Desktop/Allan LABVIEW/E5 Logger/KeithleyLoggerBackup/Error/", \
                 logfreq = 60,\
                 dateTimeStringFormat = "%Y-%m-%d %H:%M:%S"):
        self.UpLim= UpLim
        self.LowLim = LowLim
        self.chanNums = chanNums
        self.initCmds = [cmd.format(chan=",".join([str(i) for i in chanNums])) for cmd in initCmds]
        self.logDirectory = logD
        self.logDirectoryBackup = logDBackup
        self.errDirectory = errD
        self.logfreq = logfreq
        self.name = name
        self.convData = convData
        self.lastTime = datetime.datetime.fromtimestamp(0)
        self.dateTimeStringFormat = dateTimeStringFormat
            
    def appendInitCmds(self, cmds):
        if isinstance(cmds, str):
            cmds = [cmds]
        self.initCmds.extend(cmds)
            
    def write(self, cmds):
        if hasattr(self, 'multimeter'):
           self.multimeter.write(cmds)
    # This is the logging part. Data is stored under a file "TEMP1 2012-01-19.csv", 
    # or whatever today's date is, and has lines of the format:
    # 2012-01-19 17:21:16, 24.458197         
    def processData(self,data,time):
        dt = time - self.lastTime
        if dt.seconds < self.logfreq:
            return
        self.lastTime = time
        timestr = time.strftime(self.dateTimeStringFormat)
        filetimestr = time.strftime("%Y-%m-%d")
        datastr = timestr + ''.join([', {:f}'.format(self.convData(i)) for i in data])
#         print(['{:f}'.format(self.convData(i)) for i in data])
#         for i in data:
#             print(i)
#             if ('{:f}'.format(self.convData(i))> 8) or ('{:f}'.format(self.convData(i))< 0):
#                 print(i, 'is out of bounds')
#             elif ('{:f}'.format(self.convData(i))< 8) and ('{:f}'.format(self.convData(i))> 0):
#                        'is messed up, it is currently reading', int(data[i])) 
        #print("{}: {}".format(self.name, datastr))
        # Write to file of format [logDirectory]/
        try:
            with open("%s%s %s.csv" % (self.logDirectory,self.name,filetimestr),'a') as f:
                f.write(datastr + '\n')
        except IOError:
            print "Some sort of IO error. Check the server connection?"
            with open("%sError - %s  %s.csv" % (self.errDirectory,self.name,filetimestr),'a') as f:
                f.write(datastr + '\n')
                f.write("Some sort of IO error. Check the server connection?")

        try:
            with open("%s%s %s.csv" % (self.logDirectoryBackup,self.name,filetimestr),'a') as f:
                f.write(datastr + '\n')
        except IOError:
            print "Ok, even backup log directory is having trouble. Shit has gone to hell! Abandon ship!"
wrong1 =[]
counter1= []
num=[]
wrong2=[]
class keithley:
    # default preamble
    preamble = ["*RST\n",
            "SYST:PRES\n",\
            "SYST:BEEP OFF\n",\
            "TRAC:CLE\n",\
            "TRAC:CLE:AUTO OFF\n",\
            "INIT:CONT OFF\n",\
            "TRIG:COUN 1\n",\
            "FORM:ELEM READ\n"]

    channels = []

    def __init__(self, channels = [], port=3, timeout=2, debug=False):
        self.appendChannels(channels)
        self.port = port
        self.timeout = timeout
        self.debug = debug;

    def __enter__(self):
        self.serial = serial.Serial(self.port, timeout=self.timeout)
        for command in self.preamble:
            self.write(command)
            time.sleep(0.5)
        self.serial.flushInput()
        return self

    def __exit__(self, *exc_info):
        try:
            close_it = self.serial.close
        except AttributeError:
            pass
        else:
            close_it()
    
    def write(self, command):
        if isinstance(command, str):
            if self.debug:
                print command.strip()
            self.serial.write(command)
        elif isinstance(command, list):
            for cmd in command:
                self.write(cmd)
        else:
            raise Exception
            
    def appendChannels(self, channels):
        if isinstance(channels, channel):
            channels = [channels]
        self.channels.extend(channels)
    
    def initChannels(self):
        clist = []
        idx = 0
        for channel in self.channels:
            channel.multimeter = self
            self.write(channel.initCmds)
            clist.extend([str(c) for c in channel.chanNums])
            channel.dataIdx = range(idx, idx + len(channel.chanNums))
            idx += len(channel.chanNums)
        scanlist = '(@' + ','.join(clist) + ')'
        self.write("ROUT:SCAN {}\n".format(scanlist))
        self.write("SAMP:COUN {}\n".format(len(clist)))
        self.write("ROUT:SCAN:LSEL INT\n")
                
    def getData(self):
        self.write("READ?\n")       

        data = self.serial.readline().split(',')       
        time = datetime.datetime.now()
        check= []
        ch= []
        conv =[]
        UL= []
        LL= []
        l= []
        wrong =[]
        counter= []
            

        try:
            print time.strftime("%Y-%m-%d %H:%M:%S") + ": " + ", ".join(["%.3g" % float(datum.strip('\x13').strip('\n').strip('').rstrip()[:-1]) for datum in data])
            for channel in self.channels:
                cdata = [float(data[i].strip('\x13').strip('\n').strip('').rstrip()[:-1]) for i in channel.dataIdx]
                check.append(cdata)
                ch.append(channel.chanNums)
                conv.append(channel.convData(cdata[0]))
                UL.append(channel.UpLim)
                LL.append(channel.LowLim)
                channel.processData(cdata,time)
            check =  [val for sublist in check for val in sublist]
#             print('Orignal data:', check)
            print'Converted data:', conv
#             print(UL)
#             print(LL)
            z=0
            for i in range(len(conv)):
                if (conv[i] > UL[i]) or (conv[i] < LL[i]):
                    wrong.append(ch[i])
                    counter.append(conv[i])
                    wrong1.append(ch[i])
                    counter1.append(conv[i])
            
            wrong= [val for sublist in wrong for val in sublist]
            global num
            num= np.array(len(wrong))
            if len(wrong) is not 0:
                print'Prohibited Values coming from these channels:', [wrong[i] for i in range(len(wrong))]
                z= 1
            if len(wrong) is 0:
                z=0
            global wrong2
            wrong2= wrong
            return z
   
        except ValueError:
            if data == ['']:
                print time.strftime("%Y-%m-%d %H:%M:%S") + ": Error: Received nothing from Keithley"
            else:
                print time.strftime("%Y-%m-%d %H:%M:%S") + ": Error: Received %s from Keithley" % (str(data))

    def mail(self):
        global wrong1
        global counter1
        global wrong2
        receiver = "amadiaheno@berkeley.edu"
        body = 'Channel(s)', yagmail.raw(wrong1[-len(wrong2):]),'is reading a prohibited value(s) of', yagmail.raw(counter1[-len(wrong2):]), 'GET BACK TO THE LAB, NOW!'


        yag = yagmail.SMTP(user='e5ultracoldberkeley1@gmail.com', password= 'superradiance', host= 'smtp.gmail.com')
        yag.send(
        to=receiver,
        subject="E5 Keithley Logger Problem",
        contents=body,
        )  
        
        del wrong1[:]
        del counter1[:]
        
    def check(self):
        
        return num
