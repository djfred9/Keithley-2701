import sys
import smtplib

class Condition:

	def __init__(self, channel, average=False, running=False, idle=False, lockout=False, index=0):
		self.channel = channel
		self.running = running
		self.idle = idle
		self.lockout = lockout
		self.average = average
		self.index = index
		
	def inRange(self, range):
		history = self.channel.history	
		if not history:
			return False
		if self.average:
			data = [item[self.index] for item in history]
			value = sum(data)/len(data)
			return value >= range[0] and value <= range[1]
		else:
			return all([item[self.index] >= range[0] and item[self.index] <= range[1] for item in history]) 
		
	def isRunning(self):		
		if not self.idle or not self.channel.history:
			return False
		else:
			item = self.channel.history[-1]
			return not (item[self.index] >= self.idle[0] and item[self.index] <= self.idle[1])
			
	def isLockout(self):
		if not self.lockout or not self.channel.history:
			return False
		return not self.inRange(self.lockout)			
			
	def isWarn(self, isRunning):		
		if isRunning:
			if not self.running or not self.channel.history:
				return False
			return not self.inRange(self.running)
		else:
			if not self.idle or not self.channel.history:
				return False
			return not self.inRange(self.idle)
			
	def getName(self):
		return self.channel.name
		
	def getWarning(self,isRunning):
		if isRunning:
			range = self.running
		else:
			range = self.idle

		history = self.channel.history	
		if not history:
			value = 'N/A'
		if self.average:
			data = [item[self.index] for item in history]
			value = "{:.2f}".format(sum(data)/len(data))
		else:
			data = [item[self.index] for item in history]
			value = "[{min:.2f}, {max:.2f}]".format(min=min(data),max=max(data))
				
		return "{name} = {value} is out of range ({low},{high})".format(name=self.channel.name,value=value,low=range[0],high=range[1])

class EmailReporter:
	def __init__(self, server, senderName, sender, recipients, subject):
		self.server = server

		self.senderName = senderName
		self.sender = sender
		self.recipients = recipients
		self.subject = subject

	def report(self, message):
	
		body = \
"""From: {senderName} <{sender}>
To: <{recipients}>
Subject: {subject}

{message}
""".format(senderName = self.senderName, sender=self.sender, recipients=", ".join(self.recipients), subject=self.subject, message=message)

		try:
			smtp = smtplib.SMTP(self.server)
			smtp.sendmail(self.sender, self.recipients, body)         
		except smtplib.SMTPResponseException as sre:
			print("Error sending email: SMTPResponseException: " + sre.smtp_code + " " + sre.smtp_error)
		except smtplib.SMTPRecipientsRefused as srr:
			print("Error sending email: SMTPRecipientsRefused")
			for recipient,error in srr.recipients.items():
				print("\t{0}: {1}".format(*error))
		except smtplib.SMTPException as e:
		   print("Error sending email:  {0}: {1}".format(type(e).__name__, e))
		
class Interlock:
	def __init__(self, stateCondition, conditions, reporter, statusFile):
		self.stateCondition = stateCondition
		self.conditions = conditions
		self.conditions.append(self.stateCondition)
		self.reporter = reporter
		self.statusFile = statusFile
		
		self.lastWarn = set([])
		self.lastLockout = set([])
		self.lockout = False
		self.wasRunning = False
		
	def checkInterlock(self):
		isRunning = self.stateCondition.isRunning()
		
		globalLockout = False
		lockoutChannels = set([])
		warnChannels = set([])
		warnings = []
		for condition in self.conditions:
			lockout = condition.isLockout()
			globalLockout = globalLockout or lockout

			if lockout:
				lockoutChannels.add(condition.getName())

			if condition.isWarn(isRunning):
				warnChannels.add(condition.getName())
				warnings.append(condition.getWarning(isRunning))

		if globalLockout:
			self.triggerLockout()

		if warnChannels != self.lastWarn:
			print('sending warning')
			self.sendWarning(warnings, globalLockout, isRunning, warnChannels)
			
		self.lastWarn = warnChannels
		self.wasRunning = isRunning

		self.saveStatus(globalLockout, isRunning, lockoutChannels, warnChannels)

	def triggerLockout(self):
		return True #not implemented yet

	def sendWarning(self, warnings, globalLockout, isRunning, warnChannels):
		message = []
		try:
			if globalLockout:
				message.append("Interlock: ENGAGED!")
				
			if isRunning:
				message.append("Status: running")
			else:
				message.append("Status: idle")
				
			if warnChannels:
				warnLabel = ", ".join(warnChannels)
				message.append("Warnings: ")
				for item in warnings:
					message.append("\t"+item)
			else:
				message.append("Warnings: N/A")			

			self.reporter.report("\n".join(message))
		except:
			e = sys.exc_info()[0]
			print("Error sending interlock warning: {0}: {1}".format(type(e).__name__, e))

	def saveStatus(self, globalLockout, isRunning, lockoutChannels, warnChannels):
		message = []
		try:
			if globalLockout:
				message.append("Interlock: ENGAGED")
				message.append("Lockout: " + ", ".join(lockoutChannels))
				
			if isRunning:
				message.append("Status: running")
			else:
				message.append("Status: idle")
				
			message.append("Warnings: " + ", ".join(warnChannels))
			
			with open(self.statusFile, 'w') as f:
				for line in message:
					f.write(line)
					f.write("\n")
		except:
			e = sys.exc_info()[0]
			print("Error saving interlock status: {0}: {1}".format(type(e).__name__, e))
				
		return True
		
