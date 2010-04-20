from django.db import models
from django.contrib.auth.models import User

from postgresqleu.countries.models import Country

from datetime import date, timedelta

class Member(models.Model):
	user = models.ForeignKey(User, null=False, blank=False, primary_key=True)
	fullname = models.CharField(max_length=500, null=False, blank=False,
								verbose_name='Full name')
	country = models.ForeignKey(Country, null=False, blank=False)
	listed = models.BooleanField(null=False, blank=False, default=True,
								 verbose_name='Listed in the public membership list')
	paiduntil = models.DateField(null=True, blank=True)
	membersince = models.DateField(null=True, blank=True)

	@property
	def expiressoon(self):
		if self.paiduntil:
			if self.paiduntil < date.today() + timedelta(60):
				return True
			else:
				return False
		else:
			return True

	def __unicode__(self):
		return "%s (%s)" % (self.fullname, self.user.username)

class MemberLog(models.Model):
	member = models.ForeignKey(Member, null=False, blank=False)
	timestamp = models.DateTimeField(null=False)
	message = models.TextField(null=False, blank=False)

	def __unicode__(self):
		return "%s: %s" % (self.timestamp, self.message)