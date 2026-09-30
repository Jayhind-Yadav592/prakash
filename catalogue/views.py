from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Medicine, HealthCategory, HealthCondition, Manufacturer

def home(request):
    categories = list(HealthCategory.objects.all())
    categories.sort(key=lambda c: c.item_count, reverse=True)
    categories = categories[:12]
    featured_medicines = Medicine.objects.filter(is_featured=True, is_active=True)[:5]
    stats = {
        'sku_count': Medicine.objects.filter(is_active=True).count(),
        'manufacturer_count': Manufacturer.objects.filter(medicines__isnull=False).distinct().count(),
        'category_count': HealthCategory.objects.count(),
    }
    return render(request, 'home.html', {
        'categories': categories,
        'featured_medicines': featured_medicines,
        'stats': stats,
    })

def medicine_list(request):
    medicines = Medicine.objects.filter(is_active=True).order_by('name')
    
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
    
    manufacturers = Manufacturer.objects.filter(medicines__isnull=False).distinct().order_by('name')
    forms = Medicine.objects.values_list('form', flat=True).distinct()
    forms = [f for f in forms if f] # remove empty strings
    
    view_type = request.GET.get('view', 'grid')
    
    return render(request, 'medicines.html', {
        'page_obj': page_obj,
        'manufacturers': manufacturers,
        'forms': forms,
        'view_type': view_type
    })

def medicine_detail(request, slug):
    medicine = get_object_or_404(Medicine, slug=slug, is_active=True)
    
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
        ).exclude(id=medicine.id).distinct()[:4]
    )
    
    # If fewer than 4, fill with other medicines in category
    if len(related_medicines) < 4:
        needed = 4 - len(related_medicines)
        already_ids = [m.id for m in related_medicines] + [medicine.id]
        extras = Medicine.objects.filter(
            category_filter,
            is_active=True
        ).exclude(id__in=already_ids).distinct()[:needed]
        related_medicines.extend(list(extras))
        
    return render(request, 'medicine_detail.html', {
        'medicine': medicine,
        'related_medicines': related_medicines
    })

def category_list(request):
    categories = list(HealthCategory.objects.all())
    categories.sort(key=lambda c: c.item_count, reverse=True)
    return render(request, 'categories.html', {'categories': categories})

def category_detail(request, slug):
    category = get_object_or_404(HealthCategory, slug=slug)
    conditions = category.conditions.all()
    medicines = Medicine.objects.filter(
        Q(category=category) | Q(categories=category),
        is_active=True
    ).distinct().order_by('name')
    
    paginator = Paginator(medicines, 24)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    all_categories = HealthCategory.objects.all().order_by('name')
    
    return render(request, 'category_detail.html', {
        'category': category,
        'conditions': conditions,
        'page_obj': page_obj,
        'all_categories': all_categories
    })
    
def condition_detail(request, category_slug, condition_slug):
    category = get_object_or_404(HealthCategory, slug=category_slug)
    condition = get_object_or_404(HealthCondition, slug=condition_slug, category=category)
    medicines = Medicine.objects.filter(conditions=condition, is_active=True).order_by('name')
    
    paginator = Paginator(medicines, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    all_categories = HealthCategory.objects.all().order_by('name')
    
    return render(request, 'category_detail.html', {
        'category': category,
        'condition': condition,
        'conditions': category.conditions.all(),
        'page_obj': page_obj,
        'all_categories': all_categories
    })

def search(request):
    query = request.GET.get('q', '')
    medicines = Medicine.objects.filter(is_active=True).order_by('name')
    
    if query:
        medicines = medicines.filter(
            Q(name__icontains=query) |
            Q(generic_name__icontains=query) |
            Q(manufacturer__name__icontains=query) |
            Q(categories__name__icontains=query) |
            Q(conditions__name__icontains=query)
        ).distinct()
        
    # Additional filters
    form = request.GET.get('form')
    if form:
        medicines = medicines.filter(form__icontains=form)
        
    mfg = request.GET.get('manufacturer')
    if mfg:
        medicines = medicines.filter(manufacturer__name__icontains=mfg)

    paginator = Paginator(medicines, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    manufacturers = Manufacturer.objects.filter(medicines__isnull=False).distinct().order_by('name')
    forms = Medicine.objects.values_list('form', flat=True).distinct()
    forms = [f for f in forms if f]
    
    return render(request, 'search_results.html', {
        'page_obj': page_obj,
        'query': query,
        'manufacturers': manufacturers,
        'forms': forms,
        'total_results': medicines.count()
    })

def about(request):
    return render(request, 'about.html')

def contact(request):
    return render(request, 'contact.html')
