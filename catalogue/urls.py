from django.urls import path
from . import views

app_name = 'catalogue'

urlpatterns = [
    path('', views.home, name='home'),
    path('medicines/', views.medicine_list, name='medicine_list'),
    path('medicines/<slug:slug>/', views.medicine_detail, name='medicine_detail'),
    path('health-categories/', views.category_list, name='category_list'),
    path('health-categories/<slug:slug>/', views.category_detail, name='category_detail'),
    path('health-categories/<slug:category_slug>/<slug:condition_slug>/', views.condition_detail, name='condition_detail'),
    path('search/', views.search, name='search'),
    path('api/search-suggest/', views.search_suggest, name='search_suggest'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
]
