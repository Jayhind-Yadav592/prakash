from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = "Creates or resets the default administrator account for the MediCare dashboard."

    def add_arguments(self, parser):
        parser.add_argument('--username', default='admin', help='Username for the admin account (default: admin)')
        parser.add_argument('--password', default='medicareadmin2026', help='Password for the admin account (default: medicareadmin2026)')
        parser.add_argument('--email', default='admin@medicare.com', help='Email for the admin account')

    def handle(self, *args, **options):
        username = options['username']
        password = options['password']
        email = options['email']

        user, created = User.objects.get_or_create(
            username=username,
            defaults={'email': email, 'is_staff': True, 'is_superuser': True}
        )
        user.set_password(password)
        user.email = email
        user.is_staff = True
        user.is_superuser = True
        user.save()

        action = "Created" if created else "Updated"
        self.stdout.write(self.style.SUCCESS(f"[OK] Admin user '{username}' successfully {action.lower()}!"))
        self.stdout.write(f"     Username: {username}")
        self.stdout.write(f"     Password: {password}")
        self.stdout.write(f"     Dashboard URL: /dashboard/login/")
