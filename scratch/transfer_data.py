import os
import sys

# Ensure current project directory is in sys.path
BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
curr_dir = os.path.abspath('.')
if curr_dir not in sys.path:
    sys.path.insert(0, curr_dir)

import sqlite3
import django

# Setup Django (which connects to Neon Postgres via settings.py)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medicarehub.settings')
django.setup()

from catalogue.models import HealthCategory, Manufacturer, HealthCondition, Medicine, CategoryImage
from django.contrib.auth.models import User

SQLITE_PATH = os.path.join(curr_dir, 'db.sqlite3')

def transfer_all_data():
    print(f"Reading data from SQLite: {SQLITE_PATH}")
    if not os.path.exists(SQLITE_PATH):
        print("db.sqlite3 not found!")
        return

    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # 1. Health Categories
    print("--- Transferring Health Categories ---")
    cur.execute("SELECT * FROM catalogue_healthcategory")
    cat_rows = cur.fetchall()
    cat_map = {}
    for r in cat_rows:
        obj, created = HealthCategory.objects.update_or_create(
            id=r['id'],
            defaults={
                'name': r['name'],
                'slug': r['slug'],
                'source_folder': r['source_folder'],
                'description': r['description'],
                'icon': r['icon'],
            }
        )
        cat_map[r['id']] = obj
    print(f"Saved {len(cat_map)} Health Categories in PostgreSQL.")

    # 2. Manufacturers
    print("--- Transferring Manufacturers ---")
    cur.execute("SELECT * FROM catalogue_manufacturer")
    mfg_rows = cur.fetchall()
    mfg_map = {}
    for r in mfg_rows:
        obj, created = Manufacturer.objects.update_or_create(
            id=r['id'],
            defaults={
                'name': r['name'],
                'slug': r['slug'],
            }
        )
        mfg_map[r['id']] = obj
    print(f"Saved {len(mfg_map)} Manufacturers in PostgreSQL.")

    # 3. Health Conditions
    print("--- Transferring Health Conditions ---")
    cur.execute("SELECT * FROM catalogue_healthcondition")
    cond_rows = cur.fetchall()
    cond_map = {}
    for r in cond_rows:
        obj, created = HealthCondition.objects.update_or_create(
            id=r['id'],
            defaults={
                'name': r['name'],
                'slug': r['slug'],
                'description': r['description'],
                'category_id': r['category_id'],
                'icon': r['icon'],
            }
        )
        cond_map[r['id']] = obj
    print(f"Saved {len(cond_map)} Health Conditions in PostgreSQL.")

    # 4. Medicines
    print("--- Transferring Medicines ---")
    cur.execute("SELECT * FROM catalogue_medicine")
    med_rows = cur.fetchall()
    med_map = {}
    for r in med_rows:
        import json
        faqs_val = r['faqs']
        if isinstance(faqs_val, str):
            try:
                faqs_val = json.loads(faqs_val)
            except:
                faqs_val = []

        obj, created = Medicine.objects.update_or_create(
            id=r['id'],
            defaults={
                'name': r['name'],
                'slug': r['slug'],
                'generic_name': r['generic_name'],
                'composition': r['composition'],
                'form': r['form'],
                'manufacturer_id': r['manufacturer_id'],
                'category_id': r['category_id'],
                'subcategory_id': r['subcategory_id'],
                'description': r['description'],
                'overview': r['overview'],
                'uses': r['uses'],
                'how_it_works': r['how_it_works'],
                'side_effects': r['side_effects'],
                'precautions': r['precautions'],
                'storage': r['storage'],
                'also_known_as': r['also_known_as'],
                'pack_size': r['pack_size'],
                'brand_name': r['brand_name'],
                'strength': r['strength'],
                'route': r['route'],
                'active_ingredients': r['active_ingredients'],
                'inactive_ingredients': r['inactive_ingredients'],
                'dosage_information': r['dosage_information'],
                'serious_side_effects': r['serious_side_effects'],
                'contraindications': r['contraindications'],
                'interactions': r['interactions'],
                'source_name': r['source_name'],
                'source_url': r['source_url'],
                'last_verified_at': r['last_verified_at'],
                'faqs': faqs_val,
                'prescription_required': bool(r['prescription_required']),
                'drug_type': r['drug_type'],
                'habit_forming': bool(r['habit_forming']),
                'pregnancy_category': r['pregnancy_category'],
                'alcohol_interaction': r['alcohol_interaction'],
                'is_featured': bool(r['is_featured']),
                'is_active': bool(r['is_active']),
            }
        )
        med_map[r['id']] = obj
    print(f"Saved {len(med_map)} Medicines in PostgreSQL.")

    # 4b. Medicine M2M Categories
    print("--- Transferring Medicine M2M Categories & Conditions ---")
    try:
        cur.execute("SELECT * FROM catalogue_medicine_categories")
        for m2m in cur.fetchall():
            try:
                med = Medicine.objects.get(id=m2m['medicine_id'])
                med.categories.add(m2m['healthcategory_id'])
            except: pass
    except Exception as e:
        print("Medicine M2M categories note:", e)

    try:
        cur.execute("SELECT * FROM catalogue_medicine_conditions")
        for m2m in cur.fetchall():
            try:
                med = Medicine.objects.get(id=m2m['medicine_id'])
                med.conditions.add(m2m['healthcondition_id'])
            except: pass
    except Exception as e:
        print("Medicine M2M conditions note:", e)

    # 5. Category Images
    print("--- Transferring Category Images ---")
    cur.execute("SELECT * FROM catalogue_categoryimage")
    img_rows = cur.fetchall()
    for r in img_rows:
        try:
            obj, created = CategoryImage.objects.update_or_create(
                id=r['id'],
                defaults={
                    'category_id': r['category_id'],
                    'medicine_id': r['medicine_id'],
                    'image': r['image'],
                    'image_hash': r['image_hash'],
                    'file_name': r['file_name'],
                    'file_path': r['file_path'],
                    'file_size': r['file_size'],
                    'is_primary': bool(r['is_primary']),
                    'is_active': bool(r['is_active']),
                }
            )
        except Exception as err:
            print(f"Error transferring CategoryImage {r['file_name']}: {err}")

    # 5b. CategoryImage M2M categories
    try:
        cur.execute("SELECT * FROM catalogue_categoryimage_categories")
        for m2m in cur.fetchall():
            try:
                ci = CategoryImage.objects.get(id=m2m['categoryimage_id'])
                ci.categories.add(m2m['healthcategory_id'])
            except: pass
    except Exception as e:
        print("CategoryImage M2M note:", e)

    conn.close()

    print("\n==========================================")
    print("PostgreSQL Database Verification:")
    print(f"Health Categories: {HealthCategory.objects.count()}")
    print(f"Manufacturers:     {Manufacturer.objects.count()}")
    print(f"Medicines:        {Medicine.objects.count()}")
    print(f"Category Images:  {CategoryImage.objects.count()}")
    print("==========================================")

if __name__ == '__main__':
    transfer_all_data()
