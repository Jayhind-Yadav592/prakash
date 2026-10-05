from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.core.cache import cache
from .models import Medicine, HealthCategory, HealthCondition, Manufacturer, CategoryImage

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

def home(request):
    categories = get_categories_with_counts()[:12]
    featured_medicines = list(
        Medicine.objects.filter(
            is_active=True,
            category_image_assets__isnull=False
        ).select_related('manufacturer', 'category').prefetch_related('category_image_assets', 'images').distinct()[:16]
    )
    if len(featured_medicines) < 8:
        featured_medicines = list(
            Medicine.objects.filter(
                is_active=True
            ).select_related('manufacturer', 'category').prefetch_related('category_image_assets', 'images')[:16]
        )
    stats = get_site_stats()
    return render(request, 'home.html', {
        'categories': categories,
        'featured_medicines': featured_medicines,
        'stats': stats,
    })

def medicine_list(request):
    medicines = Medicine.objects.filter(is_active=True).select_related('manufacturer', 'category').prefetch_related('category_image_assets', 'images').order_by('name')
    
    # Filter by form
    form = request.GET.get('form')
    if form:
        medicines = medicines.filter(form__icontains=form)
        
    # Filter by manufacturer
    mfg = request.GET.get('manufacturer')
    if mfg:
        medicines = medicines.filter(manufacturer__name__icontains=mfg)
        
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
        'view_type': view_type
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
        ).exclude(id=medicine.id).select_related('manufacturer', 'category').prefetch_related('category_image_assets', 'images').distinct()[:8]
    )
    
    # If fewer than 8, fill with other medicines in category
    if len(related_medicines) < 8:
        needed = 8 - len(related_medicines)
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
    
    category_images = list(
        CategoryImage.objects.filter(
            Q(category=category) | Q(categories=category),
            is_active=True
        ).select_related('medicine', 'medicine__manufacturer').distinct()
    )
    
    all_categories = get_categories_with_counts()
    
    return render(request, 'category_detail.html', {
        'category': category,
        'conditions': conditions,
        'page_obj': page_obj,
        'category_images': category_images,
        'all_categories': all_categories
    })
    
def condition_detail(request, category_slug, condition_slug):
    category = get_object_or_404(HealthCategory, slug=category_slug)
    condition = get_object_or_404(HealthCondition, slug=condition_slug, category=category)
    medicines = Medicine.objects.filter(
        conditions=condition, is_active=True
    ).select_related('manufacturer', 'category').prefetch_related('category_image_assets', 'images').order_by('name')
    
    paginator = Paginator(medicines, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    category_images = list(
        CategoryImage.objects.filter(
            Q(category=category) | Q(categories=category),
            is_active=True
        ).select_related('medicine', 'medicine__manufacturer').distinct()
    )
    
    all_categories = get_categories_with_counts()
    
    return render(request, 'category_detail.html', {
        'category': category,
        'condition': condition,
        'conditions': list(category.conditions.all()),
        'page_obj': page_obj,
        'category_images': category_images,
        'all_categories': all_categories
    })

def search(request):
    query = request.GET.get('q', '').strip()
    medicines = Medicine.objects.filter(is_active=True).select_related('manufacturer', 'category').prefetch_related('category_image_assets', 'images').order_by('name')
    
    if query:
        search_filter = (
            Q(name__icontains=query) |
            Q(generic_name__icontains=query) |
            Q(brand_name__icontains=query) |
            Q(also_known_as__icontains=query) |
            Q(composition__icontains=query) |
            Q(overview__icontains=query) |
            Q(uses__icontains=query) |
            Q(manufacturer__name__icontains=query) |
            Q(category__name__icontains=query) |
            Q(categories__name__icontains=query) |
            Q(conditions__name__icontains=query)
        )
        words = query.split()
        if len(words) > 1:
            for w in words:
                if len(w) > 2:
                    search_filter |= (
                        Q(name__icontains=w) |
                        Q(generic_name__icontains=w) |
                        Q(brand_name__icontains=w) |
                        Q(also_known_as__icontains=w) |
                        Q(composition__icontains=w) |
                        Q(category__name__icontains=w) |
                        Q(categories__name__icontains=w)
                    )
        medicines = medicines.filter(search_filter).distinct()
        
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
        'total_results': total_results
    })

def about(request):
    return render(request, 'about.html')

def contact(request):
    return render(request, 'contact.html')
