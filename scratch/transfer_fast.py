import os
import sys

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
curr_dir = os.path.abspath('.')
if curr_dir not in sys.path:
    sys.path.insert(0, curr_dir)

import sqlite3
import json
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medicarehub.settings')
django.setup()

from catalogue.models import HealthCategory, Manufacturer, HealthCondition, Medicine, CategoryImage
from django.db import connection

SQLITE_PATH = os.path.join(curr_dir, 'db.sqlite3')

def fast_transfer():
    print("Starting Fast Bulk Transfer to Neon PostgreSQL...")
    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Clear existing to prevent duplicate conflicts
    print("Clearing tables in Postgres...")
    with connection.cursor() as pg_cur:
        pg_cur.execute("TRUNCATE TABLE catalogue_categoryimage_categories, catalogue_medicine_categories, catalogue_medicine_conditions, catalogue_categoryimage, catalogue_medicine, catalogue_healthcondition, catalogue_manufacturer, catalogue_healthcategory CASCADE;")

    # 1. Health Categories
    cur.execute("SELECT * FROM catalogue_healthcategory")
    cats = [
        HealthCategory(
            id=r['id'],
            name=r['name'],
            slug=r['slug'],
            source_folder=r['source_folder'],
            description=r['description'],
            icon=r['icon']
        )
        for r in cur.fetchall()
    ]
    HealthCategory.objects.bulk_create(cats)
    print(f"Bulk created {len(cats)} Categories.")

    # 2. Manufacturers
    cur.execute("SELECT * FROM catalogue_manufacturer")
    mfgs = [
        Manufacturer(
            id=r['id'],
            name=r['name'],
            slug=r['slug']
        )
        for r in cur.fetchall()
    ]
    Manufacturer.objects.bulk_create(mfgs)
    print(f"Bulk created {len(mfgs)} Manufacturers.")

    # 3. Health Conditions
    cur.execute("SELECT * FROM catalogue_healthcondition")
    conds = [
        HealthCondition(
            id=r['id'],
            name=r['name'],
            slug=r['slug'],
            description=r['description'],
            category_id=r['category_id'],
            icon=r['icon']
        )
        for r in cur.fetchall()
    ]
    HealthCondition.objects.bulk_create(conds)
    print(f"Bulk created {len(conds)} Conditions.")

    # 4. Medicines
    cur.execute("SELECT * FROM catalogue_medicine")
    meds = []
    for r in cur.fetchall():
        faqs_val = r['faqs']
        if isinstance(faqs_val, str):
            try:
                faqs_val = json.loads(faqs_val)
            except:
                faqs_val = []
        meds.append(
            Medicine(
                id=r['id'],
                name=r['name'],
                slug=r['slug'],
                generic_name=r['generic_name'],
                composition=r['composition'],
                form=r['form'],
                manufacturer_id=r['manufacturer_id'],
                category_id=r['category_id'],
                subcategory_id=r['subcategory_id'],
                description=r['description'],
                overview=r['overview'],
                uses=r['uses'],
                how_it_works=r['how_it_works'],
                side_effects=r['side_effects'],
                precautions=r['precautions'],
                storage=r['storage'],
                also_known_as=r['also_known_as'],
                pack_size=r['pack_size'],
                brand_name=r['brand_name'],
                strength=r['strength'],
                route=r['route'],
                active_ingredients=r['active_ingredients'],
                inactive_ingredients=r['inactive_ingredients'],
                dosage_information=r['dosage_information'],
                serious_side_effects=r['serious_side_effects'],
                contraindications=r['contraindications'],
                interactions=r['interactions'],
                source_name=r['source_name'],
                source_url=r['source_url'],
                last_verified_at=r['last_verified_at'],
                faqs=faqs_val,
                prescription_required=bool(r['prescription_required']),
                drug_type=r['drug_type'],
                habit_forming=bool(r['habit_forming']),
                pregnancy_category=r['pregnancy_category'],
                alcohol_interaction=r['alcohol_interaction'],
                is_featured=bool(r['is_featured']),
                is_active=bool(r['is_active'])
            )
        )
    Medicine.objects.bulk_create(meds)
    print(f"Bulk created {len(meds)} Medicines.")

    # 5. Category Images
    cur.execute("SELECT * FROM catalogue_categoryimage")
    imgs = [
        CategoryImage(
            id=r['id'],
            category_id=r['category_id'],
            medicine_id=r['medicine_id'],
            image=r['image'],
            image_hash=r['image_hash'],
            file_name=r['file_name'],
            file_path=r['file_path'],
            file_size=r['file_size'],
            is_primary=bool(r['is_primary']),
            is_active=bool(r['is_active'])
        )
        for r in cur.fetchall()
    ]
    CategoryImage.objects.bulk_create(imgs)
    print(f"Bulk created {len(imgs)} Category Images.")

    # 6. M2M Tables
    cur.execute("SELECT * FROM catalogue_medicine_categories")
    med_cats = cur.fetchall()
    with connection.cursor() as pg_cur:
        for r in med_cats:
            pg_cur.execute("INSERT INTO catalogue_medicine_categories (medicine_id, healthcategory_id) VALUES (%s, %s) ON CONFLICT DO NOTHING;", [r['medicine_id'], r['healthcategory_id']])

    cur.execute("SELECT * FROM catalogue_categoryimage_categories")
    img_cats = cur.fetchall()
    with connection.cursor() as pg_cur:
        for r in img_cats:
            pg_cur.execute("INSERT INTO catalogue_categoryimage_categories (categoryimage_id, healthcategory_id) VALUES (%s, %s) ON CONFLICT DO NOTHING;", [r['categoryimage_id'], r['healthcategory_id']])

    # Reset postgres sequences so new IDs auto-increment properly
    with connection.cursor() as pg_cur:
        for table in ['catalogue_healthcategory', 'catalogue_manufacturer', 'catalogue_healthcondition', 'catalogue_medicine', 'catalogue_categoryimage']:
            pg_cur.execute(f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), coalesce(max(id), 1)) FROM {table};")

    conn.close()

    print("\n✅ Fast Bulk Transfer Completed Successfully!")
    print(f"Health Categories in Postgres: {HealthCategory.objects.count()}")
    print(f"Manufacturers in Postgres:     {Manufacturer.objects.count()}")
    print(f"Medicines in Postgres:        {Medicine.objects.count()}")
    print(f"Category Images in Postgres:  {CategoryImage.objects.count()}")

if __name__ == '__main__':
    fast_transfer()
