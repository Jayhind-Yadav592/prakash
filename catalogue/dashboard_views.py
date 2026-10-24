import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from django.core.cache import cache
from django.db.models import Q, Count
from django.utils.text import slugify

from .models import Medicine, HealthCategory, Manufacturer, MedicineImage, CategoryImage

def is_admin_user(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)

def clear_catalog_cache():
    """Clear cached catalog querysets so changes reflect immediately."""
    cache.delete('site_stats')
    cache.delete('categories_with_counts')
    cache.delete('active_manufacturers_annotated')
    cache.delete('active_forms')
    cache.delete('all_gallery_medicines')

def get_unique_slug(model_class, text, current_id=None):
    base_slug = slugify(text) or "item"
    slug = base_slug
    counter = 1
    qs = model_class.objects.filter(slug=slug)
    if current_id:
        qs = qs.exclude(id=current_id)
    while qs.exists():
        slug = f"{base_slug}-{counter}"
        counter += 1
        qs = model_class.objects.filter(slug=slug)
        if current_id:
            qs = qs.exclude(id=current_id)
    return slug


def dashboard_login(request):
    """Admin Dashboard Login view with password authentication."""
    if is_admin_user(request.user):
        return redirect('dashboard:home')

    next_url = request.GET.get('next', 'dashboard:home')
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        if not username or not password:
            messages.error(request, 'Please provide both username and password.')
            return render(request, 'dashboard/login.html', {'next': next_url, 'username': username})

        user = authenticate(request, username=username, password=password)
        if user is not None and (user.is_staff or user.is_superuser):
            auth_login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            if next_url and next_url != 'dashboard:login':
                return redirect(next_url)
            return redirect('dashboard:home')
        else:
            messages.error(request, 'Invalid credentials or administrative privileges required.')

    return render(request, 'dashboard/login.html', {'next': next_url})


def dashboard_logout(request):
    """Admin Dashboard Logout view."""
    auth_logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('dashboard:login')


@user_passes_test(is_admin_user, login_url='dashboard:login')
def dashboard_home(request):
    """Main dashboard overview with KPI cards and recent medicines."""
    total_medicines = Medicine.objects.count()
    active_medicines = Medicine.objects.filter(is_active=True).count()
    total_categories = HealthCategory.objects.count()
    total_manufacturers = Manufacturer.objects.count()
    rx_count = Medicine.objects.filter(prescription_required=True).count()
    otc_count = total_medicines - rx_count

    recent_medicines = (
        Medicine.objects.select_related('manufacturer', 'category')
        .prefetch_related('images', 'category_image_assets')
        .order_by('-updated_at')[:8]
    )

    top_categories = (
        HealthCategory.objects.annotate(
            med_count=Count('primary_medicines', filter=Q(primary_medicines__is_active=True))
        )
        .order_by('-med_count')[:6]
    )

    context = {
        'total_medicines': total_medicines,
        'active_medicines': active_medicines,
        'total_categories': total_categories,
        'total_manufacturers': total_manufacturers,
        'rx_count': rx_count,
        'otc_count': otc_count,
        'recent_medicines': recent_medicines,
        'top_categories': top_categories,
        'nav_active': 'home',
    }
    return render(request, 'dashboard/home.html', context)


@user_passes_test(is_admin_user, login_url='dashboard:login')
def dashboard_medicine_list(request):
    """List of all medicines with live search, category filter, and pagination."""
    query = request.GET.get('q', '').strip()
    category_id = request.GET.get('category', '').strip()
    status_filter = request.GET.get('status', '').strip()

    medicines = Medicine.objects.select_related('manufacturer', 'category').prefetch_related('images', 'category_image_assets').order_by('-updated_at')

    if query:
        medicines = medicines.filter(
            Q(name__icontains=query) |
            Q(generic_name__icontains=query) |
            Q(composition__icontains=query) |
            Q(brand_name__icontains=query) |
            Q(manufacturer__name__icontains=query)
        )

    if category_id:
        medicines = medicines.filter(
            Q(category_id=category_id) | Q(categories__id=category_id)
        ).distinct()

    if status_filter == 'active':
        medicines = medicines.filter(is_active=True)
    elif status_filter == 'inactive':
        medicines = medicines.filter(is_active=False)

    paginator = Paginator(medicines, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    categories = HealthCategory.objects.order_by('name')

    context = {
        'page_obj': page_obj,
        'categories': categories,
        'query': query,
        'selected_category': category_id,
        'selected_status': status_filter,
        'total_found': paginator.count,
        'nav_active': 'medicines',
    }
    return render(request, 'dashboard/medicine_list.html', context)


@user_passes_test(is_admin_user, login_url='dashboard:login')
def dashboard_medicine_add(request):
    """Add a new medicine with instant image upload and category assignment."""
    categories = HealthCategory.objects.order_by('name')
    manufacturers = Manufacturer.objects.order_by('name')
    common_forms = ['Tablet', 'Capsule', 'Syrup', 'Injection', 'Cream', 'Ointment', 'Gel', 'Drops', 'Inhaler', 'Suspension', 'Powder']

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if not name:
            messages.error(request, 'Medicine Name is required.')
            return render(request, 'dashboard/medicine_form.html', {
                'medicine': None,
                'categories': categories,
                'manufacturers': manufacturers,
                'common_forms': common_forms,
                'nav_active': 'medicines_add',
                'action': 'add'
            })

        generic_name = request.POST.get('generic_name', '').strip()
        form = request.POST.get('form', '').strip()
        strength = request.POST.get('strength', '').strip()
        pack_size = request.POST.get('pack_size', '').strip()
        composition = request.POST.get('composition', '').strip()
        description = request.POST.get('description', '').strip()
        overview = request.POST.get('overview', '').strip()
        uses = request.POST.get('uses', '').strip()
        how_it_works = request.POST.get('how_it_works', '').strip()
        side_effects = request.POST.get('side_effects', '').strip()
        precautions = request.POST.get('precautions', '').strip()
        storage = request.POST.get('storage', '').strip()
        brand_name = request.POST.get('brand_name', '').strip()
        route = request.POST.get('route', 'Oral').strip()
        
        prescription_required = request.POST.get('prescription_required') == 'on'
        is_featured = request.POST.get('is_featured') == 'on'
        is_active = request.POST.get('is_active') == 'on'

        # Manufacturer selection or creation
        mfg_id = request.POST.get('manufacturer_id')
        new_mfg_name = request.POST.get('new_manufacturer', '').strip()
        manufacturer = None
        if new_mfg_name:
            manufacturer, _ = Manufacturer.objects.get_or_create(
                name=new_mfg_name,
                defaults={'slug': slugify(new_mfg_name)}
            )
        elif mfg_id:
            manufacturer = Manufacturer.objects.filter(id=mfg_id).first()

        if not manufacturer:
            # Fallback to default or first
            manufacturer = Manufacturer.objects.first()
            if not manufacturer:
                manufacturer = Manufacturer.objects.create(name='General Pharma', slug='general-pharma')

        # Category
        cat_id = request.POST.get('category_id')
        category = HealthCategory.objects.filter(id=cat_id).first() if cat_id else None

        # Unique slug
        slug = get_unique_slug(Medicine, name)

        med = Medicine.objects.create(
            name=name,
            slug=slug,
            generic_name=generic_name,
            form=form,
            strength=strength,
            pack_size=pack_size,
            composition=composition,
            description=description,
            overview=overview,
            uses=uses,
            how_it_works=how_it_works,
            side_effects=side_effects,
            precautions=precautions,
            storage=storage,
            brand_name=brand_name,
            route=route,
            manufacturer=manufacturer,
            category=category,
            prescription_required=prescription_required,
            is_featured=is_featured,
            is_active=is_active,
        )

        if category:
            med.categories.set([category])

        # Image Upload
        if 'image' in request.FILES:
            uploaded_file = request.FILES['image']
            MedicineImage.objects.create(
                medicine=med,
                image=uploaded_file,
                is_primary=True
            )

        clear_catalog_cache()
        messages.success(request, f"Medicine '{med.name}' was created successfully!")
        return redirect('dashboard:medicine_list')

    return render(request, 'dashboard/medicine_form.html', {
        'medicine': None,
        'categories': categories,
        'manufacturers': manufacturers,
        'common_forms': common_forms,
        'nav_active': 'medicines_add',
        'action': 'add'
    })


@user_passes_test(is_admin_user, login_url='dashboard:login')
def dashboard_medicine_edit(request, pk):
    """Edit existing medicine details, change/replace product image, update category."""
    med = get_object_or_404(Medicine, pk=pk)
    categories = HealthCategory.objects.order_by('name')
    manufacturers = Manufacturer.objects.order_by('name')
    common_forms = ['Tablet', 'Capsule', 'Syrup', 'Injection', 'Cream', 'Ointment', 'Gel', 'Drops', 'Inhaler', 'Suspension', 'Powder']

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if not name:
            messages.error(request, 'Medicine Name cannot be empty.')
            return render(request, 'dashboard/medicine_form.html', {
                'medicine': med,
                'categories': categories,
                'manufacturers': manufacturers,
                'common_forms': common_forms,
                'nav_active': 'medicines',
                'action': 'edit'
            })

        med.name = name
        med.generic_name = request.POST.get('generic_name', '').strip()
        med.form = request.POST.get('form', '').strip()
        med.strength = request.POST.get('strength', '').strip()
        med.pack_size = request.POST.get('pack_size', '').strip()
        med.composition = request.POST.get('composition', '').strip()
        med.description = request.POST.get('description', '').strip()
        med.overview = request.POST.get('overview', '').strip()
        med.uses = request.POST.get('uses', '').strip()
        med.how_it_works = request.POST.get('how_it_works', '').strip()
        med.side_effects = request.POST.get('side_effects', '').strip()
        med.precautions = request.POST.get('precautions', '').strip()
        med.storage = request.POST.get('storage', '').strip()
        med.brand_name = request.POST.get('brand_name', '').strip()
        med.route = request.POST.get('route', 'Oral').strip()
        
        med.prescription_required = request.POST.get('prescription_required') == 'on'
        med.is_featured = request.POST.get('is_featured') == 'on'
        med.is_active = request.POST.get('is_active') == 'on'

        # Manufacturer
        mfg_id = request.POST.get('manufacturer_id')
        new_mfg_name = request.POST.get('new_manufacturer', '').strip()
        if new_mfg_name:
            manufacturer, _ = Manufacturer.objects.get_or_create(
                name=new_mfg_name,
                defaults={'slug': slugify(new_mfg_name)}
            )
            med.manufacturer = manufacturer
        elif mfg_id:
            mfg = Manufacturer.objects.filter(id=mfg_id).first()
            if mfg:
                med.manufacturer = mfg

        # Category
        cat_id = request.POST.get('category_id')
        if cat_id:
            category = HealthCategory.objects.filter(id=cat_id).first()
            med.category = category
            if category:
                med.categories.set([category])
        else:
            med.category = None

        # Image Upload/Replacement
        if 'image' in request.FILES:
            uploaded_file = request.FILES['image']
            # Find or create primary MedicineImage
            primary_img = med.images.filter(is_primary=True).first() or med.images.first()
            if primary_img:
                primary_img.image = uploaded_file
                primary_img.is_primary = True
                primary_img.save()
            else:
                MedicineImage.objects.create(
                    medicine=med,
                    image=uploaded_file,
                    is_primary=True
                )

        med.save()
        clear_catalog_cache()
        messages.success(request, f"Medicine '{med.name}' was updated successfully!")
        return redirect('dashboard:medicine_list')

    return render(request, 'dashboard/medicine_form.html', {
        'medicine': med,
        'categories': categories,
        'manufacturers': manufacturers,
        'common_forms': common_forms,
        'nav_active': 'medicines',
        'action': 'edit'
    })


@user_passes_test(is_admin_user, login_url='dashboard:login')
def dashboard_medicine_delete(request, pk):
    """Delete a medicine with confirmation."""
    med = get_object_or_404(Medicine, pk=pk)
    if request.method == 'POST':
        med_name = med.name
        med.delete()
        clear_catalog_cache()
        messages.success(request, f"Medicine '{med_name}' has been permanently deleted.")
        return redirect('dashboard:medicine_list')

    return render(request, 'dashboard/medicine_confirm_delete.html', {
        'medicine': med,
        'nav_active': 'medicines',
    })


@user_passes_test(is_admin_user, login_url='dashboard:login')
def dashboard_category_list(request):
    """List of all health categories with medicine counts and edit options."""
    categories = HealthCategory.objects.annotate(
        medicine_count=Count('primary_medicines')
    ).order_by('name')

    context = {
        'categories': categories,
        'nav_active': 'categories',
    }
    return render(request, 'dashboard/category_list.html', context)


@user_passes_test(is_admin_user, login_url='dashboard:login')
def dashboard_category_add(request):
    """Add a new health category."""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if not name:
            messages.error(request, 'Category Name is required.')
            return render(request, 'dashboard/category_form.html', {'category': None, 'action': 'add', 'nav_active': 'categories'})

        description = request.POST.get('description', '').strip()
        slug = get_unique_slug(HealthCategory, name)

        cat = HealthCategory(
            name=name,
            slug=slug,
            description=description,
        )
        if 'icon' in request.FILES:
            cat.icon = request.FILES['icon']
        cat.save()

        clear_catalog_cache()
        messages.success(request, f"Category '{cat.name}' created successfully!")
        return redirect('dashboard:category_list')

    return render(request, 'dashboard/category_form.html', {'category': None, 'action': 'add', 'nav_active': 'categories'})


@user_passes_test(is_admin_user, login_url='dashboard:login')
def dashboard_category_edit(request, pk):
    """Edit category name, description, and upload/change category image."""
    cat = get_object_or_404(HealthCategory, pk=pk)

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if not name:
            messages.error(request, 'Category Name cannot be empty.')
            return render(request, 'dashboard/category_form.html', {'category': cat, 'action': 'edit', 'nav_active': 'categories'})

        cat.name = name
        cat.description = request.POST.get('description', '').strip()

        if 'icon' in request.FILES:
            cat.icon = request.FILES['icon']

        cat.save()
        clear_catalog_cache()
        messages.success(request, f"Category '{cat.name}' updated successfully!")
        return redirect('dashboard:category_list')

    return render(request, 'dashboard/category_form.html', {'category': cat, 'action': 'edit', 'nav_active': 'categories'})


@user_passes_test(is_admin_user, login_url='dashboard:login')
def dashboard_category_delete(request, pk):
    """Delete a health category with safety checks."""
    cat = get_object_or_404(HealthCategory, pk=pk)
    med_count = cat.primary_medicines.count()

    if request.method == 'POST':
        cat_name = cat.name
        # Unlink medicines instead of deleting them
        cat.primary_medicines.update(category=None)
        cat.delete()
        clear_catalog_cache()
        messages.success(request, f"Category '{cat_name}' has been deleted. (Medicines unlinked safely).")
        return redirect('dashboard:category_list')

    return render(request, 'dashboard/category_confirm_delete.html', {
        'category': cat,
        'med_count': med_count,
        'nav_active': 'categories',
    })
