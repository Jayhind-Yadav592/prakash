from django.test import TestCase, Client
from django.contrib.auth.models import User
from catalogue.models import Medicine, HealthCategory, Manufacturer, MedicineImage
from io import BytesIO
from PIL import Image

class DashboardTestSuite(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_user(
            username='testadmin',
            password='testpassword123',
            is_staff=True,
            is_superuser=True
        )
        self.category = HealthCategory.objects.create(name='Test Category', slug='test-category')
        self.mfg = Manufacturer.objects.create(name='Test Pharma', slug='test-pharma')
        self.medicine = Medicine.objects.create(
            name='Test Medicine 100mg',
            slug='test-medicine-100mg',
            generic_name='Test Generic',
            form='Tablet',
            strength='100mg',
            manufacturer=self.mfg,
            category=self.category,
            is_active=True
        )

    def test_unauthenticated_dashboard_redirect(self):
        res = self.client.get('/dashboard/')
        self.assertEqual(res.status_code, 302)
        self.assertIn('/dashboard/login/', res.url)

    def test_login_flow(self):
        # Invalid
        res = self.client.post('/dashboard/login/', {'username': 'testadmin', 'password': 'wrong'})
        self.assertEqual(res.status_code, 200)

        # Valid
        res = self.client.post('/dashboard/login/', {'username': 'testadmin', 'password': 'testpassword123'}, follow=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn('Dashboard Overview', res.content.decode('utf-8'))

    def test_dashboard_medicine_views(self):
        self.client.login(username='testadmin', password='testpassword123')
        
        # List view
        res = self.client.get('/dashboard/medicines/')
        self.assertEqual(res.status_code, 200)
        self.assertIn('Test Medicine 100mg', res.content.decode('utf-8'))

        # Add view GET
        res = self.client.get('/dashboard/medicines/add/')
        self.assertEqual(res.status_code, 200)

        # Add view POST with image
        img_io = BytesIO()
        test_img = Image.new('RGB', (200, 200), color=(10, 100, 200))
        test_img.save(img_io, format='JPEG')
        img_io.seek(0)
        img_io.name = 'new_med.jpg'

        res = self.client.post('/dashboard/medicines/add/', {
            'name': 'New Aspirin 500mg',
            'generic_name': 'Acetylsalicylic acid',
            'form': 'Tablet',
            'strength': '500mg',
            'manufacturer_id': self.mfg.id,
            'category_id': self.category.id,
            'is_active': 'on',
            'image': img_io,
        }, follow=True)
        self.assertEqual(res.status_code, 200)

        new_med = Medicine.objects.filter(name='New Aspirin 500mg').first()
        self.assertIsNotNone(new_med)
        self.assertTrue(new_med.get_display_image_url.startswith('/media/'))

        # Edit view POST
        res = self.client.post(f'/dashboard/medicines/edit/{new_med.id}/', {
            'name': 'New Aspirin 500mg (Updated)',
            'generic_name': 'Acetylsalicylic acid',
            'form': 'Tablet',
            'strength': '500mg',
            'manufacturer_id': self.mfg.id,
            'category_id': self.category.id,
            'is_active': 'on',
        }, follow=True)
        self.assertEqual(res.status_code, 200)
        new_med.refresh_from_db()
        self.assertEqual(new_med.name, 'New Aspirin 500mg (Updated)')

        # Delete view POST
        res = self.client.post(f'/dashboard/medicines/delete/{new_med.id}/', follow=True)
        self.assertEqual(res.status_code, 200)
        self.assertIsNone(Medicine.objects.filter(id=new_med.id).first())

    def test_dashboard_category_views(self):
        self.client.login(username='testadmin', password='testpassword123')

        # List
        res = self.client.get('/dashboard/categories/')
        self.assertEqual(res.status_code, 200)

        # Add
        res = self.client.post('/dashboard/categories/add/', {
            'name': 'Dermatology Care',
            'description': 'Skin health medicines and topicals',
        }, follow=True)
        self.assertEqual(res.status_code, 200)
        cat = HealthCategory.objects.filter(name='Dermatology Care').first()
        self.assertIsNotNone(cat)

        # Edit
        res = self.client.post(f'/dashboard/categories/edit/{cat.id}/', {
            'name': 'Dermatology & Skin',
            'description': 'Updated skin description',
        }, follow=True)
        self.assertEqual(res.status_code, 200)
        cat.refresh_from_db()
        self.assertEqual(cat.name, 'Dermatology & Skin')

        # Delete
        res = self.client.post(f'/dashboard/categories/delete/{cat.id}/', follow=True)
        self.assertEqual(res.status_code, 200)
        self.assertIsNone(HealthCategory.objects.filter(id=cat.id).first())
