from django.shortcuts import render, get_object_or_404
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

def get_banner_medicines():
    """Retrieve 10 featured medicines for the premium e-commerce NEURASSIAL-style banner slider with distinct HD visuals and tailored color themes."""
    banners = [
        {
            'name': 'Atorvastatin',
            'clean_title': 'Atorvastatin',
            'category_name': 'Cardiovascular / Heart Health',
            'formulation': 'Film-Coated Tablet • 20 mg',
            'generic_name': 'Atorvastatin Calcium',
            'standard': 'WHO-GMP & US-FDA Monograph',
            'image_url': '/media/branding/slider/atorvastatin.jpg',
            'slug': 'atorvastain',
            'description': 'High-efficacy HMG-CoA reductase inhibitor for comprehensive lipid regulation and cardiovascular risk management across clinical healthcare facilities.',
            'accent_hex': '#0284C7',
            'gradient_from': '#0369A1',
            'gradient_to': '#38BDF8',
            'secondary_wave': '#E0F2FE',
            'glow_color': 'bg-sky-100/50',
            'dot_color': '#0284C7',
        },
        {
            'name': 'Allegra',
            'clean_title': 'Allegra',
            'category_name': 'Allergy & Respiratory Health',
            'formulation': 'Non-Drowsy Tablet • 120 mg',
            'generic_name': 'Fexofenadine Hydrochloride',
            'standard': 'WHO-GMP Batch Certified',
            'image_url': '/media/branding/slider/allegra.jpg',
            'slug': 'allegra',
            'description': 'Second-generation non-sedating H1 receptor antagonist delivering reliable 24-hour symptom relief for allergic rhinitis and chronic urticaria.',
            'accent_hex': '#9333EA',
            'gradient_from': '#7E22CE',
            'gradient_to': '#C026D3',
            'secondary_wave': '#F3E8FF',
            'glow_color': 'bg-purple-100/50',
            'dot_color': '#9333EA',
        },
        {
            'name': 'Amlodipine',
            'clean_title': 'Amlodipine',
            'category_name': 'Hypertension & Cardiology',
            'formulation': 'Oral Tablet • 5 mg',
            'generic_name': 'Amlodipine Besylate',
            'standard': 'Pharmacopeial Grade Batch',
            'image_url': '/media/branding/slider/amlodipine.jpg',
            'slug': 'amlodipine',
            'description': 'Long-acting dihydropyridine calcium channel blocker providing sustained arterial vasodilation and consistent 24-hour blood pressure control.',
            'accent_hex': '#E11D48',
            'gradient_from': '#BE123C',
            'gradient_to': '#FB7185',
            'secondary_wave': '#FFE4E6',
            'glow_color': 'bg-rose-100/50',
            'dot_color': '#E11D48',
        },
        {
            'name': 'Abilify',
            'clean_title': 'Abilify',
            'category_name': 'Neuropsychiatry & Wellness',
            'formulation': 'Oral Tablet • 15 mg',
            'generic_name': 'Aripiprazole',
            'standard': 'Hospital Dispensing Certified',
            'image_url': '/media/branding/slider/abilify.jpg',
            'slug': 'abilify',
            'description': 'Atypical second-generation antipsychotic and dopamine-serotonin system stabilizer with verified clinical safety and bioavailability.',
            'accent_hex': '#1E40AF',
            'gradient_from': '#1E3A8A',
            'gradient_to': '#60A5FA',
            'secondary_wave': '#DBEAFE',
            'glow_color': 'bg-blue-100/50',
            'dot_color': '#1E40AF',
        },
        {
            'name': 'Aleve',
            'clean_title': 'Aleve',
            'category_name': 'Pain Relief & Anti-Inflammatory',
            'formulation': 'Strength to Last Tablet • 220 mg',
            'generic_name': 'Naproxen Sodium',
            'standard': 'GMP Verified Formulation',
            'image_url': '/media/branding/slider/aleve.jpg',
            'slug': 'aleve',
            'description': 'High-potency nonsteroidal anti-inflammatory formulation (NSAID) engineered for up to 12-hour sustained relief from musculoskeletal pain.',
            'accent_hex': '#0284C7',
            'gradient_from': '#0369A1',
            'gradient_to': '#06B6D4',
            'secondary_wave': '#CFFAFE',
            'glow_color': 'bg-cyan-100/50',
            'dot_color': '#0284C7',
        },
        {
            'name': 'Glimepiride',
            'clean_title': 'Glimepiride 4MG',
            'category_name': 'Endocrinology & Diabetes Care',
            'formulation': 'Oral Tablet • 4 mg',
            'generic_name': 'Glimepiride (Sulfonylurea)',
            'standard': 'Standard International Batch',
            'image_url': '/media/branding/slider/glimepiride.jpg',
            'slug': 'glimepiride-4mg',
            'description': 'Third-generation sulfonylurea oral antidiabetic formulation providing targeted pancreatic stimulation for optimal glycemic management.',
            'accent_hex': '#059669',
            'gradient_from': '#047857',
            'gradient_to': '#34D399',
            'secondary_wave': '#D1FAE5',
            'glow_color': 'bg-emerald-100/50',
            'dot_color': '#059669',
        },
        {
            'name': 'Levothyroxine',
            'clean_title': 'Levothyroxine',
            'category_name': 'Thyroid & Endocrine Care',
            'formulation': 'Microgram Tablet • 100 mcg',
            'generic_name': 'Levothyroxine Sodium',
            'standard': 'High-Precision Batch Monograph',
            'image_url': '/media/branding/slider/levothyroxine.jpg',
            'slug': 'levothyroxine',
            'description': 'Pure synthetic crystalline thyroid hormone replacer matching endogenous T4 physiology for precise long-term hypothyroidism management.',
            'accent_hex': '#BE185D',
            'gradient_from': '#9D174D',
            'gradient_to': '#F472B6',
            'secondary_wave': '#FCE7F3',
            'glow_color': 'bg-pink-100/50',
            'dot_color': '#BE185D',
        },
        {
            'name': 'Atrovent',
            'clean_title': 'Atrovent',
            'category_name': 'Pulmonology & Respiratory Care',
            'formulation': 'Inhalation Aerosol • 20 mcg',
            'generic_name': 'Ipratropium Bromide',
            'standard': 'Aerosol Inhalation Standard',
            'image_url': '/media/branding/slider/atrovent.jpg',
            'slug': 'atrovent',
            'description': 'Potent anticholinergic bronchodilator aerosol engineered for rapid airway relaxation and maintenance treatment of bronchospasm.',
            'accent_hex': '#0D9488',
            'gradient_from': '#0F766E',
            'gradient_to': '#2DD4BF',
            'secondary_wave': '#CCFBF1',
            'glow_color': 'bg-teal-100/50',
            'dot_color': '#0D9488',
        },
        {
            'name': 'Aplenzin',
            'clean_title': 'Aplenzin',
            'category_name': 'Therapeutics & Smoking Cessation',
            'formulation': 'Extended-Release Tablet • 174 mg',
            'generic_name': 'Bupropion Hydrobromide',
            'standard': 'Extended Delivery Matrix',
            'image_url': '/media/branding/slider/aplenzin.jpg',
            'slug': 'aplenzin',
            'description': 'Specialized dual norepinephrine-dopamine reuptake inhibitor (NDRI) matrix designed for once-daily extended therapeutic bioavailability.',
            'accent_hex': '#D97706',
            'gradient_from': '#B45309',
            'gradient_to': '#FBBF24',
            'secondary_wave': '#FEF3C7',
            'glow_color': 'bg-amber-100/50',
            'dot_color': '#D97706',
        },
        {
            'name': 'Ascorbic Acid C',
            'clean_title': 'Ascorbic Acid C',
            'category_name': 'Vitamins & Clinical Nutrition',
            'formulation': 'Nutritional Supplement • 1000 mg',
            'generic_name': 'Ascorbic Acid (Vitamin C)',
            'standard': 'USP Nutritional Grade',
            'image_url': '/media/branding/slider/ascorbic_acid.jpg',
            'slug': 'ascorbic-acid-c',
            'description': 'High-purity essential water-soluble antioxidant formulation supporting immune defense, collagen biosynthesis, and cellular integrity.',
            'accent_hex': '#EA580C',
            'gradient_from': '#C2410C',
            'gradient_to': '#FB923C',
            'secondary_wave': '#FFEDD5',
            'glow_color': 'bg-orange-100/50',
            'dot_color': '#EA580C',
        },
    ]
    return banners

def home(request):
    categories = get_categories_with_counts()[:12]
    banner_medicines = get_banner_medicines()
    all_gallery_medicines = get_all_gallery_medicines()
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
        'banner_medicines': banner_medicines,
        'all_gallery_medicines': all_gallery_medicines,
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

def contact(request):
    return render(request, 'contact.html')
