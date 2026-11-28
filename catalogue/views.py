from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.core.cache import cache
from .models import Medicine, HealthCategory, HealthCondition, Manufacturer, CategoryImage
from .search_engine import execute_smart_search

def get_categories_with_counts():
    """Retrieve all categories with pre-computed item counts in a single query, cached for fast response."""
    cached = cache.get('categories_with_counts')
    if cached is not None:
        return cached

    categories = list(HealthCategory.objects.all())
    # Single batch query to count CategoryImages per category
    img_counts = dict(
        CategoryImage.objects.filter(is_active=True)
        .values('category_id')
        .annotate(c=Count('id'))
        .values_list('category_id', 'c')
    )
    # Single batch query to count Medicines per primary category
    med_counts = dict(
        Medicine.objects.filter(is_active=True)
        .values('category_id')
        .annotate(c=Count('id'))
        .values_list('category_id', 'c')
    )

    for cat in categories:
        count = img_counts.get(cat.id) or med_counts.get(cat.id) or 5
        cat._item_count = count

    categories.sort(key=lambda c: getattr(c, '_item_count', 0), reverse=True)
    cache.set('categories_with_counts', categories, 600)
    return categories

def get_site_stats():
    """Retrieve site totals cached in memory."""
    cached = cache.get('site_stats')
    if cached is not None:
        return cached
    stats = {
        'sku_count': Medicine.objects.filter(is_active=True).count(),
        'manufacturer_count': Manufacturer.objects.filter(medicines__isnull=False).distinct().count(),
        'category_count': HealthCategory.objects.count(),
    }
    cache.set('site_stats', stats, 600)
    return stats

def get_active_manufacturers():
    """Retrieve active manufacturers with pre-annotated medicine counts in 1 single query, cached in memory."""
    cached = cache.get('active_manufacturers_annotated')
    if cached is not None:
        return cached
    mfg_list = list(
        Manufacturer.objects.filter(medicines__isnull=False)
        .annotate(medicine_count=Count('medicines', filter=Q(medicines__is_active=True), distinct=True))
        .filter(medicine_count__gt=0)
        .order_by('name')
    )
    cache.set('active_manufacturers_annotated', mfg_list, 600)
    return mfg_list

def get_active_forms():
    """Retrieve distinct medicine dosage forms cached in memory."""
    cached = cache.get('active_forms')
    if cached is not None:
        return cached
    forms = [f for f in Medicine.objects.values_list('form', flat=True).distinct() if f]
    cache.set('active_forms', forms, 600)
    return forms

def get_all_gallery_medicines():
    """Retrieve all active medicine image assets with linked medicines cached in memory for the horizontal gallery."""
    cached = cache.get('all_gallery_medicines')
    if cached is not None:
        return cached
    images = list(
        CategoryImage.objects.filter(is_active=True)
        .select_related('medicine', 'medicine__manufacturer', 'category')
        .order_by('file_name')
    )
    cache.set('all_gallery_medicines', images, 600)
    return images

def get_hero_slides():
    """Returns premium 3D healthcare hero slides in user-specified sequence."""
    return [
        {
            'id': 'vitamins-supplements-a',
            'name': 'Vitamins & Dietary Supplements (Option A)',
            'slug': 'vitamins-supplements',
            'generic_name': 'Daily Multivitamins, Minerals & Antioxidants',
            'category_badge': 'Daily Wellness & Active Immunity',
            'tagline': 'Boost Your Vitality, Nourish Your Life',
            'description': 'Formulated with pure bio-available nutrients, essential minerals, and antioxidants for daily wellness.',
            'accent_color': '#D97706',
            'bg_color': '#FFFBEB',
            'image_webp': '/static/branding/hero/vitamins_supplements_a.webp',
            'image_jpg': '/static/branding/hero/vitamins_supplements_a.jpg',
            'cta_url': '/health-categories/vitamins-supplements/',
        },
        {
            'id': 'orthopedic-supports',
            'name': 'Orthopedic Supports & Mobility Braces',
            'slug': 'orthopedic-products',
            'generic_name': 'Hinged Knee Braces, Lumbar Belts & Splints',
            'category_badge': 'Joint Stability & Pain Relief',
            'tagline': 'Regain Your Mobility, Live Pain-Free',
            'description': 'Designed for everyday comfort, joint stability, athletic recovery, and rehabilitation support.',
            'accent_color': '#0284C7',
            'bg_color': '#F0F9FF',
            'image_webp': '/static/branding/hero/orthopedic_supports.webp',
            'image_jpg': '/static/branding/hero/orthopedic_supports.jpg',
            'cta_url': '/health-categories/orthopedic-products/',
        },
        {
            'id': 'surgical-instruments',
            'name': 'Surgical Instruments & OR Equipment',
            'slug': 'surgical-products',
            'generic_name': 'Precision Scissors, Forceps & Operating Room Gear',
            'category_badge': 'Surgical Precision & Clinical Trust',
            'tagline': 'Advancing Surgical Excellence, Precision & Trust',
            'description': 'Engineered for ultimate accuracy, sterile reliability, and enhanced clinical patient outcomes.',
            'accent_color': '#0F766E',
            'bg_color': '#F0FDFA',
            'image_webp': '/static/branding/hero/surgical_instruments.webp',
            'image_jpg': '/static/branding/hero/surgical_instruments.jpg',
            'cta_url': '/health-categories/surgical-products/',
        },
        {
            'id': 'vitamins-supplements-b',
            'name': 'Vitamins & Dietary Supplements (Option B — Alternate)',
            'slug': 'vitamins-supplements',
            'generic_name': 'Bioactive Multivitamins, Omega-3 & Cellular Energy',
            'category_badge': 'Immunity Defense & Cellular Vitality',
            'tagline': 'Fuel Your Body, Elevate Your Wellness',
            'description': 'Scientifically calibrated daily essentials to strengthen immune defenses and sustain optimal wellness.',
            'accent_color': '#EA580C',
            'bg_color': '#FFF7ED',
            'image_webp': '/static/branding/hero/vitamins_supplements_b.webp',
            'image_jpg': '/static/branding/hero/vitamins_supplements_b.jpg',
            'cta_url': '/health-categories/vitamins-supplements/',
        },
        {
            'id': 'pharmaceutical-injectables',
            'name': 'Pharmaceutical Injectables & IV Solutions',
            'slug': 'injectables',
            'generic_name': 'Sterile Vials, Ampoules & Hospital Infusions',
            'category_badge': 'Clinical Precision & Sterile Dosing',
            'tagline': 'Protect Your Health, Live Better',
            'description': 'Engineered for precise dosing, maximum patient safety, and optimal clinical therapeutic results.',
            'accent_color': '#0878D1',
            'bg_color': '#EAF5FF',
            'image_webp': '/static/branding/hero/injectables_solutions.webp',
            'image_jpg': '/static/branding/hero/injectables_solutions.jpg',
            'cta_url': '/health-categories/',
        },
        {
            'id': 'oral-tablets-formulations',
            'name': 'Oral Tablets & Pharmaceutical Formulations',
            'slug': 'oral-tablets',
            'generic_name': 'Tablets, Capsules & Essential Therapeutics',
            'category_badge': 'Therapeutic Care & Precise Dosage',
            'tagline': 'Protect Your Health, Live Better',
            'description': 'Premium oral tablets and pharmaceutical solutions engineered for rapid absorption and optimal clinical care.',
            'accent_color': '#2563EB',
            'bg_color': '#EFF6FF',
            'image_webp': '/static/branding/hero/oral_tablets_formulations.webp',
            'image_jpg': '/static/branding/hero/oral_tablets_formulations.jpg',
            'cta_url': '/health-categories/',
        },
    ]

def home(request):
    categories = get_categories_with_counts()[:12]
    all_gallery_medicines = get_all_gallery_medicines()
    hero_slides = get_hero_slides()
    featured_medicines = list(Medicine.objects.filter(
        is_featured=True, is_active=True
    ).select_related('manufacturer', 'category').prefetch_related('category_image_assets', 'images')[:5])
    if not featured_medicines:
        featured_medicines = list(Medicine.objects.filter(
            is_active=True
        ).select_related('manufacturer', 'category').prefetch_related('category_image_assets', 'images')[:5])
    stats = get_site_stats()
    return render(request, 'home.html', {
        'categories': categories,
        'hero_slides': hero_slides,
        'all_gallery_medicines': all_gallery_medicines,
        'featured_medicines': featured_medicines,
        'stats': stats,
    })

def medicine_list(request):
    medicines = Medicine.objects.filter(is_active=True).select_related('manufacturer', 'category').prefetch_related('category_image_assets', 'images').order_by('name')
    
    # Filter by form
    form = request.GET.get('form', '').strip()
    if form:
        medicines = medicines.filter(form__icontains=form)
        
    # Filter by manufacturer
    mfg = request.GET.get('manufacturer', '').strip()
    if mfg:
        medicines = medicines.filter(manufacturer__name__icontains=mfg)

    # Filter by keyword search
    q = request.GET.get('q', '').strip()
    if q:
        medicines = medicines.filter(
            Q(name__icontains=q) |
            Q(generic_name__icontains=q) |
            Q(composition__icontains=q) |
            Q(description__icontains=q)
        )
        
    active_filters_count = (1 if form else 0) + (1 if mfg else 0) + (1 if q else 0)
        
    paginator = Paginator(medicines, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    manufacturers = get_active_manufacturers()
    forms = get_active_forms()
    
    view_type = request.GET.get('view', 'grid')
    
    return render(request, 'medicines.html', {
        'page_obj': page_obj,
        'manufacturers': manufacturers,
        'forms': forms,
        'view_type': view_type,
        'active_filters_count': active_filters_count,
        'query': q,
    })

def medicine_detail(request, slug):
    medicine = get_object_or_404(
        Medicine.objects.select_related('manufacturer', 'category', 'subcategory').prefetch_related('category_image_assets', 'images', 'categories', 'conditions'),
        slug=slug, is_active=True
    )
    
    # Query distinct real-image medicines from the same category
    category_filter = Q()
    if medicine.category:
        category_filter = Q(category=medicine.category) | Q(categories=medicine.category)
    elif medicine.categories.exists():
        category_filter = Q(categories__in=medicine.categories.all())

    # Prioritize related medicines that have their own unique distinct image asset
    related_medicines = list(
        Medicine.objects.filter(
            category_filter,
            is_active=True,
            category_image_assets__isnull=False
        ).exclude(id=medicine.id).select_related('manufacturer', 'category').prefetch_related('category_image_assets', 'images').distinct()[:4]
    )
    
    # If fewer than 4, fill with other medicines in category
    if len(related_medicines) < 4:
        needed = 4 - len(related_medicines)
        already_ids = [m.id for m in related_medicines] + [medicine.id]
        extras = Medicine.objects.filter(
            category_filter,
            is_active=True
        ).exclude(id__in=already_ids).select_related('manufacturer', 'category').prefetch_related('category_image_assets', 'images').distinct()[:needed]
        related_medicines.extend(list(extras))
        
    return render(request, 'medicine_detail.html', {
        'medicine': medicine,
        'related_medicines': related_medicines
    })

def category_list(request):
    categories = get_categories_with_counts()
    return render(request, 'categories.html', {'categories': categories})

def category_detail(request, slug):
    category = get_object_or_404(HealthCategory, slug=slug)
    conditions = list(category.conditions.all())
    medicines = Medicine.objects.filter(
        Q(category=category) | Q(categories=category),
        is_active=True
    ).select_related('manufacturer', 'category').prefetch_related('category_image_assets', 'images').distinct().order_by('name')
    
    paginator = Paginator(medicines, 24)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    all_categories = get_categories_with_counts()
    
    return render(request, 'category_detail.html', {
        'category': category,
        'conditions': conditions,
        'page_obj': page_obj,
        'all_categories': all_categories
    })

def category_detail_redirect(request, slug):
    """Gracefully redirect old /category/<slug>/ URLs to /health-categories/<slug>/"""
    return redirect('catalogue:category_detail', slug=slug, permanent=True)
    
def condition_detail(request, category_slug, condition_slug):
    category = get_object_or_404(HealthCategory, slug=category_slug)
    condition = get_object_or_404(HealthCondition, slug=condition_slug, category=category)
    medicines = Medicine.objects.filter(
        conditions=condition, is_active=True
    ).select_related('manufacturer', 'category').prefetch_related('category_image_assets', 'images').distinct().order_by('name')
    
    paginator = Paginator(medicines, 24)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    all_categories = get_categories_with_counts()
    
    return render(request, 'category_detail.html', {
        'category': category,
        'condition': condition,
        'conditions': list(category.conditions.all()),
        'page_obj': page_obj,
        'all_categories': all_categories
    })

def search(request):
    query = request.GET.get('q', '').strip()
    
    if query:
        medicines, matched_categories, matched_conditions, meta_info = execute_smart_search(query)
    else:
        medicines = Medicine.objects.filter(is_active=True).select_related(
            'manufacturer', 'category'
        ).prefetch_related('category_image_assets', 'images').order_by('name')
        matched_categories = HealthCategory.objects.none()
        matched_conditions = HealthCondition.objects.none()
        meta_info = {}
        
    # Additional filters
    form = request.GET.get('form')
    if form:
        medicines = medicines.filter(form__icontains=form)
        
    mfg = request.GET.get('manufacturer')
    if mfg:
        medicines = medicines.filter(manufacturer__name__icontains=mfg)

    total_results = medicines.count() if query or form or mfg else Medicine.objects.filter(is_active=True).count()
    paginator = Paginator(medicines, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    manufacturers = get_active_manufacturers()
    forms = get_active_forms()
    
    return render(request, 'search_results.html', {
        'page_obj': page_obj,
        'query': query,
        'manufacturers': manufacturers,
        'forms': forms,
        'total_results': total_results,
        'matched_categories': matched_categories,
        'matched_conditions': matched_conditions,
        'meta_info': meta_info,
    })

def search_suggest(request):
    """Instant JSON search API for predictive search dropdown autocomplete."""
    query = request.GET.get('q', '').strip()
    if not query or len(query) < 2:
        return JsonResponse({'medicines': [], 'categories': [], 'conditions': []})

    medicines_qs, categories_qs, conditions_qs, meta = execute_smart_search(query)
    
    meds_data = []
    for med in medicines_qs[:6]:
        meds_data.append({
            'name': med.name,
            'generic_name': med.generic_name,
            'form': med.form,
            'manufacturer': med.manufacturer.name if med.manufacturer else '',
            'image_url': med.get_display_image_url,
            'url': f'/medicines/{med.slug}/',
            'category': med.category.name if med.category else '',
        })

    cats_data = []
    for cat in categories_qs[:3]:
        cats_data.append({
            'name': cat.name,
            'url': f'/health-categories/{cat.slug}/',
            'item_count': cat.item_count,
        })

    conds_data = []
    for cond in conditions_qs[:3]:
        conds_data.append({
            'name': cond.name,
            'url': f'/health-categories/{cond.category.slug}/{cond.slug}/' if cond.category else f'/search/?q={cond.name}',
            'category_name': cond.category.name if cond.category else '',
        })

    return JsonResponse({
        'query': query,
        'medicines': meds_data,
        'categories': cats_data,
        'conditions': conds_data,
        'has_symptom_expansion': meta.get('has_symptom_expansion', False),
    })

def about(request):
    return render(request, 'about.html')

def quality_standards(request):
    all_categories = get_categories_with_counts()
    return render(request, 'quality_standards.html', {
        'all_categories': all_categories,
        'nav_active': 'quality_standards',
    })

def contact(request):
    return render(request, 'contact.html')

def faq(request):
    return render(request, 'faq.html')

def disclaimer(request):
    return render(request, 'disclaimer.html')

def privacy_policy(request):
    return render(request, 'privacy_policy.html')

def terms_conditions(request):
    return render(request, 'terms_conditions.html')
