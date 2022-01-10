import secrets

from django.db.models import Q
from faker import Faker
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User


class CreateFakerUsers(APIView):
    def post(self, request, count):
        faker = Faker()

        for _ in range(count):
            username = faker.first_name()
            first_name = faker.first_name()
            last_name = faker.last_name()
            email = faker.email()
            password = 'Gpw9n9bf1'

            while User.objects.filter(Q(username__iexact=username)).exists():
                token = secrets.token_hex(3)
                username = f'{token}_{username}'
            while User.objects.filter(Q(email__iexact=email)).exists():
                token = secrets.token_hex(3)
                email = f'{token}_{email}'
            user = User.objects.create(
                username=username,
                first_name=first_name,
                last_name=last_name,
                email=email,
                password=password
            )
            user.set_password(password)
            user.save()

        return Response(f'Created {count} accounts successfully!')
