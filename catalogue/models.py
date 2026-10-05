from django.db import models
from django.utils.text import slugify

class Manufacturer(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class HealthCategory(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    source_folder = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    icon = models.ImageField(upload_to='categories/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_ui_theme(self):
        """Returns corporate medical icon, colors, and badge styling for the category."""
        slug = (self.slug or slugify(self.name)).lower()
        themes = {
            'cancer': {
                'icon': 'fas fa-ribbon',
                'bg_gradient': 'from-purple-500/10 via-fuchsia-500/15 to-purple-500/5',
                'text_color': 'text-purple-600',
                'border_color': 'border-purple-200/80 group-hover:border-purple-500',
                'badge_bg': 'bg-purple-50 text-purple-700 border-purple-200/60',
                'icon_bg': 'bg-gradient-to-br from-purple-100 to-fuchsia-50 text-purple-600 group-hover:from-purple-600 group-hover:to-fuchsia-600 group-hover:text-white',
            },
            'vitamins-supplements': {
                'icon': 'fas fa-capsules',
                'bg_gradient': 'from-emerald-500/10 via-teal-500/15 to-emerald-500/5',
                'text_color': 'text-emerald-600',
                'border_color': 'border-emerald-200/80 group-hover:border-emerald-500',
                'badge_bg': 'bg-emerald-50 text-emerald-700 border-emerald-200/60',
                'icon_bg': 'bg-gradient-to-br from-emerald-100 to-teal-50 text-emerald-600 group-hover:from-emerald-600 group-hover:to-teal-600 group-hover:text-white',
            },
            'diabetes': {
                'icon': 'fas fa-syringe',
                'bg_gradient': 'from-blue-500/10 via-sky-500/15 to-blue-500/5',
                'text_color': 'text-blue-600',
                'border_color': 'border-blue-200/80 group-hover:border-blue-500',
                'badge_bg': 'bg-blue-50 text-blue-700 border-blue-200/60',
                'icon_bg': 'bg-gradient-to-br from-blue-100 to-sky-50 text-blue-600 group-hover:from-blue-600 group-hover:to-sky-600 group-hover:text-white',
            },
            'heart-health': {
                'icon': 'fas fa-heart-pulse',
                'bg_gradient': 'from-rose-500/10 via-red-500/15 to-rose-500/5',
                'text_color': 'text-rose-600',
                'border_color': 'border-rose-200/80 group-hover:border-rose-500',
                'badge_bg': 'bg-rose-50 text-rose-700 border-rose-200/60',
                'icon_bg': 'bg-gradient-to-br from-rose-100 to-red-50 text-rose-600 group-hover:from-rose-600 group-hover:to-red-600 group-hover:text-white',
            },
            'respiratory-health': {
                'icon': 'fas fa-lungs',
                'bg_gradient': 'from-cyan-500/10 via-sky-500/15 to-cyan-500/5',
                'text_color': 'text-cyan-600',
                'border_color': 'border-cyan-200/80 group-hover:border-cyan-500',
                'badge_bg': 'bg-cyan-50 text-cyan-700 border-cyan-200/60',
                'icon_bg': 'bg-gradient-to-br from-cyan-100 to-sky-50 text-cyan-600 group-hover:from-cyan-600 group-hover:to-sky-600 group-hover:text-white',
            },
            'sexual-health': {
                'icon': 'fas fa-venus-mars',
                'bg_gradient': 'from-pink-500/10 via-rose-500/15 to-pink-500/5',
                'text_color': 'text-pink-600',
                'border_color': 'border-pink-200/80 group-hover:border-pink-500',
                'badge_bg': 'bg-pink-50 text-pink-700 border-pink-200/60',
                'icon_bg': 'bg-gradient-to-br from-pink-100 to-rose-50 text-pink-600 group-hover:from-pink-600 group-hover:to-rose-600 group-hover:text-white',
            },
            'digestive-health': {
                'icon': 'fas fa-shield-halved',
                'bg_gradient': 'from-amber-500/10 via-orange-500/15 to-amber-500/5',
                'text_color': 'text-amber-600',
                'border_color': 'border-amber-200/80 group-hover:border-amber-500',
                'badge_bg': 'bg-amber-50 text-amber-700 border-amber-200/60',
                'icon_bg': 'bg-gradient-to-br from-amber-100 to-orange-50 text-amber-600 group-hover:from-amber-600 group-hover:to-orange-600 group-hover:text-white',
            },
            'kidney-health': {
                'icon': 'fas fa-flask-vial',
                'bg_gradient': 'from-teal-500/10 via-cyan-500/15 to-teal-500/5',
                'text_color': 'text-teal-600',
                'border_color': 'border-teal-200/80 group-hover:border-teal-500',
                'badge_bg': 'bg-teal-50 text-teal-700 border-teal-200/60',
                'icon_bg': 'bg-gradient-to-br from-teal-100 to-cyan-50 text-teal-600 group-hover:from-teal-600 group-hover:to-cyan-600 group-hover:text-white',
            },
            'skin-health': {
                'icon': 'fas fa-spa',
                'bg_gradient': 'from-orange-500/10 via-amber-500/15 to-orange-500/5',
                'text_color': 'text-orange-600',
                'border_color': 'border-orange-200/80 group-hover:border-orange-500',
                'badge_bg': 'bg-orange-50 text-orange-700 border-orange-200/60',
                'icon_bg': 'bg-gradient-to-br from-orange-100 to-amber-50 text-orange-600 group-hover:from-orange-600 group-hover:to-amber-600 group-hover:text-white',
            },
            'eye-care': {
                'icon': 'fas fa-eye',
                'bg_gradient': 'from-indigo-500/10 via-blue-500/15 to-indigo-500/5',
                'text_color': 'text-indigo-600',
                'border_color': 'border-indigo-200/80 group-hover:border-indigo-500',
                'badge_bg': 'bg-indigo-50 text-indigo-700 border-indigo-200/60',
                'icon_bg': 'bg-gradient-to-br from-indigo-100 to-blue-50 text-indigo-600 group-hover:from-indigo-600 group-hover:to-blue-600 group-hover:text-white',
            },
            'womens-health': {
                'icon': 'fas fa-venus',
                'bg_gradient': 'from-fuchsia-500/10 via-pink-500/15 to-fuchsia-500/5',
                'text_color': 'text-fuchsia-600',
                'border_color': 'border-fuchsia-200/80 group-hover:border-fuchsia-500',
                'badge_bg': 'bg-fuchsia-50 text-fuchsia-700 border-fuchsia-200/60',
                'icon_bg': 'bg-gradient-to-br from-fuchsia-100 to-pink-50 text-fuchsia-600 group-hover:from-fuchsia-600 group-hover:to-pink-600 group-hover:text-white',
            },
            'pain-relief': {
                'icon': 'fas fa-bolt-lightning',
                'bg_gradient': 'from-red-500/10 via-rose-500/15 to-red-500/5',
                'text_color': 'text-red-600',
                'border_color': 'border-red-200/80 group-hover:border-red-500',
                'badge_bg': 'bg-red-50 text-red-700 border-red-200/60',
                'icon_bg': 'bg-gradient-to-br from-red-100 to-rose-50 text-red-600 group-hover:from-red-600 group-hover:to-rose-600 group-hover:text-white',
            },
            'allergy-medicine': {
                'icon': 'fas fa-head-side-cough',
                'bg_gradient': 'from-emerald-500/10 via-teal-500/15 to-emerald-500/5',
                'text_color': 'text-emerald-600',
                'border_color': 'border-emerald-200/80 group-hover:border-emerald-500',
                'badge_bg': 'bg-emerald-50 text-emerald-700 border-emerald-200/60',
                'icon_bg': 'bg-gradient-to-br from-emerald-100 to-teal-50 text-emerald-600 group-hover:from-emerald-600 group-hover:to-teal-600 group-hover:text-white',
            },
            'anticovulsant': {
                'icon': 'fas fa-brain',
                'bg_gradient': 'from-violet-500/10 via-purple-500/15 to-violet-500/5',
                'text_color': 'text-violet-600',
                'border_color': 'border-violet-200/80 group-hover:border-violet-500',
                'badge_bg': 'bg-violet-50 text-violet-700 border-violet-200/60',
                'icon_bg': 'bg-gradient-to-br from-violet-100 to-purple-50 text-violet-600 group-hover:from-violet-600 group-hover:to-purple-600 group-hover:text-white',
            },
            'asthma-medicine': {
                'icon': 'fas fa-wind',
                'bg_gradient': 'from-sky-500/10 via-blue-500/15 to-sky-500/5',
                'text_color': 'text-sky-600',
                'border_color': 'border-sky-200/80 group-hover:border-sky-500',
                'badge_bg': 'bg-sky-50 text-sky-700 border-sky-200/60',
                'icon_bg': 'bg-gradient-to-br from-sky-100 to-blue-50 text-sky-600 group-hover:from-sky-600 group-hover:to-blue-600 group-hover:text-white',
            },
            'antidepressants-medicine': {
                'icon': 'fas fa-brain',
                'bg_gradient': 'from-indigo-500/10 via-violet-500/15 to-indigo-500/5',
                'text_color': 'text-indigo-600',
                'border_color': 'border-indigo-200/80 group-hover:border-indigo-500',
                'badge_bg': 'bg-indigo-50 text-indigo-700 border-indigo-200/60',
                'icon_bg': 'bg-gradient-to-br from-indigo-100 to-violet-50 text-indigo-600 group-hover:from-indigo-600 group-hover:to-violet-600 group-hover:text-white',
            },
            'birth-control-medicine': {
                'icon': 'fas fa-shield-heart',
                'bg_gradient': 'from-pink-500/10 via-rose-500/15 to-pink-500/5',
                'text_color': 'text-pink-600',
                'border_color': 'border-pink-200/80 group-hover:border-pink-500',
                'badge_bg': 'bg-pink-50 text-pink-700 border-pink-200/60',
                'icon_bg': 'bg-gradient-to-br from-pink-100 to-rose-50 text-pink-600 group-hover:from-pink-600 group-hover:to-rose-600 group-hover:text-white',
            },
            'blood-pressure-medicine': {
                'icon': 'fas fa-heart-circle-bolt',
                'bg_gradient': 'from-rose-500/10 via-red-500/15 to-rose-500/5',
                'text_color': 'text-rose-600',
                'border_color': 'border-rose-200/80 group-hover:border-rose-500',
                'badge_bg': 'bg-rose-50 text-rose-700 border-rose-200/60',
                'icon_bg': 'bg-gradient-to-br from-rose-100 to-red-50 text-rose-600 group-hover:from-rose-600 group-hover:to-red-600 group-hover:text-white',
            },
            'cholesterol': {
                'icon': 'fas fa-dna',
                'bg_gradient': 'from-amber-500/10 via-yellow-500/15 to-amber-500/5',
                'text_color': 'text-amber-600',
                'border_color': 'border-amber-200/80 group-hover:border-amber-500',
                'badge_bg': 'bg-amber-50 text-amber-700 border-amber-200/60',
                'icon_bg': 'bg-gradient-to-br from-amber-100 to-yellow-50 text-amber-600 group-hover:from-amber-600 group-hover:to-yellow-600 group-hover:text-white',
            },
            'stop-smoking-medicine': {
                'icon': 'fas fa-ban-smoking',
                'bg_gradient': 'from-slate-500/10 via-gray-500/15 to-slate-500/5',
                'text_color': 'text-slate-700',
                'border_color': 'border-slate-300 group-hover:border-slate-500',
                'badge_bg': 'bg-slate-100 text-slate-800 border-slate-200',
                'icon_bg': 'bg-gradient-to-br from-slate-200 to-gray-100 text-slate-700 group-hover:from-slate-700 group-hover:to-gray-800 group-hover:text-white',
            },
            'thyroid-medicine': {
                'icon': 'fas fa-shield-halved',
                'bg_gradient': 'from-teal-500/10 via-emerald-500/15 to-teal-500/5',
                'text_color': 'text-teal-600',
                'border_color': 'border-teal-200/80 group-hover:border-teal-500',
                'badge_bg': 'bg-teal-50 text-teal-700 border-teal-200/60',
                'icon_bg': 'bg-gradient-to-br from-teal-100 to-emerald-50 text-teal-600 group-hover:from-teal-600 group-hover:to-emerald-600 group-hover:text-white',
            },
        }
        return themes.get(slug, {
            'icon': 'fas fa-notes-medical',
            'bg_gradient': 'from-blue-500/10 via-cyan-500/15 to-blue-500/5',
            'text_color': 'text-primary',
            'border_color': 'border-blue-200/80 group-hover:border-primary',
            'badge_bg': 'bg-blue-50 text-primary border-blue-200/60',
            'icon_bg': 'bg-gradient-to-br from-blue-100 to-cyan-50 text-primary group-hover:from-primary group-hover:to-blue-700 group-hover:text-white',
        })

    @property
    def get_images(self):
        from .models import CategoryImage
        return CategoryImage.objects.filter(
            models.Q(category=self) | models.Q(categories=self),
            is_active=True
        ).distinct()

    @property
    def item_count(self):
        if hasattr(self, '_item_count') and self._item_count is not None:
            return self._item_count
        img_count = self.get_images.count()
        if img_count > 0:
            return img_count
        med_count = self.primary_medicines.filter(is_active=True).count() or self.all_medicines.filter(is_active=True).count()
        if med_count > 0:
            return med_count
        return self.conditions.count() or 5

    def get_image_url(self):
        """Returns the dedicated medical visual image for this category."""
        slug = (self.slug or slugify(self.name)).lower()
        mapping = {
            'cancer': 'cancer.webp',
            'sexual-health': 'sexual-health.webp',
            'antidepressants-medicine': 'antidepressants-medicine.webp',
            'antidepressants': 'antidepressants-medicine.webp',
            'heart-health': 'heart-health.webp',
            'respiratory-health': 'respiratory-health.webp',
            'blood-pressure-medicine': 'blood-pressure-medicine.webp',
            'blood-pressure': 'blood-pressure-medicine.webp',
            'vitamins-supplements': 'vitamins-supplements.webp',
            'vitamins': 'vitamins-supplements.webp',
            'pain-relief': 'pain-relief.webp',
            'asthma-medicine': 'asthma-medicine.webp',
            'asthma': 'asthma-medicine.webp',
            'diabetes': 'diabetes.webp',
            'womens-health': 'womens-health.webp',
            'allergy-medicine': 'allergy-medicine.webp',
            'allergy': 'allergy-medicine.webp',
            'anticovulsant': 'anticovulsant.webp',
            'birth-control-medicine': 'birth-control-medicine.webp',
            'cholesterol': 'cholesterol.webp',
            'stop-smoking-medicine': 'stop-smoking-medicine.webp',
            'thyroid-medicine': 'thyroid-medicine.webp',
            'digestive-health': 'digestive-health.webp',
            'kidney-health': 'kidney-health.webp',
            'skin-health': 'skin-health.webp',
            'eye-care': 'eye-care.webp',
        }
        filename = mapping.get(slug, f"{slug}.webp")
        return f"/static/images/health-categories/{filename}"

    @property
    def image_url(self):
        return self.get_image_url()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Health Categories"

class CategoryImage(models.Model):
    category = models.ForeignKey(HealthCategory, on_delete=models.CASCADE, related_name='category_images', null=True, blank=True)
    categories = models.ManyToManyField(HealthCategory, related_name='all_category_images', blank=True)
    medicine = models.ForeignKey('Medicine', on_delete=models.SET_NULL, null=True, blank=True, related_name='category_image_assets')
    image = models.ImageField(upload_to='category_images/')
    image_hash = models.CharField(max_length=64, unique=True, db_index=True)
    file_name = models.CharField(max_length=255)
    file_path = models.CharField(max_length=500, blank=True)
    file_size = models.BigIntegerField(default=0)
    is_primary = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_primary', 'file_name']

    @property
    def clean_title(self):
        import os, re
        base = os.path.splitext(self.file_name)[0]
        # Clean up common file patterns (e.g. TAB, CAP, underscores)
        base = re.sub(r'[\-_]+', ' ', base)
        base = re.sub(r'\s+', ' ', base).strip()
        return base.title()

    @property
    def get_medicine_slug(self):
        if self.medicine:
            return self.medicine.slug
        from django.utils.text import slugify
        return slugify(self.clean_title)

    def __str__(self):
        cat_name = self.category.name if self.category else "Uncategorized"
        return f"{cat_name} - {self.file_name} ({self.image_hash[:8]})"

class HealthCondition(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    description = models.TextField(blank=True)
    category = models.ForeignKey(HealthCategory, on_delete=models.CASCADE, related_name='conditions')
    icon = models.ImageField(upload_to='conditions/', blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Medicine(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    generic_name = models.CharField(max_length=255, blank=True)
    composition = models.TextField(blank=True)
    form = models.CharField(max_length=100, blank=True) # e.g. Tablet, Capsule, Syrup
    manufacturer = models.ForeignKey(Manufacturer, on_delete=models.CASCADE, related_name='medicines')
    
    # Categories and Conditions
    category = models.ForeignKey(HealthCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='primary_medicines')
    subcategory = models.ForeignKey(HealthCondition, on_delete=models.SET_NULL, null=True, blank=True, related_name='primary_medicines')
    
    categories = models.ManyToManyField(HealthCategory, related_name='all_medicines', blank=True)
    conditions = models.ManyToManyField(HealthCondition, related_name='all_medicines', blank=True)
    
    description = models.TextField(blank=True)
    overview = models.TextField(blank=True)
    uses = models.TextField(blank=True)
    how_it_works = models.TextField(blank=True)
    side_effects = models.TextField(blank=True)
    precautions = models.TextField(blank=True)
    storage = models.TextField(blank=True)
    also_known_as = models.CharField(max_length=255, blank=True)
    pack_size = models.CharField(max_length=100, blank=True)
    
    brand_name = models.CharField(max_length=255, blank=True)
    strength = models.CharField(max_length=100, blank=True)
    route = models.CharField(max_length=100, default='Oral', blank=True)
    active_ingredients = models.TextField(blank=True)
    inactive_ingredients = models.TextField(blank=True)
    dosage_information = models.TextField(blank=True)
    serious_side_effects = models.TextField(blank=True)
    contraindications = models.TextField(blank=True)
    interactions = models.TextField(blank=True)
    
    # Verification & Source metadata
    source_name = models.CharField(max_length=255, default='FDA / DailyMed / NLM', blank=True)
    source_url = models.URLField(max_length=500, default='https://dailymed.nlm.nih.gov/', blank=True)
    last_verified_at = models.DateField(null=True, blank=True)
    faqs = models.JSONField(default=list, blank=True)
    
    prescription_required = models.BooleanField(default=False)
    drug_type = models.CharField(max_length=100, blank=True)
    habit_forming = models.BooleanField(default=False)
    pregnancy_category = models.CharField(max_length=50, blank=True)
    alcohol_interaction = models.CharField(max_length=255, blank=True)
    
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        if not self.strength and any(c.isdigit() for c in self.name):
            import re
            m = re.search(r'\b\d+(\.\d+)?\s*(mg|mcg|gm|ml|iu|k)?\b', self.name, re.IGNORECASE)
            if m:
                self.strength = m.group(0).strip()
        super().save(*args, **kwargs)

    @property
    def get_display_image_url(self):
        # Tier 1: Directly linked real CategoryImage asset (in-memory if prefetched, otherwise query)
        if hasattr(self, '_prefetched_objects_cache') and 'category_image_assets' in self._prefetched_objects_cache:
            for direct_asset in self.category_image_assets.all():
                if direct_asset.is_active and direct_asset.image:
                    return direct_asset.image.url
        else:
            direct_asset = self.category_image_assets.filter(is_active=True).first()
            if direct_asset and direct_asset.image:
                return direct_asset.image.url

        # Explicit MedicineImage if present
        if hasattr(self, '_prefetched_objects_cache') and 'images' in self._prefetched_objects_cache:
            for first_img in self.images.all():
                if getattr(first_img, 'is_primary', False) and first_img.image:
                    return first_img.image.url
            for first_img in self.images.all():
                if first_img.image:
                    return first_img.image.url
        else:
            first_img = self.images.filter(is_primary=True).first() or self.images.first()
            if first_img and first_img.image:
                return first_img.image.url

        # Determine category
        cat_to_check = self.category
        if not cat_to_check:
            if hasattr(self, '_prefetched_objects_cache') and 'categories' in self._prefetched_objects_cache:
                cat_list = self.categories.all()
                cat_to_check = cat_list[0] if cat_list else None
            elif self.categories.exists():
                cat_to_check = self.categories.first()

        # Tier 2: Exact or high-confidence keyword match in real CategoryImages
        import re
        med_keywords = [
            w.lower() for w in re.split(r'[\s\-_,]+', self.name + ' ' + (self.generic_name or ''))
            if len(w) > 2 and not re.match(r'^\d+(mg|ml|gm|mcg|k)?$', w.lower())
        ]

        from .models import CategoryImage
        if cat_to_check and med_keywords:
            cat_images = CategoryImage.objects.filter(
                models.Q(category=cat_to_check) | models.Q(categories=cat_to_check),
                is_active=True
            ).distinct()

            for cat_img in cat_images:
                fn_lower = cat_img.file_name.lower()
                if any(kw in fn_lower for kw in med_keywords):
                    if cat_img.image:
                        return cat_img.image.url

        # Fallback to empty string if no authentic matching image found (never show wrong drug image)
        return ""

    def __str__(self):
        return self.name

class MedicineImage(models.Model):
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='medicines/')
    is_primary = models.BooleanField(default=False)

    def __str__(self):
        return f"Image for {self.medicine.name}"
