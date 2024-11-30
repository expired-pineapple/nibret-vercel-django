from django.core.management.base import BaseCommand
from properties.models import Loaners, Criteria, HomeLoan
import uuid
import random
from faker import Faker

class Command(BaseCommand):
    help = 'Generate sample home loan data'

    def handle(self, *args, **kwargs):
        fake = Faker()

        # Create Loaners
        for _ in range(20):
            Loaners.objects.create(
                id=uuid.uuid4(),
                logo=fake.image_url(),
                name=fake.company(),
                real_state_provided=random.choice([True, False]),
                phone=fake.phone_number()
            )

        # Create Criteria
        for _ in range(20):
            Criteria.objects.create(
                id=uuid.uuid4(),
                description=fake.paragraph()
            )

        # Create Home Loans
        loaners = Loaners.objects.all()
        criterias = Criteria.objects.all()
        for _ in range(20):
            HomeLoan.objects.create(
                id=uuid.uuid4(),
                name=fake.catch_phrase(),
                description=fake.paragraph(),
                loaner=random.choice(loaners),
                criterias=random.choice(criterias)
            )