from django.conf import settings

from datetime import datetime, timedelta

from postgresqleu.mailqueue.util import send_simple_mail
from postgresqleu.invoices.util import InvoiceManager

from models import Sponsor
import postgresqleu.invoices.models as invoicemodels

class InvoiceProcessor(object):
	# Process invoices for sponsorship (this should include both automatic
	# and manual invoices, as long as they are created through the system)
	def process_invoice_payment(self, invoice):
		try:
			sponsor = Sponsor.objects.get(pk=invoice.processorid)
		except Sponsor.DoesNotExist:
			raise Exception("Could not find conference sponsor %s" % invoice.processorid)

		if sponsor.confirmed:
			# This sponsorship was already confirmed. Typical case for this is the contract
			# was signed manually, and then the invoice was generated. In this case, we just
			# don't care, so we return without updating the date of the confirmation.
			return

		sponsor.confirmed = True
		sponsor.confirmedat = datetime.now()
		sponsor.confirmedby = "Invoice payment"
		sponsor.save()

		conference = sponsor.conference

		send_simple_mail(conference.sponsoraddr,
						 conference.sponsoraddr,
						 "Confirmed sponsor: %s" % sponsor.name,
						 "The sponsor\n%s\nhas completed payment of the sponsorship invoice,\nand is now activated.\nBenefits are not claimed yet." % sponsor.name)

	# An invoice was canceled.
	def process_invoice_cancellation(self, invoice):
		try:
			sponsor = Sponsor.objects.get(pk=invoice.processorid)
		except Sponsor.DoesNotExist:
			raise Exception("Could not find conference sponsor %s" % invoice.processorid)

		if sponsor.confirmed:
			raise Exception("Cannot cancel this invoice, the sponsorship has already been marked as confirmed!")

		# Else the sponsor is not yet confirmed, so we can safely remove the invoice. We will leave the
		# sponsorship registration in place, so we can create a new one if we have to.
		sponsor.invoice = None
		sponsor.save()


	# Return the user to the sponsor page if they have paid.
	def get_return_url(self, invoice):
		try:
			sponsor = Sponsor.objects.get(pk=invoice.processorid)
		except Sponsor.DoesNotExist:
			raise Exception("Could not find conference sponsorship %s" % invoice.processorid)
		return "%s/events/sponsor/%s/" % (settings.SITEBASE_SSL, sponsor.id)


# Generate an invoice for sponsorship
def create_sponsor_invoice(request, user_name, name, address, conference, level, sponsorid):
	invoicerows = [
		['%s %s sponsorship' % (conference, level), 1, level.levelcost],
	]
	manager = InvoiceManager()
	processor = invoicemodels.InvoiceProcessor.objects.get(processorname="confsponsor processor")
	return manager.create_invoice(
		request.user,
		request.user.email,
		user_name,
		'%s\n%s' % (name, address),
		'%s sponsorship' % conference.conferencename,
		datetime.now(),
		datetime.now() + timedelta(days=30),
		invoicerows,
		processor = processor,
		processorid = sponsorid,
		bankinfo = True,
		accounting_account = settings.ACCOUNTING_CONFSPONSOR_ACCOUNT,
		accounting_object = conference.accounting_object,
	)